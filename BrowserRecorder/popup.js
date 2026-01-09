const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const downloadBtn = document.getElementById("downloadBtn");
const status = document.getElementById("status");

let recordingInProgress = false;

// Initialize UI state
chrome.storage.local.get({ recording: false }, (data) => {
  if (data.recording) {
    startBtn.disabled = true;
    stopBtn.disabled = false;
    downloadBtn.disabled = true;
    status.textContent = "Recording...";
  } else {
    startBtn.disabled = false;
    stopBtn.disabled = true;
    downloadBtn.disabled = false;
    status.textContent = "Ready";
  }
});

// Start recording
startBtn.onclick = async () => {
  chrome.storage.local.set({ recording: true, steps: [] }, () => {
    if (chrome.runtime.lastError) {
      console.error("Error starting recording:", chrome.runtime.lastError);
      return;
    }
    startBtn.disabled = true;
    stopBtn.disabled = false;
    downloadBtn.disabled = true;
    status.textContent = "Recording...";
  });
};

// Stop recording
stopBtn.onclick = async () => {
  chrome.storage.local.set({ recording: false }, () => {
    if (chrome.runtime.lastError) {
      console.error("Error stopping recording:", chrome.runtime.lastError);
      return;
    }
    startBtn.disabled = false;
    stopBtn.disabled = true;
    downloadBtn.disabled = false;
    status.textContent = "Recording stopped. Ready to download.";
  });
};

// Download JSON
downloadBtn.onclick = async () => {
  // Check if any recording is in progress
  const result = await chrome.storage.local.get({ recordingInProgress: false });
  if (result.recordingInProgress) {
    alert("Please wait, steps are still being saved.");
    return;
  }

  const steps = await new Promise((resolve) => {
    chrome.storage.local.get({ steps: [] }, (data) => resolve(data.steps || []));
  });

  if (!steps || steps.length === 0) {
    alert("No steps recorded yet!");
    return;
  }

  const blob = new Blob([JSON.stringify(steps, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "recorded_test.json";
  a.click();
  URL.revokeObjectURL(url);
};