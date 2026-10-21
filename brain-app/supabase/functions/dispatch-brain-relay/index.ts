import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  if (req.method !== "POST") return reply({ error: "POST required" }, 405);

  const authHeader = req.headers.get("Authorization") || "";
  if (!authHeader.startsWith("Bearer ")) return reply({ error: "Sign in to the Brain App first." }, 401);

  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const anonKey = Deno.env.get("SUPABASE_ANON_KEY");
  const githubToken = Deno.env.get("BRAIN_APP_GITHUB_TOKEN");
  if (!supabaseUrl || !anonKey) return reply({ error: "Supabase function environment is incomplete." }, 500);
  if (!githubToken) return reply({ error: "Secure dispatch is not configured. No task was sent." }, 503);

  const supabase = createClient(supabaseUrl, anonKey, { global: { headers: { Authorization: authHeader } }, auth: { persistSession: false } });
  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) return reply({ error: "Your session could not be verified. Sign in again." }, 401);

  let input: Record<string, unknown>;
  try { input = await req.json(); } catch { return reply({ error: "Invalid JSON request." }, 400); }
  const task = String(input.task || "").trim();
  const provider = String(input.provider || "auto");
  const role = String(input.role || "continue");
  const priorPacket = String(input.prior_packet || "");
  const nextWorker = String(input.next_worker || "review the complete relay packet");
  const taskId = String(input.task_id || "");
  const projectId = String(input.project_id || "");
  if (!task || !taskId) return reply({ error: "A task description and saved task ID are required for private dispatch." }, 400);
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(taskId)) return reply({ error: "Invalid task ID." }, 400);
  if (task.length > 8000 || priorPacket.length > 20000) return reply({ error: "Task packet is too large. Shorten the task/context and retry." }, 413);
  if (!["auto", "openrouter", "gemini", "groq"].includes(provider)) return reply({ error: "Unsupported provider." }, 400);
  if (!["create", "continue", "review"].includes(role)) return reply({ error: "Unsupported worker role." }, 400);

  // RLS ensures the signed-in owner can only dispatch a task they own.
  const { data: ownedTask, error: taskError } = await supabase.from("brain_tasks")
    .select("id,project_id").eq("id", taskId).eq("owner_id", user.id).maybeSingle();
  if (taskError) return reply({ error: "Could not verify the saved task." }, 500);
  if (!ownedTask) return reply({ error: "This task is not saved to your private cloud workspace yet. Sync and retry." }, 403);
  if (projectId && ownedTask.project_id && projectId !== ownedTask.project_id) return reply({ error: "Task/project mismatch." }, 400);

  const { data: workerRun, error: runError } = await supabase.from("brain_worker_runs").insert({
    owner_id: user.id,
    task_id: taskId,
    provider,
    status: "queued",
    request_payload: { task, task_id: taskId, project_id: ownedTask.project_id || projectId, provider, role, prior_packet: priorPacket, next_worker: nextWorker }
  }).select("id").single();
  if (runError || !workerRun) return reply({ error: "Could not save a private relay request. Nothing was dispatched." }, 500);

  const owner = "Astridrosexxx84";
  const repo = "Astridrose-automation-";
  const workflow = "brain-app-relay.yml";
  const apiUrl = `https://api.github.com/repos/${owner}/${repo}/actions/workflows/${workflow}/dispatches`;
  const dispatch = await fetch(apiUrl, {
    method: "POST",
    headers: {
      "Accept": "application/vnd.github+json",
      "Authorization": `Bearer ${githubToken}`,
      "X-GitHub-Api-Version": "2022-11-28",
      "Content-Type": "application/json",
      "User-Agent": "Brain-App-Relay-Dispatcher"
    },
    body: JSON.stringify({ ref: "main", inputs: {
      // Public workflow inputs contain only a placeholder and the opaque run ID.
      task: "Private Brain App task — retrieve via authenticated relay bridge.",
      provider, role, prior_packet: "", next_worker: "private bridge", task_id: "", project_id: "",
      private_run_id: workerRun.id
    } })
  });
  if (!dispatch.ok) {
    await supabase.from("brain_worker_runs").update({ status: "failed", error_category: "github_dispatch_failed", finished_at: new Date().toISOString() }).eq("id", workerRun.id).eq("status", "queued");
    const detail = (await dispatch.text()).slice(0, 300);
    return reply({ error: `GitHub dispatch failed (HTTP ${dispatch.status}). The private request was marked failed.`, detail }, 502);
  }
  return reply({ ok: true, message: "Private relay dispatched. Task content was stored in the private workspace.", run_id: workerRun.id, workflow_url: `https://github.com/${owner}/${repo}/actions/workflows/${workflow}` }, 200);
});

function reply(body: Record<string, unknown>, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { ...corsHeaders, "Content-Type": "application/json", "Cache-Control": "no-store" } });
}
