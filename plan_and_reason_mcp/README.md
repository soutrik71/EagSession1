# Plan and Reason MCP Agent

This repository contains a Multi-modal Chat Protocol (MCP) agent implementation that demonstrates a methodical approach to reasoning and problem-solving. The agent breaks down user requests into logical steps, using a variety of tools to complete tasks.

## Architecture

The system consists of two main components:

1. **MCP Server** (`example2_improved.py`): Provides the tools and functionality that the agent can use
2. **Agent** (`talk2mcp_agent.py`): Orchestrates the reasoning and execution process

## Code Flow

### MCP Server (example2_improved.py)

The server provides a collection of tools in several categories:

- **Basic Math Operations**: add, subtract, multiply, divide, etc.
- **Advanced Math Operations**: sqrt, factorial, trigonometric functions, etc.
- **Special Operations**: fibonacci generation, ASCII conversion, exponential sum
- **Image Operations**: create thumbnails
- **Notepad Operations**: open, add text, close

Each tool is registered with the FastMCP framework and includes proper parameter typing and documentation.

### Agent (talk2mcp_agent.py)

The agent follows a structured execution flow:

1. **Configuration and Initialization**
   - Load environment variables
   - Initialize Gemini client
   - Set up global state

2. **LLM Interaction**
   - Generate responses with timeout handling
   - Process LLM responses
   - Handle function calls and final answers

3. **Tool Management**
   - Format tool descriptions for LLM consumption
   - Create system prompts
   - Handle tool execution

4. **Main Execution Flow**
   - Initialize connection to the MCP server
   - Process iterations of reasoning and action
   - Handle errors and cleanup

## Prompt Structure

The system uses a carefully designed prompt that guides the LLM through a methodical reasoning process:

1. **Reasoning Step**: Analyze the situation and explain the thought process
2. **Self-Correction/Verification Step**: Review reasoning and planned actions
3. **Action Step**: Execute a function call or provide a final answer

The prompt includes:
- Clear operational guidelines
- Tool descriptions with usage examples
- Structured response format requirements
- Error handling instructions

## Example Execution

Below is the output from executing a sample query: "Find the ASCII values of characters in INDIA, calculate the sum of exponentials of those values, and show the result in Notepad."

```
Starting main execution...
Establishing connection to MCP server...
Connection established, creating session...
Session created, initializing...
Requesting tool list...
Successfully retrieved 22 tools
[Tool descriptions added...]

Evaluating system prompt...
Prompt Evaluation Results:
explicit_reasoning: ✅
structured_output: ✅
tool_separation: ✅
conversation_loop: ✅
instructional_framing: ✅
internal_self_checks: ✅
reasoning_type_awareness: ✅
fallbacks: ✅
Overall Clarity: The prompt is well-structured and provides clear instructions for a methodical computer agent.

Processing query: Find the ASCII values of characters in INDIA, calculate the sum of exponentials of those values, and show the result in Notepad.
Starting iteration loop...

--- Iteration 1 ---
LLM Reasoning: The user wants me to first find the ASCII values of characters in the word 'INDIA'. Then calculate the sum of exponentials of those values. Finally, show the result in Notepad.
Function Call: strings_to_chars_to_int(string="INDIA")
Result: [73, 78, 68, 73, 65]

--- Iteration 2 ---
LLM Reasoning: Now I need to calculate the sum of exponentials of these ASCII values [73, 78, 68, 73, 65].
Function Call: int_list_to_exponential_sum(numbers=[73, 78, 68, 73, 65])
Result: 7.599822246093079e+33

--- Iteration 3 ---
LLM Reasoning: I need to show this result in Notepad. First, I will open Notepad.
Function Call: open_notepad()
Result: Notepad opened successfully

--- Iteration 4 ---
LLM Reasoning: Now I need to add the exponential sum into the notepad.
Function Call: add_text_in_notepad(text="7.599822246093079e+33")
Result: Text:'7.599822246093079e+33' added successfully

--- Iteration 5 ---
LLM Reasoning: The task is complete. I need to close the notepad.
Function Call: close_notepad()
Result: Notepad closed successfully

=== Operations Complete ===

## Key Capabilities

1. **Methodical Reasoning**: The agent breaks down problems into logical steps
2. **Self-Correction**: The agent verifies its reasoning before taking action
3. **Tool Integration**: Seamless use of diverse tools to complete tasks
4. **Robust Error Handling**: Graceful handling of timeouts and exceptions
5. **Context Awareness**: Maintains conversation context across iterations