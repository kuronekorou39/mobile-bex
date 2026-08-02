const themeEl = document.getElementById("theme");
const usernameEl = document.getElementById("username");
const statusEl = document.getElementById("status");

// Load saved settings
chrome.storage.sync.get(["theme", "username"], (data) => {
  if (chrome.runtime.lastError) {
    statusEl.textContent = `Load failed: ${chrome.runtime.lastError.message}`;
    return;
  }
  if (data.theme) themeEl.value = data.theme;
  if (data.username) usernameEl.value = data.username;
});

// Save settings
document.getElementById("save").addEventListener("click", () => {
  chrome.storage.sync.set(
    { theme: themeEl.value, username: usernameEl.value },
    () => {
      if (chrome.runtime.lastError) {
        statusEl.textContent = `Save failed: ${chrome.runtime.lastError.message}`;
        return;
      }
      statusEl.textContent = "Settings saved!";
      setTimeout(() => { statusEl.textContent = ""; }, 2000);
    }
  );
});
