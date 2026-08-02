// Phase 2: Background Service Worker test

// Service Worker はアイドルで終了・再起動するため、結果はグローバル変数ではなく
// chrome.storage.local に永続化する（再起動時に既存の結果を消さないようマージする）
const RESULTS_KEY = "testResults";

// 読み込み→マージ→書き込みを直列化し、並行更新で結果が欠けないようにする
let saveQueue = Promise.resolve();

function saveResults(partial) {
  saveQueue = saveQueue.then(async () => {
    const data = await chrome.storage.local.get(RESULTS_KEY);
    const merged = Object.assign({}, data[RESULTS_KEY], partial);
    await chrome.storage.local.set({ [RESULTS_KEY]: merged });
  });
  return saveQueue;
}

async function loadResults() {
  await saveQueue; // 進行中の保存を待ってから読む
  const data = await chrome.storage.local.get(RESULTS_KEY);
  return data[RESULTS_KEY] || {};
}

const results = {};

// Test 1: Service Worker is alive
results.serviceWorker = "running";
console.log("[mobile-bex] Background service worker started.");

// Test 2: chrome.runtime API
try {
  results.runtimeId = chrome.runtime.id;
  results.runtimeGetManifest = !!chrome.runtime.getManifest();
  console.log("[mobile-bex] chrome.runtime.id:", chrome.runtime.id);
} catch (e) {
  results.runtimeError = e.message;
}

// Test 4: chrome.tabs API
try {
  results.tabsApiExists = typeof chrome.tabs !== "undefined";
  results.tabsQueryExists = typeof chrome.tabs.query === "function";
} catch (e) {
  results.tabsError = e.message;
}

saveResults(results);

// Test 3: chrome.storage API
try {
  chrome.storage.local.set({ testKey: "hello from mobile-bex" }, () => {
    if (chrome.runtime.lastError) {
      saveResults({ storageSetError: chrome.runtime.lastError.message });
      return;
    }
    chrome.storage.local.get("testKey", (data) => {
      const storageGet = data.testKey === "hello from mobile-bex";
      saveResults({ storageSet: true, storageGet });
      console.log("[mobile-bex] chrome.storage test:", storageGet);
    });
  });
} catch (e) {
  saveResults({ storageError: e.message });
}

// Listen for messages from popup/content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "getResults") {
    loadResults().then((stored) => {
      sendResponse({ results: stored, timestamp: Date.now() });
    });
    return true; // async response
  }
  if (message.type === "getTabs") {
    chrome.tabs.query({}, (tabs) => {
      sendResponse({
        tabCount: tabs.length,
        tabs: tabs.map((t) => ({ id: t.id, title: t.title, url: t.url })),
      });
    });
    return true; // async response
  }
});

// Test 5: chrome.runtime.onInstalled
chrome.runtime.onInstalled.addListener((details) => {
  saveResults({ onInstalled: details.reason });
  console.log("[mobile-bex] onInstalled:", details.reason);
});
