let currentUrl = location.href;
let screenshotManager = null;

async function isRecording() {
  const { recording } = await chrome.storage.local.get("recording");
  return recording === true;
}

// Initialize screenshot manager
function initScreenshotManager() {
  if (window.ScreenshotManager) {
    screenshotManager = new window.ScreenshotManager();
    console.log('📸 Screenshot manager initialized');
  }
}

/* Record initial navigation */
window.addEventListener("load", async () => {
  if (!(await isRecording())) return;
  
  initScreenshotManager();

  const stepId = await addStep({
    action: "navigate",
    url: location.href
  });
  
  // Capture screenshot for navigation
  if (screenshotManager) {
    await screenshotManager.captureSimple(stepId);
  }
});

/* Detect SPA URL changes */
const observer = new MutationObserver(async () => {
  if (location.href !== currentUrl) {
    currentUrl = location.href;

    if (!(await isRecording())) return;

    const stepId = await addStep({
      action: "navigate",
      url: currentUrl
    });
    
    // Capture screenshot for navigation
    if (screenshotManager) {
      // Wait a bit for page to render
      setTimeout(async () => {
        await screenshotManager.captureSimple(stepId);
      }, 500);
    }
  }
});

observer.observe(document, { childList: true, subtree: true });

/* Click events */
document.addEventListener("click", async (e) => {
  if (!(await isRecording())) return;

  const el = e.target;
  const selector = getUniqueSelector(el);

  const stepId = await addStep({
    action: "click",
    selector,
    selectorBackup: getXPath(el),
    text: el.innerText?.trim()?.slice(0, 120) || ""
  });
  
  // Capture screenshot with element highlighted
  if (screenshotManager) {
    await screenshotManager.captureWithHighlight(el, stepId);
  }
});

/* Input events - capture on blur to get final value */
const inputTimers = new Map();

document.addEventListener("input", async (e) => {
  if (!(await isRecording())) return;

  const el = e.target;
  const selector = getUniqueSelector(el);
  
  // Clear existing timer for this element
  if (inputTimers.has(el)) {
    clearTimeout(inputTimers.get(el));
  }
  
  // Set new timer to capture after user stops typing
  const timer = setTimeout(async () => {
    const stepId = await addStep({
      action: "type",
      selector,
      value: el.value,
      placeholder: el.placeholder || ""
    });
    
    // Capture screenshot of input field
    if (screenshotManager) {
      await screenshotManager.captureWithHighlight(el, stepId);
    }
    
    inputTimers.delete(el);
  }, 1000); // Wait 1 second after last keystroke
  
  inputTimers.set(el, timer);
});

/* When recording toggles ON, log current page and init screenshot manager */
chrome.storage.onChanged.addListener(async (changes) => {
  if (changes.recording) {
    if (changes.recording.newValue === true) {
      // Recording started
      initScreenshotManager();
      
      // Clear old screenshots
      if (window.ScreenshotManager) {
        await window.ScreenshotManager.clearScreenshots();
      }
      
      const stepId = await addStep({
        action: "navigate",
        url: location.href
      });
      
      // Capture initial screenshot
      if (screenshotManager) {
        await screenshotManager.captureSimple(stepId);
      }
    } else {
      // Recording stopped
      console.log('📸 Recording stopped, screenshots saved');
    }
  }
});