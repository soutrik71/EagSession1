# Tree Search Reasoning System

This module implements a tree search-based reasoning system that helps explore and evaluate different paths to solve problems. It consists of two main components:

## Components

### 1. cot_tools.py
This file contains the core tools for Chain of Thought (CoT) reasoning and path evaluation:

- **show_reasoning(steps)**: Displays step-by-step reasoning process
- **calculate(expression)**: Evaluates mathematical expressions
- **verify(expression, expected)**: Verifies calculation results
- **check_consistency(steps)**: Analyzes consistency of reasoning steps
- **explore_path(steps)**: Simulates reasoning steps for a given path
- **evaluate_paths(paths)**: Evaluates and ranks different reasoning paths

The tools use rich formatting for better visualization and include error handling and validation.

### 2. sim_main.py
This is the main simulation file that orchestrates the tree search process:

- Uses Google's Gemini AI for generating reasoning paths
- Implements async communication with the tools
- Handles path exploration and evaluation
- Provides detailed logging and visualization
- Includes timeout handling for AI responses

## How It Works

1. The system starts by generating multiple reasoning paths using Gemini AI
2. Each path is explored and evaluated using the tools in cot_tools.py
3. The best path is selected based on evaluation criteria
4. The selected path is decomposed into detailed steps
5. Each step is executed and verified
6. Final results are presented with rich formatting

## Usage

To run the simulation:

```bash
python sim_main.py
```

For development mode:

```bash
python cot_tools.py dev
```

## Dependencies

- FastMCP for tool management
- Rich for console formatting
- Google Gemini AI for path generation
- Python 3.10+

## Features

- Multiple path exploration
- Step-by-step reasoning visualization
- Mathematical calculation verification
- Consistency checking
- Rich console output
- Async operation support
- Error handling and validation

## Example

The system can solve problems like:
```
(23 + 7) * (15 - 8)
```

It will:
1. Generate multiple solution paths
2. Evaluate each path
3. Select the best approach
4. Execute step-by-step calculations
5. Verify results
6. Present the final answer 