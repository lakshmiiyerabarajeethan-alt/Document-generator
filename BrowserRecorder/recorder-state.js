let stepId = 1;

async function addStep(step) {
  console.log("addStep called with:", { ...step, screenshot: step.screenshot ? "present" : "missing" });
  
  const data = await new Promise(resolve => {
    chrome.storage.local.get({ steps: [] }, (data) => resolve(data));
  });
  
  const steps = data.steps || [];
  const newStep = { id: stepId++, timestamp: Date.now(), ...step };
  
  steps.push(newStep);
  
  await new Promise(resolve => {
    chrome.storage.local.set({ steps }, () => {
      if (chrome.runtime.lastError) {
        console.error("Error saving step:", chrome.runtime.lastError);
      } else {
        console.log("Step saved to storage, total steps:", steps.length);
      }
      resolve();
    });
  });
}