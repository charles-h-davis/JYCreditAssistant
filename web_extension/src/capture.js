/**
 * Capture the visible tab and hand back a PNG Blob for the backend's Gemini
 * `/cost-to-buy/extract` endpoint.
 *
 * `captureVisibleTab` only needs `activeTab`, which is granted when the user
 * clicks the extension icon (i.e. when the popup opens). It captures the visible
 * viewport, so the price must be on screen.
 */
export async function captureVisibleTab() {
  let windowId;
  try {
    const win = await chrome.windows.getCurrent();
    windowId = win && win.id;
  } catch {
    windowId = undefined;
  }
  let dataUrl;
  try {
    dataUrl =
      windowId == null
        ? await chrome.tabs.captureVisibleTab({ format: "png" })
        : await chrome.tabs.captureVisibleTab(windowId, { format: "png" });
  } catch {
    throw new Error(
      "Can't capture this page (browser and Chrome Web Store pages are protected). " +
        "Open a product page and try again.",
    );
  }
  const response = await fetch(dataUrl);
  return await response.blob();
}
