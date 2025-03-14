// Save target language preference when changed
document.getElementById('targetLanguage').addEventListener('change', (event) => {
    chrome.storage.sync.set({ targetLang: event.target.value });
});

// Load saved target language
chrome.storage.sync.get(['targetLang'], function (result) {
    if (result.targetLang) {
        document.getElementById('targetLanguage').value = result.targetLang;
    }
});

document.getElementById('translateButton').addEventListener('click', async () => {
    const text = document.getElementById('inputText').value.trim();
    const source = document.getElementById('sourceLanguage').value;
    const target = document.getElementById('targetLanguage').value;
    const resultDiv = document.getElementById('result');

    if (!text) {
        resultDiv.textContent = "Please enter some text to translate.";
        return;
    }

    if (source === target && source !== 'auto') {
        resultDiv.textContent = "Source and target languages cannot be the same.";
        return;
    }

    resultDiv.textContent = "Translating...";

    try {
        // If source is 'auto', use 'en' as default source language
        const sourceLang = source === 'auto' ? 'en' : source;
        const response = await fetch(`https://api.mymemory.translated.net/get?q=${encodeURIComponent(text)}&langpair=${sourceLang}|${target}`);

        if (!response.ok) {
            throw new Error("Translation API error");
        }

        const data = await response.json();
        if (data.responseData && data.responseData.translatedText) {
            resultDiv.textContent = data.responseData.translatedText;
        } else {
            throw new Error(data.responseDetails || "Translation failed");
        }
    } catch (error) {
        console.error('Translation error:', error);
        resultDiv.textContent = `Error: ${error.message || "Failed to translate. Please try again later."}`;
    }
});
