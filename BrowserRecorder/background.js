chrome.storage.onChanged.addListener(async ({ recording }) => {
  if (!recording) return;

  if (recording.newValue === true) {
    chrome.action.setBadgeText({ text: "REC" });
    chrome.action.setBadgeBackgroundColor({ color: "#d93025" });
  } else {
    chrome.action.setBadgeText({ text: "" });
  }
});
