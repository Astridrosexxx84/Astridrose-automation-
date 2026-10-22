(() => {
  "use strict";
  const KEY = "brain-app-mvp-v1";
  const $ = (id) => document.getElementById(id);
  const now = () => new Date().toISOString();
  const uid = () => (crypto && crypto.randomUUID) ? crypto.randomUUID() : String(Date.now()) + Math.random().toString(16).slice(2);
  const statuses = {waiting:"Waiting",working:"Working",handed_off:"Handed off",blocked:"Blocked",complete:"Complete"};
  let state = loadState();
  let selectedProjectId = state.projects[0]?.id || null;
  let selectedTaskId = state.tasks.find(t => t.projectId === selectedProjectId)?.id || null;
  let toastTimer;
  let relayDispatchedAt = null;

  // Free Supabase backend: browser uses only the public publishable key;
  // row-level security limits database access to the signed-in owner.
  const SUPABASE_URL = "https://cjqgdqcbtcwsgbbqrqcf.supabase.co";
  const SUPABASE_PUBLISHABLE_KEY = "sb_publishable__pFBwxTsfTJwEDIGVjhppQ_qKomVqf-";
  const cloudClient = window.supabase?.createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, {global:{headers:{"x-brain-sync-version":"1"}}});
  let cloudUser = null;
  let cloudReady = false;
  let syncingCloud = false;
  let cloudSyncPending = false;
  let cloudSyncTimer = null;

  function setCloudStatus(message, bad=false) {
    const el = $("cloudStatus");
    if (!el) return;
    el.textContent = message;
    el.className = bad ? "muted status-blocked" : "muted";
  }
  function scheduleCloudSync() {
    if (!cloudUser || !cloudReady || !cloudClient) return;
    if (syncingCloud) {
      // Do not lose edits/results that arrive while a cloud write is in flight.
      cloudSyncPending = true;
      return;
    }
    clearTimeout(cloudSyncTimer);
    cloudSyncTimer = setTimeout(() => syncLocalToCloud().catch(e => setCloudStatus("Cloud sync paused: " + (e.message || "network error"), true)), 900);
  }
  function toRemoteProject(p) {
    return {id:p.id, owner_id:cloudUser.id, name:p.name || "Untitled project", description:p.description || "", status:"active", created_at:p.createdAt || now(), updated_at:p.updatedAt || now(), sync_version:p.syncVersion || 1};
  }
  function toRemoteTask(t) {
    return {id:t.id, owner_id:cloudUser.id, project_id:t.projectId || null, title:t.name || "Untitled task", goal:t.goal || "", context:t.context || "", status:({waiting:"queued",working:"running",handed_off:"review",blocked:"blocked",complete:"completed"})[t.status] || "queued", priority:3, assigned_worker:t.worker || null, current_worker:t.worker || "", next_worker:t.nextWorker || "", result_summary:t.output || "", current_output:t.output || "", next_action:t.next || "", created_at:t.createdAt || now(), updated_at:t.updatedAt || now(), deleted_at:t.deletedAt || null, sync_version:t.syncVersion || 1};
  }
  function fromRemoteProject(p) {
    return {id:p.id,name:p.name,description:p.description || "",createdAt:p.created_at || now(),updatedAt:p.updated_at || now(),syncVersion:p.sync_version || 1};
  }
  function fromRemoteTask(t) {
    const status = ({queued:"waiting",running:"working",review:"handed_off",blocked:"blocked",completed:"complete",failed:"blocked",cancelled:"blocked"})[t.status] || "waiting";
    return {id:t.id,projectId:t.project_id,name:t.title,goal:t.goal || "",context:t.context || "",status,worker:t.current_worker || t.assigned_worker || "",nextWorker:t.next_worker || "",output:t.current_output || t.result_summary || "",next:t.next_action || "",createdAt:t.created_at || now(),updatedAt:t.updated_at || now(),deletedAt:t.deleted_at || null,syncVersion:t.sync_version || 1};
  }
  function mergeByFreshness(localItems, remoteItems) {
    const byId = new Map();
    for (const item of [...remoteItems, ...localItems]) {
      const prior = byId.get(item.id);
      // A remote deletion tombstone must beat stale copies from other devices,
      // regardless of their local clock or updatedAt value.
      if (prior?.deletedAt && !item.deletedAt) continue;
      if (item.deletedAt && !prior?.deletedAt) {
        byId.set(item.id, item);
        continue;
      }
      // A result recovered from a worker run can have an older finished_at
      // than the task row's last sync. Preserve that usable result over an
      // empty review/completed copy, but let a newer "working" retry clear it.
      const priorHasOutput = !!String(prior?.output || "").trim();
      const itemHasOutput = !!String(item.output || "").trim();
      const reviewStates = ["handed_off", "complete"];
      if (itemHasOutput && !priorHasOutput && reviewStates.includes(item.status) && reviewStates.includes(prior?.status)) {
        byId.set(item.id, item);
        continue;
      }
      if (priorHasOutput && !itemHasOutput && reviewStates.includes(prior.status) && reviewStates.includes(item.status)) continue;
      if (!prior || Date.parse(item.updatedAt || 0) >= Date.parse(prior.updatedAt || 0)) byId.set(item.id, item);
    }
    // Keep the revision from the copy that won the merge. Do not upgrade a
    // stale local edit to the newest remote revision: compare-and-set must reject it.
    return [...byId.values()].map(item => ({
      ...item,
      syncVersion: item.syncVersion || 1
    }));
  }
  function applySavedVersions(items, savedRows) {
    const byId = new Map((savedRows || []).map(row => [row.id, row]));
    for (const item of items) {
      const saved = byId.get(item.id);
      if (!saved) throw new Error("Cloud save was not confirmed; refresh before retrying.");
      // Do not replace the local edit timestamp with the server's write time.
      // A newer local edit may have arrived while the request was in flight.
      item.syncVersion = saved.sync_version;
    }
  }
  function differsFromRemoteProject(project, remote) {
    if (!remote) return true;
    const next = toRemoteProject(project);
    return ["name", "description", "status"].some(key => next[key] !== remote[key]);
  }
  function differsFromRemoteTask(task, remote) {
    if (!remote) return true;
    const next = toRemoteTask(task);
    return ["project_id", "title", "goal", "context", "status", "priority", "assigned_worker", "current_worker", "next_worker", "result_summary", "current_output", "next_action", "deleted_at"].some(key => (next[key] ?? null) !== (remote[key] ?? null));
  }
  async function syncLocalToCloud() {
    if (!cloudClient || !cloudUser) return;
    if (syncingCloud) {
      cloudSyncPending = true;
      return;
    }
    syncingCloud = true;
    try {
      // Pull the newest cloud state before writing. Otherwise an older device
      // can upsert its entire stale local workspace and overwrite newer edits
      // made elsewhere simply because it changed one unrelated task.
      const [remoteProjectsResult, remoteTasksResult] = await Promise.all([
        cloudClient.from("brain_projects").select("*").order("updated_at", {ascending:false}),
        cloudClient.from("brain_tasks").select("*").order("updated_at", {ascending:false})
      ]);
      if (remoteProjectsResult.error) throw remoteProjectsResult.error;
      if (remoteTasksResult.error) throw remoteTasksResult.error;
      const remoteProjects = remoteProjectsResult.data || [];
      const remoteTasks = remoteTasksResult.data || [];
      state.projects = mergeByFreshness(state.projects, remoteProjects.map(fromRemoteProject));
      state.tasks = mergeByFreshness(state.tasks, remoteTasks.map(fromRemoteTask)).filter(task => !task.deletedAt);
      const validProjectIds = new Set(state.projects.map(project => project.id));
      state.tasks = state.tasks.filter(task => validProjectIds.has(task.projectId));
      const remoteProjectsById = new Map(remoteProjects.map(row => [row.id, row]));
      const remoteTasksById = new Map(remoteTasks.map(row => [row.id, row]));
      const projectsToSync = state.projects.filter(project => differsFromRemoteProject(project, remoteProjectsById.get(project.id)));
      const tasksToSync = state.tasks.filter(task => differsFromRemoteTask(task, remoteTasksById.get(task.id)));
      try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (_) {}
      if (projectsToSync.length) {
        const {data, error} = await cloudClient.from("brain_projects").upsert(projectsToSync.map(toRemoteProject), {onConflict:"id"}).select("id,sync_version");
        if (error) throw error;
        applySavedVersions(projectsToSync, data);
      }
      if (tasksToSync.length) {
        const {data, error} = await cloudClient.from("brain_tasks").upsert(tasksToSync.map(toRemoteTask), {onConflict:"id"}).select("id,sync_version");
        if (error) throw error;
        applySavedVersions(tasksToSync, data);
      }
      try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (_) {}
      setCloudStatus("Cloud sync connected · saved to this device and Supabase");
    } finally {
      syncingCloud = false;
      // Flush changes that were requested during the in-flight write.
      if (cloudSyncPending && cloudReady) {
        cloudSyncPending = false;
        scheduleCloudSync();
      }
    }
  }
  async function applyPrivateRelayResults() {
    if (!cloudClient || !cloudUser || !state.tasks.length) return false;
    // Recover only tasks that can accept a relay result. A global latest-30 query
    // can silently miss an older in-flight task when other tasks run more often.
    const recoverableTasks = state.tasks.filter(task =>
      ["handed_off", "working"].includes(task.status) ||
      (task.status === "complete" && !String(task.output || "").trim())
    );
    if (!recoverableTasks.length) return false;
    const recoverableTaskIds = recoverableTasks.map(task => task.id);
    const { data: runs, error } = await cloudClient.from("brain_worker_runs")
      .select("id,task_id,status,response_payload,error_category,finished_at")
      .in("task_id", recoverableTaskIds)
      .in("status", ["succeeded", "failed"])
      .order("finished_at", {ascending:false});
    if (error) throw error;
    let changed = false;
    for (const run of runs || []) {
      const task = state.tasks.find(item => item.id === run.task_id);
      if (!task) continue;
      // A completed task can still be missing its output if an earlier cloud sync
      // persisted the status before the relay result. Recover that result even if
      // the task's sync timestamp is newer than the worker run's finish timestamp.
      const recoveringMissingOutput = ["handed_off", "working", "complete"].includes(task.status) && !String(task.output || "").trim();
      if (!["handed_off", "working"].includes(task.status) && !recoveringMissingOutput) continue;
      if (!recoveringMissingOutput && Date.parse(run.finished_at || 0) < Date.parse(task.updatedAt || 0)) continue;
      const packet = run.response_payload || {};
      const turns = Array.isArray(packet.turns) ? packet.turns : [];
      const outputs = turns.filter(turn => turn?.outcome === "success" && turn?.worker_output)
        .map(turn => "**" + String(turn.provider || "AI worker") + "**\\n" + String(turn.worker_output));
      task.output = outputs.join("\\n\\n") || (run.error_category ? "Relay failed: " + run.error_category : "Relay finished without a usable output.");
      task.status = run.status === "succeeded" ? "handed_off" : "blocked";
      task.next = String(packet.next_action || (run.status === "succeeded" ? "Verify the returned output against the goal and acceptance criteria before marking complete." : "Check the relay error and retry when ready."));
      task.worker = "Private AI relay";
      task.updatedAt = run.finished_at || now();
      changed = true;
    }
    if (changed) {
      try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (_) {}
    }
    return changed;
  }

  async function loadVerificationEvents() {
    if (!cloudClient || !cloudUser) return;
    const { data, error } = await cloudClient.from("brain_task_events")
      .select("id,task_id,event_type,details,created_at")
      .in("event_type", ["verification_passed", "verification_failed"])
      .order("created_at", {ascending:false}).limit(100);
    if (error) throw error;
    const latest = new Map();
    for (const event of data || []) {
      if (!latest.has(event.task_id)) latest.set(event.task_id, event);
    }
    for (const task of state.tasks) {
      const event = latest.get(task.id);
      if (!event) continue;
      const details = event.details || {};
      task.verification = {
        passed: event.event_type === "verification_passed",
        notes: String(details.notes || ""),
        criteria: String(details.acceptance_criteria || ""),
        at: event.created_at,
        reviewer: String(details.reviewer || "Signed-in owner"),
        source: String(details.source || "Brain App")
      };
    }
  }

  async function recordVerification(passed) {
    const task = currentTask();
    if (!task) return;
    if (!cloudClient || !cloudUser || !cloudReady) {
      toast("Sign in and wait for cloud sync before recording durable verification.");
      return;
    }
    const notes = $("verificationNotes").value.trim();
    if (!String(task.goal || "").trim()) {
      toast("Add the goal / acceptance criteria before verifying.");
      $("taskGoal").focus();
      return;
    }
    if (!String(task.output || "").trim()) {
      toast("There is no output to verify yet.");
      $("taskOutput").focus();
      return;
    }
    if (!notes) {
      toast("Add a short note describing what you checked.");
      $("verificationNotes").focus();
      return;
    }
    const timestamp = now();
    const eventType = passed ? "verification_passed" : "verification_failed";
    const details = {
      acceptance_criteria: task.goal,
      notes,
      output_present: true,
      outcome: passed ? "pass" : "fail",
      reviewer: "signed-in owner",
      source: "brain-app-verification-ui",
      verified_at: timestamp
    };
    const buttonIds = ["verifyPassBtn", "verifyFailBtn"];
    buttonIds.forEach(id => $(id).disabled = true);
    try {
      // Ensure the task and project exist remotely before writing an event with a
      // foreign key to the task. This also covers a brand-new local-only task.
      const project = state.projects.find(item => item.id === task.projectId);
      if (!project) throw new Error("Task project is missing; save or restore the project first.");
      const { data: savedProject, error: projectError } = await cloudClient.from("brain_projects").upsert(toRemoteProject(project), {onConflict:"id"}).select("id,sync_version").single();
      if (projectError) throw projectError;
      applySavedVersions([project], [savedProject]);
      const { data: savedTask, error: taskError } = await cloudClient.from("brain_tasks").upsert(toRemoteTask(task), {onConflict:"id"}).select("id,sync_version").single();
      if (taskError) throw taskError;
      applySavedVersions([task], [savedTask]);
      const { error } = await cloudClient.from("brain_task_events").insert({
        owner_id: cloudUser.id,
        task_id: task.id,
        event_type: eventType,
        details
      });
      if (error) throw error;
      task.verification = {passed, notes, criteria:task.goal, at:timestamp, reviewer:"Signed-in owner", source:"Brain App"};
      task.status = passed ? "complete" : "handed_off";
      task.next = passed
        ? "Verified against the stated goal by the signed-in owner. Choose the next goal."
        : "Verification failed. Address the recorded gap, update the output, then verify again.";
      task.updatedAt = timestamp;
      persist();
      render();
      renderVerification();
      setCloudStatus("Verification evidence saved privately to this task.");
      toast(passed ? "Verified and saved privately." : "Failure recorded privately; task remains open.");
    } catch (error) {
      setCloudStatus("Could not save verification evidence: " + (error.message || "unknown error"), true);
      toast("Verification was not saved. Check cloud sync and retry.");
    } finally {
      buttonIds.forEach(id => $(id).disabled = false);
    }
  }

  function proposeNextAction() {
    const task = currentTask();
    if (!task?.verification) {
      toast("Verify the current result first; proposals must be grounded in recorded evidence.");
      return;
    }
    const goal = String(task.goal || "").trim();
    const output = String(task.output || "").trim();
    const notes = String(task.verification.notes || "").trim();
    if (!goal || !output || !notes) {
      toast("A goal, output, and verification notes are required before proposing the next action.");
      return;
    }
    const excerpt = output.replace(/\s+/g, " ").slice(0, 240);
    task.next = task.verification.passed
      ? "PROPOSED NEXT ACTION — NOT EXECUTED. The signed-in owner marked the goal verified. Review the saved output for any broader project scope not covered by this goal; if none remains, define the next goal as a new task.\n\nEvidence basis — goal: " + goal + "\nVerified output excerpt: " + excerpt + "\nOwner's check: " + notes
      : "PROPOSED CORRECTIVE ACTION — NOT EXECUTED. Address the failed check before marking this task complete. Use the existing output as the starting point and change only what is needed to satisfy the goal.\n\nEvidence basis — goal: " + goal + "\nCurrent output excerpt: " + excerpt + "\nFailure notes: " + notes;
    task.updatedAt = now();
    persist();
    render();
    $("nextActionProposal").textContent = task.next;
    toast("Evidence-based next action proposed and saved; nothing was run.");
  }

  function renderVerification() {
    const task = currentTask();
    const evidence = task?.verification;
    $("verificationNotes").value = evidence?.notes || "";
    $("verificationEvidence").textContent = evidence
      ? (evidence.passed ? "PASS" : "FAIL") + " · " + new Date(evidence.at).toLocaleString() + " · " + evidence.reviewer + "\nCriteria: " + evidence.criteria + "\nChecked: " + evidence.notes
      : "No verification evidence recorded for this task yet.";
    $("verifyPassBtn").disabled = !task;
    $("verifyFailBtn").disabled = !task;
    $("proposeNextActionBtn").disabled = !evidence;
    $("nextActionProposal").textContent = evidence ? (task.next || "No next-action proposal saved yet.") : "Record a verification outcome first.";
  }

  async function mergeCloudWorkspace() {
    if (!cloudClient || !cloudUser) return;
    syncingCloud = true;
    cloudReady = false;
    setCloudStatus("Signing in · merging this device with your private cloud workspace…");
    try {
      const [pr, tr] = await Promise.all([
        cloudClient.from("brain_projects").select("*").order("updated_at",{ascending:false}),
        cloudClient.from("brain_tasks").select("*").order("updated_at",{ascending:false})
      ]);
      if (pr.error) throw pr.error;
      if (tr.error) throw tr.error;
      const remoteProjects = (pr.data || []).map(fromRemoteProject);
      const remoteTasks = (tr.data || []).map(fromRemoteTask);
      state.projects = mergeByFreshness(state.projects, remoteProjects);
      state.tasks = mergeByFreshness(state.tasks, remoteTasks);
      // Keep deletion tombstones in the database, but never re-upload/render them.
      state.tasks = state.tasks.filter(t => !t.deletedAt);
      const validProjects = new Set(state.projects.map(p=>p.id));
      state.tasks = state.tasks.filter(t=>validProjects.has(t.projectId));
      // Recover completed private relay outputs even if the app was closed while workers ran.
      await applyPrivateRelayResults();
      await loadVerificationEvents();
      // Persist the merged view locally before uploading any locally-only records.
      try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (_) {}
      syncingCloud = false;
      await syncLocalToCloud();
      syncingCloud = true;
      cloudReady = true;
      if (cloudSyncPending) {
        cloudSyncPending = false;
        scheduleCloudSync();
      }
      selectedProjectId = state.projects[0]?.id || null;
      selectedTaskId = state.tasks.find(t=>t.projectId===selectedProjectId)?.id || null;
      render();
      setCloudStatus("Cloud sync connected · workspace merged");
    } catch (e) {
      setCloudStatus("Cloud sync could not start: " + (e.message || "check connection and account"), true);
    } finally {
      syncingCloud = false;
      cloudReady = !!cloudUser;
    }
  }
  async function setupCloudAuth() {
    const authForm = $("authForm");
    authForm.addEventListener("submit", async e => {
      e.preventDefault();
      if (!cloudClient) {
        setCloudStatus("Cloud sign-in is unavailable because the Supabase library did not load. Check your connection and reload this page.", true);
        return;
      }
      const email = $("authEmail").value.trim();
      const password = $("authPassword").value;
      const action = e.submitter?.value || "signin";
      const buttons = [$("authSubmit"), $("authSignupBtn")];
      buttons.forEach(button => button.disabled = true);
      try {
        const result = action === "signup"
          ? await cloudClient.auth.signUp({email,password})
          : await cloudClient.auth.signInWithPassword({email,password});
        if (result.error) throw result.error;
        if (action === "signup" && !result.data.session) setCloudStatus("Account created. Check your email to confirm it, then sign in.");
        else if (result.data.user) {
          cloudUser = result.data.user;
          await mergeCloudWorkspace();
          setAuthUI();
        }
      } catch (err) {
        setCloudStatus((action === "signup" ? "Account creation failed: " : "Sign-in failed: ") + (err.message || "unknown error"), true);
      } finally { buttons.forEach(button => button.disabled = false); }
    });
    $("signOutBtn").addEventListener("click", async () => {
      if (!cloudClient) {
        setCloudStatus("Cloud sign-out is unavailable because the Supabase library did not load. Reload the page and try again.", true);
        return;
      }
      $("signOutBtn").disabled = true;
      try {
        const {error} = await cloudClient.auth.signOut();
        if (error) throw error;
        cloudUser = null; cloudReady = false; setAuthUI(); setCloudStatus("Signed out · workspace remains on this device");
      } catch (err) {
        setCloudStatus("Could not sign out: " + (err.message || "unknown error"), true);
      } finally { $("signOutBtn").disabled = false; }
    });
    if (!cloudClient) {
      setCloudStatus("Cloud sync unavailable: the Supabase library did not load. Sign-in controls will explain the problem if tapped; check your connection and reload.", true);
      return;
    }
    cloudClient.auth.onAuthStateChange((_event, session) => {
      cloudUser = session?.user || null;
      setAuthUI();
      if (cloudUser && !cloudReady) setTimeout(() => mergeCloudWorkspace(), 0);
      if (!cloudUser) { cloudReady = false; setCloudStatus("Not signed in · this device only"); }
    });
    const {data, error} = await cloudClient.auth.getSession();
    if (error) {
      setCloudStatus("Cloud session check failed: " + (error.message || "unknown error"), true);
      return;
    }
    cloudUser = data.session?.user || null;
    setAuthUI();
    if (cloudUser) await mergeCloudWorkspace();
    else setCloudStatus("Not signed in · sign in to enable private cloud sync");
  }
  function setAuthUI() {
    const signed = !!cloudUser;
    $("authEmail").hidden = signed;
    $("authPassword").hidden = signed;
    $("authSubmit").hidden = signed;
    $("authSignupBtn").hidden = signed;
    $("signOutBtn").hidden = !signed;
    $("authIdentity").textContent = signed ? "Signed in as " + cloudUser.email : "Sign in or create a free account";
  }


  function seedState() {
    const p = {id:uid(),name:"Brain App development",description:"Build the coordinator and sequential AI handoff system.",createdAt:now(),updatedAt:now()};
    const t = {id:uid(),projectId:p.id,name:"Build the first usable control room",status:"working",worker:"ChatGPT (manual build)",nextWorker:"Gemini / Groq / another verified free route",goal:"Create a usable app where separate projects and tasks persist, and work can be handed from one AI worker to the next without restarting.",context:"MVP is a static phone-first web app. Provider integrations must be verified before being shown as connected. Never put API keys in browser code.",output:"The initial project dashboard and packet editor are in place. Project and task data is stored in this browser and can be exported as JSON.",next:"Add a secure server-side/GitHub Actions worker runner, then test a real sequential relay: worker A creates an artifact, worker B continues it, worker C reviews it.",createdAt:now(),updatedAt:now()};
    return {version:1,projects:[p],tasks:[t]};
  }
  function loadState() {
    try {
      const raw = localStorage.getItem(KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && Array.isArray(parsed.projects) && Array.isArray(parsed.tasks)) return parsed;
      }
    } catch (e) { console.warn("Could not load local workspace", e); }
    return seedState();
  }
  function persist() {
    try { localStorage.setItem(KEY, JSON.stringify(state)); }
    catch (e) { toast("Browser storage is full or unavailable. Export a backup."); }
    scheduleCloudSync();
  }
  function esc(value) {
    return String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  }
  function toast(message) {
    $("toast").textContent = message;
    $("toast").classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => $("toast").classList.remove("show"), 2500);
  }
  function projectTasks(projectId) { return state.tasks.filter(t => t.projectId === projectId); }
  function currentTask() { return state.tasks.find(t => t.id === selectedTaskId && t.projectId === selectedProjectId); }
  function renderSimpleResult() {
    const task = state.tasks
      .filter(item => item.name === "Brain connection check" && String(item.goal || "").includes("BRAIN-APP-OK"))
      .sort((a, b) => Date.parse(b.updatedAt || b.createdAt || 0) - Date.parse(a.updatedAt || a.createdAt || 0))[0];
    const stateEl = $("simpleResultState");
    const outputEl = $("simpleResultOutput");
    const hintEl = $("simpleResultHint");
    if (!stateEl || !outputEl || !hintEl) return;
    if (!task) {
      stateEl.textContent = "Not run yet. Tap “Run a safe test” above.";
      stateEl.className = "simple-result-state";
      outputEl.textContent = "Your result will appear here automatically.";
      hintEl.textContent = "Expected answer: BRAIN-APP-OK. Tap “Run a safe test” to begin.";
      return;
    }
    const output = String(task.output || "").trim();
    const expectedFound = output.includes("BRAIN-APP-OK");
    const lastChanged = task.updatedAt || task.createdAt;
    const when = lastChanged && Number.isFinite(Date.parse(lastChanged)) ? new Date(lastChanged).toLocaleString() : "time unavailable";
    if (task.status === "blocked") {
      stateEl.textContent = "Test failed or was blocked. Run it again after checking the problem.";
      stateEl.className = "simple-result-state is-error";
    } else if (expectedFound) {
      stateEl.textContent = "Saved result says SUCCESS — last updated " + when + ".";
      stateEl.className = "simple-result-state is-success";
    } else if (output) {
      stateEl.textContent = "Result received — the expected answer was not found.";
      stateEl.className = "simple-result-state is-error";
    } else if (task.status === "handed_off" || task.status === "working") {
      stateEl.textContent = "Test is running or awaiting review. No fresh answer is available yet.";
      stateEl.className = "simple-result-state is-working";
    } else {
      stateEl.textContent = "Test is ready. Tap “Run a safe test” above.";
      stateEl.className = "simple-result-state";
    }
    outputEl.textContent = output || "No answer yet. Keep this page open; the result should appear here automatically.";
    hintEl.textContent = expectedFound
      ? "This is a saved result, last updated " + when + ". It is historical evidence, not proof that a new test ran just now. Run a new test to check again."
      : "Expected answer: BRAIN-APP-OK. You do not need to open the task queue or technical tools.";
  }

  function render() {
    if (!state.projects.some(p => p.id === selectedProjectId)) selectedProjectId = state.projects[0]?.id || null;
    if (!state.tasks.some(t => t.id === selectedTaskId && t.projectId === selectedProjectId)) {
      selectedTaskId = state.tasks.find(t => t.projectId === selectedProjectId)?.id || null;
    }
    const allOpen = state.tasks.filter(t => t.status !== "complete");
    $("projectCount").textContent = state.projects.length;
    $("openCount").textContent = allOpen.length;
    $("handoffCount").textContent = state.tasks.filter(t => t.status === "handed_off").length;
    $("projectList").innerHTML = state.projects.length ? state.projects.map(p => `<button type="button" class="project-card ${p.id===selectedProjectId?"selected":""}" data-project="${esc(p.id)}"><strong>${esc(p.name)}</strong><p>${esc(p.description || "No description yet")}</p><p>${projectTasks(p.id).length} tasks · Updated ${new Date(p.updatedAt).toLocaleDateString()}</p></button>`).join("") : '<div class="empty">No projects yet. Create one to start a workspace.</div>';
    const project = state.projects.find(p => p.id === selectedProjectId);
    $("selectedProjectTitle").textContent = project ? project.name : "Choose a project";
    $("newTaskBtn").disabled = !project;
    if (!project) {
      $("taskList").className = "task-list empty";
      $("taskList").textContent = "Create a project to start its task queue.";
    } else {
      const tasks = projectTasks(project.id);
      const taskQuery = $("taskSearch").value.trim().toLowerCase();
      const statusFilter = $("taskStatusFilter").value;
      const visibleTasks = tasks.filter(t => {
        if (statusFilter !== "all" && t.status !== statusFilter) return false;
        const haystack = [t.name, t.goal, t.context, t.output, t.next, t.worker, t.nextWorker].join(" ").toLowerCase();
        return !taskQuery || haystack.includes(taskQuery);
      });
      $("taskCount").textContent = visibleTasks.length === tasks.length
        ? `${tasks.length} ${tasks.length === 1 ? "task" : "tasks"}`
        : `${visibleTasks.length} of ${tasks.length} tasks`;
      $("taskList").className = "task-list";
      $("taskList").innerHTML = visibleTasks.length ? visibleTasks.map(t => `<button type="button" class="task-card ${t.id===selectedTaskId?"selected":""}" data-task="${esc(t.id)}"><span class="task-top"><strong>${esc(t.name)}</strong><span class="task-status status-${esc(t.status)}">${esc(statuses[t.status]||t.status)}</span></span><p>Next: ${esc(t.nextWorker || "Unassigned")} · ${esc(t.next || "No next action recorded")}</p></button>`).join("") : tasks.length ? '<div class="empty">No tasks match. Try another search or status.</div>' : '<div class="empty">Queue is empty. Add a specific task.</div>';
    }
    renderPacket();
    renderVerification();
    renderSimpleResult();
  }
  function renderPacket() {
    const t = currentTask();
    $("packetForm").hidden = !t;
    $("packetEmpty").hidden = !!t;
    $("packetStatus").textContent = t ? (statuses[t.status] || t.status) : "No task selected";
    if (!t) return;
    $("taskName").value = t.name || "";
    $("taskStatus").value = t.status || "waiting";
    $("taskWorker").value = t.worker || "";
    $("nextWorker").value = t.nextWorker || "";
    $("taskGoal").value = t.goal || "";
    $("taskContext").value = t.context || "";
    $("taskOutput").value = t.output || "";
    $("taskNext").value = t.next || "";
  }
  function syncPacketFromForm(trimValues=false) {
    const t = currentTask();
    if (!t) return false;
    // Keep raw text while typing so trailing spaces can be entered normally.
    const read = id => trimValues ? $(id).value.trim() : $(id).value;
    t.name = read("taskName");
    t.status = $("taskStatus").value;
    t.worker = read("taskWorker");
    t.nextWorker = read("nextWorker");
    t.goal = read("taskGoal");
    t.context = read("taskContext");
    t.output = read("taskOutput");
    t.next = read("taskNext");
    t.updatedAt = now();
    const p = state.projects.find(p => p.id === selectedProjectId);
    if (p) p.updatedAt = t.updatedAt;
    return true;
  }
  function savePacket(showMessage=true) {
    if (!syncPacketFromForm(true)) return false;
    persist(); render();
    if (showMessage) toast("Work packet saved.");
    return true;
  }
  // Persist edits as they happen without re-rendering the form (which would move the cursor).
  $("packetForm").addEventListener("input", () => {
    if (!syncPacketFromForm()) return;
    persist();
  });
  function packetText(t) {
    return ["BRAIN APP — PORTABLE WORK PACKET","",`Task: ${t.name}`,`Task ID: ${t.id}`,`Project: ${state.projects.find(p=>p.id===t.projectId)?.name || "Unknown"}`,`Status: ${statuses[t.status] || t.status}`,`Current worker: ${t.worker || "Unassigned"}`,`Next worker: ${t.nextWorker || "Unassigned"}`,"", "GOAL / DEFINITION OF DONE",t.goal || "(not set)","","CONTEXT / CONSTRAINTS / EVIDENCE",t.context || "(none)","","CURRENT OUTPUT / ARTIFACT",t.output || "(none)","","NEXT ACTION",t.next || "(not set)","","INSTRUCTIONS FOR NEXT WORKER: Continue from the actual artifact above. Do not restart completed work. Update the output and next action, record any tests/evidence, and hand off to the next worker. Respect verified free-tier limits."].join("\n");
  }
  $("newProjectBtn").addEventListener("click", () => { $("projectForm").reset(); $("projectDialog").showModal(); });
  $("projectForm").addEventListener("submit", e => {
    e.preventDefault();
    if (e.submitter?.value === "cancel") { $("projectDialog").close(); return; }
    const name = $("projectName").value.trim();
    if (!name) return;
    const p = {id:uid(),name,description:$("projectDescription").value.trim(),createdAt:now(),updatedAt:now()};
    state.projects.push(p); selectedProjectId = p.id; selectedTaskId = null;
    persist(); $("projectDialog").close(); render(); toast("Project created.");
  });
  $("newTaskBtn").addEventListener("click", () => { if (!selectedProjectId) return; $("taskForm").reset(); $("taskDialog").showModal(); });
  $("taskForm").addEventListener("submit", e => {
    e.preventDefault();
    if (e.submitter?.value === "cancel") { $("taskDialog").close(); return; }
    const name = $("newTaskName").value.trim(), goal = $("newTaskGoal").value.trim();
    if (!name || !goal) return;
    const t = {id:uid(),projectId:selectedProjectId,name,goal,status:"waiting",worker:"",nextWorker:"",context:"",output:"",next:"",createdAt:now(),updatedAt:now()};
    state.tasks.push(t); selectedTaskId = t.id;
    const p = state.projects.find(p=>p.id===selectedProjectId); if(p)p.updatedAt=now();
    persist(); $("taskDialog").close(); render(); toast("Task added to queue.");
  });
  $("showToolsBtn")?.addEventListener("click", () => {
    const simple = document.body.classList.toggle("simple-mode");
    const button = $("showToolsBtn");
    button.textContent = simple ? "Show all tools" : "Hide extra tools";
    button.setAttribute("aria-expanded", String(!simple));
  });
  $("quickTestBtn").addEventListener("click", () => {
    const button = $("quickTestBtn");
    if (button.disabled) return;
    let project = state.projects.find(p => p.id === selectedProjectId);
    if (!project) {
      project = {id:uid(),name:"My first Brain test",description:"A safe sample task to check the private AI workers.",createdAt:now(),updatedAt:now()};
      state.projects.push(project);
      selectedProjectId = project.id;
    }
    const existing = state.tasks.find(t => t.projectId === project.id && t.name === "Brain connection check" && t.goal.includes("BRAIN-APP-OK"));
    let task = existing;
    if (!task) {
      task = {id:uid(),projectId:project.id,name:"Brain connection check",goal:"Reply with exactly BRAIN-APP-OK. Do not use tools or external services.",status:"waiting",worker:"",nextWorker:"",context:"Safe sample task. Contains no private information.",output:"",next:"",createdAt:now(),updatedAt:now()};
      state.tasks.push(task);
    }
    selectedTaskId = task.id;
    // Clear the previous answer before dispatch so an old success cannot mask a new attempt.
    task.output = "";
    task.status = "working";
    task.updatedAt = now();
    persist(); render();
    $("quickTestStatus").textContent = "New test started. Waiting for a fresh answer…";
    button.disabled = true;
    button.textContent = "Starting your test…";
    $("runRelayBtn").click();
    setTimeout(() => {
      button.disabled = false;
      button.textContent = "▶ Run a safe test again";
      if (!$("simpleResultOutput").textContent.trim() || $("simpleResultOutput").textContent.includes("No answer yet")) {
        $("quickTestStatus").textContent = "Test started. Waiting for the answer in “Your test result” below.";
      }
    }, 1200);
  });
  // Mobile quick navigation keeps the two most-used work areas one tap apart.
  $("jumpQueueBtn")?.addEventListener("click", () => {
    document.querySelector(".tasks-panel")?.scrollIntoView({behavior:window.matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth",block:"start"});
    $("taskSearch")?.focus({preventScroll:true});
  });
  $("jumpDetailsBtn")?.addEventListener("click", () => {
    document.querySelector(".packet-panel")?.scrollIntoView({behavior:window.matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth",block:"start"});
    if (currentTask()) $("taskOutput")?.focus({preventScroll:true});
  });
  $("projectList").addEventListener("click", e => {
    const btn = e.target.closest("[data-project]"); if (!btn) return;
    // Save the current editor before changing projects, just as task switching does.
    savePacket(false);
    selectedProjectId = btn.dataset.project; selectedTaskId = null; render();
  });
  $("taskSearch").addEventListener("input", render);
  $("taskStatusFilter").addEventListener("change", render);
  $("taskList").addEventListener("click", e => {
    const btn = e.target.closest("[data-task]"); if (!btn) return;
    if (selectedTaskId && selectedTaskId !== btn.dataset.task) savePacket(false);
    selectedTaskId = btn.dataset.task; render();
  });
  $("packetForm").addEventListener("submit", e => { e.preventDefault(); savePacket(); });
  $("verifyPassBtn").addEventListener("click", () => recordVerification(true));
  $("verifyFailBtn").addEventListener("click", () => recordVerification(false));
  $("proposeNextActionBtn").addEventListener("click", proposeNextAction);
  $("handoffBtn").addEventListener("click", () => {
    if (!savePacket(false)) return;
    const t = currentTask();
    if (!t) return;
    if (!t.nextWorker.trim()) { toast("Set a next worker first."); $("nextWorker").focus(); return; }
    t.status = "handed_off"; t.worker = t.worker || "Unassigned";
    t.next = (t.next ? t.next + "\n\n" : "") + "HANDOFF PREPARED at " + now() + ". Next worker: " + t.nextWorker + ". Continue from the saved output; do not restart.";
    t.updatedAt = now(); persist(); render();
    const packet = packetText(t);
    if (navigator.clipboard?.writeText) navigator.clipboard.writeText(packet).then(()=>toast("Handoff saved and packet copied."),()=>toast("Handoff saved. Use Copy packet to transfer it."));
    else toast("Handoff saved. Use Copy packet to transfer it.");
  });
  $("copyPacketBtn").addEventListener("click", () => {
    const t = currentTask(); if (!t) return;
    const copy = packetText(t);
    if (navigator.clipboard?.writeText) navigator.clipboard.writeText(copy).then(()=>toast("Portable packet copied."),()=>fallbackCopy(copy));
    else fallbackCopy(copy);
  });
  function relayRequestText() {
    const t = currentTask();
    if (!t) return null;
    if (!confirm("This relay request includes the selected task packet. Your repository is PUBLIC, so its task, context and current output will be committed to public Git history and may be visible to others. Continue only if all included content is safe to publish.")) return null;
    return JSON.stringify({
      task: "Brain App task: " + (t.name || "Untitled task") + "\n\nGoal: " + (t.goal || "(not set)"),
      task_id: t.id,
      project_id: t.projectId,
      provider: $("relayProviderSelect")?.value || "auto",
      role: t.output ? "continue" : "create",
      prior_packet: packetText(t),
      next_worker: t.nextWorker || "review the previous worker and choose the next concrete step"
    }, null, 2);
  }
  $("runRelayBtn").addEventListener("click", async () => {
    const t = currentTask();
    if (!t) { toast("Select a task first."); return; }
    if (!cloudClient) {
      toast("Cloud relay is unavailable because the secure connection did not load.");
      return;
    }
    if (!cloudUser) {
      // Try a free anonymous Supabase session so a first-time user can run the
      // relay without creating an email/password account. The server still
      // verifies the resulting Supabase JWT before dispatching GitHub Actions.
      try {
        const { data, error } = await cloudClient.auth.signInAnonymously();
        if (error) throw error;
        cloudUser = data.user || data.session?.user || null;
        if (!cloudUser) throw new Error("No anonymous session was returned.");
        setAuthUI();
        await mergeCloudWorkspace();
      } catch (err) {
        const detail = String(err?.message || "");
        if (/anonymous|disabled|not enabled|signups not allowed/i.test(detail)) {
          toast("No account needed, but anonymous sign-in must be enabled once in Supabase Auth settings. I’m keeping the relay protected.");
        } else {
          toast("Could not start a temporary free session: " + (detail || "please retry."));
        }
        return;
      }
    }
    if (!confirm("Run the AI worker chain for this task? The in-app private route sends only an opaque run ID to GitHub Actions; task text/results are stored in your private Supabase workspace and task content is sent to the configured AI providers. The repository is public, and older manual/file-triggered routes may expose content. Do not include passwords, API keys, personal details, or confidential material.")) return;
    const button = $("runRelayBtn");
    button.disabled = true;
    button.textContent = "Starting workers…";
    try {
      await syncLocalToCloud();
      const { data, error } = await cloudClient.functions.invoke("dispatch-brain-relay", {
        body: {
          task: "Brain App task: " + (t.name || "Untitled task") + "\n\nGoal: " + (t.goal || "(not set)"),
          task_id: t.id,
          project_id: t.projectId,
          provider: $("relayProviderSelect")?.value || "auto",
          role: t.output ? "continue" : "create",
          prior_packet: packetText(t),
          next_worker: t.nextWorker || "review the previous worker and choose the next concrete step"
        }
      });
      if (error) throw error;
      if (!data?.run_id) throw new Error("Private relay dispatch returned no run ID; no result can be tracked safely.");
      relayDispatchedAt = Date.now();
      t.status = "handed_off";
      t.worker = t.worker || "Brain App relay";
      t.next = "Private relay accepted at " + now() + ". Waiting for the result to return automatically.";
      t.updatedAt = now();
      persist(); render();
      toast("Private dispatch accepted. Results will return automatically.");
      // Keep the user in Brain App and make the next state visible immediately.
      const statusPanel = document.querySelector(".relay-status-panel");
      if (statusPanel) statusPanel.scrollIntoView({behavior:"smooth",block:"start"});
      refreshRelayStatus();
      // Poll the owner-protected worker-run row; result text never travels through public artifacts.
      const privateRunId = data.run_id;
      let privatePolls = 0;
      const pollPrivateResult = async () => {
        if (!cloudClient || !cloudUser || privatePolls++ >= 180) return;
        try {
          const { data: run, error: runError } = await cloudClient.from("brain_worker_runs")
            .select("status,response_payload,error_category,finished_at")
            .eq("id", privateRunId).maybeSingle();
          if (runError) throw runError;
          if (run?.status === "succeeded" || run?.status === "failed") {
            const packet = run.response_payload || {};
            const turns = Array.isArray(packet.turns) ? packet.turns : [];
            const outputs = turns.filter(turn => turn?.outcome === "success" && turn?.worker_output)
              .map(turn => "**" + String(turn.provider || "AI worker") + "**\\n" + String(turn.worker_output));
            t.output = outputs.join("\\n\\n") || (run.error_category ? "Relay failed: " + run.error_category : "Relay finished without a usable output.");
            // A successful worker run proves the relay completed, not that the deliverable meets the goal.
            // Keep successful output in review until a person or independent verifier checks it.
            t.status = run.status === "succeeded" ? "handed_off" : "blocked";
            t.next = String(packet.next_action || (run.status === "succeeded" ? "Review the returned output against the goal and acceptance criteria. Mark complete only after verification." : "Check the relay error and retry when ready."));
            t.worker = "Private AI relay";
            t.updatedAt = now();
            persist(); render();
            await syncLocalToCloud().catch(() => {});
            toast(run.status === "succeeded" ? "Private relay result received and saved." : "Private relay finished with an error. Check the task result.");
            return;
          }
        } catch (pollError) {
          console.warn("Private relay result polling paused:", pollError?.message || "request failed");
        }
        setTimeout(pollPrivateResult, 8000);
      };
      setTimeout(pollPrivateResult, 5000);
      // The published status file updates only after the workflow finishes. Check
      // briefly in the background so the user doesn't mistake the previous run
      // for the result of the request they just sent.
      let checksRemaining = 18;
      const poll = async () => {
        await refreshRelayStatus();
        checksRemaining -= 1;
        if (checksRemaining > 0 && relayDispatchedAt && Date.now() - relayDispatchedAt < 180000) {
          setTimeout(poll, 10000);
        }
      };
      setTimeout(poll, 10000);
    } catch (err) {
      // Supabase FunctionsHttpError often hides the server's useful JSON
      // message in err.context; surface the real blocker instead of a generic toast.
      let detail = err?.message || "check dispatcher setup";
      try {
        const response = err?.context;
        if (response && typeof response.json === "function") {
          const payload = await response.clone().json();
          if (payload?.error) detail = String(payload.error);
          if (payload?.detail) detail += " " + String(payload.detail);
        }
      } catch (_) {}
      toast("Could not start relay: " + detail);
    } finally {
      button.disabled = false;
      button.textContent = "Run AI workers now";
    }
  });
  // The header action must use the same authenticated in-app dispatcher, not GitHub's manual workflow form.
  $("runRelayTopBtn")?.addEventListener("click", () => $("runRelayBtn")?.click());

  $("copyRelayRequestBtn").addEventListener("click", () => {
    const request = relayRequestText();
    if (!request) return;
    if (navigator.clipboard?.writeText) navigator.clipboard.writeText(request).then(()=>toast("Relay request JSON copied. It is not sent until committed to GitHub."),()=>fallbackCopy(request));
    else fallbackCopy(request);
  });
  $("downloadRelayRequestBtn").addEventListener("click", () => {
    const request = relayRequestText();
    if (!request) return;
    const blob = new Blob([request + "\n"], {type:"application/json"});
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "relay-request.json"; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast("Relay request downloaded. It still needs to be committed to GitHub to start the workers.");
  });
  function fallbackCopy(text) {
    const area = document.createElement("textarea"); area.value=text; area.style.position="fixed"; area.style.opacity="0"; document.body.appendChild(area); area.select();
    try { document.execCommand("copy"); toast("Packet copied."); } catch(e) { toast("Copy unavailable. Export a JSON backup instead."); }
    area.remove();
  }
  $("relayResultFile").addEventListener("change", async e => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      if (file.size > 5 * 1024 * 1024) throw new Error("Relay result file is larger than 5 MB.");
      const incoming = JSON.parse(await file.text());
      if (!incoming || !Array.isArray(incoming.turns)) throw new Error("Choose brain-relay-packet.json from the relay artifact.");
      let t;
      if (incoming.task_id) {
        t = state.tasks.find(task => task.id === incoming.task_id);
        if (!t) throw new Error("This relay result belongs to a task ID that is not in this browser workspace. Import the matching Brain App backup first; no task was changed.");
        selectedProjectId = t.projectId;
        selectedTaskId = t.id;
      } else {
        t = currentTask();
        if (!t) throw new Error("This older relay result has no task ID. Select the intended task before importing it.");
      }
      const lines = [
        "Relay outcome: " + String(incoming.overall_outcome || incoming.outcome || "unknown"),
        "Successful workers: " + Number(incoming.successful_turns || 0) + "/" + Number(incoming.total_turns || incoming.turns.length || 0)
      ];
      for (const turn of incoming.turns.slice(0, 10)) {
        lines.push("");
        lines.push("## " + String(turn.provider || "worker") + " / " + String(turn.model || "unknown") + " — " + String(turn.outcome || "unknown"));
        if (turn.error_category) lines.push("Blocker: " + String(turn.error_category));
        if (turn.worker_output) lines.push(String(turn.worker_output));
      }
      const imported = lines.join("\n");
      t.output = [t.output, imported].filter(Boolean).join("\n\n--- Imported relay result ---\n\n");
      t.worker = incoming.turns.slice(0, 10).map(turn => String(turn.provider || "worker")).join(" → ");
      const relayOutcome = String(incoming.overall_outcome || incoming.outcome || "unknown").toLowerCase();
      // A completed relay is no longer "working": successful/partial results await human review.
      t.status = relayOutcome === "error" ? "blocked" : "handed_off";
      if (incoming.next_action) t.next = String(incoming.next_action);
      t.context = [t.context, "Relay result imported locally at " + now() + ". API keys and provider credentials are not part of the result packet."].filter(Boolean).join("\n\n");
      t.updatedAt = now();
      persist();
      render();
      toast(relayOutcome === "success" ? "Relay result imported · ready for your review." : relayOutcome === "partial" ? "Partial relay result imported · review worker errors." : "Relay result imported · check the blocker.");
    } catch (error) {
      alert("Import failed: " + (error.message || "Invalid relay result."));
    } finally {
      e.target.value = "";
    }
  });
  $("deleteTaskBtn").addEventListener("click", async () => {
    const t = currentTask(); if (!t) return;
    if (!confirm(`Delete task "${t.name}"? This cannot be undone unless you have a backup.`)) return;
    const button = $("deleteTaskBtn");
    button.disabled = true;
    try {
      // Keep a private tombstone so stale copies on other devices cannot
      // resurrect this task during the next workspace merge.
      if (cloudClient && cloudUser) {
        const {error} = await cloudClient.from("brain_tasks").update({deleted_at: now(), sync_version: t.syncVersion || 1}).eq("id", t.id).eq("owner_id", cloudUser.id);
        if (error) throw error;
      }
      state.tasks = state.tasks.filter(x=>x.id!==t.id);
      selectedTaskId=null;
      persist();
      render();
      toast(cloudClient && cloudUser ? "Task deleted on this device and in cloud." : "Task deleted on this device. Sign in to sync deletions.");
    } catch (error) {
      toast("Task was not deleted: " + (error.message || "cloud delete failed"));
    } finally {
      button.disabled = false;
    }
  });
  $("exportBtn").addEventListener("click", () => {
    const data = JSON.stringify({...state,exportedAt:now()},null,2);
    const blob = new Blob([data],{type:"application/json"});
    const url = URL.createObjectURL(blob); const a=document.createElement("a"); a.href=url; a.download="brain-app-backup-"+new Date().toISOString().slice(0,10)+".json"; a.click(); URL.revokeObjectURL(url); toast("Backup exported.");
  });
  $("importFile").addEventListener("change", async e => {
    const file = e.target.files?.[0]; if (!file) return;
    try {
      const incoming = JSON.parse(await file.text());
      if (!incoming || !Array.isArray(incoming.projects) || !Array.isArray(incoming.tasks)) throw new Error("This file is not a Brain App backup.");
      if (!confirm("Import this backup and replace the workspace currently stored in this browser? Export the current workspace first if you need it.")) return;
      state = {version:1,projects:incoming.projects,tasks:incoming.tasks.filter(t=>incoming.projects.some(p=>p.id===t.projectId))};
      selectedProjectId=state.projects[0]?.id||null; selectedTaskId=null; persist(); render(); toast("Backup imported.");
    } catch(err) { alert("Import failed: "+err.message); }
    finally { e.target.value=""; }
  });
  async function refreshRelayStatus() {
    const summary = $("relayStatusSummary");
    const list = $("relayStatusProviders");
    const link = $("relayRunLink");
    summary.textContent = "Checking the latest relay run…";
    list.replaceChildren();
    try {
      const response = await fetch("./relay-status.json?t=" + Date.now(), {cache:"no-store"});
      if (!response.ok) throw new Error(response.status === 404 ? "No relay status has been published yet." : "Status unavailable (HTTP " + response.status + ").");
      const data = await response.json();
      const successes = Number(data.successful_turns || 0);
      const total = Number(data.total_turns || 0);
      const updatedMs = Date.parse(data.updated_at || "");
      const stale = !Number.isFinite(updatedMs) || Date.now() - updatedMs > 24 * 60 * 60 * 1000;
      const waitingForThisDispatch = !!relayDispatchedAt && (!Number.isFinite(updatedMs) || updatedMs < relayDispatchedAt);
      const partial = successes > 0 && successes < total;
      const outcome = data.outcome === "success" ? "Completed successfully" : partial ? "Partially completed" : "Run did not complete successfully";
      const updated = Number.isFinite(updatedMs) ? new Date(updatedMs).toLocaleString() : "time unavailable";
      if (waitingForThisDispatch) {
        summary.className = "muted status-working";
        summary.textContent = "Your request was sent to GitHub Actions. Waiting for this run to finish; the result below is from an earlier run (" + updated + ").";
      } else {
        summary.className = "muted " + (stale || (successes === 0 && total > 0) ? "status-blocked" : partial ? "status-working" : "status-complete");
        summary.textContent = (stale ? "LAST RUN IS STALE (over 24h). " : "") + outcome + " · " + successes + "/" + total + " workers succeeded · Updated " + updated;
        if (relayDispatchedAt && Number.isFinite(updatedMs) && updatedMs >= relayDispatchedAt) relayDispatchedAt = null;
      }
      const runId = String(data.run_id || "");
      if (/^\d+$/.test(runId)) { link.href = "https://github.com/Astridrosexxx84/Astridrose-automation-/actions/runs/" + encodeURIComponent(runId); link.textContent = "Open this run ↗"; }
      for (const turn of (Array.isArray(data.turns) ? data.turns : [])) {
        const card = document.createElement("div"); card.className = "provider";
        const name = document.createElement("strong"); name.textContent = String(turn.provider || "Worker");
        const state = document.createElement("span"); state.className = "state " + (turn.outcome === "success" ? "manual" : "unknown");
        state.textContent = turn.outcome === "success" ? "Succeeded" : "Failed" + (turn.error_category ? " · " + turn.error_category : "");
        card.append(name, state);
        if (turn.model) { const model = document.createElement("span"); model.className = "footnote"; model.textContent = String(turn.model); card.append(model); }
        list.append(card);
      }
    } catch (error) {
      summary.className = "muted status-blocked";
      summary.textContent = error.message || "Could not load relay status.";
      link.href = "https://github.com/Astridrosexxx84/Astridrose-automation-/actions/workflows/brain-app-relay.yml"; link.textContent = "Open workflow history ↗";
    }
  }
  $("refreshRelayStatus").addEventListener("click", refreshRelayStatus);
  refreshRelayStatus();
  // Keep the visible dashboard current without requiring repeated manual refresh taps.
  setInterval(() => {
    if (!document.hidden) refreshRelayStatus();
  }, 60000);
  if ("serviceWorker" in navigator && location.protocol === "https:") navigator.serviceWorker.register("./service-worker.js").catch(() => {});
  render();
  setupCloudAuth().catch(e => setCloudStatus("Cloud setup failed: " + (e.message || "unknown error"), true));
})();