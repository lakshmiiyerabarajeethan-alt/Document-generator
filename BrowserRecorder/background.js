// Screenshot handler
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "captureScreenshot") {
    console.log("Screenshot request received from tab:", sender.tab?.id);
    
    if (!sender.tab || !sender.tab.windowId) {
      console.error("No valid tab or window ID");
      sendResponse({ screenshot: null, error: "No valid tab" });
      return true;
    }
    
    chrome.tabs.captureVisibleTab(
      sender.tab.windowId, 
      { format: "png" }, 
      (dataUrl) => {
        if (chrome.runtime.lastError) {
          console.error("Screenshot capture error:", chrome.runtime.lastError.message);
          sendResponse({ screenshot: null, error: chrome.runtime.lastError.message });
        } else {
          console.log("Screenshot captured successfully");
          sendResponse({ screenshot: dataUrl });
        }
      }
    );
    return true;
  }
  
  // Download screenshot handler
  if (msg.type === "downloadScreenshot") {
    console.log("Downloading screenshot:", msg.filename);
    
    chrome.downloads.download({
      url: msg.dataUrl,
      filename: msg.filename,
      conflictAction: 'uniquify',
      saveAs: false
    }, (downloadId) => {
      if (chrome.runtime.lastError) {
        console.error("Download error:", chrome.runtime.lastError.message);
        sendResponse({ success: false, error: chrome.runtime.lastError.message });
      } else {
        console.log("Screenshot downloaded, ID:", downloadId);
        sendResponse({ success: true, downloadId: downloadId });
      }
    });
    return true;
  }
});

// Badge update
chrome.storage.onChanged.addListener(async ({ recording }) => {
  if (!recording) return;
  if (recording.newValue === true) {
    chrome.action.setBadgeText({ text: "REC" });
    chrome.action.setBadgeBackgroundColor({ color: "#d93025" });
  } else {
    chrome.action.setBadgeText({ text: "" });
  }
});