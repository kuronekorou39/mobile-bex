// Phase 2: Popup script — shows API test results

const container = document.getElementById("results");
const tabsList = document.getElementById("tabs-list");

function status(ok) {
  return ok
    ? '<span class="pass">PASS</span>'
    : '<span class="fail">FAIL</span>';
}

function row(label, ok) {
  return `<div class="test"><span>${label}</span>${status(ok)}</div>`;
}

// Get results from background service worker
chrome.runtime.sendMessage({ type: "getResults" }, (response) => {
  if (chrome.runtime.lastError || !response) {
    container.innerHTML = `<div class="test"><span>Service Worker</span><span class="fail">NO RESPONSE</span></div>`;
    return;
  }

  const r = response.results;
  let html = "";
  html += row("Service Worker", r.serviceWorker === "running");
  html += row("chrome.runtime.id", !!r.runtimeId);
  html += row("chrome.runtime.getManifest()", r.runtimeGetManifest);
  html += row("chrome.runtime.onInstalled", !!r.onInstalled);
  html += row("chrome.storage.local.set()", r.storageSet);
  html += row("chrome.storage.local.get()", r.storageGet);
  html += row("chrome.tabs API exists", r.tabsApiExists);
  html += row("chrome.tabs.query exists", r.tabsQueryExists);
  container.innerHTML = html;
});

// Test chrome.tabs.query
chrome.runtime.sendMessage({ type: "getTabs" }, (response) => {
  if (chrome.runtime.lastError || !response) {
    tabsList.textContent = "chrome.tabs.query: FAILED";
    return;
  }

  // タイトルやURLに "<" が含まれても壊れないよう textContent で組み立てる
  tabsList.textContent = "";

  const header = document.createElement("div");
  const strong = document.createElement("strong");
  strong.textContent = `Tabs (${response.tabCount}):`;
  header.appendChild(strong);
  tabsList.appendChild(header);

  response.tabs.forEach((tab) => {
    const div = document.createElement("div");
    div.appendChild(document.createTextNode(tab.title || "(no title)"));
    div.appendChild(document.createElement("br"));
    div.appendChild(document.createTextNode(tab.url || "(no url)"));
    tabsList.appendChild(div);
  });
});
