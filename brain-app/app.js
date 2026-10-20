(() => {
  "use strict";
  const KEY = "brain-app-mvp-v1";
  const $ = (id) => document.getElementById(id);
  const now = () => new Date().toISOString();
  const uid = () => (crypto && crypto.randomUUID) ? crypto.randomUUID() : String(Date.now()) + Math.random().toString(16).slice(2);
  const statuses = {waiting:"Waiting",working:"Working",handed_off:"Handed off",blocked:"Blocked",complete:"Complete"};
  let state = loadState();
  let selectedProjectId = state.projects[0]?.id || null;
  let selectedTaskId = null;
  let toastTimer;

  // Free Supabase backend: browser uses only the public publishable key;
  // row-level security limits database access to the signed-in owner.
  const SUPABASE_URL = "https://cjqgdqcbtcwsgbbqrqcf.supabase.co";
  const SUPABASE_PUBLISHABLE_KEY = "sb_publishable__pFBwxTsfTJwEDIGVjhppQ_qKomVqf-";
  const cloudClient = window.supabase?.createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY);
  let cloudUser = null;
  let cloudReady = false;
  let syncingCloud = false;
  let cloudSyncTimer = null;

  function setCloudStatus(message, bad=false) {
    const el = $("cloudStatus");
    if (!el) return;
    el.textContent = message;
    el.className = bad ? "muted status-blocked" : "muted";
  }
  function scheduleCloudSync() {
    if (!cloudUser || !cloudReady || syncingCloud || !cloudClient) return;
    clearTimeout(cloudSyncTimer);
    cloudSyncTimer = setTimeout(() => syncLocalToCloud().catch(e => setCloudStatus("Cloud sync paused: " + (e.message || "network error"), true)), 900);
  }
  function toRemoteProject(p) {
    return {id:p.id, owner_id:cloudUser.id, name:p.name || "Untitled project", description:p.description || "", status:"active", created_at:p.createdAt || now(), updated_at:p.updatedAt || now()};
  }
  function toRemoteTask(t) {
    return {id:t.id, owner_id:cloudUser.id, project_id:t.projectId || null, title:t.name || "Untitled task", goal:t.goal || "", context:t.context || "", status:({waiting:"queued",working:"running",handed_off:"review",blocked:"blocked",complete:"completed"})[t.status] || "queued", priority:3, assigned_worker:t.worker || null, current_worker:t.worker || "", next_worker:t.nextWorker || "", result_summary:t.output || "", current_output:t.output || "", next_action:t.next || "", created_at:t.createdAt || now(), updated_at:t.updatedAt || now()};
  }
  function fromRemoteProject(p) {
    return {id:p.id,name:p.name,description:p.description || "",createdAt:p.created_at || now(),updatedAt:p.updated_at || now()};
  }
  function fromRemoteTask(t) {
    const status = ({queued:"waiting",running:"working",review:"handed_off",blocked:"blocked",completed:"complete",failed:"blocked",cancelled:"blocked"})[t.status] || "waiting";
    return {id:t.id,projectId:t.project_id,name:t.title,goal:t.goal || "",context:t.context || "",status,worker:t.current_worker || t.assigned_worker || "",nextWorker:t.next_worker || "",output:t.current_output || t.result_summary || "",next:t.next_action || "",createdAt:t.created_at || now(),updatedAt:t.updated_at || now()};
  }
  function mergeByFreshness(localItems, remoteItems) {
    const byId = new Map();
    for (const item of [...remoteItems, ...localItems]) {
      const prior = byId.get(item.id);
      if (!prior || Date.parse(item.updatedAt || 0) >= Date.parse(prior.updatedAt || 0)) byId.set(item.id, item);
    }
    return [...byId.values()];
  }
  async function syncLocalToCloud() {
    if (!cloudClient || !cloudUser || syncingCloud) return;
    syncingCloud = true;
    try {
      // Upsert parents first, then tasks so project references are valid.
      if (state.projects.length) {
        const {error} = await cloudClient.from("brain_projects").upsert(state.projects.map(toRemoteProject), {onConflict:"id"});
        if (error) throw error;
      }
      if (state.tasks.length) {
        const {error} = await cloudClient.from("brain_tasks").upsert(state.tasks.map(toRemoteTask), {onConflict:"id"});
        if (error) throw error;
      }
      setCloudStatus("Cloud sync connected · saved to this device and Supabase");
    } finally { syncingCloud = false; }
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
      const validProjects = new Set(state.projects.map(p=>p.id));
      state.tasks = state.tasks.filter(t=>validProjects.has(t.projectId));
      // Persist the merged view locally before uploading any locally-only records.
      try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (_) {}
      syncingCloud = false;
      await syncLocalToCloud();
      syncingCloud = true;
      cloudReady = true;
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
    const status = $("cloudStatus");
    if (!cloudClient) {
      setCloudStatus("Cloud sync unavailable: Supabase client did not load.", true);
      return;
    }
    $("authForm").addEventListener("submit", async e => {
      e.preventDefault();
      const email = $("authEmail").value.trim();
      const password = $("authPassword").value;
      const action = e.submitter?.value || "signin";
      $("authSubmit").disabled = true;
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
        setCloudStatus("Sign-in failed: " + (err.message || "unknown error"), true);
      } finally { $("authSubmit").disabled = false; }
    });
    $("signOutBtn").addEventListener("click", async () => {
      const {error} = await cloudClient.auth.signOut();
      if (error) { setCloudStatus("Could not sign out: " + error.message, true); return; }
      cloudUser = null; cloudReady = false; setAuthUI(); setCloudStatus("Signed out · workspace remains on this device");
    });
    cloudClient.auth.onAuthStateChange((_event, session) => {
      cloudUser = session?.user || null;
      setAuthUI();
      if (cloudUser && !cloudReady) setTimeout(() => mergeCloudWorkspace(), 0);
      if (!cloudUser) { cloudReady = false; setCloudStatus("Not signed in · this device only"); }
    });
    const {data} = await cloudClient.auth.getSession();
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
      $("taskList").className = "task-list";
      $("taskList").innerHTML = tasks.length ? tasks.map(t => `<button type="button" class="task-card ${t.id===selectedTaskId?"selected":""}" data-task="${esc(t.id)}"><span class="task-top"><strong>${esc(t.name)}</strong><span class="task-status status-${esc(t.status)}">${esc(statuses[t.status]||t.status)}</span></span><p>Next: ${esc(t.nextWorker || "Unassigned")} · ${esc(t.next || "No next action recorded")}</p></button>`).join("") : '<div class="empty">Queue is empty. Add a specific task.</div>';
    }
    renderPacket();
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
  $("projectList").addEventListener("click", e => {
    const btn = e.target.closest("[data-project]"); if (!btn) return;
    // Save the current editor before changing projects, just as task switching does.
    savePacket(false);
    selectedProjectId = btn.dataset.project; selectedTaskId = null; render();
  });
  $("taskList").addEventListener("click", e => {
    const btn = e.target.closest("[data-task]"); if (!btn) return;
    if (selectedTaskId && selectedTaskId !== btn.dataset.task) savePacket(false);
    selectedTaskId = btn.dataset.task; render();
  });
  $("packetForm").addEventListener("submit", e => { e.preventDefault(); savePacket(); });
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
      provider: "auto",
      role: t.output ? "continue" : "create",
      prior_packet: packetText(t),
      next_worker: t.nextWorker || "review the previous worker and choose the next concrete step"
    }, null, 2);
  }
  $("runRelayBtn").addEventListener("click", async () => {
    const t = currentTask();
    if (!t) { toast("Select a task first."); return; }
    if (!cloudClient || !cloudUser) {
      toast("Sign in to the Brain App first. The secure relay dispatcher requires an account.");
      $("authEmail")?.focus();
      return;
    }
    if (!confirm("Run the AI worker chain for this task? The repository is public, so do not send private or sensitive task content. This sends the task packet to GitHub Actions and the configured free AI providers.")) return;
    const button = $("runRelayBtn");
    button.disabled = true;
    button.textContent = "Starting workers…";
    try {
      const { data, error } = await cloudClient.functions.invoke("dispatch-brain-relay", {
        body: {
          task: "Brain App task: " + (t.name || "Untitled task") + "\n\nGoal: " + (t.goal || "(not set)"),
          task_id: t.id,
          project_id: t.projectId,
          provider: "auto",
          role: t.output ? "continue" : "create",
          prior_packet: packetText(t),
          next_worker: t.nextWorker || "review the previous worker and choose the next concrete step"
        }
      });
      if (error) throw error;
      t.status = "handed_off";
      t.worker = t.worker || "Brain App relay";
      t.next = "AI relay dispatched at " + now() + ". Refresh worker status to check completion; then import the relay artifact.";
      t.updatedAt = now();
      persist(); render();
      toast("AI relay started. Check Latest relay run for status.");
      if (data?.run_url) window.open(data.run_url, "_blank", "noopener");
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
      t.status = incoming.overall_outcome === "error" ? "blocked" : "working";
      if (incoming.next_action) t.next = String(incoming.next_action);
      t.context = [t.context, "Relay result imported locally at " + now() + ". API keys and provider credentials are not part of the result packet."].filter(Boolean).join("\n\n");
      t.updatedAt = now();
      persist();
      render();
      toast("Relay result added to the selected task.");
    } catch (error) {
      alert("Import failed: " + (error.message || "Invalid relay result."));
    } finally {
      e.target.value = "";
    }
  });
  $("deleteTaskBtn").addEventListener("click", () => {
    const t = currentTask(); if (!t) return;
    if (!confirm(`Delete task "${t.name}"? This cannot be undone unless you have a backup.`)) return;
    state.tasks = state.tasks.filter(x=>x.id!==t.id); selectedTaskId=null; persist(); render(); toast("Task deleted.");
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
      const partial = successes > 0 && successes < total;
      const outcome = data.outcome === "success" ? "Completed successfully" : partial ? "Partially completed" : "Run did not complete successfully";
      const updated = Number.isFinite(updatedMs) ? new Date(updatedMs).toLocaleString() : "time unavailable";
      summary.className = "muted " + (stale || (successes === 0 && total > 0) ? "status-blocked" : partial ? "status-working" : "status-complete");
      summary.textContent = (stale ? "LAST RUN IS STALE (over 24h). " : "") + outcome + " · " + successes + "/" + total + " workers succeeded · Updated " + updated;
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