async function jsonFetch(url, options) {
  const res = await fetch(url, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.detail || `Request failed: ${res.status}`);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

// --- Profiles ---
export const getProfiles = () => jsonFetch("/api/profiles");
export const createProfile = (name) =>
  jsonFetch("/api/profiles", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
export const deleteProfile = (id) =>
  jsonFetch(`/api/profiles/${id}`, { method: "DELETE" });

// --- DAC paths ---
export const getDacPaths = () => jsonFetch("/api/dac-paths");
export const createDacPath = (name, notes) =>
  jsonFetch("/api/dac-paths", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, notes: notes || null }),
  });
export const patchDacPath = (id, patch) =>
  jsonFetch(`/api/dac-paths/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
export const deleteDacPath = (id) =>
  jsonFetch(`/api/dac-paths/${id}`, { method: "DELETE" });

// --- Tracks ---
export const getTracks = () => jsonFetch("/api/tracks");
export const addCurrentTrack = () =>
  jsonFetch("/api/tracks/add-current", { method: "POST" });

// --- Session setups ---
export const getSessionSetups = (profileId) =>
  jsonFetch(`/api/profiles/${profileId}/session-setups`);
export const createSessionSetup = (profileId, name) =>
  jsonFetch(`/api/profiles/${profileId}/session-setups`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
export const getSessionSetupDetail = (id) =>
  jsonFetch(`/api/session-setups/${id}`);
export const deleteSessionSetup = (id) =>
  jsonFetch(`/api/session-setups/${id}`, { method: "DELETE" });

// --- Playlist songs/segments ---
export const addSongToSetup = (setupId) =>
  jsonFetch(`/api/session-setups/${setupId}/songs`, { method: "POST" });
export const deleteSong = (songId) =>
  jsonFetch(`/api/songs/${songId}`, { method: "DELETE" });
export const markSegmentStart = (songId) =>
  jsonFetch(`/api/songs/${songId}/segments/mark-start`, { method: "POST" });
export const markSegmentEnd = (segmentId) =>
  jsonFetch(`/api/segments/${segmentId}/mark-end`, { method: "PATCH" });
export const patchSegment = (segmentId, patch) =>
  jsonFetch(`/api/segments/${segmentId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
export const deleteSegment = (segmentId) =>
  jsonFetch(`/api/segments/${segmentId}`, { method: "DELETE" });

// --- Preferences (session setup fields) ---
export const patchSessionSetup = (id, patch) =>
  jsonFetch(`/api/session-setups/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });

// --- Clicker mode ---
export const setMode = (mode) =>
  jsonFetch("/api/mode", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode }),
  });

// --- Free Play ---
export const startFreePlay = () => jsonFetch("/api/free-play/start", { method: "POST" });
export const stopFreePlay = () => jsonFetch("/api/free-play/stop", { method: "POST" });
