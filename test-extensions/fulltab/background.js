// Full Tab Page Test: opens page.html in a new tab on icon click
chrome.action.onClicked.addListener(() => {
  chrome.tabs.create({ url: chrome.runtime.getURL("page.html") });
});
