let currentUrl = location.href;

async function isRecording() {
  const { recording } = await chrome.storage.local.get("recording");
  return recording === true;
}

/* Record initial navigation */
window.addEventListener("load", async () => {
  if (!(await isRecording())) return;

  await addStep({
    action: "navigate",
    url: location.href
  });
});

/* Detect SPA URL changes */
const observer = new MutationObserver(async () => {
  if (location.href !== currentUrl) {
    currentUrl = location.href;

    if (!(await isRecording())) return;

    await addStep({
      action: "navigate",
      url: currentUrl
    });
  }
});

observer.observe(document, { childList: true, subtree: true });

/* Click events */
document.addEventListener("click", async (e) => {
  if (!(await isRecording())) return;

  const el = e.target;
  const selector = getUniqueSelector(el);

  await addStep({
    action: "click",
    selector,
    selectorBackup: getXPath(el),
    text: el.innerText?.trim()?.slice(0, 120) || ""
  });
});

/* Input events */
document.addEventListener("input", async (e) => {
  if (!(await isRecording())) return;

  const el = e.target;
  const selector = getUniqueSelector(el);

  await addStep({
    action: "type",
    selector,
    value: el.value,
    placeholder: el.placeholder || ""
  });
});

/* When recording toggles ON, log current page */
chrome.storage.onChanged.addListener(async (changes) => {
  if (changes.recording && changes.recording.newValue === true) {
    await addStep({
      action: "navigate",
      url: location.href
    });
  }
});
