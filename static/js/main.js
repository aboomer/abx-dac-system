import { connectWS } from "./ws.js";
import { initSetupPage } from "./setup.js";
import { initSessionPage } from "./session.js";
import { initCalibrationPage } from "./calibration.js";

const PAGES = ["setup", "session", "complete", "calibration", "guide"];
const NAV_HIDDEN_PAGES = new Set(["session"]); // Free Play joins this in Stage 4

export function showPage(name) {
  for (const p of PAGES) {
    document.getElementById(`page-${p}`).classList.toggle("hidden", p !== name);
  }
  document.getElementById("nav-bar").classList.toggle("hidden", NAV_HIDDEN_PAGES.has(name));
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
