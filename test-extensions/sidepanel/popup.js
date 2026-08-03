// sidePanel API Test: Popup script — shows test results

const container = document.getElementById("results");
const summaryEl = document.getElementById("summary");
const retryBtn = document.getElementById("retry-btn");

function status(ok) {
  return ok
    ? '<span class="pass">PASS</span>'
    : '<span class="fail">FAIL</span>';
}

function row(label, ok) {
  return `<div class="test"><span>${label}</span>${status(ok)}</div>`;
}

function renderResults(r) {
  const tests = [
    ["setOptions()", r.setOptions],
    ["getOptions() → enabled:true", r.getOptions],
    ["setPanelBehavior()", r.setPanelBehavior],
    ["getPanelBehavior()", r.getPanelBehavior],
    ["open()", r.open],
    ["getLayout()", r.getLayout],
    ["close()", r.close],
  ];

  let html = "";
  let passed = 0;
  const total = tests.length;

  for (const [label, ok] of tests) {
    html += row(label, ok);
    if (ok) passed++;
  }

  container.innerHTML = html;

  const allPass = passed === total;
  summaryEl.textContent = `${passed}/${total} PASS`;
  summaryEl.className = allPass ? "summary-pass" : "summary-fail";
}

function fetchResults(messageType) {
  chrome.runtime.sendMessage({ type: messageType }, (response) => {
    if (chrome.runtime.lastError || !response) {
      container.innerHTML =
        '<div class="test"><span>Service Worker</span><span class="fail">NO RESPONSE</span></div>';
      summaryEl.textContent = "0/7 PASS";
      summaryEl.className = "summary-fail";
      return;
    }
    renderResults(response.results);
  });
}

// Initial load
fetchResults("getResults");

// Open Side Panel button
document.getElementById("open-panel-btn").addEventListener("click", async () => {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      await chrome.sidePanel.open({ tabId: tab.id });
    }
  } catch (e) {
    console.error("sidePanel.open error:", e);
  }
});

// Retry button
retryBtn.addEventListener("click", () => {
  container.innerHTML =
    '<div class="test"><span>Re-running...</span><span class="wait">...</span></div>';
  summaryEl.textContent = "";
  summaryEl.className = "";
  fetchResults("rerunTests");
});
