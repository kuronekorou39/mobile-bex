// Create a custom DevTools panel
chrome.devtools.panels.create(
  "BEX Test",
  null,
  "panel.html",
  (panel) => {
    console.log("[mobile-bex] DevTools panel created:", panel);
  }
);
