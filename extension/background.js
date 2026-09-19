// ============================================================
// BUY ME NOT - BACKGROUND SESSION TRACKER
// ============================================================

// 1. Initialize session variables if they don't exist yet
chrome.storage.session.get(['sessionStartTime', 'productViews'], (data) => {
    if (!data.sessionStartTime) {
        chrome.storage.session.set({
            sessionStartTime: Date.now(),
            productViews: 0
        });
    }
});

// 2. Increment product view count when an Amazon product page loads
chrome.webNavigation.onCompleted.addListener((details) => {
    // Only count top-level page loads, not background iframes
    if (details.frameId === 0 && (details.url.includes("/dp/") || details.url.includes("/product/"))) {
        chrome.storage.session.get(['productViews'], (data) => {
            const currentViews = data.productViews || 0;
            chrome.storage.session.set({ productViews: currentViews + 1 });
        });
    }
}, { url: [{ hostContains: 'amazon.' }] });

// 3. Send session data to the popup when requested
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === "GET_SESSION_DATA") {
        chrome.storage.session.get(['sessionStartTime', 'productViews'], (data) => {
            const startTime = data.sessionStartTime || Date.now();
            const views = data.productViews || 0;
            const sessionLengthMinutes = (Date.now() - startTime) / 60000;
            
            sendResponse({
                sessionLength: sessionLengthMinutes.toFixed(1),
                productViews: views
            });
        });
        
        // IMPORTANT: You must return true when sending an asynchronous response
        // in a Chrome extension message listener, otherwise the popup receives undefined.
        return true; 
    }
});