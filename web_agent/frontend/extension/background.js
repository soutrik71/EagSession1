// API endpoint configuration
const API_BASE_URL = 'http://localhost:8000';

// Track connection status and active tabs
let isConnected = true;
let activeConnections = new Set();

// Initialize connection status
function initializeConnection() {
  isConnected = true;
  activeConnections.clear();
  console.log('Background script initialized');
}

// Function to check if a tab is still valid
async function isTabValid(tabId) {
  try {
    await chrome.tabs.get(tabId);
    return true;
  } catch (error) {
    console.warn(`Tab ${tabId} is no longer valid:`, error);
    activeConnections.delete(tabId);
    return false;
  }
}

// Function to send message to tab with retry
async function sendTabMessageWithRetry(tabId, message, maxRetries = 3) {
  if (!await isTabValid(tabId)) {
    throw new Error('Tab not valid');
  }

  for (let i = 0; i < maxRetries; i++) {
    try {
      await chrome.tabs.sendMessage(tabId, message);
      return;
    } catch (error) {
      console.warn(`Attempt ${i + 1} failed to send tab message:`, error);
      if (i === maxRetries - 1) {
        throw error;
      }
      await new Promise(resolve => setTimeout(resolve, Math.pow(2, i) * 1000));
    }
  }
}

// Handle messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  // Handle ping messages immediately
  if (request.action === 'ping') {
    console.log('Received ping, sending pong');
    sendResponse({ action: 'pong', status: 'connected' });
    return true;
  }

  if (!sender.tab) {
    console.error('No tab information in sender');
    sendResponse({ error: 'Invalid sender' });
    return false;
  }
  
  // Track this tab's connection
  activeConnections.add(sender.tab.id);
  
  if (!isConnected) {
    sendResponse({ error: 'Extension disconnected. Please reload the page.' });
    return false;
  }

  if (request.action === 'research') {
    // Validate request
    if (!request.entity || !request.type) {
      sendResponse({ error: 'Invalid request: missing entity or type' });
      return false;
    }

    // Send immediate acknowledgment
    sendResponse({ received: true, status: 'processing' });
    
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
      if (!activeConnections.has(sender.tab.id)) {
        console.warn('Tab connection lost');
        return;
      }
      
      try {
        // Ensure data is properly structured
        const formattedData = {
          action: 'researchResult',
          requestId: request.requestId,
          data: {
            answer: data.answer || data.result || (data.tool_calls ? data.tool_calls.map(call => call.result).join('\n') : JSON.stringify(data)),
            entity: request.entity,
            type: request.type
          }
        };

        await sendTabMessageWithRetry(sender.tab.id, formattedData);
      } catch (err) {
        console.error('Failed to send success message:', err);
        activeConnections.delete(sender.tab.id);
        if (activeConnections.size === 0) {
          isConnected = false;
          chrome.runtime.reload();
        }
      }
    })
    .catch(async error => {
      console.error('API Error:', error);
      
      if (!activeConnections.has(sender.tab.id)) {
        console.warn('Tab connection lost');
        return;
      }
      
      try {
        const errorData = {
          action: 'researchError',
          requestId: request.requestId,
          error: `Failed to fetch data: ${error.message}. Please make sure the API server is running at ${API_BASE_URL}`,
          entity: request.entity,
          type: request.type
        };

        await sendTabMessageWithRetry(sender.tab.id, errorData);
      } catch (err) {
        console.error('Failed to send error message:', err);
        activeConnections.delete(sender.tab.id);
        if (activeConnections.size === 0) {
          isConnected = false;
          chrome.runtime.reload();
        }
      }
    });
    
    // Return true to indicate we'll send a response asynchronously
    return true;
  }
  
  // Handle unknown actions
  sendResponse({ error: `Unknown action: ${request.action}` });
  return false;
});

// Listen for tab removal
chrome.tabs.onRemoved.addListener((tabId) => {
  activeConnections.delete(tabId);
});

// Listen for installation or update
chrome.runtime.onInstalled.addListener(() => {
  console.log('Extension installed/updated');
  initializeConnection();
});

// Handle extension errors
chrome.runtime.onSuspend.addListener(() => {
  console.log('Extension being suspended');
  isConnected = false;
  activeConnections.clear();
});

// Keep the service worker alive and check connection
setInterval(() => {
  if (activeConnections.size > 0 && !isConnected) {
    chrome.runtime.reload();
  }
}, 20000);

const sendMessage = (buttonId) => {
  return new Promise(async (resolve, reject) => {
    if (state.activeRequest) {
      reject(new Error('A request is already in progress'));
      return;
    }

    state.activeRequest = true; // Set active request to true

    // Create new controller for this request
    state.currentController = new AbortController();
    
    const timeoutId = setTimeout(() => {
      if (state.currentController) {
        state.currentController.abort();
      }
      state.activeRequest = false; // Reset active request on timeout
      reject(new Error('Request timeout - no response after 30s'));
    }, 30000);

    try {
      console.log('Checking connection before sending message...');
      
      // Try to reconnect if needed
      if (!await reconnectToExtension()) {
        throw new Error('Failed to establish connection to extension');
      }

      console.log('Connection confirmed, sending message...');
      state.lastRequestTime = Date.now();

      chrome.runtime.sendMessage({
        action: 'research',
        type: buttonId === 'news-btn' ? 'news' : 'financial',
        entity: state.lastSelectedText,
        requestId: Date.now().toString()
      }, response => {
        clearTimeout(timeoutId);
        
        if (chrome.runtime.lastError) {
          console.error('Runtime error:', chrome.runtime.lastError);
          state.activeRequest = false; // Reset active request on error
          reject(new Error(chrome.runtime.lastError.message));
          return;
        }
        
        // Check if request was aborted
        if (state.currentController && state.currentController.signal.aborted) {
          console.log('Request was aborted');
          state.activeRequest = false; // Reset active request on abort
          reject(new Error('Request was cancelled'));
          return;
        }

        console.log('Received response:', response);
        
        // Accept response if it has either received:true or valid data
        if (response.received || (response.data && response.data.answer)) {
          resolve(response);
        } else {
          state.activeRequest = false; // Reset active request on invalid response
          reject(new Error('Response missing required data'));
        }
      });
    } catch (err) {
      console.error('Error in sendMessage:', err);
      clearTimeout(timeoutId);
      state.activeRequest = false; // Reset active request on error
      reject(new Error(`Failed to send message: ${err.message}`));
    }
  });
};

async function handleButtonClick(buttonId) {
  // Cancel any existing request
  if (state.currentController) {
    state.currentController.abort();
    state.currentController = null;
  }
  
  // Clean up previous state
  if (state.loadingDiv) {
    state.loadingDiv.remove();
  }
  
  // Reset active request state
  state.activeRequest = false; 
  
  removeExistingResults();
  state.loadingDiv = createLoadingIndicator(state.shadowRoot, `Fetching information for "${state.lastSelectedText}"...`);
  
  let retryCount = 0;
  const maxRetries = 3;

  while (retryCount < maxRetries) {
    try {
      state.activeRequest = true; // Set active request to true
      
      // Add delay between retries with exponential backoff
      if (retryCount > 0) {
        const backoffDelay = Math.min(1000 * Math.pow(2, retryCount), 10000);
        await new Promise(resolve => setTimeout(resolve, backoffDelay));
      }

      // Check if request was cancelled before sending
      if (state.currentController && state.currentController.signal.aborted) {
        console.log('Request was cancelled before sending');
        return;
      }

      const response = await sendMessage(buttonId);
      
      // Check if request was cancelled after receiving response
      if (state.currentController && state.currentController.signal.aborted) {
        console.log('Request was cancelled after receiving response');
        return;
      }
      
      // Format the response data
      const responseData = response.data || response.answer || (response.tool_calls ? response.tool_calls.map(call => call.result).join('\n') : null);
      
      if (responseData) {
        showResults(responseData);
        if (state.loadingDiv) {
          state.loadingDiv.remove();
        }
        state.popup.style.display = 'none';
        state.activeRequest = false; // Reset active request after success
        state.currentController = null;
        return;
      }
      
      throw new Error('No usable data in response');
      
    } catch (error) {
      // If request was cancelled, just return
      if (error.message === 'Request was cancelled') {
        console.log('Request cancelled, stopping retries');
        return;
      }
      
      console.warn(`Attempt ${retryCount + 1} failed:`, error);
      retryCount++;
      
      if (retryCount === maxRetries) {
        console.error('Failed to send message after retries:', error);
        if (state.loadingDiv) {
          state.loadingDiv.remove();
        }
        showError('Connection Error', `
          <p>Failed to connect to the extension. Please:</p>
          <ol>
            <li>Check if the extension is enabled</li>
            <li>Reload the page</li>
            <li>Try your search again</li>
          </ol>
          <p>Error details: ${error.message}</p>
          <p>If the problem persists, try reloading the extension from chrome://extensions</p>
        `);
        state.activeRequest = false; // Reset active request on failure
        break;
      }
      
      // Update loading message for retry
      if (state.loadingDiv) {
        const message = state.loadingDiv.querySelector('p');
        if (message) {
          message.textContent = `Retrying... Attempt ${retryCount + 1} of ${maxRetries}`;
        }
      }
    }
  }
  
  state.activeRequest = false; // Final reset
  state.currentController = null;
  state.popup.style.display = 'none';
} 