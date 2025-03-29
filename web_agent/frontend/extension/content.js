// Global state management
const state = {
  lastSelectedText: '',
  activeRequest: false,
  lastRequestTime: null,
  popup: null,
  loadingDiv: null,
  shadowRoot: null,
  container: null,
  currentController: null,
  isReconnecting: false
};

// Create shadow DOM container
function createShadowContainer() {
  state.container = document.createElement('div');
  state.container.id = 'financial-research-container';
  document.body.appendChild(state.container);
  state.shadowRoot = state.container.attachShadow({ mode: 'closed' });
  return state.shadowRoot;
}

// Create and inject required styles
function injectStyles(root) {
  const style = document.createElement('style');
  style.textContent = `
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    .financial-research-popup {
      position: fixed;
      z-index: 2147483647;
      background: white;
      border: 1px solid #ccc;
      border-radius: 4px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
      padding: 10px;
      display: none;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      font-size: 14px;
      line-height: 1.4;
      color: #333;
    }
    .financial-research-result {
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 2147483647;
      background: white;
      border: 1px solid #ccc;
      border-radius: 4px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
      padding: 15px;
      max-width: 400px;
      max-height: 80vh;
      overflow-y: auto;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      font-size: 14px;
      line-height: 1.4;
      color: #333;
    }
    .financial-research-error {
      border-color: #ff4444;
    }
    .financial-research-button {
      display: block;
      width: 100%;
      margin: 5px 0;
      padding: 8px;
      border: 1px solid #ccc;
      border-radius: 4px;
      background: #f8f8f8;
      cursor: pointer;
      font-size: 14px;
      transition: background-color 0.2s;
      font-family: inherit;
      color: inherit;
    }
    .financial-research-button:hover {
      background: #eee;
    }
    .financial-research-close {
      position: absolute;
      right: 5px;
      top: 5px;
      border: none;
      background: none;
      font-size: 20px;
      cursor: pointer;
      padding: 0 5px;
      opacity: 0.6;
      color: inherit;
    }
    .financial-research-close:hover {
      opacity: 1;
    }
    .financial-research-spinner {
      display: inline-block;
      width: 20px;
      height: 20px;
      border: 2px solid #ccc;
      border-radius: 50%;
      border-top-color: #333;
      animation: spin 1s linear infinite;
      margin: 10px auto;
    }
    * {
      box-sizing: border-box;
    }
  `;
  root.appendChild(style);
}

// Create popup element
function createPopup(root) {
  const popup = document.createElement('div');
  popup.className = 'financial-research-popup';
  
  const title = document.createElement('h3');
  title.textContent = 'Research Options';
  title.style.margin = '0 0 10px 0';
  title.style.fontSize = '14px';
  
  const newsBtn = document.createElement('button');
  newsBtn.id = 'news-btn';
  newsBtn.className = 'financial-research-button';
  newsBtn.textContent = 'Get Latest News';
  
  const financialBtn = document.createElement('button');
  financialBtn.id = 'financial-btn';
  financialBtn.className = 'financial-research-button';
  financialBtn.textContent = 'Get Financial Info';
  
  popup.appendChild(title);
  popup.appendChild(newsBtn);
  popup.appendChild(financialBtn);
  
  root.appendChild(popup);
  return popup;
}

// Create loading indicator
function createLoadingIndicator(root, text) {
  const div = document.createElement('div');
  div.className = 'financial-research-result';
  
  const closeBtn = document.createElement('button');
  closeBtn.className = 'financial-research-close';
  closeBtn.textContent = '×';
  closeBtn.addEventListener('click', () => div.remove());
  
  const title = document.createElement('h3');
  title.textContent = 'Loading...';
  title.style.margin = '0 0 10px 0';
  title.style.paddingRight = '20px';
  
  const spinner = document.createElement('div');
  spinner.className = 'financial-research-spinner';
  
  const message = document.createElement('p');
  message.textContent = text;
  message.style.margin = '10px 0 0 0';
  
  div.appendChild(closeBtn);
  div.appendChild(title);
  div.appendChild(spinner);
  div.appendChild(message);
  
  root.appendChild(div);
  return div;
}

// Show error message
function showError(title, message) {
  const div = document.createElement('div');
  div.className = 'financial-research-result financial-research-error';
  
  const closeBtn = document.createElement('button');
  closeBtn.className = 'financial-research-close';
  closeBtn.textContent = '×';
  closeBtn.addEventListener('click', () => div.remove());
  
  const titleElem = document.createElement('h3');
  titleElem.textContent = title;
  titleElem.style.margin = '0 0 10px 0';
  titleElem.style.paddingRight = '20px';
  titleElem.style.color = '#ff4444';
  
  const content = document.createElement('div');
  content.innerHTML = message;
  
  div.appendChild(closeBtn);
  div.appendChild(titleElem);
  div.appendChild(content);
  
  state.shadowRoot.appendChild(div);
}

// Show results
function showResults(data) {
  const div = document.createElement('div');
  div.className = 'financial-research-result';
  
  const closeBtn = document.createElement('button');
  closeBtn.className = 'financial-research-close';
  closeBtn.textContent = '×';
  closeBtn.addEventListener('click', () => div.remove());
  
  const title = document.createElement('h3');
  title.textContent = `Research Results for "${data.entity || state.lastSelectedText}"`;
  title.style.margin = '0 0 10px 0';
  title.style.paddingRight = '20px';
  
  let formattedAnswer = '';
  try {
    if (typeof data === 'string') {
      formattedAnswer = data;
    } else if (data.answer) {
      formattedAnswer = data.answer;
    } else if (data.data && data.data.answer) {
      formattedAnswer = data.data.answer;
    } else {
      formattedAnswer = JSON.stringify(data, null, 2);
    }
  } catch (err) {
    console.error('Error formatting data:', err);
    formattedAnswer = 'Error formatting response data. Please try again.';
  }
  
  const content = document.createElement('pre');
  content.style.whiteSpace = 'pre-wrap';
  content.style.fontFamily = 'inherit';
  content.style.margin = '0';
  content.textContent = formattedAnswer;
  
  div.appendChild(closeBtn);
  div.appendChild(title);
  div.appendChild(content);
  
  state.shadowRoot.appendChild(div);
}

// Remove existing results
function removeExistingResults() {
  const root = state.shadowRoot;
  if (!root) return;
  root.querySelectorAll('.financial-research-result').forEach(el => el.remove());
}

// Add reconnection function
async function reconnectToExtension() {
  if (state.isReconnecting) return false;
  
  state.isReconnecting = true;
  let attempts = 0;
  const maxAttempts = 3;
  
  while (attempts < maxAttempts) {
    try {
      console.log(`Attempting to reconnect (attempt ${attempts + 1}/${maxAttempts})`);
      
      // Test connection with timeout
      const response = await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => reject(new Error('Connection timeout')), 2000);
        
        chrome.runtime.sendMessage({ action: 'ping' }, response => {
          clearTimeout(timeout);
          if (chrome.runtime.lastError) {
            reject(chrome.runtime.lastError);
          } else if (response && response.action === 'pong') {
            resolve(response);
          } else {
            reject(new Error('Invalid response'));
          }
        });
      });
      
      if (response.status === 'connected') {
        console.log('Connection restored');
        state.isReconnecting = false;
        return true;
      }
      
      throw new Error('Connection check failed');
    } catch (error) {
      console.warn(`Reconnection attempt ${attempts + 1} failed:`, error);
      attempts++;
      
      if (attempts === maxAttempts) {
        console.error('Failed to reconnect after all attempts');
        state.isReconnecting = false;
        return false;
      }
      
      // Wait before retry with exponential backoff
      await new Promise(resolve => setTimeout(resolve, Math.min(1000 * Math.pow(2, attempts), 5000)));
    }
  }
  
  state.isReconnecting = false;
  return false;
}

// Modify sendMessage function
const sendMessage = (buttonId) => {
  return new Promise(async (resolve, reject) => {
    if (state.activeRequest) {
      console.log('Request already in progress, rejecting');
      reject(new Error('A request is already in progress'));
      return;
    }

    try {
      state.activeRequest = true;
      console.log('Setting active request to true');

      const message = {
        action: 'research',
        type: buttonId === 'news-btn' ? 'news' : 'financial',
        entity: state.lastSelectedText,
        requestId: Date.now().toString()
      };

      console.log('Sending message:', message);

      chrome.runtime.sendMessage(message, response => {
        if (chrome.runtime.lastError) {
          console.error('Runtime error:', chrome.runtime.lastError);
          state.activeRequest = false;
          reject(new Error(chrome.runtime.lastError.message));
          return;
        }

        if (!response) {
          console.error('Empty response received');
          state.activeRequest = false;
          reject(new Error('Empty response received'));
          return;
        }

        console.log('Received response:', response);

        if (response.error) {
          state.activeRequest = false;
          reject(new Error(response.error));
          return;
        }

        if (response.received || (response.data && response.data.answer)) {
          resolve(response);
        } else {
          state.activeRequest = false;
          reject(new Error('Response missing required data'));
        }
      });
    } catch (err) {
      console.error('Error in sendMessage:', err);
      state.activeRequest = false;
      reject(err);
    }
  });
};

// Modify handleButtonClick function
async function handleButtonClick(buttonId) {
  console.log('Button clicked:', buttonId);
  
  if (state.activeRequest) {
    console.log('Request already in progress, ignoring click');
    return;
  }

  try {
    removeExistingResults();
    state.loadingDiv = createLoadingIndicator(state.shadowRoot, `Fetching information for "${state.lastSelectedText}"...`);

    console.log('Sending request...');
    const response = await sendMessage(buttonId);
    console.log('Received response:', response);

    if (response.data && response.data.answer) {
      showResults(response.data);
    } else if (response.received) {
      console.log('Request acknowledged, waiting for data...');
    } else {
      throw new Error('Invalid response format');
    }
  } catch (error) {
    console.error('Error handling button click:', error);
    if (state.loadingDiv) {
      state.loadingDiv.remove();
    }
    showError('Error', error.message);
  } finally {
    state.activeRequest = false;
    if (state.loadingDiv) {
      state.loadingDiv.remove();
    }
    if (state.popup) {
      state.popup.style.display = 'none';
    }
  }
}

// Handle text selection
function handleTextSelection(e) {
  if (!state.popup || state.activeRequest) return;
  
  const selection = window.getSelection();
  const selectedText = selection.toString().trim();
  
  if (state.popup.contains(e.target)) {
    return;
  }
  
  if (!selectedText) {
    state.popup.style.display = 'none';
    return;
  }
  
  state.lastSelectedText = selectedText;
  
  const range = selection.getRangeAt(0);
  const rect = range.getBoundingClientRect();
  
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;
  const popupWidth = 250;
  
  let left = rect.left + window.scrollX;
  let top = rect.bottom + window.scrollY + 5;
  
  if (left + popupWidth > viewportWidth) {
    left = viewportWidth - popupWidth - 10;
  }
  
  if (top + 100 > viewportHeight) {
    top = rect.top + window.scrollY - 105;
  }
  
  state.popup.style.left = `${left}px`;
  state.popup.style.top = `${top}px`;
  state.popup.style.display = 'block';
}

// Handle clicks outside popup
function handleOutsideClick(e) {
  if (state.popup && !state.popup.contains(e.target) && 
      window.getSelection().toString().trim() === '') {
    state.popup.style.display = 'none';
  }
}

// Handle messages from background script
function handleBackgroundMessage(message) {
  try {
    removeExistingResults();
    
    if (message.action === 'researchResult') {
      showResults(message.data);
    } else if (message.action === 'researchError') {
      showError('Research Error', `
        <p>Error while researching "${state.lastSelectedText}":</p>
        <p>${message.error}</p>
        <p>If this error persists, please try reloading the extension.</p>
      `);
    }
    
    if (state.loadingDiv) {
      state.loadingDiv.remove();
    }
  } catch (err) {
    console.error('Content script error:', err);
    showError('Extension Error', `
      <p>The extension encountered an error. Please:</p>
      <ol>
        <li>Close this message</li>
        <li>Reload the page</li>
        <li>Try your search again</li>
      </ol>
    `);
  }
}

// Initialize event listeners
function initializeEventListeners() {
  document.addEventListener('mouseup', handleTextSelection);
  document.addEventListener('click', handleOutsideClick);
  chrome.runtime.onMessage.addListener(handleBackgroundMessage);
}

// Initialize extension
function initializeExtension() {
  try {
    const root = createShadowContainer();
    injectStyles(root);
    state.popup = createPopup(root);
    
    // Handle button clicks with debouncing
    let clickTimeout;
    state.popup.addEventListener('click', async (e) => {
      const target = e.target;
      if (target.id === 'news-btn' || target.id === 'financial-btn') {
        e.preventDefault();
        e.stopPropagation();
        
        // Prevent double clicks
        if (clickTimeout) return;
        clickTimeout = setTimeout(() => clickTimeout = null, 1000);
        
        await handleButtonClick(target.id);
      }
    }, true);
  } catch (err) {
    console.error('Failed to initialize extension UI:', err);
    throw err; // Re-throw to show in console
  }
}

// Start the extension
try {
  initializeExtension();
  initializeEventListeners();
} catch (err) {
  console.error('Failed to initialize extension:', err);
}

// Add message listener for background script responses
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'researchResult') {
    if (state.loadingDiv) {
      state.loadingDiv.remove();
    }
    
    if (!message.data) {
      showError('Error', 'No data received from server');
      return;
    }
    
    showResults(message.data);
    state.popup.style.display = 'none';
  }
  
  if (message.action === 'researchError') {
    if (state.loadingDiv) {
      state.loadingDiv.remove();
    }
    
    showError('Error', message.error || 'Unknown error occurred');
    state.popup.style.display = 'none';
  }
});