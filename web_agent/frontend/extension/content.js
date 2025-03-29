// Create and style the popup menu
const popup = document.createElement('div');
popup.id = 'financial-research-popup';
popup.style.display = 'none';
popup.innerHTML = `
  <div class="popup-content">
    <h3>Research Options</h3>
    <button id="news-btn">Get Latest News</button>
    <button id="financial-btn">Get Financial Info</button>
  </div>
`;
document.body.appendChild(popup);

// Store selected text globally
let lastSelectedText = '';

// Handle text selection
document.addEventListener('mouseup', function(e) {
  const selection = window.getSelection();
  const selectedText = selection.toString().trim();
  
  // If clicking on the popup itself, don't hide it
  if (popup.contains(e.target)) {
    return;
  }
  
  // Hide popup if no text is selected
  if (!selectedText) {
    popup.style.display = 'none';
    return;
  }
  
  // Store the selected text
  lastSelectedText = selectedText;
  
  // Show popup near the selected text
  const range = selection.getRangeAt(0);
  const rect = range.getBoundingClientRect();
  
  // Calculate position to keep popup in viewport
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;
  const popupWidth = 250; // minimum width from CSS
  
  let left = rect.left + window.scrollX;
  let top = rect.bottom + window.scrollY + 5;
  
  // Adjust horizontal position if popup would go off screen
  if (left + popupWidth > viewportWidth) {
    left = viewportWidth - popupWidth - 10;
  }
  
  // Adjust vertical position if popup would go off screen
  if (top + 100 > viewportHeight) { // 100 is approximate popup height
    top = rect.top + window.scrollY - 105; // Show above selection
  }
  
  popup.style.display = 'block';
  popup.style.position = 'fixed';
  popup.style.left = `${left}px`;
  popup.style.top = `${top}px`;
  popup.style.zIndex = '10000';
});

// Handle button clicks
document.addEventListener('click', function(e) {
  // If clicking outside popup and not selecting text, hide popup
  if (!popup.contains(e.target) && window.getSelection().toString().trim() === '') {
    popup.style.display = 'none';
  }
});

// Remove any existing results when showing new ones
function removeExistingResults() {
  const existingResults = document.querySelectorAll('.research-result');
  existingResults.forEach(result => result.remove());
}

// Function to send message with retry
async function sendMessageWithRetry(message, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await new Promise((resolve, reject) => {
        chrome.runtime.sendMessage(message, response => {
          if (chrome.runtime.lastError) {
            reject(chrome.runtime.lastError);
          } else {
            resolve(response);
          }
        });
      });
    } catch (error) {
      console.warn(`Attempt ${i + 1} failed:`, error);
      if (i === maxRetries - 1) {
        throw error;
      }
      // Wait before retrying (exponential backoff)
      await new Promise(resolve => setTimeout(resolve, Math.pow(2, i) * 1000));
    }
  }
}

popup.addEventListener('click', async function(e) {
  if (e.target.id === 'news-btn' || e.target.id === 'financial-btn') {
    removeExistingResults();
    
    // Show loading state
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'research-result';
    loadingDiv.innerHTML = `
      <button class="close-btn">&times;</button>
      <h3>Loading...</h3>
      <div class="content">
        <div class="loading"></div>
        Fetching information for "${lastSelectedText}"...
      </div>
    `;
    document.body.appendChild(loadingDiv);
    
    // Add close button functionality to loading div
    loadingDiv.querySelector('.close-btn').addEventListener('click', () => {
      loadingDiv.remove();
    });
    
    try {
      // Send message to background script with retry
      await sendMessageWithRetry({
        action: 'research',
        type: e.target.id === 'news-btn' ? 'news' : 'financial',
        entity: lastSelectedText
      });
    } catch (error) {
      console.error('Failed to send message after retries:', error);
      // Show error message
      const errorDiv = document.createElement('div');
      errorDiv.className = 'research-result error';
      errorDiv.innerHTML = `
        <button class="close-btn">&times;</button>
        <h3>Connection Error</h3>
        <div class="content">
          <p>Failed to connect to the extension. Please:</p>
          <ol>
            <li>Check if the extension is enabled</li>
            <li>Reload the page</li>
            <li>Try your search again</li>
          </ol>
          <p>If the problem persists, try reloading the extension from chrome://extensions</p>
        </div>
      `;
      
      errorDiv.querySelector('.close-btn').addEventListener('click', () => {
        errorDiv.remove();
      });
      
      document.body.appendChild(errorDiv);
      loadingDiv.remove();
    }
    
    popup.style.display = 'none';
  }
});

// Listen for messages from background script with error handling
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  try {
    removeExistingResults();
    
    if (message.action === 'researchResult') {
      // Create result display
      const resultDiv = document.createElement('div');
      resultDiv.className = 'research-result';
      
      // Format the response data properly
      let formattedAnswer = '';
      
      try {
        if (typeof message.data === 'object') {
          if (message.data.answer) {
            formattedAnswer = message.data.answer;
          } else if (message.data.tool_calls) {
            formattedAnswer = message.data.tool_calls.map(call => call.result).join('\n');
          } else {
            formattedAnswer = JSON.stringify(message.data, null, 2);
          }
        } else {
          formattedAnswer = String(message.data);
        }
      } catch (err) {
        console.error('Error formatting data:', err);
        formattedAnswer = 'Error formatting response data. Please try again.';
      }
      
      resultDiv.innerHTML = `
        <button class="close-btn">&times;</button>
        <h3>Research Results for "${lastSelectedText}"</h3>
        <div class="content">
          <pre style="white-space: pre-wrap; font-family: inherit;">${formattedAnswer}</pre>
        </div>
      `;
      
      // Add close button functionality
      resultDiv.querySelector('.close-btn').addEventListener('click', () => {
        resultDiv.remove();
      });
      
      // Add to page
      document.body.appendChild(resultDiv);
    } else if (message.action === 'researchError') {
      // Show error message
      const errorDiv = document.createElement('div');
      errorDiv.className = 'research-result error';
      errorDiv.innerHTML = `
        <button class="close-btn">&times;</button>
        <h3>Error</h3>
        <div class="content">
          <p>Error while researching "${lastSelectedText}":</p>
          <p>${message.error}</p>
          <p>If this error persists, please try reloading the extension.</p>
        </div>
      `;
      
      // Add close button functionality
      errorDiv.querySelector('.close-btn').addEventListener('click', () => {
        errorDiv.remove();
      });
      
      // Add to page
      document.body.appendChild(errorDiv);
    }
  } catch (err) {
    console.error('Content script error:', err);
    // Show error message for context invalidation
    const errorDiv = document.createElement('div');
    errorDiv.className = 'research-result error';
    errorDiv.innerHTML = `
      <button class="close-btn">&times;</button>
      <h3>Extension Error</h3>
      <div class="content">
        <p>The extension encountered an error. Please:</p>
        <ol>
          <li>Close this message</li>
          <li>Reload the page</li>
          <li>Try your search again</li>
        </ol>
      </div>
    `;
    
    errorDiv.querySelector('.close-btn').addEventListener('click', () => {
      errorDiv.remove();
    });
    
    document.body.appendChild(errorDiv);
  }
}); 