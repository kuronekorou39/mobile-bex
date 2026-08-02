const status = document.getElementById("status");

// 通知アイコン: Chrome の通知は SVG をデコードできないため 16x16 の単色 PNG を使う
const ICON_BLUE =
  "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAAAFklEQVR42mNQTX5NEmIY1TCqYfhqAAB2SXMQ7LkbdQAAAABJRU5ErkJggg==";
const ICON_GREEN =
  "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAAAFklEQVR42mNQOhpHEmIY1TCqYfhqAACML0UQHDyfkAAAAABJRU5ErkJggg==";
const ICON_RED =
  "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAAAFklEQVR42mO4o6ZGEmIY1TCqYfhqAAATqigQ9kvG0QAAAABJRU5ErkJggg==";

function log(msg) {
  status.textContent = msg;
  console.log("[mobile-bex] Notifications:", msg);
}

// Basic notification
document.getElementById("basic").addEventListener("click", () => {
  chrome.notifications.create("basic-test", {
    type: "basic",
    iconUrl: ICON_BLUE,
    title: "BEX Test Notification",
    message: "This is a basic notification from mobile-bex!",
    priority: 2
  }, (id) => {
    log(chrome.runtime.lastError
      ? `Error: ${chrome.runtime.lastError.message}`
      : `Created: ${id}`);
  });
});

// Progress notification
document.getElementById("progress").addEventListener("click", () => {
  chrome.notifications.create("progress-test", {
    type: "progress",
    iconUrl: ICON_GREEN,
    title: "Download Progress",
    message: "Downloading extension data...",
    progress: 65
  }, (id) => {
    log(chrome.runtime.lastError
      ? `Error: ${chrome.runtime.lastError.message}`
      : `Progress: ${id}`);
  });
});

// Notification with buttons
document.getElementById("buttons").addEventListener("click", () => {
  chrome.notifications.create("buttons-test", {
    type: "basic",
    iconUrl: ICON_RED,
    title: "Action Required",
    message: "Do you want to proceed?",
    buttons: [
      { title: "Yes" },
      { title: "No" }
    ],
    requireInteraction: true
  }, (id) => {
    log(chrome.runtime.lastError
      ? `Error: ${chrome.runtime.lastError.message}`
      : `Buttons: ${id}`);
  });
});

// Clear all notifications
document.getElementById("clear").addEventListener("click", () => {
  chrome.notifications.getAll((notifications) => {
    const ids = Object.keys(notifications);
    ids.forEach(id => chrome.notifications.clear(id));
    log(`Cleared ${ids.length} notification(s)`);
  });
});
