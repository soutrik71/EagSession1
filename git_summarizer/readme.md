# GitHub Repository Analyzer

A Chrome extension powered by AI that provides detailed code structure and architecture analysis of GitHub repositories.

## Project Structure

```
git_summarizer/
├── backend/
│   ├── main.py           # FastAPI backend server
│   └── requirements.txt  # Python dependencies
└── extension/
    ├── css/
    │   └── styles.css    # Extension styling
    ├── js/
    │   └── popup.js      # Extension logic
    ├── icons/            # Extension icons
    ├── manifest.json     # Extension manifest
    └── popup.html        # Extension popup interface
```

## Features

- **One-Click Analysis**: Automatically detects GitHub repository URLs
- **AI-Powered Analysis**: Uses Google's Gemini AI to analyze repository structure
- **Detailed Insights**: Provides analysis of:
  - Architecture and Design Patterns
  - Code Organization
  - Dependencies
  - Main Components
  - Data Flow
  - Potential Improvements

## Technical Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **LangChain**: Framework for developing applications powered by language models
- **Gemini AI**: Google's advanced language model for code analysis
- **GitPython**: Library for interacting with Git repositories

### Frontend (Chrome Extension)
- **Vanilla JavaScript**: Pure JavaScript for extension logic
- **Chrome Extension APIs**: For tab management and URL detection
- **Modern CSS**: Clean, responsive design with animations

## Setup Instructions

### Backend Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Create a `.env` file in the backend directory:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

4. Start the backend server:
```bash
python main.py
```
The server will run on `http://localhost:8000`

### Extension Setup

1. Open Google Chrome
2. Go to `chrome://extensions/`
3. Enable "Developer mode" (top right)
4. Click "Load unpacked"
5. Select the `git_summarizer/extension` directory

## How It Works

### Backend Workflow

1. **Repository Cloning**:
   - Receives GitHub repository URL
   - Creates temporary directory
   - Clones repository using GitPython
   - Handles cleanup after analysis

2. **Code Analysis**:
   - Walks through repository structure
   - Filters out unnecessary files (.git)
   - Creates file structure map

3. **AI Analysis**:
   - Uses Gemini AI through LangChain
   - Analyzes repository structure
   - Generates comprehensive report

### Extension Workflow

1. **URL Detection**:
   - Automatically detects GitHub repository URLs
   - Validates URL format
   - Enables/disables analysis button

2. **Analysis Request**:
   - Sends repository URL to backend
   - Displays loading indicator
   - Handles errors gracefully

3. **Result Display**:
   - Formats AI analysis with proper HTML
   - Supports markdown-style formatting
   - Provides scrollable result view

## API Endpoints

### POST /analyze-repo
Analyzes a GitHub repository

**Request Body**:
```json
{
    "repo_url": "https://github.com/username/repository"
}
```

**Response**:
```json
{
    "analysis": "Detailed analysis in markdown format",
    "status": "success",
    "message": "Repository analyzed successfully"
}
```

## Error Handling

- Invalid repository URLs
- Connection failures
- Server errors
- Repository access issues
- Analysis failures

## Security Features

- URL validation
- HTML content sanitization
- Error message sanitization
- Temporary file cleanup
- API key protection

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - Feel free to use and modify for your needs.
