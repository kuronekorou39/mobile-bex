// Omnibox Test: keyword "bex"
// Type "bex " in address bar to trigger suggestions

const SUGGESTIONS = [
  { content: "https://example.com", description: "Example.com — サンプルサイト" },
  { content: "https://chromium.org", description: "Chromium — ブラウザプロジェクト" },
  { content: "https://developer.chrome.com/docs/extensions", description: "Chrome Extensions Docs" },
];

chrome.omnibox.onInputStarted.addListener(() => {
  console.log("[mobile-bex] Omnibox input started");
  chrome.omnibox.setDefaultSuggestion({
    description: "BEX Search: %s を検索"
  });
});

chrome.omnibox.onInputChanged.addListener((text, suggest) => {
  console.log("[mobile-bex] Omnibox input:", text);
  const filtered = SUGGESTIONS.filter(s =>
    s.description.toLowerCase().includes(text.toLowerCase()) ||
    s.content.toLowerCase().includes(text.toLowerCase())
  );
  suggest(filtered.length > 0 ? filtered : SUGGESTIONS);
});

chrome.omnibox.onInputEntered.addListener((text, disposition) => {
  console.log("[mobile-bex] Omnibox entered:", text, disposition);
  const url = text.startsWith("http")
    ? text
    : "https://www.google.com/search?q=" + encodeURIComponent(text);

  if (disposition === "newForegroundTab") {
    chrome.tabs.create({ url });
  } else if (disposition === "newBackgroundTab") {
    chrome.tabs.create({ url, active: false });
  } else {
    // currentTab or any other value
    chrome.tabs.update({ url });
  }
});
