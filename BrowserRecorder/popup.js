const startBtn               = document.getElementById("startBtn");
const stopBtn                = document.getElementById("stopBtn");
const downloadBtn            = document.getElementById("downloadBtn");
const downloadScreenshotsBtn = document.getElementById("downloadScreenshotsBtn");
const debugBtn               = document.getElementById("debugBtn");
const status                 = document.getElementById("status");
const debugInfo              = document.getElementById("debugInfo");

let debugVisible = false;

async function syncUI() {
  const { recording, steps, screenshots } = await chrome.storage.local.get(["recording", "steps", "screenshots"]);
  if (recording) {
    status.innerText = "Recording...";
    status.classList.add("recording");
    startBtn.disabled = true;
    stopBtn.disabled  = false;
    downloadBtn.disabled            = true;
    downloadScreenshotsBtn.disabled = true;
  } else {
    status.classList.remove("recording");
    startBtn.disabled = false;
    stopBtn.disabled  = true;
    const hasSteps       = steps?.length > 0;
    const hasScreenshots = screenshots?.length > 0;
    downloadBtn.disabled            = !hasSteps;
    downloadScreenshotsBtn.disabled = !hasScreenshots;
    status.innerText = hasSteps
      ? `Ready (${steps.length} steps, ${screenshots?.length || 0} screenshots)`
      : "Not recording";
  }
}

async function contentScriptAlive(tabId) {
  return new Promise(resolve => {
    chrome.tabs.sendMessage(tabId, { action: "ping" }, response => {
      resolve(!chrome.runtime.lastError && response?.alive === true);
    });
  });
}

async function injectContentScripts(tabId) {
  const files = ["selector-utils.js", "screenshot-manager.js", "recorder-state.js", "content.js"];
  for (const file of files) {
    await chrome.scripting.executeScript({ target: { tabId }, files: [file] });
  }
  console.log("✅ Scripts injected into tab", tabId);
}

// ------------------------------------------------------------------
// Start Recording
// ------------------------------------------------------------------
startBtn.onclick = async () => {
  status.innerText  = "Starting...";
  startBtn.disabled = true;

  // Reset storage — including recordingTabId from any previous session
  await chrome.storage.local.set({
    recording: false,
    steps: [],
    screenshots: [],
    recordingTabId: null
  });

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  if (!tab?.id || !tab.url?.startsWith("http")) {
    status.innerText  = "⚠️ Navigate to an http/https page first";
    startBtn.disabled = false;
    return;
  }

  try {
    const alive = await contentScriptAlive(tab.id);
    if (!alive) {
      console.log("Injecting content scripts into tab", tab.id);
      await injectContentScripts(tab.id);
      await new Promise(r => setTimeout(r, 300));
    }

    // Store the tab ID so content.js on OTHER tabs ignores storage events
    await chrome.storage.local.set({ recording: true, recordingTabId: tab.id });
    await syncUI();

  } catch (err) {
    console.error("Start recording failed:", err);
    status.innerText  = "⚠️ Injection failed — try reloading the page";
    startBtn.disabled = false;
  }
};

// ------------------------------------------------------------------
// Stop Recording
// ------------------------------------------------------------------
stopBtn.onclick = async () => {
  await chrome.storage.local.set({ recording: false });
  const { steps, screenshots } = await chrome.storage.local.get(["steps", "screenshots"]);
  console.log(`Stopped. Steps: ${steps?.length || 0}, Screenshots: ${screenshots?.length || 0}`);
  await syncUI();
};

// ------------------------------------------------------------------
// Download JSON
// ------------------------------------------------------------------
downloadBtn.onclick = async () => {
  const { steps, screenshots } = await chrome.storage.local.get(["steps", "screenshots"]);
  if (!steps?.length) { alert("No steps recorded."); return; }

  const stepsWithScreenshots = steps.map(step => {
    const shot = screenshots?.find(s => s.id === step.id);
    return shot ? { ...step, screenshot: shot.filename } : step;
  });

  const exportData = {
    metadata: {
      recordedAt:       new Date().toISOString(),
      totalSteps:       steps.length,
      totalScreenshots: screenshots?.length || 0,
      browser:          navigator.userAgent
    },
    steps: stepsWithScreenshots
  };

  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
  const url  = URL.createObjectURL(blob);
  const ts   = new Date().toISOString().replace(/[:.]/g, "-").slice(0, -5);

  chrome.downloads.download({ url, filename: `recorded_${ts}.json`, saveAs: true }, () => {
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
};

// ------------------------------------------------------------------
// Download Screenshots
// ------------------------------------------------------------------
downloadScreenshotsBtn.onclick = async () => {
  const { screenshots } = await chrome.storage.local.get("screenshots");
  if (!screenshots?.length) { alert("No screenshots captured."); return; }
  chrome.runtime.sendMessage(
    { action: "downloadScreenshots", screenshots, downloadPath: "screenshots" },
    r => r?.success && alert(`✅ Downloading ${screenshots.length} screenshots`)
  );
};

// ------------------------------------------------------------------
// Debug
// ------------------------------------------------------------------
debugBtn.onclick = async () => {
  const { recording, steps, screenshots, recordingTabId } = await chrome.storage.local.get(
    ["recording", "steps", "screenshots", "recordingTabId"]
  );
  const info = {
    recording,
    recordingTabId,
    stepCount:       steps?.length       || 0,
    screenshotCount: screenshots?.length || 0,
    steps:       (steps       || []).slice(0, 3),
    screenshots: (screenshots || []).slice(0, 2).map(s => ({
      id: s.id, filename: s.filename, dataUrlLength: s.dataUrl?.length || 0
    }))
  };
  debugInfo.innerHTML = `<pre>${JSON.stringify(info, null, 2)}</pre>`;
  debugInfo.style.display = debugVisible ? "none" : "block";
  debugVisible = !debugVisible;
};

chrome.storage.onChanged.addListener((_, area) => { if (area === "local") syncUI(); });
syncUI();