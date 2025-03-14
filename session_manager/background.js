// Session storage structure
class SessionManager {
  constructor() {
    this.currentSession = {
      date: new Date().toISOString().split('T')[0],
      windows: new Map()
    };
    this.initializeListeners();
    // Initialize current state when extension loads
    this.initializeCurrentState();
  }

  async initializeCurrentState() {
    try {
      const windows = await chrome.windows.getAll({ populate: true });
      for (const window of windows) {
        const tabsMap = new Map();
        for (const tab of window.tabs) {
          tabsMap.set(tab.id, {
            url: tab.url,
            title: tab.title,
            favicon: tab.favIconUrl,
            lastAccessed: new Date().toISOString()
          });
        }
        this.currentSession.windows.set(window.id, tabsMap);
      }
    } catch (error) {
      console.error('Error initializing current state:', error);
    }
  }

  initializeListeners() {
    // Track tab updates
    chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
      if (changeInfo.status === 'complete') {
        this.updateTab(tab);
      }
    });

    // Track window creation
    chrome.windows.onCreated.addListener((window) => {
      this.addWindow(window);
    });

    // Track window removal
    chrome.windows.onRemoved.addListener((windowId) => {
      this.removeWindow(windowId);
    });

    // Track tab creation
    chrome.tabs.onCreated.addListener((tab) => {
      this.addTab(tab);
    });

    // Track tab removal
    chrome.tabs.onRemoved.addListener((tabId, removeInfo) => {
      this.removeTab(tabId, removeInfo.windowId);
    });

    // Handle messages from popup and options pages
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      if (request.action === 'saveSession') {
        this.saveSession(request.name)
          .then(response => sendResponse(response))
          .catch(error => sendResponse({ success: false, error: error.message }));
        return true;
      } else if (request.action === 'restoreSession') {
        this.restoreSession(request.sessionKey, request.selectedWindows)
          .then(() => sendResponse({ success: true }))
          .catch(error => sendResponse({ success: false, error: error.message }));
        return true;
      }

      if (request.action === 'getSessionWindows') {
        this.getSessionWindows(request.sessionKey)
          .then(windows => sendResponse({ success: true, windows }))
          .catch(error => sendResponse({ success: false, error: error.message }));
        return true;
      }
    });
  }

  async updateTab(tab) {
    if (!this.currentSession.windows.has(tab.windowId)) {
      this.currentSession.windows.set(tab.windowId, new Map());
    }
    
    const windowTabs = this.currentSession.windows.get(tab.windowId);
    windowTabs.set(tab.id, {
      url: tab.url,
      title: tab.title,
      favicon: tab.favIconUrl,
      lastAccessed: new Date().toISOString()
    });
  }

  async addWindow(window) {
    this.currentSession.windows.set(window.id, new Map());
  }

  async removeWindow(windowId) {
    this.currentSession.windows.delete(windowId);
  }

  async addTab(tab) {
    await this.updateTab(tab);
  }

  async removeTab(tabId, windowId) {
    const windowTabs = this.currentSession.windows.get(windowId);
    if (windowTabs) {
      windowTabs.delete(tabId);
    }
  }

  async saveSession(name) {
    try {
      const windows = await chrome.windows.getAll({ populate: true });
      const sessionData = {
        name: name,
        date: new Date().toLocaleString(),
        windows: windows.map(window => ({
          windowId: window.id,
          tabs: window.tabs.map(tab => ({
            url: tab.url,
            title: tab.title,
            favicon: tab.favIconUrl
          }))
        }))
      };

      const sessionKey = `session_${Date.now()}`;
      await chrome.storage.local.set({ [sessionKey]: sessionData });
      return { success: true };
    } catch (error) {
      console.error('Error saving session:', error);
      throw new Error('Failed to save session');
    }
  }

  async getSessionWindows(sessionKey) {
    const data = await chrome.storage.local.get(sessionKey);
    const session = data[sessionKey];
    if (!session) throw new Error('Session not found');
    return session.windows;
  }

  async restoreSession(sessionKey, selectedWindows = null) {
    const data = await chrome.storage.local.get(sessionKey);
    const session = data[sessionKey];

    if (!session) return;

    // If no specific windows selected, restore all windows
    const windowsToRestore = selectedWindows 
      ? session.windows.filter(w => selectedWindows.includes(w.windowId))
      : session.windows;

    // Close current windows if restoring all
    if (!selectedWindows) {
      const currentWindows = await chrome.windows.getAll();
      for (const window of currentWindows) {
        await chrome.windows.remove(window.id);
      }
    }

    // Restore selected windows and their tabs
    for (const window of windowsToRestore) {
      const tabs = window.tabs.map(tab => ({ url: tab.url }));
      const newWindow = await chrome.windows.create({ url: tabs[0].url });
      
      // Create remaining tabs in the window
      for (let i = 1; i < tabs.length; i++) {
        await chrome.tabs.create({ 
          windowId: newWindow.id,
          url: tabs[i].url 
        });
      }
    }
  }
}

// Initialize the session manager
const sessionManager = new SessionManager(); 