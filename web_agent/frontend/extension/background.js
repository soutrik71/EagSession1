// API endpoint configuration
const API_BASE_URL = 'http://localhost:8000';

// Track connection status
let isConnected = true;

// Function to send message to tab with retry
async function sendTabMessageWithRetry(tabId, message, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      await chrome.tabs.sendMessage(tabId, message);
      return;
    } catch (error) {
      console.warn(`Attempt ${i + 1} failed to send tab message:`, error);
      if (i === maxRetries - 1) {
        throw error;
      }
      // Wait before retrying (exponential backoff)
      await new Promise(resolve => setTimeout(resolve, Math.pow(2, i) * 1000));
    }
  }
}

// Handle messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (!isConnected) {
    sendResponse({ error: 'Extension disconnected. Please reload the page.' });
    return false;
  }

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
    .then(async data => {
      try {
        // Send successful response back to content script with retry
        await sendTabMessageWithRetry(sender.tab.id, {
          action: 'researchResult',
          data: data
        });
      } catch (err) {
        console.error('Failed to send success message:', err);
        isConnected = false;
        chrome.runtime.reload();
      }
    })
    .catch(async error => {
      console.error('API Error:', error);
      try {
        // Send error back to content script with retry
        await sendTabMessageWithRetry(sender.tab.id, {
          action: 'researchError',
          error: `Failed to fetch data: ${error.message}. Please make sure the API server is running at ${API_BASE_URL}`
        });
      } catch (err) {
        console.error('Failed to send error message:', err);
        isConnected = false;
        chrome.runtime.reload();
      }
    });
    
    return true; // Keep the message channel open for async response
  }
});

// Listen for installation or update
chrome.runtime.onInstalled.addListener(() => {
  console.log('Extension installed/updated');
  isConnected = true;
});

// Handle extension errors
chrome.runtime.onSuspend.addListener(() => {
  console.log('Extension being suspended');
  isConnected = false;
});

// Keep the service worker alive and check connection
setInterval(() => {
  if (!isConnected) {
    chrome.runtime.reload();
  }
}, 20000); 