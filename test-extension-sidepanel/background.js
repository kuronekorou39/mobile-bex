// sidePanel API Test: Background Service Worker
// Tests all 7 chrome.sidePanel API methods

const results = {};

async function runTests() {
  // Test 1: setOptions
  try {
    await chrome.sidePanel.setOptions({ path: "sidepanel.html" });
    results.setOptions = true;
  } catch (e) {
    results.setOptions = false;
    results.setOptionsError = e.message;
  }

  // Test 2: getOptions
  try {
    const opts = await chrome.sidePanel.getOptions({});
    results.getOptions = opts && opts.enabled === true;
    results.getOptionsValue = opts;
  } catch (e) {
    results.getOptions = false;
    results.getOptionsError = e.message;
  }

  // Test 3: setPanelBehavior
  try {
    await chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });
    results.setPanelBehavior = true;
  } catch (e) {
    results.setPanelBehavior = false;
    results.setPanelBehaviorError = e.message;
  }

  // Test 4: getPanelBehavior
  try {
    const behavior = await chrome.sidePanel.getPanelBehavior();
    results.getPanelBehavior =
      behavior && typeof behavior.openPanelOnActionClick === "boolean";
    results.getPanelBehaviorValue = behavior;
  } catch (e) {
    results.getPanelBehavior = false;
    results.getPanelBehaviorError = e.message;
  }

  // Test 5: open
  try {
    await chrome.sidePanel.open({ tabId: 0 });
    results.open = true;
  } catch (e) {
    results.open = false;
    results.openError = e.message;
  }

  // Test 6: getLayout
  try {
    const layout = await chrome.sidePanel.getLayout();
    results.getLayout = layout && typeof layout === "object";
    results.getLayoutValue = layout;
  } catch (e) {
    results.getLayout = false;
    results.getLayoutError = e.message;
  }

  // Test 7: close
  try {
    await chrome.sidePanel.close({ tabId: 0 });
    results.close = true;
  } catch (e) {
    results.close = false;
    results.closeError = e.message;
  }

  console.log("[mobile-bex] sidePanel test results:", results);
}

// runTests(); // 起動時の自動実行を無効化（起動ハングの原因）

// Listen for messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "getResults") {
    sendResponse({ results, timestamp: Date.now() });
  }
  if (message.type === "rerunTests") {
    runTests().then(() => {
      sendResponse({ results, timestamp: Date.now() });
    });
    return true; // async response
  }
});
