import { getProfiles, createProfile, getTracks, addCurrentTrack,
  getSessionSetups, createSessionSetup, getSessionSetupDetail,
  addSongToSetup, deleteSong, markSegmentStart, markSegmentEnd,
  patchSegment, deleteSegment } from "./api.js";
import { onMessage } from "./ws.js";
import { showPage } from "./main.js";
import { startSessionScreen } from "./session.js";

const TRIAL_OPTIONS = [5, 10, 15, 20];
const MOCK_TRIAL_DURATION_SECONDS = 30; // matches session_config.json default in Phase 5

let profiles = [];
let currentProfileId = localStorage.getItem("abx_profile_id") || null;

let tracks = [];
let selectedTrackId = null;
let trialCount = null;

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

async function loadTracks() {
  tracks = await getTracks();
  renderTrackList();
}

async function handleAddCurrentTrack() {
  try {
    await addCurrentTrack();
    await loadTracks();
  } catch (err) {
    alert(err.message);
  }
}

function renderTrackList() {
  const el = document.getElementById("track-list");
  if (tracks.length === 0) {
    el.innerHTML = `<div class="text-xl text-slate-500 px-2 py-8 text-center">
      No tracks yet — play something on Volumio, then tap "+ Add Current Track"
    </div>`;
    return;
  }
  el.innerHTML = tracks
    .map(
      (t) => `
    <button class="w-full text-left px-5 py-4 rounded-xl transition-colors border-2 ${
      t.id === selectedTrackId
        ? "bg-emerald-900 border-emerald-500"
        : "bg-slate-700 border-transparent active:bg-slate-600"
    }"
      onclick="selectTrack('${t.id}')">
      <div class="flex items-center gap-4">
        ${
          t.album_art_url
            ? `<img src="${t.album_art_url}" class="w-16 h-16 rounded-lg object-cover flex-shrink-0" loading="lazy">`
            : `<div class="w-16 h-16 rounded-lg bg-slate-600 flex-shrink-0"></div>`
        }
        <div class="flex-1 flex items-center justify-between min-w-0">
          <div class="min-w-0">
            <div class="text-2xl font-semibold truncate">${t.title}</div>
            <div class="text-lg text-slate-400 truncate">${t.artist} · from ${formatDuration(t.seek_seconds)}</div>
          </div>
          <div class="text-xl text-slate-400 font-mono flex-shrink-0 ml-4">${formatDuration(t.duration_seconds)}</div>
        </div>
      </div>
    </button>
  `
    )
    .join("");
}

function selectTrack(id) {
  selectedTrackId = id;
  renderTrackList();
  updateStartButton();
}

function renderTrialPicker() {
  const el = document.getElementById("trial-picker");
  el.innerHTML = TRIAL_OPTIONS.map(
    (n) => `
    <button onclick="setTrials(${n})"
      class="text-2xl font-bold w-16 h-16 rounded-xl transition-colors ${
        n === trialCount ? "bg-emerald-600" : "bg-slate-700 active:bg-slate-600"
      }">
      ${n}
    </button>
  `
  ).join("");
  const estimateEl = document.getElementById("trial-estimate");
  estimateEl.textContent = trialCount ? `~${Math.round((trialCount * MOCK_TRIAL_DURATION_SECONDS) / 60)} min` : "";
}

function setTrials(n) {
  trialCount = n;
  renderTrialPicker();
}

function updateStartButton() {
  const btn = document.getElementById("start-session-btn");
  const ready = selectedTrackId !== null && trialCount !== null;
  btn.disabled = !ready;
  btn.classList.toggle("bg-emerald-600", ready);
  btn.classList.toggle("active:bg-emerald-500", ready);
  btn.classList.toggle("bg-slate-700", !ready);
  btn.classList.toggle("text-slate-500", !ready);
  btn.classList.toggle("cursor-not-allowed", !ready);
}

function handleStartSession() {
  startSessionScreen(trialCount);
  showPage("session");
}

// --- Session setups + playlist editor ---

async function loadSessionSetups() {
  const select = document.getElementById("setup-select");
  const editBtn = document.getElementById("edit-playlist-btn");

  if (!currentProfileId) {
    select.innerHTML = `<option value="">Select a profile first</option>`;
    setEditPlaylistEnabled(false);
    return;
  }

  sessionSetups = await getSessionSetups(currentProfileId);

  if (sessionSetups.length === 0) {
    select.innerHTML = `<option value="">No session setups yet</option>`;
    currentSetupId = null;
    setEditPlaylistEnabled(false);
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
}

function setEditPlaylistEnabled(enabled) {
  const btn = document.getElementById("edit-playlist-btn");
  btn.disabled = !enabled;
  btn.classList.toggle("bg-slate-700", true);
  btn.classList.toggle("active:bg-slate-600", enabled);
  btn.classList.toggle("text-slate-500", !enabled);
  btn.classList.toggle("cursor-not-allowed", !enabled);
}

function selectSetup(id) {
  currentSetupId = id;
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

function closePlaylistEditor() {
  document.getElementById("playlist-editor-overlay").classList.add("hidden");
}

async function refreshPlaylistEditor() {
  currentSetupDetail = await getSessionSetupDetail(currentSetupId);
  document.getElementById("playlist-editor-title").textContent = currentSetupDetail.name;
  renderPlaylistSongs();
}

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
  loadTracks();
  renderTrialPicker();

  onMessage("tracks_updated", (msg) => {
    tracks = msg.tracks;
    renderTrackList();
  });

  window.selectProfile = selectProfile;
  window.promptNewProfile = promptNewProfile;
  window.addCurrentTrack = handleAddCurrentTrack;
  window.selectTrack = selectTrack;
  window.setTrials = setTrials;
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
}
