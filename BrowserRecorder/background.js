// SAFELY listen for storage changes (MV3 compatible)
if (chrome.storage && chrome.storage.onChanged) {
  chrome.storage.onChanged.addListener(({ recording }) => {
    if (!recording) return;

    if (recording.newValue === true) {
      chrome.action.setBadgeText({ text: "REC" });
      chrome.action.setBadgeBackgroundColor({ color: "#d93025" });
    } else {
      chrome.action.setBadgeText({ text: "" });
    }
  });
}

// Listen for storage changes to update badge
chrome.storage.onChanged.addListener(async ({ recording }) => {
  if (!recording) return;

  if (recording.newValue === true) {
    chrome.action.setBadgeText({ text: "REC" });
    chrome.action.setBadgeBackgroundColor({ color: "#d93025" });
  } else {
    chrome.action.setBadgeText({ text: "" });
  }
});

// Handle messages
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {

  // 🔴 FIXED screenshot capture
  if (request.action === 'captureScreenshot') {

    if (!sender.tab || sender.tab.windowId === undefined) {
      sendResponse({
        success: false,
        error: "No active tab/window for screenshot"
      });
      return;
    }

    // Ensure tab is active (IMPORTANT)
    chrome.tabs.update(sender.tab.id, { active: true }, () => {

      chrome.tabs.captureVisibleTab(
        sender.tab.windowId,
        { format: 'png' },
        (dataUrl) => {
          if (chrome.runtime.lastError) {
            console.error('Capture error:', chrome.runtime.lastError.message);
            sendResponse({
              success: false,
              error: chrome.runtime.lastError.message
            });
          } else {
            sendResponse({
              success: true,
              dataUrl
            });
          }
        }
      );
    });

    return true; // async
  }

  // Download screenshots
  if (request.action === 'downloadScreenshots') {
    downloadAllScreenshots(request.screenshots, request.downloadPath);
    sendResponse({ success: true });
    return true;
  }
});

/**
 * Download all screenshots as individual files
 */
async function downloadAllScreenshots(screenshots, basePath = 'screenshots') {
  if (!screenshots || screenshots.length === 0) {
    console.warn("No screenshots to download");
    return;
  }

  console.log(`⬇ Downloading ${screenshots.length} screenshots...`);

  for (let i = 0; i < screenshots.length; i++) {
    const screenshot = screenshots[i];

    try {
      if (!screenshot.dataUrl) {
        console.warn("Missing dataUrl for", screenshot.filename);
        continue;
      }

      await chrome.downloads.download({
        url: screenshot.dataUrl, // ✅ IMPORTANT: use dataUrl directly
        filename: `${basePath}/${screenshot.filename}`,
        saveAs: false,
        conflictAction: "overwrite"
      });

      // throttle downloads (Chrome requirement)
      await new Promise(r => setTimeout(r, 200));

    } catch (err) {
      console.error("Download failed:", err);
    }
  }

  console.log("✅ Screenshot download completed");
}
