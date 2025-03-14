document.addEventListener('DOMContentLoaded', async () => {
  await loadSessions();
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

    for (const key of sessionKeys) {
      const session = storage[key];
      const sessionElement = createSessionElement(session, key);
      sessionList.appendChild(sessionElement);
    }
  } catch (error) {
    console.error('Error loading sessions:', error);
    const sessionList = document.getElementById('sessionList');
    sessionList.innerHTML = '<div class="error">Error loading sessions. Please try again.</div>';
  }
}

function createSessionElement(session, key) {
  const div = document.createElement('div');
  div.className = 'session-card';

  const infoDiv = document.createElement('div');
  infoDiv.className = 'session-info';

  const nameDiv = document.createElement('div');
  nameDiv.className = 'session-name';
  nameDiv.textContent = session.name;

  const dateDiv = document.createElement('div');
  dateDiv.className = 'session-date';
  dateDiv.textContent = `Created: ${session.date}`;

  const tabCount = session.windows.reduce((sum, window) => sum + window.tabs.length, 0);
  const windowCount = session.windows.length;

  const statsDiv = document.createElement('div');
  statsDiv.className = 'session-stats';
  statsDiv.textContent = `${windowCount} window${windowCount !== 1 ? 's' : ''}, ${tabCount} tab${tabCount !== 1 ? 's' : ''}`;

  infoDiv.appendChild(nameDiv);
  infoDiv.appendChild(dateDiv);
  infoDiv.appendChild(statsDiv);

  // Add window selection
  const windowsDiv = document.createElement('div');
  windowsDiv.className = 'windows-list';
  session.windows.forEach((window, index) => {
    const windowDiv = document.createElement('div');
    windowDiv.className = 'window-item';
    
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.id = `window-${key}-${window.windowId}`;
    checkbox.value = window.windowId;
    checkbox.checked = true; // Default all selected

    const label = document.createElement('label');
    label.htmlFor = checkbox.id;
    label.textContent = `Window ${index + 1} (${window.tabs.length} tabs)`;

    windowDiv.appendChild(checkbox);
    windowDiv.appendChild(label);
    windowsDiv.appendChild(windowDiv);
  });

  infoDiv.appendChild(windowsDiv);

  const actionsDiv = document.createElement('div');
  actionsDiv.className = 'actions';

  const restoreButton = document.createElement('button');
  restoreButton.className = 'button restore-btn';
  restoreButton.textContent = 'Restore Selected';
  restoreButton.addEventListener('click', () => {
    const selectedWindows = Array.from(div.querySelectorAll('input[type="checkbox"]:checked'))
      .map(cb => parseInt(cb.value));
    restoreSession(key, selectedWindows);
  });

  const restoreAllButton = document.createElement('button');
  restoreAllButton.className = 'button restore-btn';
  restoreAllButton.textContent = 'Restore All';
  restoreAllButton.addEventListener('click', () => restoreSession(key));

  const deleteButton = document.createElement('button');
  deleteButton.className = 'button delete-btn';
  deleteButton.textContent = 'Delete';
  deleteButton.addEventListener('click', () => deleteSession(key));

  actionsDiv.appendChild(restoreButton);
  actionsDiv.appendChild(restoreAllButton);
  actionsDiv.appendChild(deleteButton);

  div.appendChild(infoDiv);
  div.appendChild(actionsDiv);

  return div;
}

async function restoreSession(sessionKey, selectedWindows = null) {
  const message = selectedWindows 
    ? 'This will restore selected windows. Continue?' 
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