## How to install and create an uv project

`Command to create a new uv project:`
```bash
cd folder_name/
uv init #existing folder

# Install dependencies
# copy the dependencies from pyproject.toml
# uv add dependency1 dependency2 dependency3 ...
uv sync

# Run the project
uv run python main.py

# Or activate the venv and run the project
source .venv/bin/activate #linux
.venv\Scripts\activate #windows
python main.py # python -m main

# update conda with uv
conda activate env
uv pip install -e .
```

`References:`

[uv-deep-dive](https://www.saaspegasus.com/guides/uv-deep-dive/)

[uv-environments](https://docs.astral.sh/uv/pip/environments/#__tabbed_1_2)

[introducing-uv](https://codemaker2016.medium.com/introducing-uv-next-gen-python-package-manager-b78ad39c95d7)


## Addition of existing mcp server to the cursor:

1. First, you need a Brave Search API key:
   - Create an account on Brave Search
   - Generate an API key

2. Add the MCP server to Cursor:
   - Open Cursor
   - Go to Settings > Cursor Settings > Features
   - Click "Add new MCP server"
   - Enter the following details:
     - Name: Brave Search
     - Type: Command
     - Command: `npx -y @smithery/cli@latest run @smithery-ai/brave-search --config "{\"braveApiKey\":\"YOUR_API_KEY\"}"`
     (Replace YOUR_API_KEY with your actual Brave Search API key)

3. After adding:
   - Go back to Settings > MCP
   - Click the refresh button
   - The Cursor agent will then be able to see and use the Brave Search tools

The MCP server will then be available for use in Cursor, allowing you to perform web searches directly from the IDE.

```
Similarly we added Github MCP server to the cursor:

1. Add the MCP server to Cursor:
   - Open Cursor
   - Go to Settings > Cursor Settings > Features
   - Click "Add new MCP server"
   - Enter the following details:
     - Name: Github
     - Type: Command
     - Command: `npx -y @smithery/cli@latest run @smithery-ai/github --config "{\"githubPersonalAccessToken\":\"YOUR_ACCESS_TOKEN\"}"`
     (Replace YOUR_ACCESS_TOKEN with your actual Github personal access token)

2. After adding:
   - Go back to Settings > MCP
   - Click the refresh button
   - The Cursor agent will then be able to see and use the Github tools

list of commands:
Create/update files
Search repositories
Create repository
Get file contents
Push files
Create issues
Create pull requests
Fork repository
Create branch
List commits
List/update issues
Add issue comments
Search code/issues/users

```

## Adding custom MCP server to the cursor:

1. Start the MCP server:

```bash
uv run python server.py
```

2. Add the MCP server to Cursor:
   - Open Cursor
   - Go to Preferences > Cursor Settings > MCP
   - Click "Add new MCP server"
   - Enter the following details:
     - Name: MCP Server
     - Type: uv --directory C:/workspace/EagSession1/mcp_full_course/mcp_server run server.py

3. After adding:
   - Go back to Settings > MCP
   - Click the refresh button
   - The Cursor agent will then be able to see and use the MCP server tools


