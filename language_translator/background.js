// Create context menu item
chrome.runtime.onInstalled.addListener(() => {
    chrome.contextMenus.create({
        id: "translateSelection",
        title: "Translate Selection",
        contexts: ["selection"]
    });
});

// Function to inject scripts
async function injectScripts(tabId) {
    try {
        // Inject CSS first
        await chrome.scripting.insertCSS({
            target: { tabId: tabId },
            files: ['content.css']
        });

        // Then inject the content script
        await chrome.scripting.executeScript({
            target: { tabId: tabId },
            files: ['content.js']
        });

        return true;
    } catch (error) {
        console.error('Script injection error:', error);
        return false;
    }
}

// Handle context menu click
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
    if (info.menuItemId === "translateSelection") {
        try {
            // Inject scripts if needed
            await injectScripts(tab.id);
            
            // Send message to content script
            chrome.tabs.sendMessage(tab.id, {
                action: "translate",
                text: info.selectionText
            }, (response) => {
                if (chrome.runtime.lastError) {
                    console.error('Error sending message:', chrome.runtime.lastError);
                    // Try re-injecting scripts and sending message again
                    injectScripts(tab.id).then(() => {
                        chrome.tabs.sendMessage(tab.id, {
                            action: "translate",
                            text: info.selectionText
                        });
                    });
                }
            });
        } catch (error) {
            console.error('Error:', error);
        }
    }
});

// Listen for tab updates to inject scripts
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url && tab.url.startsWith('http')) {
        injectScripts(tabId);
    }
}); 