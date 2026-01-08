async function showRecordedSteps() {
  const { steps } = await chrome.storage.local.get("steps");
  console.log("Recorded Steps:", steps);
  return steps;
}

async function clearSteps() {
  await chrome.storage.local.set({ steps: [] });
  console.log("Steps cleared");
}

async function printSelectors() {
  document.querySelectorAll("*").forEach(el => {
    const sel = getUniqueSelector(el);
    if (sel) console.log(sel);
  });
}

console.log("Playground loaded. Available:");
console.log("showRecordedSteps()");
console.log("clearSteps()");
console.log("printSelectors()");
