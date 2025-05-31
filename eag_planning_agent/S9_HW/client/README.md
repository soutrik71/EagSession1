# FastMCP 2.0 Client Architecture

## 🎯 Overview

The FastMCP 2.0 client implements a sophisticated **AI-orchestrated multi-server MCP (Model Context Protocol) system** that processes user queries through a three-stage pipeline:

```
User Query → 🧠 Perception → 🎯 Decision → ⚡ Action → 📊 Result
```

This architecture enables intelligent tool selection, optimal execution planning, and seamless coordination across multiple MCP servers.

## 🏗️ Architecture Overview

### Core Philosophy
The system follows a **"Analyze → Plan → Execute"** paradigm where:
- **Perception** understands what the user wants
- **Decision** plans how to achieve it
- **Action** executes the plan efficiently

### Module Structure
```
client/
├── modules/
│   ├── perception.py     # 🧠 Query Analysis & Tool Selection
│   ├── decision.py       # 🎯 Execution Planning & Strategy
│   └── action.py         # ⚡ Tool Execution & Result Processing
├── core/
│   ├── session.py        # 🔗 Multi-server MCP connections
│   └── tool_call.py      # 🛠️ Tool execution engine
├── single_loop.py        # 📋 Complete pipeline demonstration
└── llm_utils.py          # 🤖 LLM integration utilities
```

---

## 🧠 Perception Module (`modules/perception.py`)

### **Role**: Query Understanding & Tool Recommendation
The perception module acts as the **"understanding brain"** of the system.

### **Key Responsibilities**:
1. **Query Enhancement**: Transforms user input into standalone, context-aware questions
2. **Intent Recognition**: Identifies what the user wants to accomplish
3. **Entity Extraction**: Extracts key information from the query
4. **Tool Selection**: Recommends appropriate MCP servers and tools
5. **Context Integration**: Incorporates chat history when needed

### **How It Works**:
```python
# Input: Raw user query + chat history
query = "What is the sum of 25 and 37?"
chat_history = []

# Process through LangChain pipeline
perception_engine = await create_perception_engine()
result = await perception_engine.analyze_query(query, chat_history)

# Output: PerceptionResult with tool recommendations
```

### **Output Structure (`PerceptionResult`)**:
```python
PerceptionResult(
    enhanced_question="What is the sum of 25 and 37?",
    intent="mathematical_calculation",
    entities=["25", "37"],
    selected_servers=["calculator"],
    selected_tools=[
        SelectedTool(
            tool_name="calculator_add",
            server="calculator", 
            reasoning="Addition operation needed"
        )
    ],
    reasoning="Simple arithmetic requiring calculator tools"
)
```

### **Intelligence Features**:
- **Live Server Discovery**: Connects to active MCP servers to get real-time tool information
- **Contextual Analysis**: Uses GPT-4o with structured prompting for intelligent tool selection
- **Fallback Handling**: Graceful degradation when servers are unavailable

---

## 🎯 Decision Module (`modules/decision.py`)

### **Role**: Execution Strategy & Detailed Planning
The decision module acts as the **"strategic planner"** of the system.

### **Key Responsibilities**:
1. **Strategy Selection**: Chooses optimal execution approach (single, parallel, sequential, hybrid)
2. **Tool Orchestration**: Plans the sequence and dependencies of tool calls
3. **Parameter Mapping**: Determines exact parameters for each tool call
4. **Dependency Management**: Handles inter-tool dependencies and data flow
5. **Risk Assessment**: Identifies potential execution issues

### **How It Works**:
```python
# Input: PerceptionResult from previous stage
decision_engine = await create_decision_engine()
result = await decision_engine.analyze_decision_from_perception(perception_result)

# Alternative: Direct tool list input
result = await decision_engine.analyze_decision(
    enhanced_question="What is the sum of 25 and 37?",
    recommended_tools=["calculator_add"]
)
```

### **Output Structure (`DecisionResult`)**:
```python
DecisionResult(
    strategy=ExecutionStrategy.SINGLE_TOOL,
    total_steps=1,
    tool_calls=[
        ToolCall(
            step=1,
            tool_name="calculator_add",
            parameters={"input": {"a": 25, "b": 37}},
            dependency="none",
            purpose="Add two numbers to get final answer",
            result_variable=None
        )
    ],
    execution_sequence="Single direct calculation",
    final_result_processing="Return numeric result directly",
    reasoning="Simple arithmetic operation requiring one tool call"
)
```

### **Execution Strategies**:
- **`SINGLE_TOOL`**: One tool, straightforward execution
- **`PARALLEL_TOOLS`**: Multiple independent tools executed simultaneously  
- **`SEQUENTIAL_TOOLS`**: Tools executed in sequence with dependencies
- **`HYBRID_TOOLS`**: Mix of parallel and sequential execution

### **Intelligence Features**:
- **Smart Parameter Extraction**: Uses LLM to extract exact parameters from natural language
- **Dependency Resolution**: Automatically handles tool output → input relationships
- **Strategy Optimization**: Selects the most efficient execution approach

---

## ⚡ Action Module (`modules/action.py`)

### **Role**: Tool Execution & Result Processing
The action module acts as the **"execution engine"** of the system.

### **Key Responsibilities**:
1. **Plan Execution**: Executes the decision plan with proper timing and coordination
2. **Multi-server Communication**: Manages connections to multiple MCP servers
3. **Error Handling**: Handles tool failures and provides meaningful error messages
4. **Result Processing**: Formats and presents final results to users
5. **Performance Monitoring**: Tracks execution times and success rates

### **How It Works**:
```python
# Option 1: Execute with pre-computed decision
action_result = await execute_with_decision_result(query, decision_result)

# Option 2: Full pipeline (perception + decision + action)
action_result = await execute_query_full_pipeline(query)

# Option 3: Direct engine usage
async with create_action_engine() as engine:
    result = await engine.execute_decision(query, decision_result)
```

### **Output Structure (`ActionResult`)**:
```python
ActionResult(
    success=True,
    query="What is the sum of 25 and 37?",
    strategy="ExecutionStrategy.SINGLE_TOOL",
    total_steps=1,
    execution_time=0.55,
    final_answer="✅ {\n  \"result\": 62.0\n}",
    detailed_results={
        "strategy_used": "ExecutionStrategy.SINGLE_TOOL",
        "tools_executed": 1,
        "successful_tools": 1,
        "failed_tools": 0,
        "tool_results": [...]
    },
    tool_execution_log=["Starting execution...", "Completed successfully"],
    error=None
)
```

### **Execution Features**:
- **Async Execution**: Non-blocking execution with proper resource management
- **Session Management**: Efficient connection pooling and cleanup
- **Real-time Logging**: Detailed execution logs for debugging and monitoring
- **Result Formatting**: Human-readable result presentation

---

## 📋 Single Loop Demo (`single_loop.py`)

### **Purpose**: Complete Pipeline Demonstration
The `single_loop.py` script demonstrates the **full three-stage pipeline** working together seamlessly.

### **What It Does**:
```python
# 1. Perception Stage
perception_result = await call_perception_engine(query, chat_history)

# 2. Decision Stage  
decision_result = await call_decision_engine(perception_result)

# 3. Action Stage
action_result = await call_action_engine(query, decision_result)
```

### **Key Integration Points**:

#### **1. Perception → Decision Integration**:
```python
# Perception outputs PerceptionResult
perception_result = PerceptionResult(
    selected_tools=[SelectedTool(tool_name="calculator_add", ...)]
)

# Decision accepts PerceptionResult via special method
decision_result = await decision_engine.analyze_decision_from_perception(perception_result)
```

#### **2. Decision → Action Integration**:
```python
# Decision outputs DecisionResult with detailed tool calls
decision_result = DecisionResult(
    tool_calls=[ToolCall(tool_name="calculator_add", parameters={...})]
)

# Action executes the decision plan directly
action_result = await execute_with_decision_result(query, decision_result)
```

### **Data Flow Example**:
```
Query: "What is the sum of 25 and 37?"
    ↓
🧠 Perception: 
    - Enhanced: "What is the sum of 25 and 37?"
    - Tools: ["calculator_add"]
    ↓
🎯 Decision:
    - Strategy: SINGLE_TOOL  
    - Call: calculator_add(a=25, b=37)
    ↓
⚡ Action:
    - Execute: calculator_add tool
    - Result: 62.0
    ↓
📊 Final: "✅ { \"result\": 62.0 }"
```

---

## 🚀 Usage Examples

### **1. Simple Mathematical Query**:
```python
query = "What is 15 * 8?"
result = await execute_query_full_pipeline(query)
# Result: 120
```

### **2. Complex Multi-tool Query**:
```python
query = "What is 5 factorial and what is the square root of 144?"
result = await execute_query_full_pipeline(query)
# Executes: calculator_factorial(5) AND calculator_sqrt(144) in parallel
# Result: "5! = 120 and √144 = 12"
```

### **3. Sequential Dependency Query**:
```python
query = "Calculate sine of 45 degrees, then square that result"
result = await execute_query_full_pipeline(query)
# Executes: calculator_sin(45) → calculator_power(result, 2)
```

### **4. Web Search + Calculation**:
```python
query = "Search for the height of Mount Everest and convert it to feet"
result = await execute_query_full_pipeline(query)
# Executes: web_search → unit_conversion
```

---

## 🔧 Configuration & Setup

### **Required Dependencies**:
- **LangChain**: For LLM integration and structured prompting
- **Pydantic**: For data validation and serialization
- **AsyncIO**: For non-blocking execution
- **OpenAI API**: For GPT-4o integration

### **MCP Server Requirements**:
The system requires active MCP servers running on:
- **Calculator Server**: `http://127.0.0.1:4201/mcp/` (Math operations)
- **Web Tools Server**: `http://127.0.0.1:4202/mcp/` (Web search, etc.)
- **Document Search**: `http://127.0.0.1:4203/mcp/` (Document operations)

### **Environment Setup**:
```bash
# Install dependencies
uv install

# Start MCP servers (in separate terminals)
python server/server1_stream.py  # Calculator
python server/server2_stream.py  # Web Tools  
python server/server3_stream.py  # Document Search

# Run the complete pipeline demo
python client/single_loop.py
```

---

## 🎯 Key Benefits

### **1. Intelligent Automation**:
- **Smart Tool Selection**: AI chooses the right tools automatically
- **Optimal Planning**: Efficient execution strategies
- **Error Recovery**: Graceful handling of failures

### **2. Scalability**:
- **Multi-server Support**: Easily add new MCP servers
- **Parallel Execution**: Simultaneous tool calls when possible
- **Resource Management**: Efficient connection handling

### **3. Maintainability**:
- **Modular Design**: Clear separation of concerns
- **Structured Data**: Pydantic models for type safety
- **Comprehensive Logging**: Detailed execution tracking

### **4. User Experience**:
- **Natural Language**: Users ask questions in plain English
- **Fast Responses**: Optimized execution strategies
- **Rich Results**: Detailed result information

---

## 🛠️ Development & Extension

### **Adding New Modules**:
1. Follow the three-stage pattern (analyze → plan → execute)
2. Use Pydantic models for data structures
3. Implement async patterns for performance
4. Add comprehensive logging and error handling

### **Integrating New MCP Servers**:
1. Add server configuration to `tool_utils/server_config.yaml`
2. Update tool discovery in `core/session.py`
3. Test with perception module for tool selection

### **Custom Execution Strategies**:
1. Extend `ExecutionStrategy` enum in `decision.py`
2. Implement strategy logic in `action.py`
3. Update decision planning logic accordingly

---

This architecture provides a robust, scalable foundation for AI-orchestrated multi-server tool execution, with clear separation of concerns and intelligent automation at every stage. 