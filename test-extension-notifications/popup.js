const status = document.getElementById("status");

function log(msg) {
  status.textContent = msg;
  console.log("[mobile-bex] Notifications:", msg);
}

// Basic notification
document.getElementById("basic").addEventListener("click", () => {
  chrome.notifications.create("basic-test", {
    type: "basic",
    iconUrl: "data:image/svg+xml," + encodeURIComponent(
      '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48"><rect width="48" height="48" rx="8" fill="#2563eb"/><text x="24" y="32" text-anchor="middle" fill="white" font-size="24" font-family="sans-serif">B</text></svg>'
    ),
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
    iconUrl: "data:image/svg+xml," + encodeURIComponent(
      '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48"><rect width="48" height="48" rx="8" fill="#22c55e"/><text x="24" y="32" text-anchor="middle" fill="white" font-size="20" font-family="sans-serif">%</text></svg>'
    ),
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
    iconUrl: "data:image/svg+xml," + encodeURIComponent(
      '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48"><rect width="48" height="48" rx="8" fill="#dc2626"/><text x="24" y="32" text-anchor="middle" fill="white" font-size="24" font-family="sans-serif">!</text></svg>'
    ),
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
