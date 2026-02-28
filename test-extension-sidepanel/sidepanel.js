document.getElementById("ext-id").textContent = chrome.runtime.id;
document.getElementById("ua").textContent = navigator.userAgent;
document.getElementById("platform").textContent = navigator.platform;
document.getElementById("viewport").textContent =
  window.innerWidth + " x " + window.innerHeight;
document.getElementById("timestamp").textContent = new Date().toISOString();

document.getElementById("close-btn").addEventListener("click", () => {
  window.close();
});
