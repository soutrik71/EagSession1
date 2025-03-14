# Quick Translator Chrome Extension

A lightweight Chrome extension that enables instant text translation on any webpage. Select text to translate it into multiple languages with a clean, user-friendly interface.

## Features

- 🌐 Instant text translation with a simple selection
- 🔄 Support for 8 languages:
  - German (de)
  - Spanish (es)
  - French (fr)
  - Hindi (hi)
  - Kannada (kn)
  - Chinese (zh)
  - Japanese (ja)
  - Korean (ko)
- 💫 Two translation modes:
  - Preview mode: Shows translation in a floating tooltip
  - Replace mode: Replaces selected text with translation
- 🎯 Context menu integration for quick access
- 📱 Responsive and non-intrusive UI
- ⚡ Fast translation using MyMemory Translation API
- 🔒 Safe injection prevention to avoid duplicate instances

## Installation

1. Clone this repository or download the source code
2. Open Chrome and navigate to `chrome://extensions/`
3. Enable "Developer mode" in the top right corner
4. Click "Load unpacked" and select the `language_translator` folder
5. The extension icon should appear in your Chrome toolbar

## Usage

### Method 1: Direct Text Selection
1. Select any text on a webpage
2. A language selector will automatically appear near your selection
3. Choose your target language from the dropdown
4. Click either:
   - "Translate" to view the translation in a tooltip
   - "Replace" to replace the original text with the translation

### Method 2: Context Menu
1. Select text on any webpage
2. Right-click to open the context menu
3. Choose "Translate Selection"
4. View the translation in a tooltip

## Technical Implementation

### Key Components

1. **State Management**
   - Uses global window object for state management
   - Prevents multiple instance conflicts
   - Maintains UI element references

2. **UI Components**
   - Language selector dropdown
   - Translation tooltip
   - Floating translate button
   - Replace/Translate action buttons

3. **Event Handling**
   - Text selection detection
   - Scroll position adaptation
   - Click-away dismissal
   - Error handling for all user interactions

### API Integration

- Uses MyMemory Translation API
- Endpoint: `https://api.mymemory.translated.net/get`
- Parameters:
  - `q`: Text to translate
  - `langpair`: Source and target language pair (e.g., "en|de")

### Security Features

- Script injection protection
- Single instance enforcement
- Safe state management
- Error boundary implementation

## Browser Compatibility

- Chrome Version: Latest versions
- Manifest Version: 3
- Required Permissions:
  - activeTab
  - scripting
  - storage
  - contextMenus
  - tabs

## Error Handling

The extension implements comprehensive error handling for:
- Script initialization
- API communication
- UI element creation
- Translation operations
- Event listeners
- Message passing

## Development

To modify the extension:

1. Edit the relevant files:
   - `content.js`: Core functionality
   - `background.js`: Event handling
   - `popup.html/js`: User interface
   - `manifest.json`: Extension configuration

2. Test thoroughly:
   - Different websites
   - Various text selections
   - Multiple language combinations
   - Error scenarios

## Troubleshooting

Common issues and solutions:

1. Translation not working
   - Check internet connection
   - Verify API accessibility
   - Check console for specific errors

2. UI not appearing
   - Refresh the page
   - Check for conflicts with other extensions
   - Verify script injection

3. Multiple instances
   - Clear browser cache
   - Reload the extension
   - Check for error messages in console

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- MyMemory Translation API for providing translation services
- Chrome Extensions API documentation
- Contributors and testers
