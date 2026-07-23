import { getDacPaths, createDacPath, deleteDacPath } from "./api.js";

let dacPaths = [];

async function loadDacPaths() {
  dacPaths = await getDacPaths();
  renderDacPaths();
}

function renderDacPaths() {
  const el = document.getElementById("dac-path-list");
  if (dacPaths.length === 0) {
    el.innerHTML = `<div class="text-xl text-slate-500 px-2 py-8 text-center">
      No DAC paths yet — add one below
    </div>`;
    return;
  }
  el.innerHTML = dacPaths
    .map(
      (d) => `
    <div class="flex items-center justify-between px-5 py-4 rounded-xl bg-slate-700">
      <div>
        <div class="text-2xl font-semibold">${d.name}</div>
        ${d.notes ? `<div class="text-lg text-slate-400">${d.notes}</div>` : ""}
      </div>
      <button onclick="removeDacPath(${d.id})"
        class="text-xl px-4 py-2 rounded-xl bg-slate-600 active:bg-red-800">
        Remove
      </button>
    </div>
  `
    )
    .join("");
}

async function promptNewDacPath() {
  const name = prompt("DAC path name (e.g. \"Chord Qutest\"):");
  if (!name || !name.trim()) return;
  const notes = prompt("Notes (optional):") || null;
  try {
    await createDacPath(name.trim(), notes);
    await loadDacPaths();
  } catch (err) {
    alert(err.message);
  }
}

async function removeDacPath(id) {
  if (!confirm("Remove this DAC path?")) return;
  try {
    await deleteDacPath(id);
    await loadDacPaths();
  } catch (err) {
    alert(err.message);
  }
}

export function initCalibrationPage() {
  loadDacPaths();
  window.promptNewDacPath = promptNewDacPath;
  window.removeDacPath = removeDacPath;
}
