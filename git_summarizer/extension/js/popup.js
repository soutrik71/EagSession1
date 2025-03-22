document.addEventListener('DOMContentLoaded', function() {
    const analyzeBtn = document.getElementById('analyzeBtn');
    const repoUrlInput = document.getElementById('repoUrl');
    const loadingDiv = document.getElementById('loading');
    const resultDiv = document.getElementById('result');

    analyzeBtn.addEventListener('click', async () => {
        const repoUrl = repoUrlInput.value.trim();
        
        if (!isValidGithubUrl(repoUrl)) {
            alert('Please enter a valid GitHub repository URL');
            return;
        }

        try {
            loadingDiv.style.display = 'block';
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
                resultDiv.innerHTML = data.analysis;
            } else {
                throw new Error(data.error || 'Failed to analyze repository');
            }
        } catch (error) {
            resultDiv.innerHTML = `Error: ${error.message}`;
        } finally {
            loadingDiv.style.display = 'none';
        }
    });

    function isValidGithubUrl(url) {
        try {
            const parsedUrl = new URL(url);
            return parsedUrl.hostname === 'github.com' && parsedUrl.pathname.split('/').length >= 3;
        } catch {
            return false;
        }
    }
}); 