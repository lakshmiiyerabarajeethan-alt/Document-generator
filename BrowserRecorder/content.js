// Guard: prevent duplicate listener registration on re-injection
if (window.__recorderListenersAttached) {
  console.log("🔄 content.js re-injected — skipping duplicate listener setup");
} else {
  window.__recorderListenersAttached = true;
  initRecorder();
}

function initRecorder() {
  let currentUrl = location.href;

  // ------------------------------------------------------------------
  // Tab identity check — only the tab that started recording should
  // capture steps and screenshots. All other tabs ignore events.
  // ------------------------------------------------------------------
  async function isActiveRecordingTab() {
    const { recording, recordingTabId } = await chrome.storage.local.get(["recording", "recordingTabId"]);
    if (!recording) return false;

    return new Promise(resolve => {
      chrome.runtime.sendMessage({ action: "getTabId" }, response => {
        if (chrome.runtime.lastError || !response?.tabId) {
          // If we can't verify, allow (e.g. freshly injected tab)
          resolve(true);
        } else {
          resolve(response.tabId === recordingTabId);
        }
      });
    });
  }

  function getScreenshotManager() {
    return window.__screenshotManager || null;
  }

  function initScreenshotManager() {
    if (window.__screenshotManager) return;
    let attempts = 0;
    const tryInit = () => {
      if (window.ScreenshotManager) {
        window.__screenshotManager = new window.ScreenshotManager();
        console.log("📸 ScreenshotManager ready");
      } else if (attempts++ < 10) {
        setTimeout(tryInit, 200);
      } else {
        console.warn("⚠️ ScreenshotManager unavailable");
      }
    };
    tryInit();
  }

  // ------------------------------------------------------------------
  // Cooldown: block screenshots for 2s after one fires on same screen.
  // Navigation always resets it.
  // ------------------------------------------------------------------
  let lastScreenshotAt = 0;
  const COOLDOWN_MS = 2000;

  function screenshotAllowed() {
    return (Date.now() - lastScreenshotAt) > COOLDOWN_MS;
  }
  function markScreenshotTaken() {
    lastScreenshotAt = Date.now();
  }
  function resetCooldown() {
    lastScreenshotAt = 0;
  }

  // ------------------------------------------------------------------
  // Screenshot gate — meaningful completion actions only.
  // Input field focus clicks are explicitly excluded.
  // ------------------------------------------------------------------
  const COMPLETION_KEYWORDS = [
    "submit", "confirm", "apply", "done", "finish", "complete", "proceed",
    "upload", "attach", "import", "choose file", "select file", "browse",
    "search", "find", "filter", "query",
    "save", "update", "publish", "post",
    "login", "log in", "sign in", "signin", "logout", "log out", "sign out",
    "delete", "remove", "reject", "approve",
    "send", "next", "continue", "create",
  ];

  const INPUT_TAGS = new Set(["input", "textarea", "select"]);

  function isMeaningfulAction(el) {
    if (!el) return false;
    const tag  = el.tagName.toLowerCase();
    const type = (el.type || "").toLowerCase();
    const role = (el.getAttribute("role") || "").toLowerCase();

    if (INPUT_TAGS.has(tag) && type !== "file" && type !== "submit" && type !== "button") {
      return false;
    }

    if (tag === "input" && type === "file")                          return true;
    if (tag === "input" && (type === "submit" || type === "button")) return true;

    const isButtonLike = tag === "button" || role === "button" || !!el.closest("button");
    if (!isButtonLike) return false;

    const btn = el.closest("button");
    const combined = [
      el.innerText, el.value,
      el.getAttribute("aria-label"), el.getAttribute("title"), el.getAttribute("data-action"),
      btn?.innerText
    ].filter(Boolean).join(" ").toLowerCase();

    return COMPLETION_KEYWORDS.some(kw => combined.includes(kw));
  }

  // ------------------------------------------------------------------
  // Initial page load
  // ------------------------------------------------------------------
  window.addEventListener("load", async () => {
    if (!(await isActiveRecordingTab())) return;
    initScreenshotManager();
    resetCooldown();
    const sid = await window.addStep({ action: "navigate", url: location.href });
    const sm = getScreenshotManager();
    if (sm) { await sm.captureSimple(sid); markScreenshotTaken(); }
  });

  // ------------------------------------------------------------------
  // SPA navigation
  // ------------------------------------------------------------------
  new MutationObserver(async () => {
    if (location.href !== currentUrl) {
      currentUrl = location.href;
      if (!(await isActiveRecordingTab())) return;
      resetCooldown();
      const sid = await window.addStep({ action: "navigate", url: currentUrl });
      const sm = getScreenshotManager();
      if (sm) {
        setTimeout(() => { sm.captureSimple(sid); markScreenshotTaken(); }, 500);
      }
    }
  }).observe(document, { childList: true, subtree: true });

  // ------------------------------------------------------------------
  // Clicks
  // ------------------------------------------------------------------
  document.addEventListener("click", async (e) => {
    if (!(await isActiveRecordingTab())) return;
    const el  = e.target;
    const sid = await window.addStep({
      action:         "click",
      selector:       getUniqueSelector(el),
      selectorBackup: getXPath(el),
      text:           el.innerText?.trim()?.slice(0, 120) || ""
    });
    const sm = getScreenshotManager();
    if (sm && isMeaningfulAction(el) && screenshotAllowed()) {
      console.log("📸 Capturing screenshot for:", el.innerText?.trim());
      setTimeout(() => { sm.captureWithHighlight(el, sid); markScreenshotTaken(); }, 300);
    }
  });

  // ------------------------------------------------------------------
  // Typing — step only, no screenshot
  // ------------------------------------------------------------------
  const inputTimers = new Map();
  document.addEventListener("input", async (e) => {
    if (!(await isActiveRecordingTab())) return;
    const el = e.target;
    if (inputTimers.has(el)) clearTimeout(inputTimers.get(el));
    inputTimers.set(el, setTimeout(async () => {
      await window.addStep({
        action:      "type",
        selector:    getUniqueSelector(el),
        value:       el.value,
        placeholder: el.placeholder || ""
      });
      inputTimers.delete(el);
    }, 1000));
  });

  // ------------------------------------------------------------------
  // Storage change: recording flipped ON from popup
  // ------------------------------------------------------------------
  chrome.storage.onChanged.addListener(async (changes) => {
    if (!changes.recording) return;
    if (changes.recording.newValue === true) {
      // Only the recording tab initialises
      const isMe = await isActiveRecordingTab();
      if (!isMe) return;

      window.__stepId = 1;
      window.__screenshotManager = null;
      resetCooldown();
      initScreenshotManager();
      if (window.ScreenshotManager) await window.ScreenshotManager.clearScreenshots();
      setTimeout(async () => {
        await window.addStep({ action: "navigate", url: location.href });
      }, 300);
    } else {
      console.log("⏹ Recording stopped");
    }
  });

  console.log("✅ Recorder active on:", location.href);
}

// ------------------------------------------------------------------
// Message handlers
// ------------------------------------------------------------------
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "ping") {
    sendResponse({ alive: true });
  }
});