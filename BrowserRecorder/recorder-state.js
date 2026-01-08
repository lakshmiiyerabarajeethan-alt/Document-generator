let stepId = 1;

async function addStep(step) {
  const data = await chrome.storage.local.get(["steps"]);
  const steps = data.steps || [];

  steps.push({
    id: stepId++,
    timestamp: Date.now(),
    ...step
  });

  await chrome.storage.local.set({ steps });
}
