const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const downloadBtn = document.getElementById("downloadBtn");
const downloadScreenshotsBtn = document.getElementById("downloadScreenshotsBtn");
const debugBtn = document.getElementById("debugBtn");
const status = document.getElementById("status");
const debugInfo = document.getElementById("debugInfo");

let debugVisible = false;

async function syncUI() {
  const { recording, steps, screenshots } = await chrome.storage.local.get(["recording", "steps", "screenshots"]);

  if (recording) {
    status.innerText = "Recording...";
    status.classList.add("recording");
    startBtn.disabled = true;
    stopBtn.disabled = false;
    downloadBtn.disabled = true;
    downloadScreenshotsBtn.disabled = true;
  } else {
    status.classList.remove("recording");
    startBtn.disabled = false;
    stopBtn.disabled = true;
    
    // Enable download buttons only if data exists
    const hasSteps = steps && steps.length > 0;
    const hasScreenshots = screenshots && screenshots.length > 0;
    
    downloadBtn.disabled = !hasSteps;
    downloadScreenshotsBtn.disabled = !hasScreenshots;
    
    if (hasSteps) {
      status.innerText = `Ready (${steps.length} steps, ${hasScreenshots ? screenshots.length : 0} screenshots)`;
    } else {
      status.innerText = "Not recording";
    }
  }
}

async function showDebugInfo() {
  const { recording, steps, screenshots } = await chrome.storage.local.get(["recording", "steps", "screenshots"]);
  
  const info = {
    recording: recording,
    stepCount: steps ? steps.length : 0,
    screenshotCount: screenshots ? screenshots.length : 0,
    steps: steps ? steps.slice(0, 3) : [],
    screenshots: screenshots ? screenshots.slice(0, 2).map(s => ({
      id: s.id,
      filename: s.filename,
      timestamp: s.timestamp,
      dataUrlLength: s.dataUrl?.length || 0
    })) : []
  };
  
  debugInfo.innerHTML = `<pre>${JSON.stringify(info, null, 2)}</pre>`;
  debugInfo.style.display = debugVisible ? "none" : "block";
  debugVisible = !debugVisible;
}

// Initialize UI
syncUI();

// Start Recording
startBtn.onclick = async () => {
  console.log("Starting recording...");
  await chrome.storage.local.set({
    recording: true,
    steps: [],
    screenshots: []
  });
  await syncUI();
  console.log("Recording started");
};

// Stop Recording
stopBtn.onclick = async () => {
  console.log("Stopping recording...");
  await chrome.storage.local.set({ recording: false });
  const { steps, screenshots } = await chrome.storage.local.get(["steps", "screenshots"]);
  console.log(`Recording stopped. Steps: ${steps?.length || 0}, Screenshots: ${screenshots?.length || 0}`);
  await syncUI();
};

// Download JSON
downloadBtn.onclick = async () => {
  try {
    console.log("Download button clicked");
    
    const { steps, screenshots } = await chrome.storage.local.get(["steps", "screenshots"]);
    
    if (!steps || steps.length === 0) {
      console.error("No steps found in storage");
      alert("No steps recorded. Please record some actions first.");
      return;
    }
    
    console.log(`Preparing to download ${steps.length} steps`);
    
    // Add screenshot references to steps
    const stepsWithScreenshots = steps.map(step => {
      const screenshot = screenshots?.find(s => s.id === step.id);
      if (screenshot) {
        return {
          ...step,
          screenshot: screenshot.filename,
          screenshotUrl: screenshot.dataUrl?.substring(0, 100) + '...' // Truncate for JSON size
        };
      }
      return step;
    });
    
    // Create JSON with metadata
    const exportData = {
      metadata: {
        recordedAt: new Date().toISOString(),
        totalSteps: steps.length,
        totalScreenshots: screenshots?.length || 0,
        browser: navigator.userAgent
      },
      steps: stepsWithScreenshots
    };
    
    const jsonString = JSON.stringify(exportData, null, 2);
    console.log("JSON size:", jsonString.length, "bytes");
    
    const blob = new Blob([jsonString], {
      type: "application/json"
    });
    console.log("Blob created:", blob.size, "bytes");

    const url = URL.createObjectURL(blob);
    console.log("Object URL created:", url);
    
    const now = new Date();
    const timestamp = now.toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const filename = `recorded_test_${timestamp}.json`;
    console.log("Filename:", filename);
    
    if (chrome.downloads && chrome.downloads.download) {
      console.log("Using chrome.downloads API");
      chrome.downloads.download({
        url: url,
        filename: filename,
        saveAs: true
      }, (downloadId) => {
        if (chrome.runtime.lastError) {
          console.error("chrome.downloads error:", chrome.runtime.lastError);
          downloadWithAnchor(url, filename);
        } else {
          console.log("Download started successfully. ID:", downloadId);
          setTimeout(() => URL.revokeObjectURL(url), 1000);
        }
      });
    } else {
      console.log("chrome.downloads not available, using anchor method");
      downloadWithAnchor(url, filename);
    }
    
  } catch (error) {
    console.error("Error in download process:", error);
    alert(`Error downloading JSON: ${error.message}\n\nCheck the console for details.`);
  }
};

// Download Screenshots
downloadScreenshotsBtn.onclick = async () => {
  try {
    const { screenshots } = await chrome.storage.local.get("screenshots");
    
    if (!screenshots || screenshots.length === 0) {
      alert("No screenshots captured. Make sure recording captured screenshots.");
      return;
    }
    
    console.log(`Downloading ${screenshots.length} screenshots...`);
    
    // Ask user to select download location
    const downloadPath = "screenshots"; // This will create a screenshots folder in Downloads
    
    // Send message to background script to handle downloads
    chrome.runtime.sendMessage({
      action: 'downloadScreenshots',
      screenshots: screenshots,
      downloadPath: 'screenshots'
    }, (response) => {
      if (response?.success) {
        alert(`✅ Successfully downloading ${screenshots.length} screenshots!\n\nThey will be saved to your Downloads/screenshots folder.`);
      } else {
        alert("Error downloading screenshots. Check console for details.");
      }
    });
    
  } catch (error) {
    console.error("Error downloading screenshots:", error);
    alert(`Error: ${error.message}`);
  }
};

// Fallback download method
function downloadWithAnchor(url, filename) {
  console.log("Using anchor download method");
  
  try {
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.style.display = "none";
    
    document.body.appendChild(a);
    console.log("Anchor element created and added to DOM");
    
    a.click();
    console.log("Anchor clicked");
    
    setTimeout(() => {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      console.log("Anchor removed and URL revoked");
    }, 100);
    
    console.log("Download should have started");
    
  } catch (error) {
    console.error("Error in anchor download:", error);
    alert(`Download failed: ${error.message}`);
  }
}

// Debug button
debugBtn.onclick = showDebugInfo;

// Listen for storage changes
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === "local") {
    console.log("Storage changed:", changes);
    syncUI();
  }
});

// Log initial state
console.log("Popup loaded");
chrome.storage.local.get(null, (data) => {
  console.log("Initial storage state:", data);
});