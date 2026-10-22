import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { createRemoteJWKSet, jwtVerify } from "https://esm.sh/jose@5.9.6";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, x-brain-sync-version, x-supabase-api-version, x-supabase-auth-redirect, x-supabase-client-platform, x-supabase-client-version, x-supabase-client-runtime, x-supabase-client-runtime-version",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const jwks = createRemoteJWKSet(new URL("https://token.actions.githubusercontent.com/.well-known/jwks"));
const repo = "Astridrosexxx84/Astridrose-automation-";
const workflowRef = repo + "/.github/workflows/brain-app-relay.yml@refs/heads/main";

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  if (req.method !== "POST") return reply({ error: "POST required" }, 405);

  const bearer = (req.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  if (!bearer) return reply({ error: "GitHub Actions identity token required." }, 401);

  let claims: Record<string, unknown>;
  try {
    const verified = await jwtVerify(bearer, jwks, {
      issuer: "https://token.actions.githubusercontent.com",
      audience: "brain-app-relay",
    });
    claims = verified.payload as Record<string, unknown>;
  } catch {
    return reply({ error: "GitHub Actions identity token is invalid or expired." }, 401);
  }
  if (claims.repository !== repo || claims.ref !== "refs/heads/main" ||
      claims.workflow_ref !== workflowRef || claims.event_name !== "workflow_dispatch") {
    return reply({ error: "This GitHub workflow is not authorized to access the private relay." }, 403);
  }

  let input: Record<string, unknown>;
  try { input = await req.json(); } catch { return reply({ error: "Invalid JSON request." }, 400); }
  const runId = String(input.run_id || "");
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(runId)) {
    return reply({ error: "Invalid private relay run ID." }, 400);
  }

  const url = Deno.env.get("SUPABASE_URL");
  const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !serviceKey) return reply({ error: "Private relay backend is not configured." }, 500);
  const db = createClient(url, serviceKey, { auth: { persistSession: false } });
  const operation = String(input.operation || "");

  if (operation === "claim") {
    // Resolve the owner without exposing task content; recovery is scoped to that owner.
    const { data: target, error: targetError } = await db.from("brain_worker_runs")
      .select("id,owner_id").eq("id", runId).eq("status", "queued").maybeSingle();
    if (targetError) return reply({ error: "Could not inspect private relay job." }, 500);
    if (!target) return reply({ error: "Private relay job is missing or already claimed." }, 409);

    // Reconcile abandoned work before claiming the new run. The workflow timeout is
    // 15 minutes, so queued jobs older than 15 minutes and running jobs older than
    // 30 minutes cannot be healthy current executions. Only status metadata changes.
    const timestamp = new Date().toISOString();
    const queuedCutoff = new Date(Date.now() - 15 * 60 * 1000).toISOString();
    const runningCutoff = new Date(Date.now() - 30 * 60 * 1000).toISOString();
    const { error: staleQueuedError } = await db.from("brain_worker_runs")
      .update({ status: "failed", error_category: "stale_queued_run_reconciled", finished_at: timestamp })
      .eq("owner_id", target.owner_id).eq("status", "queued")
      .lt("created_at", queuedCutoff).neq("id", runId);
    if (staleQueuedError) return reply({ error: "Could not reconcile abandoned queued runs." }, 500);
    const { error: staleRunningError } = await db.from("brain_worker_runs")
      .update({ status: "failed", error_category: "stale_running_run_reconciled", finished_at: timestamp })
      .eq("owner_id", target.owner_id).eq("status", "running")
      .lt("started_at", runningCutoff).neq("id", runId);
    if (staleRunningError) return reply({ error: "Could not reconcile abandoned running jobs." }, 500);

    // Atomic compare-and-set: only one runner may claim the new queued job.
    const { data: row, error } = await db.from("brain_worker_runs")
      .update({ status: "running", started_at: timestamp })
      .eq("id", runId).eq("status", "queued")
      .select("id,request_payload").maybeSingle();
    if (error) return reply({ error: "Could not claim private relay job." }, 500);
    if (!row) return reply({ error: "Private relay job is missing or already claimed." }, 409);
    return reply({ ok: true, payload: row.request_payload }, 200);
  }

  if (operation === "complete") {
    const result = input.result;
    if (!result || typeof result !== "object" || !Array.isArray((result as Record<string, unknown>).turns)) {
      return reply({ error: "Relay result packet is malformed." }, 400);
    }
    const serialized = JSON.stringify(result);
    if (serialized.length > 200000) return reply({ error: "Relay result packet is too large." }, 413);
    const packet = result as Record<string, unknown>;
    const outcome = String(packet.overall_outcome || "error");
    if (!["success", "partial", "error"].includes(outcome)) return reply({ error: "Unknown relay outcome." }, 400);
    const status = outcome === "success" || outcome === "partial" ? "succeeded" : "failed";
    const errorCategory = outcome === "partial" ? "partial_provider_result" : outcome === "error" ? "all_providers_failed" : null;
    // Successful/partial results must come from a claimed running job. An error packet may
    // also close a queued job when OIDC/claim failed before the runner could mark it running.
    // Never overwrite a terminal state or let a success bypass the claim step.
    let completion = db.from("brain_worker_runs").update({
      status, response_payload: packet, error_category: errorCategory, finished_at: new Date().toISOString(),
    }).eq("id", runId);
    completion = outcome === "error"
      ? completion.in("status", ["running", "queued"])
      : completion.eq("status", "running");
    const { data: row, error } = await completion.select("id").maybeSingle();
    if (error) return reply({ error: "Could not store private relay result." }, 500);
    if (!row) return reply({ error: "Private relay job is missing or already finished." }, 409);
    return reply({ ok: true, status }, 200);
  }

  return reply({ error: "Operation must be claim or complete." }, 400);
});

function reply(body: Record<string, unknown>, status = 200) {
  return new Response(JSON.stringify(body), {
    status, headers: { ...corsHeaders, "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}
