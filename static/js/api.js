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
