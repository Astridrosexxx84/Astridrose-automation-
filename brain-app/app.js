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
  function savePacket(showMessage=true) {
    const t = currentTask();
    if (!t) return false;
    t.name = $("taskName").value.trim();
    t.status = $("taskStatus").value;
    t.worker = $("taskWorker").value.trim();
    t.nextWorker = $("nextWorker").value.trim();
    t.goal = $("taskGoal").value.trim();
    t.context = $("taskContext").value.trim();
    t.output = $("taskOutput").value.trim();
    t.next = $("taskNext").value.trim();
    t.updatedAt = now();
    const p = state.projects.find(p => p.id === selectedProjectId);
    if (p) p.updatedAt = now();
    persist(); render();
    if (showMessage) toast("Work packet saved.");
    return true;
  }
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
      const t = currentTask();
      if (!t) throw new Error("Select a task before importing a relay result.");
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
      if (/^\\d+$/.test(runId)) { link.href = "https://github.com/Astridrosexxx84/Astridrose-automation-/actions/runs/" + encodeURIComponent(runId); link.textContent = "Open this run ↗"; }
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
  if ("serviceWorker" in navigator && location.protocol === "https:") navigator.serviceWorker.register("./service-worker.js").catch(() => {});
  render();
})();