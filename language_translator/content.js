// Check if script is already injected
if (window.translatorInitialized) {
    throw new Error('Translator already initialized');
}
window.translatorInitialized = true;

// Global variables
const state = {
    selectedText: '',
    translateButton: null,
    tooltip: null,
    languageSelector: null,
    selectedRange: null
};

// Initialize the extension
function initializeExtension() {
    try {
        if (!state.translateButton) {
            state.translateButton = createTranslateButton();
        }
        if (!state.tooltip) {
            state.tooltip = createTooltip();
        }
        if (!state.languageSelector) {
            state.languageSelector = createLanguageSelector();
        }
    } catch (error) {
        console.error('Initialization error:', error);
    }
}

// Create language selector
function createLanguageSelector() {
    const container = document.createElement('div');
    container.id = 'translate-language-selector';
    container.style.cssText = `
        position: absolute;
        z-index: 999999;
        background: white;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        display: none;
    `;

    const select = document.createElement('select');
    select.style.cssText = `
        padding: 4px;
        margin-right: 8px;
        border: 1px solid #ddd;
        border-radius: 4px;
    `;

    const languages = [
        { code: 'de', name: 'German' },
        { code: 'es', name: 'Spanish' },
        { code: 'fr', name: 'French' },
        { code: 'hi', name: 'Hindi' },
        { code: 'kn', name: 'Kannada' },
        { code: 'zh', name: 'Chinese' },
        { code: 'ja', name: 'Japanese' },
        { code: 'ko', name: 'Korean' }
    ];

    languages.forEach(lang => {
        const option = document.createElement('option');
        option.value = lang.code;
        option.textContent = lang.name;
        select.appendChild(option);
    });

    const translateBtn = document.createElement('button');
    translateBtn.textContent = 'Translate';
    translateBtn.style.cssText = `
        padding: 4px 12px;
        background: #4285f4;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    `;

    const replaceBtn = document.createElement('button');
    replaceBtn.textContent = 'Replace';
    replaceBtn.style.cssText = `
        padding: 4px 12px;
        background: #34a853;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        margin-left: 8px;
    `;

    container.appendChild(select);
    container.appendChild(translateBtn);
    container.appendChild(replaceBtn);

    document.body.appendChild(container);

    translateBtn.addEventListener('click', () => {
        handleTranslation(state.selectedText, select.value, false);
    });

    replaceBtn.addEventListener('click', () => {
        handleTranslation(state.selectedText, select.value, true);
    });

    return container;
}

// Create floating translate button
function createTranslateButton() {
    const button = document.createElement('div');
    button.id = 'quick-translate-button';
    button.innerHTML = '🌐 <span>Translate</span>';
    button.style.position = 'absolute';
    button.style.zIndex = '999999';
    document.body.appendChild(button);
    return button;
}

// Create translation tooltip
function createTooltip() {
    const tooltip = document.createElement('div');
    tooltip.id = 'translation-tooltip';
    tooltip.style.cssText = `
        position: absolute;
        z-index: 999999;
        background: white;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        max-width: 300px;
        font-size: 14px;
        line-height: 1.4;
        display: none;
    `;
    
    // Add a close button
    const closeBtn = document.createElement('button');
    closeBtn.textContent = '×';
    closeBtn.style.cssText = `
        position: absolute;
        right: 5px;
        top: 5px;
        background: none;
        border: none;
        font-size: 16px;
        cursor: pointer;
        color: #666;
        padding: 0 5px;
    `;
    closeBtn.addEventListener('click', () => {
        tooltip.style.display = 'none';
    });
    
    tooltip.appendChild(closeBtn);
    document.body.appendChild(tooltip);
    return tooltip;
}

// Show translate button near selected text
function showTranslateButton(event) {
    if (event.target.id === 'translation-tooltip' || 
        event.target.id === 'quick-translate-button' ||
        event.target.closest('#translate-language-selector')) return;

    const selection = window.getSelection();
    state.selectedText = selection.toString().trim();
    state.selectedRange = selection.rangeCount > 0 ? selection.getRangeAt(0) : null;

    if (state.selectedText && state.selectedRange) {
        if (!state.translateButton) {
            state.translateButton = createTranslateButton();
        }

        const range = selection.getRangeAt(0);
        const rect = range.getBoundingClientRect();
        
        // Show language selector instead of translate button
        if (!state.languageSelector) {
            state.languageSelector = createLanguageSelector();
        }
        
        state.languageSelector.style.display = 'block';
        const selectorX = Math.min(rect.right + window.scrollX, window.innerWidth - 250);
        const selectorY = Math.max(rect.top + window.scrollY - 50, 10);
        
        state.languageSelector.style.left = `${selectorX}px`;
        state.languageSelector.style.top = `${selectorY}px`;
    } else {
        if (state.languageSelector) state.languageSelector.style.display = 'none';
        if (state.tooltip) state.tooltip.style.display = 'none';
    }
}

// Handle translation
async function handleTranslation(text, targetLang, shouldReplace = false) {
    if (!text) return;

    // Get the language selector position for tooltip placement
    const langSelector = document.getElementById('translate-language-selector');
    const langSelectorRect = langSelector.getBoundingClientRect();

    if (!state.tooltip) {
        state.tooltip = createTooltip();
    }
    
    // Position tooltip next to language selector
    state.tooltip.style.cssText = `
        position: absolute;
        z-index: 999999;
        background: white;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        max-width: 300px;
        font-size: 14px;
        line-height: 1.4;
        display: block;
        left: ${langSelectorRect.right + 10 + window.scrollX}px;
        top: ${langSelectorRect.top + window.scrollY}px;
    `;
    
    // Show loading message
    state.tooltip.innerHTML = `
        <button style="position: absolute; right: 5px; top: 5px; background: none; border: none; font-size: 16px; cursor: pointer; color: #666; padding: 0 5px;">×</button>
        <div style="padding: 10px;">Translating...</div>
    `;
    
    // Add click handler to close button
    state.tooltip.querySelector('button').addEventListener('click', () => {
        state.tooltip.style.display = 'none';
    });
    
    try {
        const response = await fetch(`https://api.mymemory.translated.net/get?q=${encodeURIComponent(text)}&langpair=en|${targetLang}`);
        const data = await response.json();
        
        if (data.responseData && data.responseData.translatedText) {
            if (shouldReplace && state.selectedRange) {
                // Replace the selected text with translation
                const span = document.createElement('span');
                span.className = 'translated-text';
                span.textContent = data.responseData.translatedText;
                span.title = `Original text: ${text}`;
                state.selectedRange.deleteContents();
                state.selectedRange.insertNode(span);
                
                // Hide UI elements
                if (state.languageSelector) state.languageSelector.style.display = 'none';
                if (state.tooltip) state.tooltip.style.display = 'none';
            } else {
                // Show translation in tooltip
                showTranslationTooltip(data.responseData.translatedText, langSelectorRect);
            }
        } else {
            showTranslationTooltip('Translation failed. Please try again.', langSelectorRect);
            console.error('Translation failed:', data);
        }
    } catch (error) {
        console.error('Translation error:', error);
        showTranslationTooltip('Error: Could not connect to translation service.', langSelectorRect);
    }
}

// Show translation tooltip
function showTranslationTooltip(translatedText, langSelectorRect) {
    if (!state.tooltip) {
        state.tooltip = createTooltip();
    }

    // Create content container
    const contentDiv = document.createElement('div');
    contentDiv.style.padding = '5px';
    
    // Add original text
    const originalTextDiv = document.createElement('div');
    originalTextDiv.style.marginBottom = '12px';
    originalTextDiv.style.color = '#666';
    originalTextDiv.innerHTML = `<strong>Original:</strong><br>${state.selectedText}`;
    
    // Add translated text
    const translatedTextDiv = document.createElement('div');
    translatedTextDiv.style.marginTop = '8px';
    translatedTextDiv.innerHTML = `<strong>Translation:</strong><br>${translatedText}`;
    
    // Clear previous content and add new content
    state.tooltip.innerHTML = '';
    
    // Add close button
    const closeBtn = document.createElement('button');
    closeBtn.textContent = '×';
    closeBtn.style.cssText = `
        position: absolute;
        right: 5px;
        top: 5px;
        background: none;
        border: none;
        font-size: 16px;
        cursor: pointer;
        color: #666;
        padding: 0 5px;
    `;
    closeBtn.addEventListener('click', () => {
        state.tooltip.style.display = 'none';
    });
    
    contentDiv.appendChild(originalTextDiv);
    contentDiv.appendChild(translatedTextDiv);
    state.tooltip.appendChild(closeBtn);
    state.tooltip.appendChild(contentDiv);
    
    // Position tooltip next to language selector
    state.tooltip.style.cssText = `
        position: absolute;
        z-index: 999999;
        background: white;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        max-width: 300px;
        font-size: 14px;
        line-height: 1.4;
        display: block;
        left: ${langSelectorRect.right + 10 + window.scrollX}px;
        top: ${langSelectorRect.top + window.scrollY}px;
    `;
}

// Modify the message listener to be more resilient
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    try {
        if (request.action === "translate") {
            initializeExtension();
            const selection = window.getSelection();
            state.selectedRange = selection.rangeCount > 0 ? selection.getRangeAt(0) : null;
            handleTranslation(request.text, request.targetLang || 'de', false);
            sendResponse({ status: 'success' });
        }
    } catch (error) {
        console.error('Message handling error:', error);
        sendResponse({ status: 'error', message: error.message });
    }
    return true;
});

// Initialize extension with error handling
try {
    initializeExtension();
    
    // Add event listeners with error handling
    document.addEventListener('mouseup', (e) => {
        try {
            showTranslateButton(e);
        } catch (error) {
            console.error('MouseUp handler error:', error);
        }
    });

    document.addEventListener('click', (e) => {
        try {
            if (!e.target.closest('#translate-language-selector') && 
                !e.target.closest('#translation-tooltip')) {
                if (state.languageSelector) state.languageSelector.style.display = 'none';
                if (state.tooltip) state.tooltip.style.display = 'none';
            }
        } catch (error) {
            console.error('Click handler error:', error);
        }
    });

    let scrollTimeout;
    window.addEventListener('scroll', (e) => {
        try {
            if (state.languageSelector) state.languageSelector.style.display = 'none';
            if (state.tooltip) state.tooltip.style.display = 'none';
            
            clearTimeout(scrollTimeout);
            
            scrollTimeout = setTimeout(() => {
                const selection = window.getSelection();
                if (selection.toString().trim()) {
                    showTranslateButton({ target: document.body });
                }
            }, 100);
        } catch (error) {
            console.error('Scroll handler error:', error);
        }
    }, { passive: true });

} catch (error) {
    console.error('Extension initialization error:', error);
}