const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const downloadBtn = document.getElementById("downloadBtn");
const debugBtn = document.getElementById("debugBtn");
const status = document.getElementById("status");
const debugInfo = document.getElementById("debugInfo");

let debugVisible = false;

async function syncUI() {
  const { recording, steps } = await chrome.storage.local.get(["recording", "steps"]);

  if (recording) {
    status.innerText = "Recording...";
    status.classList.add("recording");
    startBtn.disabled = true;
    stopBtn.disabled = false;
    downloadBtn.disabled = true;
  } else {
    status.classList.remove("recording");
    startBtn.disabled = false;
    stopBtn.disabled = true;
    
    // Enable download button only if steps exist
    const hasSteps = steps && steps.length > 0;
    downloadBtn.disabled = !hasSteps;
    
    if (hasSteps) {
      status.innerText = `Ready to download (${steps.length} steps)`;
    } else {
      status.innerText = "Not recording";
    }
  }
}

async function showDebugInfo() {
  const { recording, steps } = await chrome.storage.local.get(["recording", "steps"]);
  
  const info = {
    recording: recording,
    stepCount: steps ? steps.length : 0,
    steps: steps ? steps.slice(0, 3) : [], // Show first 3 steps
    storage: await chrome.storage.local.get(null)
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
    steps: []
  });
  await syncUI();
  console.log("Recording started");
};

// Stop Recording
stopBtn.onclick = async () => {
  console.log("Stopping recording...");
  await chrome.storage.local.set({ recording: false });
  const { steps } = await chrome.storage.local.get("steps");
  console.log(`Recording stopped. Total steps: ${steps ? steps.length : 0}`);
  await syncUI();
};

// Download JSON
downloadBtn.onclick = async () => {
  try {
    console.log("Download button clicked");
    
    // Get steps from storage
    const { steps } = await chrome.storage.local.get("steps");
    
    // Validate steps
    if (!steps || steps.length === 0) {
      console.error("No steps found in storage");
      alert("No steps recorded. Please record some actions first.");
      return;
    }
    
    console.log(`Preparing to download ${steps.length} steps`);
    
    // Create JSON string with pretty formatting
    const jsonString = JSON.stringify(steps, null, 2);
    console.log("JSON size:", jsonString.length, "bytes");
    
    // Create blob
    const blob = new Blob([jsonString], {
      type: "application/json"
    });
    console.log("Blob created:", blob.size, "bytes");

    // Create object URL
    const url = URL.createObjectURL(blob);
    console.log("Object URL created:", url);
    
    // Generate filename with timestamp
    const now = new Date();
    const timestamp = now.toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const filename = `recorded_test_${timestamp}.json`;
    console.log("Filename:", filename);
    
    // Try chrome.downloads API first (requires downloads permission)
    if (chrome.downloads && chrome.downloads.download) {
      console.log("Using chrome.downloads API");
      chrome.downloads.download({
        url: url,
        filename: filename,
        saveAs: true
      }, (downloadId) => {
        if (chrome.runtime.lastError) {
          console.error("chrome.downloads error:", chrome.runtime.lastError);
          // Fallback to anchor method
          downloadWithAnchor(url, filename);
        } else {
          console.log("Download started successfully. ID:", downloadId);
          setTimeout(() => URL.revokeObjectURL(url), 1000);
        }
      });
    } else {
      // Fallback to anchor element method
      console.log("chrome.downloads not available, using anchor method");
      downloadWithAnchor(url, filename);
    }
    
  } catch (error) {
    console.error("Error in download process:", error);
    alert(`Error downloading JSON: ${error.message}\n\nCheck the console for details.`);
  }
};

// Fallback download method using anchor element
function downloadWithAnchor(url, filename) {
  console.log("Using anchor download method");
  
  try {
    // Create anchor element
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.style.display = "none";
    
    // Add to document
    document.body.appendChild(a);
    console.log("Anchor element created and added to DOM");
    
    // Trigger click
    a.click();
    console.log("Anchor clicked");
    
    // Cleanup after a short delay
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

// Listen for storage changes to update UI automatically
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