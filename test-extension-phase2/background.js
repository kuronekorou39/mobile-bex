// Phase 2: Background Service Worker test

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

// Test 3: chrome.storage API
try {
  chrome.storage.local.set({ testKey: "hello from mobile-bex" }, () => {
    if (chrome.runtime.lastError) {
      results.storageSetError = chrome.runtime.lastError.message;
    } else {
      results.storageSet = true;
      chrome.storage.local.get("testKey", (data) => {
        results.storageGet = data.testKey === "hello from mobile-bex";
        console.log("[mobile-bex] chrome.storage test:", results.storageGet);
      });
    }
  });
} catch (e) {
  results.storageError = e.message;
}

// Test 4: chrome.tabs API
try {
  results.tabsApiExists = typeof chrome.tabs !== "undefined";
  results.tabsQueryExists = typeof chrome.tabs.query === "function";
} catch (e) {
  results.tabsError = e.message;
}

// Listen for messages from popup/content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "getResults") {
    sendResponse({ results, timestamp: Date.now() });
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
  results.onInstalled = details.reason;
  console.log("[mobile-bex] onInstalled:", details.reason);
});
