import { connectWS } from "./ws.js";
import { setMode } from "./api.js";
import { initSetupPage } from "./setup.js";
import { initSessionPage } from "./session.js";
import { initCalibrationPage } from "./calibration.js";

const PAGES = ["setup", "session", "complete", "calibration", "guide", "free_play"];
const NAV_HIDDEN_PAGES = new Set(["session", "free_play"]);

// Maps each page to the clicker mode that should be active while it's shown.
// null means the page manages its own mode transition (Free Play uses
// dedicated start/stop endpoints instead, since it also needs to reset
// state beyond just the mode string).
const PAGE_MODE_MAP = {
  setup: "setup",
  guide: "setup",
  calibration: "calibration",
  complete: "setup",
  session: "active_session",
  free_play: null,
};

export function showPage(name) {
  for (const p of PAGES) {
    document.getElementById(`page-${p}`).classList.toggle("hidden", p !== name);
  }
  document.getElementById("nav-bar").classList.toggle("hidden", NAV_HIDDEN_PAGES.has(name));
  const mode = PAGE_MODE_MAP[name];
  if (mode) setMode(mode);
}

function initNav() {
  document.querySelectorAll("[data-nav-page]").forEach((btn) => {
    btn.addEventListener("click", () => showPage(btn.dataset.navPage));
  });
}

initNav();
initSetupPage();
initSessionPage();
initCalibrationPage();
connectWS();
showPage("setup");
