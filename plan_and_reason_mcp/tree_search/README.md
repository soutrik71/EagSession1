# Tree Search Reasoning System

This module implements a tree search-based reasoning system that helps explore and evaluate different paths to solve problems. It consists of two main components:

## Components

### 1. cot_tools.py
This file contains the core tools for Chain of Thought (CoT) reasoning and path evaluation:

- **show_reasoning(steps)**: Displays step-by-step reasoning process with rich formatting
- **calculate(expression)**: Evaluates mathematical expressions and returns results
- **verify(expression, expected)**: Verifies calculation results against expected values
- **check_consistency(steps)**: Analyzes consistency of reasoning steps with detailed reports
- **explore_path(steps)**: Simulates and visualizes reasoning steps for a given path
- **evaluate_paths(paths)**: Evaluates and ranks different reasoning paths based on heuristics

The tools use rich formatting for better visualization and include comprehensive error handling and validation. Each tool is implemented as a FastMCP tool with proper type hints and documentation.

### 2. sim_main.py
This is the main simulation file that orchestrates the tree search process:

- **setup_gemini()**: Configures and returns a Gemini AI client
- **generate_with_timeout()**: Handles AI responses with timeout protection
- **create_system_prompt()**: Generates the system prompt for the planning agent
- **extract_function_call()**: Parses model responses for function calls
- **handle_path_exploration()**: Manages path exploration and evaluation
- **extract_steps_from_response()**: Processes and extracts calculation steps
- **execute_steps()**: Executes and verifies each calculation step
- **extract_final_answer()**: Extracts the final result from the last step

The file implements async communication with the tools and provides detailed logging and visualization throughout the process.

## How It Works

1. **Initialization**:
   - Loads environment variables and sets up Gemini AI client
   - Initializes FastMCP server for tool communication

2. **Path Generation**:
   - Uses Gemini AI to generate multiple reasoning paths
   - Each path represents a different approach to solve the problem

3. **Path Exploration**:
   - Explores each path using the tools in cot_tools.py
   - Evaluates paths based on consistency and efficiency
   - Selects the best path for detailed execution

4. **Step Execution**:
   - Decomposes the chosen path into detailed calculation steps
   - Executes each step with verification
   - Maintains consistency checks throughout the process

5. **Result Presentation**:
   - Displays the final answer with rich formatting
   - Provides detailed logging of the entire process
   - Shows verification results for each step

## Usage

To run the simulation:

```bash
python -m plan_and_reason.tree_search.sim_main
```

For development mode:

```bash
python -m plan_and_reason.tree_search.cot_tools dev
```

## Dependencies

- FastMCP for tool management
- Rich for console formatting
- Google Gemini AI for path generation
- Python 3.10+
- asyncio for async operations
- dotenv for environment management

## Features

- **Multiple Path Exploration**: Generates and evaluates different solution approaches
- **Step-by-Step Reasoning**: Visualizes the reasoning process with rich formatting
- **Mathematical Verification**: Ensures calculation accuracy at each step
- **Consistency Checking**: Analyzes step dependencies and consistency
- **Rich Console Output**: Provides clear and colorful visualization
- **Async Operation**: Efficient handling of AI and tool interactions
- **Error Handling**: Comprehensive error detection and reporting
- **Type Safety**: Full type hints for better code reliability

## Example

The system can solve problems like:
```
(23 + 7) * (15 - 8)
```

It will:
1. Generate multiple solution paths using Gemini AI
2. Evaluate each path for efficiency and consistency
3. Select the best approach based on evaluation criteria
4. Decompose the chosen path into detailed steps
5. Execute and verify each calculation step
6. Present the final answer with verification results

## Error Handling

The system includes comprehensive error handling:
- Timeout protection for AI responses
- Validation of calculation results
- Consistency checking between steps
- Clear error messages with rich formatting
- Graceful degradation on failures

## Development

For development:
1. Ensure all dependencies are installed
2. Set up your Gemini API key in .env
3. Run in development mode for tool testing
4. Use the rich console for debugging
5. Check type hints for interface compatibility 