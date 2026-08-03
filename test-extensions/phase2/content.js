// Phase 2: Content Script — tests messaging with background service worker

(function () {
  "use strict";

  // Test chrome.runtime.sendMessage from content script
  chrome.runtime.sendMessage({ type: "getResults" }, (response) => {
    const ok = !chrome.runtime.lastError && response;
    console.log("[mobile-bex] Content ↔ Background messaging:", ok ? "PASS" : "FAIL");
    if (response) {
      console.log("[mobile-bex] API results:", JSON.stringify(response.results));
    }
  });
})();
