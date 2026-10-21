import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { createRemoteJWKSet, jwtVerify } from "https://esm.sh/jose@5.9.6";

// This source mirrors the currently deployed bridge. It is not yet wired into
// dispatch-brain-relay or the relay workflow; do not treat private transport as live.
const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
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
    const { data: row, error } = await db.from("brain_worker_runs")
      .select("id,request_payload,status").eq("id", runId).maybeSingle();
    if (error) return reply({ error: "Could not read private relay job." }, 500);
    if (!row) return reply({ error: "Private relay job not found." }, 404);
    if (!["queued", "running"].includes(row.status)) return reply({ error: "Private relay job is no longer available." }, 409);
    const { error: updateError } = await db.from("brain_worker_runs")
      .update({ status: "running", started_at: new Date().toISOString() }).eq("id", runId);
    if (updateError) return reply({ error: "Could not mark private relay job running." }, 500);
    return reply({ ok: true, payload: row.request_payload }, 200);
  }

  if (operation === "complete") {
    const result = input.result;
    if (!result || typeof result !== "object" || !Array.isArray((result as Record<string, unknown>).turns)) {
      return reply({ error: "Relay result packet is malformed." }, 400);
    }
    const packet = result as Record<string, unknown>;
    const outcome = String(packet.overall_outcome || "error");
    const status = outcome === "success" || outcome === "partial" ? "succeeded" : "failed";
    const errorCategory = outcome === "partial" ? "partial_provider_result" : outcome === "error" ? "all_providers_failed" : null;
    const { data: row, error: readError } = await db.from("brain_worker_runs")
      .select("id,status").eq("id", runId).maybeSingle();
    if (readError) return reply({ error: "Could not verify private relay job." }, 500);
    if (!row) return reply({ error: "Private relay job not found." }, 404);
    if (row.status === "succeeded" || row.status === "failed") return reply({ error: "Private relay result was already recorded." }, 409);
    const { error: updateError } = await db.from("brain_worker_runs").update({
      status, response_payload: packet, error_category: errorCategory, finished_at: new Date().toISOString(),
    }).eq("id", runId);
    if (updateError) return reply({ error: "Could not store private relay result." }, 500);
    return reply({ ok: true, status }, 200);
  }

  return reply({ error: "Operation must be claim or complete." }, 400);
});

function reply(body: Record<string, unknown>, status = 200) {
  return new Response(JSON.stringify(body), {
    status, headers: { ...corsHeaders, "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}
