// Clock
function updateClock() {
  document.getElementById("clock").textContent =
    new Date().toLocaleTimeString("ja-JP", { hour: "2-digit", minute: "2-digit" });
}
updateClock();
setInterval(updateClock, 1000);

// Search
document.getElementById("search").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && e.target.value.trim()) {
    const q = e.target.value.trim();
    const url = q.includes(".") && !q.includes(" ")
      ? (q.startsWith("http") ? q : "https://" + q)
      : "https://www.google.com/search?q=" + encodeURIComponent(q);
    chrome.tabs.update({ url });
  }
});

// Info
document.getElementById("info").textContent =
  "Extension ID: " + chrome.runtime.id + " | " + new Date().toLocaleDateString("ja-JP");
