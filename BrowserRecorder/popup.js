const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const downloadBtn = document.getElementById("downloadBtn");
const status = document.getElementById("status");

async function syncUI() {
  const { recording, steps } = await chrome.storage.local.get(["recording", "steps"]);

  if (recording) {
    status.innerText = "Recording...";
    startBtn.disabled = true;
    stopBtn.disabled = false;
    downloadBtn.disabled = true;
  } else {
    status.innerText = "Not recording";
    startBtn.disabled = false;
    stopBtn.disabled = true;
    downloadBtn.disabled = !(steps && steps.length > 0);
  }
}

syncUI();

startBtn.onclick = async () => {
  await chrome.storage.local.set({
    recording: true,
    steps: []
  });
  await syncUI();
};

stopBtn.onclick = async () => {
  await chrome.storage.local.set({ recording: false });
  await syncUI();
};

downloadBtn.onclick = async () => {
  const { steps } = await chrome.storage.local.get("steps");

  const blob = new Blob([JSON.stringify(steps, null, 2)], {
    type: "application/json"
  });

  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "recorded_test.json";
  a.click();
};
