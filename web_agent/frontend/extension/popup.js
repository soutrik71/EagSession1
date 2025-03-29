// Listen for messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'researchResult') {
    // Create result display
    const resultDiv = document.createElement('div');
    resultDiv.className = 'research-result';
    resultDiv.innerHTML = `
      <button class="close-btn">&times;</button>
      <h3>Research Results</h3>
      <div class="content">${message.data.answer}</div>
    `;
    
    // Add close button functionality
    resultDiv.querySelector('.close-btn').addEventListener('click', () => {
      resultDiv.remove();
    });
    
    // Add to page
    document.body.appendChild(resultDiv);
  }
}); 