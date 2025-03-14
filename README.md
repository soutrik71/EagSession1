# Chrome Tab Session Manager

A powerful Chrome extension for managing browser sessions, allowing you to save, restore, and organize your windows and tabs efficiently.

## Features

- **Save Current Session**: Capture all your open windows and tabs with a single click
- **Window-Level Management**: 
  - View detailed information about each saved window and its tabs
  - Restore individual windows or entire sessions
  - See tab counts and window statistics
- **Rich Tab Information**:
  - Display tab titles and URLs
  - Show favicon icons for easy identification
  - Click on individual tabs to open them
- **Flexible Session Restoration**:
  - Restore entire sessions (replacing current windows)
  - Restore specific windows without affecting others
  - Open individual tabs from saved sessions
- **User-Friendly Interface**:
  - Clean, modern design
  - Expandable/collapsible window views
  - Clear session statistics
  - Loading indicators and status messages

## Installation

1. Clone this repository or download the source code
2. Open Chrome and navigate to `chrome://extensions/`
3. Enable "Developer mode" in the top right corner
4. Click "Load unpacked" and select the extension directory

## Usage

### Saving Sessions

1. Click the extension icon in your Chrome toolbar
2. Click "Save Current Session"
3. Enter a name for your session
4. The session will be saved with all current windows and tabs

### Viewing Sessions

1. Open the extension popup
2. See a list of all saved sessions with:
   - Session name
   - Date saved
   - Number of windows and tabs
3. Click "Show Details" to view window and tab information

### Restoring Sessions

You have several options for restoration:
- **Full Session**: Click "Restore All Windows" to replace current windows with the saved session
- **Single Window**: Expand a session and click "Restore Window" on any window
- **Individual Tabs**: Click any tab in the expanded view to open it in a new tab

### Managing Sessions

- **Delete**: Remove unwanted sessions using the "Delete Session" button
- **Options**: Access additional settings through the Options page

## Technical Details

### Storage

- Sessions are stored locally using Chrome's Storage API
- Each session includes:
  - Unique identifier
  - Name
  - Date created
  - Window and tab information
  - Favicon URLs

### Architecture

- **Background Script**: Manages session tracking and window/tab operations
- **Popup Interface**: Provides user interaction and session management
- **Event Handling**: Tracks window and tab changes in real-time

### Data Structure

```javascript
{
  session_[timestamp]: {
    name: string,
    date: string,
    windows: [{
      windowId: number,
      tabs: [{
        url: string,
        title: string,
        favicon: string
      }]
    }]
  }
}
```

## Permissions

The extension requires the following permissions:
- `tabs`: To access and manage browser tabs
- `windows`: To handle window operations
- `storage`: To save session data
- `unlimitedStorage`: For handling large numbers of sessions
- `host_permissions`: To access tab URLs and favicons

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
