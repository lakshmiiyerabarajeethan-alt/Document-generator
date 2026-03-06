// Use window globals so re-injection never throws "already declared"
window.__stepId = window.__stepId || 1;

window.addStep = async function addStep(step) {
  console.log("addStep called:", step.action, step.url || step.text || "");

  const data = await new Promise(resolve =>
    chrome.storage.local.get({ steps: [] }, resolve)
  );

  const steps  = data.steps || [];
  const newStep = { id: window.__stepId++, timestamp: Date.now(), ...step };
  steps.push(newStep);

  await new Promise(resolve =>
    chrome.storage.local.set({ steps }, () => {
      if (chrome.runtime.lastError) {
        console.error("Error saving step:", chrome.runtime.lastError);
      } else {
        console.log("Step saved — total:", steps.length);
      }
      resolve();
    })
  );

  return newStep.id;
};