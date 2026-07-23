import { showPage } from "./main.js";

let trialCount = null;
let currentTrial = 1;
let sessionSeed = null;
let sessionTimer = null;

export function startSessionScreen(numTrials) {
  trialCount = numTrials;
  sessionSeed = Math.floor(1000 + Math.random() * 9000);
  currentTrial = 1;
  document.getElementById("session-seed").textContent = sessionSeed;
  document.getElementById("trial-counter").textContent = `Trial ${currentTrial} of ${trialCount}`;
  document.getElementById("playback-status").textContent = "Playing";

  // Mock trial advance on a timer — replaced by real next-trial API in Phase 5
  clearInterval(sessionTimer);
  sessionTimer = setInterval(() => {
    currentTrial++;
    if (currentTrial > trialCount) {
      clearInterval(sessionTimer);
      completeSession();
      return;
    }
    document.getElementById("trial-counter").textContent = `Trial ${currentTrial} of ${trialCount}`;
  }, 4000);
}

function completeSession() {
  document.getElementById("complete-seed").textContent = sessionSeed;
  document.getElementById("complete-trials").textContent = `${trialCount} trials completed`;
  showPage("complete");
}

function newSession() {
  showPage("setup");
}

export function initSessionPage() {
  window.newSession = newSession;
}
