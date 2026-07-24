import { getProfiles, createProfile,
  getSessionSetups, createSessionSetup, getSessionSetupDetail,
  addSongToSetup, deleteSong, markSegmentStart, markSegmentEnd,
  patchSegment, deleteSegment, patchSessionSetup,
  startFreePlay, stopFreePlay } from "./api.js";
import { onMessage } from "./ws.js";
import { showPage } from "./main.js";
import { startSessionScreen } from "./session.js";

const IDENTITY_LABELS = { blind: "Blind", alias: "Alias", visible: "Visible" };

let profiles = [];
let currentProfileId = localStorage.getItem("abx_profile_id") || null;

let sessionSetups = [];
let currentSetupId = null;
let currentSetupDetail = null;

export function formatDuration(seconds) {
  if (!seconds) return "--:--";
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

async function loadProfiles() {
  profiles = await getProfiles();
  const select = document.getElementById("profile-select");

  if (profiles.length === 0) {
    select.innerHTML = `<option value="">No profiles yet</option>`;
    currentProfileId = null;
    return;
  }

  if (!currentProfileId || !profiles.some((p) => String(p.id) === String(currentProfileId))) {
    currentProfileId = String(profiles[0].id);
  }
  localStorage.setItem("abx_profile_id", currentProfileId);

  select.innerHTML = profiles
    .map(
      (p) => `<option value="${p.id}" ${String(p.id) === currentProfileId ? "selected" : ""}>${p.name}</option>`
    )
    .join("");
}

function selectProfile(id) {
  currentProfileId = id;
  localStorage.setItem("abx_profile_id", id);
  loadSessionSetups();
}

async function promptNewProfile() {
  const name = prompt("Profile name:");
  if (!name || !name.trim()) return;
  try {
    const created = await createProfile(name.trim());
    currentProfileId = String(created.id);
    await loadProfiles();
  } catch (err) {
    alert(err.message);
  }
}

function handleStartSession() {
  startSessionScreen(currentSetupDetail.num_trials);
  showPage("session");
}

// --- Session setups + playlist editor ---

async function loadSessionSetups() {
  const select = document.getElementById("setup-select");

  if (!currentProfileId) {
    select.innerHTML = `<option value="">Select a profile first</option>`;
    setEditPlaylistEnabled(false);
    currentSetupId = null;
    currentSetupDetail = null;
    renderSetupSummary();
    return;
  }

  sessionSetups = await getSessionSetups(currentProfileId);

  if (sessionSetups.length === 0) {
    select.innerHTML = `<option value="">No session setups yet</option>`;
    setEditPlaylistEnabled(false);
    currentSetupId = null;
    currentSetupDetail = null;
    renderSetupSummary();
    return;
  }

  if (!currentSetupId || !sessionSetups.some((s) => String(s.id) === String(currentSetupId))) {
    currentSetupId = String(sessionSetups[0].id);
  }

  select.innerHTML = sessionSetups
    .map(
      (s) => `<option value="${s.id}" ${String(s.id) === currentSetupId ? "selected" : ""}>${s.name}</option>`
    )
    .join("");
  setEditPlaylistEnabled(true);

  await refreshSetupSummary();
}

function setEditPlaylistEnabled(enabled) {
  const btn = document.getElementById("edit-playlist-btn");
  btn.disabled = !enabled;
  btn.classList.toggle("bg-slate-700", true);
  btn.classList.toggle("active:bg-slate-600", enabled);
  btn.classList.toggle("text-slate-500", !enabled);
  btn.classList.toggle("cursor-not-allowed", !enabled);
}

async function selectSetup(id) {
  currentSetupId = id;
  await refreshSetupSummary();
}

async function refreshSetupSummary() {
  if (!currentSetupId) {
    currentSetupDetail = null;
    renderSetupSummary();
    return;
  }
  currentSetupDetail = await getSessionSetupDetail(currentSetupId);
  renderSetupSummary();
}

function renderSetupSummary() {
  const el = document.getElementById("setup-summary");
  const btn = document.getElementById("start-session-btn");
  const s = currentSetupDetail;

  if (!s) {
    el.innerHTML = "Select or create a session setup above";
    setStartSessionEnabled(false);
    return;
  }

  const songCount = s.songs.length;
  const segmentCount = s.songs.reduce((n, song) => n + song.segments.length, 0);

  el.innerHTML = `
    <div class="text-3xl font-bold mb-2">${s.name}</div>
    <div class="text-xl text-slate-300">
      ${songCount} song${songCount === 1 ? "" : "s"} · ${segmentCount} segment${segmentCount === 1 ? "" : "s"}
    </div>
    <div class="text-xl text-slate-300 mt-1">
      ${s.num_trials} trials · ${IDENTITY_LABELS[s.identity_mode]} mode
    </div>
    ${songCount === 0 ? `<div class="text-lg text-slate-500 mt-4">Tap "Edit Playlist" to add songs before starting</div>` : ""}
  `;

  setStartSessionEnabled(songCount > 0);
}

function setStartSessionEnabled(enabled) {
  const btn = document.getElementById("start-session-btn");
  btn.disabled = !enabled;
  btn.classList.toggle("bg-emerald-600", enabled);
  btn.classList.toggle("active:bg-emerald-500", enabled);
  btn.classList.toggle("bg-slate-700", !enabled);
  btn.classList.toggle("text-slate-500", !enabled);
  btn.classList.toggle("cursor-not-allowed", !enabled);
}

async function promptNewSetup() {
  if (!currentProfileId) {
    alert("Select or create a profile first");
    return;
  }
  const name = prompt("Session setup name:");
  if (!name || !name.trim()) return;
  try {
    const created = await createSessionSetup(currentProfileId, name.trim());
    currentSetupId = String(created.id);
    await loadSessionSetups();
  } catch (err) {
    alert(err.message);
  }
}

async function openPlaylistEditor() {
  if (!currentSetupId) return;
  await refreshPlaylistEditor();
  document.getElementById("playlist-editor-overlay").classList.remove("hidden");
}

async function closePlaylistEditor() {
  document.getElementById("playlist-editor-overlay").classList.add("hidden");
  await refreshSetupSummary(); // song/segment counts on the main page may have changed
}

async function refreshPlaylistEditor() {
  currentSetupDetail = await getSessionSetupDetail(currentSetupId);
  document.getElementById("playlist-editor-title").textContent = currentSetupDetail.name;
  renderPlaylistSongs();
  renderPreferences();
}

// --- Preferences ---

function highlightButton(id, active) {
  const btn = document.getElementById(id);
  btn.classList.toggle("bg-emerald-600", active);
  btn.classList.toggle("bg-slate-700", !active);
}

function renderPreferences() {
  const s = currentSetupDetail;

  highlightButton("pref-gap-fixed-btn", s.gap_mode === "fixed");
  highlightButton("pref-gap-wait-btn", s.gap_mode === "wait_button");
  document.getElementById("pref-gap-seconds-row").classList.toggle("hidden", s.gap_mode !== "fixed");
  document.getElementById("pref-gap-seconds-value").textContent = `${s.gap_seconds.toFixed(1)}s`;

  highlightButton("pref-identity-blind-btn", s.identity_mode === "blind");
  highlightButton("pref-identity-alias-btn", s.identity_mode === "alias");
  highlightButton("pref-identity-visible-btn", s.identity_mode === "visible");

  document.getElementById("pref-num-trials-value").textContent = s.num_trials;

  highlightButton("pref-vibrate-btn", s.vibrate_after_trial);
  highlightButton("pref-whole-track-btn", s.play_whole_track);
  highlightButton("pref-randomise-btn", s.randomise_sequence);
}

async function updatePreference(patch) {
  const updated = await patchSessionSetup(currentSetupId, patch);
  Object.assign(currentSetupDetail, updated); // preserves currentSetupDetail.songs, which the PATCH response omits
  renderPreferences();
  renderSetupSummary(); // trial count / identity mode shown there too
}

function setPrefGapMode(mode) {
  updatePreference({ gap_mode: mode });
}

function nudgePrefGapSeconds(delta) {
  const next = Math.max(0, currentSetupDetail.gap_seconds + delta);
  updatePreference({ gap_seconds: next });
}

function setPrefIdentityMode(mode) {
  updatePreference({ identity_mode: mode });
}

function nudgePrefNumTrials(delta) {
  const next = Math.max(1, currentSetupDetail.num_trials + delta);
  updatePreference({ num_trials: next });
}

function togglePrefBoolean(field) {
  updatePreference({ [field]: !currentSetupDetail[field] });
}

// --- Free Play ---

async function handleStartFreePlay() {
  await startFreePlay();
  showPage("free_play");
}

async function handleStopFreePlay() {
  await stopFreePlay();
  showPage("setup");
}

// --- Playlist editor ---

function renderPlaylistSongs() {
  const el = document.getElementById("playlist-songs");
  const songs = currentSetupDetail.songs;

  if (songs.length === 0) {
    el.innerHTML = `<div class="text-xl text-slate-500 px-2 py-8 text-center">
      No songs yet — play something on Volumio, then tap "+ Add Current Track"
    </div>`;
    return;
  }

  el.innerHTML = songs
    .map((song) => {
      const segmentsHtml = song.segments
        .map((seg) => {
          const startLabel = seg.start_seconds !== null ? formatDuration(seg.start_seconds) : null;
          const endLabel = seg.end_seconds !== null ? formatDuration(seg.end_seconds) : null;
          return `
        <div class="bg-slate-800 rounded-xl p-4 flex items-center gap-3 flex-wrap">
          ${
            startLabel === null
              ? `<button onclick="doMarkSegmentStart(${song.id})" class="text-lg px-4 py-2 rounded-lg bg-emerald-700 active:bg-emerald-600">Mark Start</button>`
              : `<div class="flex items-center gap-1">
                   <span class="text-lg font-mono">Start: ${startLabel}</span>
                   <button onclick="doNudgeSegment(${seg.id},'start_delta',-1)" class="text-sm px-2 py-1 rounded bg-slate-700 active:bg-slate-600">-1s</button>
                   <button onclick="doNudgeSegment(${seg.id},'start_delta',1)" class="text-sm px-2 py-1 rounded bg-slate-700 active:bg-slate-600">+1s</button>
                 </div>`
          }
          ${
            startLabel !== null && endLabel === null
              ? `<button onclick="doMarkSegmentEnd(${seg.id})" class="text-lg px-4 py-2 rounded-lg bg-emerald-700 active:bg-emerald-600">Mark End</button>`
              : endLabel !== null
              ? `<div class="flex items-center gap-1">
                   <span class="text-lg font-mono">End: ${endLabel}</span>
                   <button onclick="doNudgeSegment(${seg.id},'end_delta',-1)" class="text-sm px-2 py-1 rounded bg-slate-700 active:bg-slate-600">-1s</button>
                   <button onclick="doNudgeSegment(${seg.id},'end_delta',1)" class="text-sm px-2 py-1 rounded bg-slate-700 active:bg-slate-600">+1s</button>
                 </div>`
              : ""
          }
          <input type="text" placeholder="Description (e.g. drum solo)" value="${seg.description || ""}"
            onblur="doUpdateSegmentDescription(${seg.id}, this.value)"
            class="flex-1 min-w-[10rem] text-lg bg-slate-700 rounded-lg px-3 py-2 border-none">
          <button onclick="doRemoveSegment(${seg.id})" class="text-lg px-3 py-2 rounded-lg bg-slate-700 active:bg-red-800">✕</button>
        </div>
      `;
        })
        .join("");

      return `
      <div class="bg-slate-800 rounded-2xl p-4">
        <div class="flex items-center gap-4 mb-3">
          ${
            song.album_art_url
              ? `<img src="${song.album_art_url}" class="w-14 h-14 rounded-lg object-cover flex-shrink-0" loading="lazy">`
              : `<div class="w-14 h-14 rounded-lg bg-slate-600 flex-shrink-0"></div>`
          }
          <div class="flex-1 min-w-0">
            <div class="text-xl font-semibold truncate">${song.title}</div>
            <div class="text-lg text-slate-400 truncate">${song.artist || ""}</div>
          </div>
          <button onclick="doRemoveSong(${song.id})" class="text-lg px-4 py-2 rounded-lg bg-slate-700 active:bg-red-800">Remove</button>
        </div>
        <div class="space-y-2 mb-2">${segmentsHtml}</div>
        <button onclick="doAddSegment(${song.id})" class="text-lg px-4 py-2 rounded-lg bg-slate-700 active:bg-slate-600">+ Add Segment</button>
      </div>
    `;
    })
    .join("");
}

async function addSongToPlaylist() {
  try {
    await addSongToSetup(currentSetupId);
    await refreshPlaylistEditor();
  } catch (err) {
    alert(err.message);
  }
}

async function doRemoveSong(songId) {
  if (!confirm("Remove this song and its segments?")) return;
  await deleteSong(songId);
  await refreshPlaylistEditor();
}

async function doAddSegment(songId) {
  try {
    await markSegmentStart(songId);
    await refreshPlaylistEditor();
  } catch (err) {
    alert(err.message);
  }
}

async function doMarkSegmentStart(songId) {
  try {
    await markSegmentStart(songId);
    await refreshPlaylistEditor();
  } catch (err) {
    alert(err.message);
  }
}

async function doMarkSegmentEnd(segmentId) {
  try {
    await markSegmentEnd(segmentId);
    await refreshPlaylistEditor();
  } catch (err) {
    alert(err.message);
  }
}

async function doNudgeSegment(segmentId, field, delta) {
  await patchSegment(segmentId, { [field]: delta });
  await refreshPlaylistEditor();
}

async function doUpdateSegmentDescription(segmentId, value) {
  await patchSegment(segmentId, { description: value });
}

async function doRemoveSegment(segmentId) {
  await deleteSegment(segmentId);
  await refreshPlaylistEditor();
}

export function initSetupPage() {
  loadProfiles().then(loadSessionSetups);

  onMessage("free_play_dac_path", (msg) => {
    document.getElementById("free-play-dac-path").textContent = msg.dac_path
      ? msg.dac_path.name
      : "No DAC paths configured";
  });

  window.selectProfile = selectProfile;
  window.promptNewProfile = promptNewProfile;
  window.startSession = handleStartSession;

  window.selectSetup = selectSetup;
  window.promptNewSetup = promptNewSetup;
  window.openPlaylistEditor = openPlaylistEditor;
  window.closePlaylistEditor = closePlaylistEditor;
  window.addSongToPlaylist = addSongToPlaylist;
  window.doRemoveSong = doRemoveSong;
  window.doAddSegment = doAddSegment;
  window.doMarkSegmentStart = doMarkSegmentStart;
  window.doMarkSegmentEnd = doMarkSegmentEnd;
  window.doNudgeSegment = doNudgeSegment;
  window.doUpdateSegmentDescription = doUpdateSegmentDescription;
  window.doRemoveSegment = doRemoveSegment;

  window.setPrefGapMode = setPrefGapMode;
  window.nudgePrefGapSeconds = nudgePrefGapSeconds;
  window.setPrefIdentityMode = setPrefIdentityMode;
  window.nudgePrefNumTrials = nudgePrefNumTrials;
  window.togglePrefBoolean = togglePrefBoolean;

  window.handleStartFreePlay = handleStartFreePlay;
  window.handleStopFreePlay = handleStopFreePlay;
}
