# FastMCP 2.0 Perception System

## Overview

This perception system provides intelligent query analysis for the FastMCP 2.0 architecture, using **LangChain with GPT-4o** and **Pydantic output parsing** to understand user queries, enhance them with chat history context, and select appropriate MCP servers and tools.

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