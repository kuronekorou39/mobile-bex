const output = document.getElementById("output");
const evalOutput = document.getElementById("eval-output");

// Get the current active tab and run a script on it
async function execOnActiveTab(func) {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: false });
  if (!tab) {
    return { error: "No active tab found" };
  }
  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func
    });
    return { result: results[0].result };
  } catch (e) {
    return { error: e.message };
  }
}

// Show inspected page info
document.getElementById("inspect-btn").addEventListener("click", async () => {
  const { result, error } = await execOnActiveTab(() => {
    return { url: location.href, title: document.title, charset: document.characterSet };
  });
  if (error) {
    output.textContent = "Error: " + error;
  } else {
    output.textContent = Object.entries(result)
      .map(([k, v]) => k + ": " + v)
      .join("\n");
  }
});

// Eval document.title
document.getElementById("eval-btn").addEventListener("click", async () => {
  const { result, error } = await execOnActiveTab(() => document.title);
  evalOutput.textContent = error ? "Error: " + error : '"' + result + '"';
});
