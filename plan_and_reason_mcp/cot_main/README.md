# Chain of Thought Calculator

A mathematical reasoning system that uses Chain of Thought (CoT) to solve problems step by step, with verification at each step.

## Overview

The system consists of two main components:

1. `cot_tools.py`: A server that provides mathematical tools
2. `cot_main.py`: The main application that orchestrates the problem-solving process

## Components

### cot_tools.py

This file provides the core mathematical tools used by the system:

- `show_reasoning(steps: list)`: Displays the step-by-step reasoning process
- `calculate(expression: str)`: Evaluates mathematical expressions
- `verify(expression: str, expected: float)`: Verifies if a calculation matches the expected result

The tools are exposed through a server interface that can run in development mode (`python cot_tools.py dev`).

### cot_main.py

This is the main application that:
1. Sets up the Gemini AI client
2. Manages the tool server
3. Orchestrates the problem-solving process
4. Handles the conversation flow

Key functions:
- `setup_gemini()`: Configures the Gemini AI client
- `generate_with_timeout()`: Gets responses from Gemini with timeout handling
- `create_system_prompt()`: Creates the prompt for the mathematical agent
- `extract_function_call()`: Parses function calls from model responses
- `handle_function_call()`: Executes the appropriate tool based on the function call

## How It Works

1. **Initialization**:
   - The main application starts the tool server
   - Sets up the Gemini AI client
   - Creates the system prompt for the mathematical agent

2. **Problem Solving**:
   - The system takes a mathematical problem
   - The agent breaks it down into steps
   - Each step is:
     - Calculated
     - Verified
     - Displayed to the user

3. **Verification**:
   - Every calculation is verified
   - The final answer is checked against the original problem
   - Any inconsistencies are reported

## Usage

1. Set up environment variables:
   ```bash
   export GEMINI_API_KEY=your_api_key
   ```

2. Run the tool server in development mode:
   ```bash
   python cot_tools.py dev
   ```

3. Run the main application:
   ```bash
   python cot_main.py
   ```

## Example

Given the problem: `(23 + 7) * (15 - 8)`

The system will:
1. Show the reasoning steps
2. Calculate each step
3. Verify each calculation
4. Present the final answer

## Error Handling

The system includes comprehensive error handling:
- Timeouts for AI responses
- Verification of calculations
- Proper cleanup of resources
- Clear error messages

## Development

To modify or extend the system:
1. Add new tools to `cot_tools.py`
2. Update the system prompt in `cot_main.py`
3. Add new function handlers as needed

## Dependencies

- Python 3.8+
- `google-generativeai`
- `mcp`
- `rich`
- `python-dotenv` 