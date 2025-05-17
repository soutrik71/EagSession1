# EAG Multiserver MCP (Master Control Program)

## Overview

EAG Multiserver MCP is a sophisticated framework for orchestrating multiple specialized AI services to handle complex user requests. The system coordinates various tools across multiple servers to complete multi-stage tasks, like searching for information, creating documents, and sending emails.

## Architecture

The system is built with a client-server architecture:

- **Client**: Orchestrates the process, manages user inputs, handles decision-making, and coordinates server interactions
- **Servers**: Specialized components providing specific functionality:
  - `gmail_server`: Email functions
  - `gsuite_server`: Google Workspace integration (Sheets, Docs, etc.)
  - `websearch_server`: Web search capabilities

## Key Components

### Client

- **perception.py**: Analyzes user queries to identify necessary sub-tasks
- **decision.py**: Makes decisions about which tools to use for each sub-task
- **action.py**: Executes tool calls and processes results
- **memory.py**: Stores conversation history for context
- **llm_provider.py**: Handles LLM integration for decision-making
- **client.py**: Main orchestration layer that ties everything together

### Servers

- **gmail_server.py**: Provides email functionality (sending emails with attachments)
- **gsuite_server.py**: Handles Google Workspace operations (creating spreadsheets, documents)
- **websearch_server.py**: Manages web search functionality

## Process Flow

The system follows this workflow as shown in the example:

1. **Initialization**:
   - Load configuration settings
   - Initialize memory store for conversation history
   - Set up server connections

2. **Query Processing**:
   - User enters a query (e.g., "Give me the driver standing for F1-2025 and create a Google sheet and send an email...")
   - System generates a unique conversation ID

3. **Decision Making**:
   - The perception chain enhances the user query and breaks it into sub-questions
   - For each sub-question, the system identifies appropriate tools to use
   - Decisions are made using a large language model (LLM)

4. **Tool Execution**:
   - Tools are executed in sequence to fulfill the user's request
   - In the example, three tools were used:
     1. `search_web`: Searched for F1 2025 driver standings
     2. `create_gsheet`: Created a Google Sheet with the retrieved data
     3. `send_email`: Sent an email to the specified address

5. **Results Processing**:
   - Results from each tool are collected and combined
   - The conversation is saved to memory and logged for reference

6. **Completion**:
   - A conversation summary is generated
   - The session is saved for future reference

## Example Usage

As shown in the terminal output:

```
Enter your questions (one per line, press Enter twice to finish):
Give me the driver standing for f1-2025 and create a google sheet and send an email stating the facts and figures with soutrik1991@gmail.com
```

The system:
1. Searched for F1 2025 driver standings information
2. Created a Google Sheet with the data: https://docs.google.com/spreadsheets/d/1zH1FoZ81qxl7f6FAFA1wq3cF7X_PGv12btH2mE6Nh7s
3. Sent an email to soutrik1991@gmail.com with the results

## Key Features

- **Multi-server coordination**: Seamlessly connects to multiple specialized servers
- **Complex task decomposition**: Breaks down complex user requests into manageable sub-tasks
- **LLM-powered decision making**: Uses large language models for intelligent task planning
- **Conversation memory**: Maintains context across interactions
- **Robust error handling**: Handles errors gracefully with detailed logging

## Technical Details

- Built using Python with asyncio for asynchronous operations
- Uses LangChain for LLM interactions
- Implements vectorized memory for conversation history
- Handles SSL verification settings for secure connections
- Stores logs and session information for debugging and auditing
