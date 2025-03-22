document.addEventListener('DOMContentLoaded', function() {
    const analyzeBtn = document.getElementById('analyzeBtn');
    const repoUrlInput = document.getElementById('repoUrl');
    const loadingDiv = document.getElementById('loading');
    const resultDiv = document.getElementById('result');
    const errorDiv = document.getElementById('error');

    // Auto-populate URL from active tab if it's a GitHub repository
    chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
        const url = tabs[0].url;
        if (isValidGithubUrl(url)) {
            repoUrlInput.value = url;
            analyzeBtn.disabled = false;
            analyzeBtn.style.opacity = '1';
            analyzeBtn.style.cursor = 'pointer';
        }
    });

    // Disable button when input is empty
    repoUrlInput.addEventListener('input', () => {
        const isValid = repoUrlInput.value.trim() && isValidGithubUrl(repoUrlInput.value.trim());
        analyzeBtn.disabled = !isValid;
        analyzeBtn.style.opacity = isValid ? '1' : '0.6';
        analyzeBtn.style.cursor = isValid ? 'pointer' : 'not-allowed';
    });

    // Handle Enter key
    repoUrlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !analyzeBtn.disabled) {
            analyzeBtn.click();
        }
    });

    analyzeBtn.addEventListener('click', async () => {
        const repoUrl = repoUrlInput.value.trim();
        
        if (!isValidGithubUrl(repoUrl)) {
            showError('Please enter a valid GitHub repository URL');
            return;
        }

        try {
            setLoading(true);
            clearError();
            resultDiv.innerHTML = '';
            
            const response = await fetch('http://localhost:8000/analyze-repo', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ repo_url: repoUrl })
            });

            const data = await response.json();
            
            if (response.ok) {
                // Format the text with basic HTML
                const formattedText = formatAnalysis(data.analysis);
                resultDiv.innerHTML = formattedText;
            } else {
                throw new Error(data.detail || 'Failed to analyze repository');
            }
        } catch (error) {
            if (error.message.includes('Failed to fetch')) {
                showError('Could not connect to the analysis server. Please make sure the server is running.');
            } else {
                showError(error.message);
            }
        } finally {
            setLoading(false);
        }
    });

    function formatAnalysis(text) {
        return text
            // Escape HTML
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            // Format headers
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            // Format lists
            .replace(/^\* (.*$)/gm, '<li>$1</li>')
            .replace(/^\d\. (.*$)/gm, '<li>$1</li>')
            // Format code blocks
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            // Format inline code
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            // Format paragraphs
            .replace(/\n\n/g, '</p><p>')
            // Wrap in paragraph
            .replace(/^(.+)$/gm, '<p>$1</p>');
    }

    function isValidGithubUrl(url) {
        try {
            const parsedUrl = new URL(url);
            const pathParts = parsedUrl.pathname.split('/').filter(Boolean);
            return parsedUrl.hostname === 'github.com' && pathParts.length >= 2;
        } catch {
            return false;
        }
    }

    function setLoading(isLoading) {
        loadingDiv.style.display = isLoading ? 'flex' : 'none';
        analyzeBtn.disabled = isLoading;
        analyzeBtn.style.opacity = isLoading ? '0.6' : '1';
        analyzeBtn.style.cursor = isLoading ? 'not-allowed' : 'pointer';
    }

    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        resultDiv.innerHTML = '';
    }

    function clearError() {
        errorDiv.style.display = 'none';
        errorDiv.textContent = '';
    }

    // Initial button state
    analyzeBtn.disabled = true;
    analyzeBtn.style.opacity = '0.6';
    analyzeBtn.style.cursor = 'not-allowed';
}); 