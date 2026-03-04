// Context Menu Test: adds items to the right-click / long-press menu

// Create menu items on install
chrome.runtime.onInstalled.addListener(() => {
  // Parent menu
  chrome.contextMenus.create({
    id: "bex-parent",
    title: "BEX Test Menu",
    contexts: ["all"]
  });

  // Sub-items
  chrome.contextMenus.create({
    id: "bex-page-info",
    parentId: "bex-parent",
    title: "Show Page Info",
    contexts: ["page"]
  });

  chrome.contextMenus.create({
    id: "bex-selection",
    parentId: "bex-parent",
    title: 'Search "%s"',
    contexts: ["selection"]
  });

  chrome.contextMenus.create({
    id: "bex-link",
    parentId: "bex-parent",
    title: "Copy Link Domain",
    contexts: ["link"]
  });

  chrome.contextMenus.create({
    id: "bex-image",
    parentId: "bex-parent",
    title: "Show Image Size",
    contexts: ["image"]
  });

  console.log("[mobile-bex] Context menu items created");
});

// Handle clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  console.log("[mobile-bex] Context menu clicked:", info.menuItemId, info);

  switch (info.menuItemId) {
    case "bex-page-info":
      chrome.tabs.sendMessage(tab.id, {
        type: "SHOW_ALERT",
        message: `Page: ${tab.title}\nURL: ${tab.url}`
      }).catch(() => {
        // Content script not injected, open as alert via scripting
        chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: (msg) => alert(msg),
          args: [`[BEX Context Menu Test]\n\nPage: ${tab.title}\nURL: ${tab.url}`]
        });
      });
      break;

    case "bex-selection":
      chrome.tabs.create({
        url: `https://www.google.com/search?q=${encodeURIComponent(info.selectionText)}`
      });
      break;

    case "bex-link":
      try {
        const domain = new URL(info.linkUrl).hostname;
        chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: (d) => alert(`[BEX] Link domain: ${d}`),
          args: [domain]
        });
      } catch (e) {
        console.error("Failed to parse link URL:", e);
      }
      break;

    case "bex-image":
      chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: (src) => {
          const img = new Image();
          img.onload = () => alert(`[BEX] Image: ${img.naturalWidth}x${img.naturalHeight}\n${src}`);
          img.onerror = () => alert(`[BEX] Image URL: ${src}`);
          img.src = src;
        },
        args: [info.srcUrl]
      });
      break;
  }
});
