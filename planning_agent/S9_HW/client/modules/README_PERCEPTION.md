# FastMCP 2.0 Perception Module

This module is responsible for analyzing user queries, enhancing them with context from past conversations, and selecting the appropriate MCP servers and tools. It utilizes a LangChain-based chain, GPT-powered LLM integration (via LLMUtils), and Pydantic for output validation.

## Overview

- **Purpose**: To process user queries, incorporate chat history, and determine the intent and best tools to use for fulfilling the request.
- **Architecture**:
  - **Chain Construction**: Reads a prompt template (`../prompts/perception_prompt.txt`), injects tool information gathered from live MCP servers (using `get_server_tools_info` and `format_tools_for_prompt`), and sets output formatting via Pydantic (`PerceptionResult` model).
  - **Core Classes**:
    - `SelectedTool`: A data model that holds tool-specific information such as tool name, the server it resides on, and reasoning behind its selection.
    - `PerceptionResult`: Aggregates the analysis result containing the enhanced question, intent, extracted entities, selected servers, and tools.
    - `FastMCPPerception`: The primary class that initializes the LLM, builds the LangChain chain, polls live MCP server data for tool info, and performs query analysis.

## How It Works

1. **Initialization**
   - On instantiation, `FastMCPPerception` initializes the LLM using `LLMUtils`.
   - The chain is built by reading the prompt template and injecting both the formatted tool information (fetched via `get_server_tools_info` and processed by `format_tools_for_prompt`) and Pydantic's format instructions.

2. **Query Analysis**
   - The `analyze_query` method takes a user query and optionally a chat history list, then formats this history for context injection.
   - The chain integrates these inputs to produce a structured result (`PerceptionResult`) that includes the enhanced question, intent, selected servers, and recommended tools.

3. **Fallback Mechanism**
   - In case the LLM fails (e.g., due to processing errors), a fallback result is generated that marks the intent as "unknown" and returns empty selections for servers and tools.

## How to Run

- **Prerequisites**:
  - Ensure that all dependencies are available: Python 3.7+, Asyncio, LangChain Core, Pydantic, and custom modules such as `LLMUtils` and tool utilities.
  - **Live MCP Servers**: This module depends on live MCP servers for retrieving tool information. The servers required include:
    - `server1_stream.py` (Calculator)
    - `server2_stream.py` (Web Tools)
    - `server3_stream.py` (Document Search)

- **Execution**:
   - Navigate to the directory `planning_agent/S9_HW/client/modules` in your terminal.
   - Run the module using the command:

    ```bash
    python perception.py
    ```

   - This will execute the `test_perception()` function, which runs several test cases to analyze sample queries and logs results including enhanced questions, identified intent, and selected tools/servers.

## Dependencies

- **Python** (3.7+ recommended)
- **Asyncio** for asynchronous operations
- **LangChain Core** for managing the prompt templates and chain orchestration
- **Pydantic** for model validation and output parsing
- **LLMUtils** (custom module) for integrating GPT/LLM capabilities
- **Tool Utilities** (`get_server_tools_info`, `format_tools_for_prompt`) for fetching live MCP server data

## Logging and Debugging

- The module uses Python's built-in `logging` module to track initialization, chain processing, server connections, and error handling.
- In the event of connection or processing failures, errors are logged and descriptive messages prompt to check MCP server status.

## Additional Notes

- **Prompt Template**: The prompt template (`perception_prompt.txt`) in the `../prompts` directory is critical to the module's operation. Changes to this template may affect output formatting and analysis.
- **Live Data**: Since the module fetches real-time information from MCP servers, ensure that these servers are running before invoking the perception engine.
- **Modularity**: The design supports future updates to LLM integration and tool information handling with minimal changes required to the core logic.

---

This README serves as a guide for developers and users to understand, run, and extend the FastMCP 2.0 Perception Module.

## Key Features

✅ **LangChain + GPT-4o**: Integrated via LLMUtils with robust SSL handling  
✅ **Pydantic Output Parsing**: Structured JSON responses with validation  
✅ **Chat History Context**: Enhances queries using conversation context  
✅ **Smart Tool Selection**: Contextual server and tool recommendation  
✅ **Live MCP Integration**: Dynamic tool discovery from running servers  
✅ **Fallback Support**: Works offline with predefined tool information  
✅ **Partial Variables**: Efficient prompt injection with tools and format instructions  
✅ **Structured Prompts**: Clear input/output sections with examples  

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                FastMCP 2.0 Perception System               │
├─────────────────────────────────────────────────────────────┤
│ User Query + Chat History                                   │
│              ↓                                             │
│ LangChain Chain (Prompt | GPT-4o | Pydantic Parser)       │
│              ↓                                             │
│ PerceptionResult: Enhanced Query + Intent + Tools         │
└─────────────────────────────────────────────────────────────┘
```

## Files Structure

```
client/
├── tool_utils.py                     # MCP tool utilities (server:tool:desc format)
├── llm_utils.py                      # LLM utilities with GPT-4o integration
├── prompts/
│   └── perception_prompt.txt         # Structured LangChain prompt template
├── modules/
│   └── perception.py                 # Main perception engine with LLMUtils
└── test_perception.py                # Comprehensive test suite
```

## Usage

### Quick Analysis

```python
from modules.perception import analyze_user_query

# Simple query
result = await analyze_user_query("What is 25 + 37?")
print(f"Intent: {result.intent}")
print(f"Enhanced: {result.enhanced_question}")
print(f"Servers: {result.selected_servers}")
print(f"Tools: {[tool.tool_name for tool in result.selected_tools]}")

# Query with chat history
history = [
    {"sender": "human", "content": "What is 10 + 5?"},
    {"sender": "ai", "content": "10 + 5 = 15"}
]
result = await analyze_user_query("Now multiply that by 2", history)
print(f"Enhanced: {result.enhanced_question}")
# Output: "Multiply the sum of 10 and 5 by 2"
```

### Persistent Engine

```python
from modules.perception import FastMCPPerception

# Create reusable perception engine
perception = FastMCPPerception()

# Analyze multiple queries efficiently  
result1 = await perception.analyze_query("Search for FastMCP info")
result2 = await perception.analyze_query("Calculate 5^3")

# Refresh cache when servers change
await perception.refresh_tools_cache()
```

## Enhanced Features

### LLMUtils Integration
- Uses `LLMUtils` from `client/llm_utils.py`
- Automatic GPT-4o setup with SSL handling
- Environment-based configuration

### Improved Chain Architecture
```python
# Chain setup with partial variables
prompt = ChatPromptTemplate.from_template(template)
prompt = prompt.partial(
    tools_info=server_tools_info,      # Static tool information
    format_instructions=pydantic_schema  # Output structure
)
chain = prompt | llm | parser
```

### Structured Prompt Design
- **Clear input sections** with headers and placeholders
- **Detailed task descriptions** with examples
- **Explicit output requirements** with guidelines
- **server:tool:desc format** for efficient tool representation

## Output Format

```python
class PerceptionResult(BaseModel):
    enhanced_question: str              # Standalone question with context
    intent: str                        # Primary intent classification  
    entities: List[str]                # Extracted important entities
    selected_servers: List[str]        # Relevant MCP server names
    selected_tools: List[SelectedTool] # Specific tools with reasoning
    reasoning: str                     # Overall selection reasoning

class SelectedTool(BaseModel):
    tool_name: str                     # Specific tool name
    server: str                        # Server hosting the tool
    reasoning: str                     # Why this tool was selected
```

## Tool Information Format

Tools are provided in optimized `server:tool:description` format:

```
calculator:calculator_add:Add two numbers
calculator:calculator_subtract:Subtract one number from another  
web_tools:web_tools_search_web:Search the web using DuckDuckGo
doc_search:doc_search_query_documents:Search and retrieve documents
```

## Testing

### Run Comprehensive Tests
```bash
cd planning_agent/S9_HW/client
uv run test_perception.py
```

**Test Coverage:**
- ✅ Tool utilities system with server:tool:desc formatting
- ✅ LLM utilities integration with GPT-4o
- ✅ Simple mathematical queries
- ✅ Web search requests  
- ✅ Context-dependent queries with history
- ✅ Document search operations
- ✅ Multi-tool complex queries
- ✅ Persistent engine performance

## Integration Requirements

### 1. MCP Servers (Optional for Live Tool Detection)
```bash
# Terminal 1: Calculator Server
uv run server/server1_stream.py  # Port 4201

# Terminal 2: Web Tools Server  
uv run server/server2_stream.py  # Port 4202

# Terminal 3: Document Search Server
uv run server/server3_stream.py  # Port 4203
```

### 2. Environment Setup
```bash
# OpenAI API Key
export OPENAI_API_KEY="your_key_here"
# or in .env file

# Dependencies
uv add langchain-openai pydantic httpx
```

## Example Results

### Mathematical Query
**Input**: `"What is 25 + 37?"`
```json
{
  "enhanced_question": "What is 25 + 37?",
  "intent": "mathematical_calculation", 
  "entities": ["25", "37", "addition"],
  "selected_servers": ["calculator"],
  "selected_tools": [
    {
      "tool_name": "calculator_add",
      "server": "calculator",
      "reasoning": "Need to add two numbers together"
    }
  ],
  "reasoning": "Simple addition operation requires calculator server"
}
```

### Context-Aware Query
**Input**: `"Now multiply that by 2"`  
**History**: Previous calculation of 15 + 25 = 40
```json
{
  "enhanced_question": "Multiply the result of 15 + 25 (which is 40) by 2",
  "intent": "mathematical_calculation",
  "entities": ["40", "2", "multiplication"],
  "selected_servers": ["calculator"], 
  "selected_tools": [
    {
      "tool_name": "calculator_multiply",
      "server": "calculator",
      "reasoning": "Need to multiply the previous result by 2"
    }
  ],
  "reasoning": "Contextual multiplication based on previous calculation"
}
```

### Multi-Tool Query
**Input**: `"Search for Python tutorials and calculate 2^8"`
```json
{
  "enhanced_question": "Search for Python tutorials and calculate 2^8", 
  "intent": "multi_task",
  "entities": ["Python", "tutorials", "2", "8", "power"],
  "selected_servers": ["web_tools", "calculator"],
  "selected_tools": [
    {
      "tool_name": "web_tools_search_web", 
      "server": "web_tools",
      "reasoning": "Search for Python tutorial information online"
    },
    {
      "tool_name": "calculator_power",
      "server": "calculator", 
      "reasoning": "Calculate 2 raised to the power of 8"
    }
  ],
  "reasoning": "Requires both web search and mathematical computation"
}
```

## Key Improvements

### ✅ **LLM Integration**
- Uses `LLMUtils` from `client/llm_utils.py`
- Automatic GPT-4o setup with SSL handling
- Environment-based configuration

### ✅ **Chain Architecture**  
- **Partial variables** for static content (tools, format instructions)
- **Template-based prompts** with clear structure
- **Efficient pipeline**: `prompt | llm | parser`

### ✅ **Prompt Engineering**
- **Structured sections**: Input Context, Tasks, Output Requirements
- **Clear guidelines** with examples
- **server:tool:desc format** for concise tool representation

### ✅ **Error Handling**
- **Graceful fallbacks** when LLM fails
- **Offline mode** with predefined tool information  
- **Robust initialization** with proper error logging

### ✅ **Performance**
- **Cached tool information** to reduce MCP calls
- **Persistent engines** for multiple queries
- **Efficient tool format** for prompt injection

## Next Steps

1. **Integration**: Connect with main agent system
2. **Workflows**: Support complex multi-step task planning  
3. **Analytics**: Add tool usage and performance metrics
4. **Optimization**: Cache management and response time improvements
5. **Extensions**: Support for custom tool types and dynamic server discovery 