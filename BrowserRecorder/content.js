let currentUrl = location.href;
let screenshotCounter = 1;

// ----------------------
// Check if extension context is valid
// ----------------------
function isContextValid() {
  try {
    return chrome.runtime?.id !== undefined;
  } catch {
    return false;
  }
}

// ----------------------
// Check if recording
// ----------------------
async function isRecording() {
  if (!isContextValid()) return false;
  
  try {
    return new Promise((resolve) => {
      chrome.storage.local.get({ recording: false }, (data) => {
        if (chrome.runtime.lastError) {
          console.error("Storage error:", chrome.runtime.lastError);
          resolve(false);
        } else {
          resolve(data.recording === true);
        }
      });
    });
  } catch (error) {
    console.error("isRecording error:", error);
    return false;
  }
}

// ----------------------
// Set recording in progress flag
// ----------------------
async function setRecordingInProgress(inProgress) {
  if (!isContextValid()) return;
  
  try {
    return new Promise((resolve) => {
      chrome.storage.local.set({ recordingInProgress: inProgress }, () => {
        if (chrome.runtime.lastError) {
          console.error("Storage error:", chrome.runtime.lastError);
        }
        resolve();
      });
    });
  } catch (error) {
    console.error("setRecordingInProgress error:", error);
  }
}

// ----------------------
// Download screenshot to file
// ----------------------
async function downloadScreenshot(dataUrl) {
  if (!dataUrl) return null;
  
  const timestamp = Date.now();
  const filename = `screenshots/screenshot_${timestamp}_${screenshotCounter++}.png`;
  
  try {
    // Send message to background to download the screenshot
    return new Promise((resolve) => {
      chrome.runtime.sendMessage({ 
        type: "downloadScreenshot", 
        dataUrl: dataUrl,
        filename: filename
      }, (response) => {
        if (chrome.runtime.lastError) {
          console.error("Download error:", chrome.runtime.lastError.message);
          resolve(null);
        } else {
          console.log("Screenshot saved as:", filename);
          resolve(filename);
        }
      });
    });
  } catch (error) {
    console.error("Error downloading screenshot:", error);
    return null;
  }
}

// ----------------------
// Capture screenshot
// ----------------------
async function captureScreenshot() {
  if (!isContextValid()) {
    console.error("Extension context invalidated");
    return null;
  }
  
  console.log("Requesting screenshot...");
  
  return new Promise((resolve) => {
    try {
      chrome.runtime.sendMessage({ type: "captureScreenshot" }, async (response) => {
        if (chrome.runtime.lastError) {
          console.error("Screenshot error:", chrome.runtime.lastError.message);
          resolve(null);
        } else if (!response) {
          console.error("No response received from background");
          resolve(null);
        } else if (!response.screenshot) {
          console.error("No screenshot in response:", response.error || "Unknown error");
          resolve(null);
        } else {
          console.log("Screenshot received, downloading...");
          const filename = await downloadScreenshot(response.screenshot);
          resolve(filename);
        }
      });
    } catch (error) {
      console.error("Error sending message:", error);
      resolve(null);
    }
  });
}

// ----------------------
// Highlight element
// ----------------------
async function highlightAndScreenshot(el) {
  if (!el) return await captureScreenshot();
  const originalOutline = el.style.outline;
  el.style.outline = "3px solid red";
  await new Promise(r => setTimeout(r, 150));
  const screenshotFile = await captureScreenshot();
  el.style.outline = originalOutline;
  return screenshotFile;
}

// ----------------------
// Add step
// ----------------------
async function addStepWithScreenshot(step) {
  console.log("Adding step:", step.action);
  await setRecordingInProgress(true);
  
  const screenshotFile = step.el ? await highlightAndScreenshot(step.el) : await captureScreenshot();
  
  if (screenshotFile) {
    console.log("Screenshot saved:", screenshotFile);
  } else {
    console.warn("No screenshot captured for step:", step.action);
  }
  
  delete step.el;
  
  await addStep({ ...step, screenshot: screenshotFile });
  await setRecordingInProgress(false);
  console.log("Step saved");
}

// ----------------------
// Record navigation
// ----------------------
window.addEventListener("load", async () => {
  if (!(await isRecording())) return;
  await addStepWithScreenshot({ action: "navigate", url: location.href });
});

// ----------------------
// SPA URL changes
// ----------------------
const observer = new MutationObserver(async () => {
  if (location.href !== currentUrl) {
    currentUrl = location.href;
    if (!(await isRecording())) return;
    await addStepWithScreenshot({ action: "navigate", url: currentUrl });
  }
});
observer.observe(document, { childList: true, subtree: true });

// ----------------------
// Click events
// ----------------------
document.addEventListener("click", async (e) => {
  if (!(await isRecording())) return;
  const el = e.target;
  await addStepWithScreenshot({
    action: "click",
    selector: getUniqueSelector(el),
    selectorBackup: getXPath(el),
    text: el.innerText?.trim()?.slice(0, 120) || "",
    el
  });
}, true);

// ----------------------
// Input events
// ----------------------
document.addEventListener("input", async (e) => {
  if (!(await isRecording())) return;
  const el = e.target;
  await addStepWithScreenshot({
    action: "type",
    selector: getUniqueSelector(el),
    value: el.value,
    placeholder: el.placeholder || "",
    el
  });
});

// ----------------------
// Recording toggled on
// ----------------------
chrome.storage.onChanged.addListener(async (changes) => {
  if (changes.recording && changes.recording.newValue === true) {
    currentUrl = location.href;
    screenshotCounter = 1; // Reset counter
    await addStepWithScreenshot({ action: "navigate", url: location.href });
  }
});