// The toolbar icon has no popup: a popup closes the moment you click the page,
// and the scan takes ~40s. Clicking just tells the content script to show its
// panel, which lives in the page and survives everything.
chrome.action.onClicked.addListener((tab) => {
  chrome.tabs.sendMessage(tab.id, { type: "SUTD_OPEN_PANEL" }).catch(() => {
    // No content script in this tab - not a SUTD page.
  });
});
