// API endpoint configuration
const API_BASE_URL = 'http://localhost:8000';

// Handle messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'research') {
    const question = request.type === 'news' 
      ? `What are the latest news for ${request.entity}?`
      : `What is the current financial condition for ${request.entity}?`;
    
    // Call the API with proper error handling
    fetch(`${API_BASE_URL}/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({ 
        question: question 
      })
    })
    .then(async response => {
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }
      return response.json();
    })
    .then(data => {
      try {
        // Send successful response back to content script
        chrome.tabs.sendMessage(sender.tab.id, {
          action: 'researchResult',
          data: data
        }).catch(err => {
          console.error('Tab messaging error:', err);
          // Try to reload the extension context
          chrome.runtime.reload();
        });
      } catch (err) {
        console.error('Extension context error:', err);
        // Try to reload the extension context
        chrome.runtime.reload();
      }
    })
    .catch(error => {
      console.error('API Error:', error);
      try {
        // Send error back to content script
        chrome.tabs.sendMessage(sender.tab.id, {
          action: 'researchError',
          error: `Failed to fetch data: ${error.message}. Please make sure the API server is running at ${API_BASE_URL}`
        }).catch(err => {
          console.error('Error message sending failed:', err);
          // Try to reload the extension context
          chrome.runtime.reload();
        });
      } catch (err) {
        console.error('Extension context error:', err);
        // Try to reload the extension context
        chrome.runtime.reload();
      }
    });
    
    return true; // Keep the message channel open for async response
  }
});

// Listen for installation or update
chrome.runtime.onInstalled.addListener(() => {
  console.log('Extension installed/updated');
});

// Handle extension errors
chrome.runtime.onSuspend.addListener(() => {
  console.log('Extension being suspended');
});

// Keep the service worker alive
setInterval(() => {
  console.log('Keeping service worker alive');
}, 20000); 