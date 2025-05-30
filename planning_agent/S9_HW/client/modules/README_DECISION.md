# FastMCP 2.0 Decision Module

This module is responsible for analyzing enhanced user queries and generating detailed execution plans with proper tool orchestration. It leverages LangChain, GPT-based LLM integration, and Pydantic models to parse and format the decision output.

## Overview

- **Purpose**: Given an enhanced user query and a set of recommended tools, the decision engine decomposes the query, determines whether a single or multiple tool strategy is needed, and constructs an executable plan.
- **Architecture**: 
  - Uses a LangChain chain that is built from a prompt template (located at `../prompts/decision_prompt.txt`), the LLM (initialized via `LLMUtils`), and a PydanticOutputParser that enforces the structure defined by the `DecisionResult` model.
  - The main classes include:
    - `ToolCall`: Specifies individual tool call details (step number, tool name, parameters, dependencies, etc.).
    - `DecisionResult`: Aggregates the overall execution plan, strategy, steps, and potential issues.
    - `FastMCPDecision`: Initializes and orchestrates the chain. It also implements a fallback mechanism in case the LLM fails to generate a proper plan.

## How It Works

1. **Initialization**
   - On instantiation, the `FastMCPDecision` class initializes the LLM using `LLMUtils`.
   - The chain is constructed by reading the decision prompt template and partially injecting output format instructions.

2. **Decision Analysis**
   - The `analyze_decision` method logs the incoming query and recommended tools.
   - It fetches filtered tool descriptions via `get_filtered_tools_summary`.
   - The chain is invoked asynchronously to generate a complete decision plan (expressed as a `DecisionResult`).

3. **Fallback Strategy**
   - If the LLM fails to generate a plan, a fallback result is created using the first recommended tool, ensuring the system can still proceed with execution.

## How to Run

- **Prerequisites**: 
  - Ensure that all dependent modules (`llm_utils`, `tool_utils`, `langchain_core`, and `pydantic`) are available in your Python environment.
  - The decision module does not directly depend on live MCP servers, but correct tool descriptions depend on proper configuration in `tool_utils`.

- **Execution**:
  - Navigate to the directory `planning_agent/S9_HW/client/modules` in your terminal.
  - Run the module using the command:

    ```bash
    python decision.py
    ```

  - This will execute the `test_decision()` function, which runs several test cases and logs the execution plan details to the console.

## Dependencies

- **Python** (3.7+ recommended)
- **Asyncio** for asynchronous execution
- **LangChain Core** for prompt management and chain orchestration
- **Pydantic** for output validation
- **LLMUtils** (custom module) for GPT/LLM integration

## Logging and Debugging

- The module uses Python's built-in `logging` module to log important initialization steps, decision analysis stages, and any errors.
- In case of LLM failure, the logs will indicate that a fallback plan is being used.

## Additional Notes

- The prompt template (`decision_prompt.txt`) plays a critical role in the chain. Any changes to its format can affect the generation of the decision plan.
- The design is intended to be modular, so future updates to LLM integration or tool descriptions can be managed with minimal changes to this module.

---

This README should assist developers and users in understanding the decision module's functionality, setup, and execution flow. 