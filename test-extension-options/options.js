const themeEl = document.getElementById("theme");
const usernameEl = document.getElementById("username");
const statusEl = document.getElementById("status");

// Load saved settings
chrome.storage.sync.get(["theme", "username"], (data) => {
  if (data.theme) themeEl.value = data.theme;
  if (data.username) usernameEl.value = data.username;
});

// Save settings
document.getElementById("save").addEventListener("click", () => {
  chrome.storage.sync.set(
    { theme: themeEl.value, username: usernameEl.value },
    () => {
      statusEl.textContent = "Settings saved!";
      setTimeout(() => { statusEl.textContent = ""; }, 2000);
    }
  );
});
