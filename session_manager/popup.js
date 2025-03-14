document.addEventListener('DOMContentLoaded', async () => {
  // Load saved sessions
  await loadSessions();

  // Add event listeners
  document.getElementById('saveBtn').addEventListener('click', saveCurrentSession);
  document.getElementById('optionsBtn').addEventListener('click', openOptions);
});

async function loadSessions() {
  try {
    const storage = await chrome.storage.local.get(null);
    const sessionList = document.getElementById('sessionList');
    sessionList.innerHTML = '';

    // Filter and sort session keys
    const sessionKeys = Object.keys(storage)
      .filter(key => key.startsWith('session_'))
      .sort((a, b) => storage[b].date.localeCompare(storage[a].date));

    if (sessionKeys.length === 0) {
      sessionList.innerHTML = '<div class="no-sessions">No saved sessions yet</div>';
      return;
    }

    for (const key of sessionKeys) {
      const session = storage[key];
      const sessionElement = createSessionElement(session, key);
      sessionList.appendChild(sessionElement);
    }
  } catch (error) {
    console.error('Error loading sessions:', error);
    sessionList.innerHTML = '<div class="error">Error loading sessions. Please try again.</div>';
  }
}

function createSessionElement(session, key) {
  const div = document.createElement('div');
  div.className = 'session-item';
  
  // Session header
  const headerDiv = document.createElement('div');
  headerDiv.className = 'session-header';

  const infoDiv = document.createElement('div');
  infoDiv.className = 'session-info';

  const nameDiv = document.createElement('div');
  nameDiv.className = 'session-name';
  nameDiv.textContent = session.name;
  
  const dateDiv = document.createElement('div');
  dateDiv.className = 'session-date';
  dateDiv.textContent = session.date;

  const tabCount = session.windows.reduce((sum, window) => sum + window.tabs.length, 0);
  const windowCount = session.windows.length;
  
  const statsDiv = document.createElement('div');
  statsDiv.className = 'session-stats';
  statsDiv.textContent = `${windowCount} window${windowCount !== 1 ? 's' : ''}, ${tabCount} tab${tabCount !== 1 ? 's' : ''}`;

  infoDiv.appendChild(nameDiv);
  infoDiv.appendChild(dateDiv);
  infoDiv.appendChild(statsDiv);

  const expandToggle = document.createElement('button');
  expandToggle.className = 'expand-toggle';
  expandToggle.textContent = 'Show Details';
  
  headerDiv.appendChild(infoDiv);
  headerDiv.appendChild(expandToggle);
  div.appendChild(headerDiv);

  // Windows list (initially hidden)
  const windowsList = document.createElement('div');
  windowsList.className = 'windows-list';
  windowsList.style.display = 'none';

  session.windows.forEach((window, windowIndex) => {
    const windowItem = document.createElement('div');
    windowItem.className = 'window-item';

    const windowHeader = document.createElement('div');
    windowHeader.className = 'window-header';

    const windowTitle = document.createElement('div');
    windowTitle.className = 'window-title';
    windowTitle.textContent = `Window ${windowIndex + 1} (${window.tabs.length} tabs)`;

    const windowActions = document.createElement('div');
    windowActions.className = 'actions-bar';

    const restoreWindowBtn = document.createElement('button');
    restoreWindowBtn.className = 'button action-btn';
    restoreWindowBtn.textContent = 'Restore Window';
    restoreWindowBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      restoreSession(key, [window.windowId]);
    });

    windowActions.appendChild(restoreWindowBtn);
    windowHeader.appendChild(windowTitle);
    windowHeader.appendChild(windowActions);
    windowItem.appendChild(windowHeader);

    // Tabs list
    const tabsList = document.createElement('div');
    tabsList.className = 'tabs-list';

    window.tabs.forEach(tab => {
      const tabItem = document.createElement('div');
      tabItem.className = 'tab-item';
      
      if (tab.favicon) {
        const favicon = document.createElement('img');
        favicon.className = 'tab-favicon';
        favicon.src = tab.favicon;
        favicon.onerror = () => favicon.style.display = 'none';
        tabItem.appendChild(favicon);
      }

      const tabTitle = document.createElement('div');
      tabTitle.className = 'tab-title';
      tabTitle.title = tab.url;
      tabTitle.textContent = tab.title || tab.url;
      
      tabItem.appendChild(tabTitle);
      tabItem.addEventListener('click', () => {
        chrome.tabs.create({ url: tab.url });
      });

      tabsList.appendChild(tabItem);
    });

    windowItem.appendChild(tabsList);
    windowsList.appendChild(windowItem);
  });

  div.appendChild(windowsList);

  // Toggle windows list visibility
  expandToggle.addEventListener('click', () => {
    const isExpanded = windowsList.style.display !== 'none';
    windowsList.style.display = isExpanded ? 'none' : 'block';
    expandToggle.textContent = isExpanded ? 'Show Details' : 'Hide Details';
  });

  // Session-level actions
  const actionsBar = document.createElement('div');
  actionsBar.className = 'actions-bar';

  const restoreAllBtn = document.createElement('button');
  restoreAllBtn.className = 'button action-btn';
  restoreAllBtn.textContent = 'Restore All Windows';
  restoreAllBtn.addEventListener('click', () => restoreSession(key));

  const deleteBtn = document.createElement('button');
  deleteBtn.className = 'button action-btn delete-btn';
  deleteBtn.textContent = 'Delete Session';
  deleteBtn.addEventListener('click', () => deleteSession(key));

  actionsBar.appendChild(restoreAllBtn);
  actionsBar.appendChild(deleteBtn);
  div.appendChild(actionsBar);
  
  return div;
}

async function saveCurrentSession() {
  try {
    // Show saving indicator
    const saveBtn = document.getElementById('saveBtn');
    const originalText = saveBtn.textContent;
    saveBtn.textContent = 'Saving...';
    saveBtn.disabled = true;

    // Get current window count and tab count
    const windows = await chrome.windows.getAll({ populate: true });
    const tabCount = windows.reduce((sum, window) => sum + window.tabs.length, 0);
    const windowCount = windows.length;

    const name = prompt(
      `Enter a name for this session (${windowCount} windows, ${tabCount} tabs):`,
      `My Session (${windowCount} windows)`
    );

    if (!name) {
      saveBtn.textContent = originalText;
      saveBtn.disabled = false;
      return;
    }

    // Send message to background script to save the session
    const response = await chrome.runtime.sendMessage({
      action: 'saveSession',
      name: name
    });

    if (response && response.success) {
      saveBtn.textContent = 'Saved!';
      setTimeout(() => {
        saveBtn.textContent = originalText;
        saveBtn.disabled = false;
      }, 2000);
      await loadSessions();
    } else {
      throw new Error(response?.error || 'Failed to save session');
    }
  } catch (error) {
    console.error('Error saving session:', error);
    alert('Failed to save session. Please try again.');
    const saveBtn = document.getElementById('saveBtn');
    saveBtn.textContent = 'Save Current Session';
    saveBtn.disabled = false;
  }
}

async function restoreSession(sessionKey, selectedWindows = null) {
  const message = selectedWindows 
    ? 'This will restore the selected window. Continue?' 
    : 'This will close all current windows and restore the session. Continue?';

  if (!confirm(message)) return;

  try {
    const response = await chrome.runtime.sendMessage({
      action: 'restoreSession',
      sessionKey: sessionKey,
      selectedWindows: selectedWindows
    });

    if (!response || !response.success) {
      throw new Error(response?.error || 'Failed to restore session');
    }
    
    if (!selectedWindows) {
      window.close();
    }
  } catch (error) {
    console.error('Error restoring session:', error);
    alert('Failed to restore session. Please try again.');
  }
}

async function deleteSession(sessionKey) {
  if (!confirm('Are you sure you want to delete this session?')) return;

  try {
    await chrome.storage.local.remove(sessionKey);
    await loadSessions();
  } catch (error) {
    console.error('Error deleting session:', error);
    alert('Failed to delete session. Please try again.');
  }
}

function openOptions() {
  chrome.runtime.openOptionsPage();
} 