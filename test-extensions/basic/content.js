// mobile-bex Test Extension - Content Script
// This script injects a banner to verify content script injection works.

(function () {
  "use strict";

  const banner = document.createElement("div");
  banner.id = "mobile-bex-test-banner";
  banner.textContent = "mobile-bex: Content Script is running!";
  document.body.prepend(banner);

  console.log("[mobile-bex] Content script injected successfully.");
})();
