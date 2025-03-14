# Quick Translator Chrome Extension

A powerful Chrome extension that allows users to instantly translate selected text into multiple languages. The extension provides both translation preview and text replacement capabilities.

## Features

- 🌐 Instant text translation
- 🔄 Multiple language support (German, Spanish, French, Hindi, Kannada, Chinese, Japanese, Korean)
- 💫 Two translation modes:
  - Preview mode (shows translation in a popup)
  - Replace mode (replaces selected text with translation)
- 🎯 Context menu integration
- 📱 Responsive design
- ⚡ Fast and lightweight

## Installation

1. Clone this repository or download the source code
2. Open Chrome and navigate to `chrome://extensions/`
3. Enable "Developer mode" in the top right corner
4. Click "Load unpacked" and select the `language_translator` folder
5. The extension icon should appear in your Chrome toolbar

## Usage

### Method 1: Using the Selection Interface

1. Select any text on a webpage
2. A language selector will appear near your selection
3. Choose your target language from the dropdown
4. Click either:
   - "Translate" to see the translation in a popup
   - "Replace" to replace the selected text with its translation

### Method 2: Using the Context Menu

1. Select any text on a webpage
2. Right-click to open the context menu
3. Select "Translate Selection"
4. The translation will appear in a popup

## Code Structure

### Main Components

1. **content.js**
   - Core functionality implementation
   - Handles text selection, translation, and UI elements
   - Manages communication between different parts of the extension

2. **background.js**
   - Manages context menu integration
   - Handles script injection
   - Manages extension lifecycle

3. **manifest.json**
   - Extension configuration
   - Permissions and resource declarations
   - Script and API configurations

### Key Functions

1. `initializeExtension()`
   - Initializes UI components
   - Sets up event listeners
   - Creates necessary DOM elements

2. `createLanguageSelector()`
   - Creates the language selection dropdown
   - Adds translation and replace buttons
   - Handles button click events

3. `handleTranslation(text, targetLang, shouldReplace)`
   - Manages the translation process
   - Communicates with translation API
   - Updates UI with translation results

4. `showTranslationTooltip(translatedText, langSelectorRect)`
   - Displays translation results
   - Manages tooltip positioning and content
   - Handles user interactions

## Technical Details

### Translation Process

1. Text Selection
   - User selects text
   - Selection event triggers UI display
   - Selected text is stored

2. Language Selection
   - User chooses target language
   - Language code is passed to translator

3. Translation
   - Text is sent to MyMemory Translation API
   - Response is processed
   - Result is displayed or text is replaced

### UI Components

1. **Language Selector**
   - Dropdown for language selection
   - Translate and Replace buttons
   - Appears near selected text

2. **Translation Tooltip**
   - Shows original and translated text
   - Close button for dismissal
   - Positioned next to language selector

### Event Handling

- `mouseup`: Triggers selection UI
- `click`: Manages UI visibility
- `scroll`: Handles UI repositioning
- Chrome message events: Manages extension communication

## API Integration

The extension uses the MyMemory Translation API:

- Endpoint: `https://api.mymemory.translated.net/get`
- Parameters:
  - `q`: Text to translate
  - `langpair`: Source and target language pair

## Error Handling

The extension includes comprehensive error handling for:

- Script initialization
- API communication
- UI element creation
- User interactions
- Extension messaging

## Browser Compatibility

- Chrome Version: Latest versions
- Manifest Version: 3
- Required Permissions:
  - activeTab
  - scripting
  - storage
  - contextMenus

## Development

To modify or enhance the extension:

1. Make changes to the relevant files
2. Reload the extension in Chrome
3. Test thoroughly across different websites
4. Check console for any errors

## Troubleshooting

Common issues and solutions:

1. Translation not working
   - Check internet connection
   - Verify API access
   - Check console for errors

2. UI not appearing
   - Reload the extension
   - Check for conflicts with other extensions
   - Verify script injection

3. Context menu missing
   - Reinstall the extension
   - Check permissions

## Future Enhancements

Potential improvements:

- Additional language support
- Custom API key configuration
- Translation history
- Offline translation support
- Custom styling options
