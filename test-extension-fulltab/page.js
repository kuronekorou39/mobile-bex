const info = document.getElementById("info");
const results = document.getElementById("results");

info.textContent = [
  `URL: ${location.href}`,
  `Extension ID: ${chrome.runtime.id}`,
  `User Agent: ${navigator.userAgent.slice(0, 80)}...`,
  `Viewport: ${innerWidth}x${innerHeight}`,
].join("\n");
info.style.whiteSpace = "pre-wrap";

// Test chrome APIs are accessible from the tab page
const tests = [];
function test(name, fn) {
  try { const r = fn(); tests.push({ name, ok: true, detail: r }); }
  catch (e) { tests.push({ name, ok: false, detail: e.message }); }
}

test("chrome.runtime.id", () => chrome.runtime.id);
test("chrome.runtime.getURL()", () => chrome.runtime.getURL("/"));
test("chrome.tabs available", () => typeof chrome.tabs);
test("Window size (full tab)", () => `${innerWidth}x${innerHeight}`);

results.innerHTML = tests.map(t =>
  `<div>${t.ok ? "✅" : "❌"} ${t.name}: <span style="color:#94a3b8">${t.detail}</span></div>`
).join("");
