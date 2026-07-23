import { getProfiles, createProfile, getTracks, addCurrentTrack } from "./api.js";
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

export function initSetupPage() {
  loadProfiles();
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
}
