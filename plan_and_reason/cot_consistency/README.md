# Chain of Thought (CoT) Calculator

A Python-based tool that implements a Chain of Thought reasoning process for mathematical calculations, with built-in verification and consistency checking.

## Overview

This project implements a mathematical reasoning agent that:
1. Solves mathematical problems step by step
2. Shows detailed reasoning for each step
3. Verifies calculations at each step
4. Checks consistency between steps
5. Provides a rich visual output of the process

## Components

### 1. Main Application (`cot_main.py`)

The main application that:
- Sets up the Gemini AI client for reasoning
- Manages the conversation flow
- Handles function calls and responses
- Provides a rich console interface

Key functions:
- `generate_with_timeout`: Generates AI responses with timeout
- `get_llm_response`: Gets responses from the language model
- `handle_function_call`: Processes different types of function calls
- `main`: Orchestrates the entire calculation process

### 2. Tools Module (`cot_tools.py`)

Contains the core calculation and verification tools:

#### Core Functions:
- `show_reasoning`: Displays step-by-step reasoning
- `calculate`: Evaluates mathematical expressions
- `verify`: Verifies calculation results
- `check_consistency`: Analyzes consistency between steps

#### Analysis Functions:
- `create_analysis_table`: Creates visualization table
- `analyze_calculation`: Analyzes individual calculation steps
- `analyze_dependencies`: Checks dependencies between steps

## How It Works

1. **Initialization**:
   - Loads environment variables
   - Sets up Gemini AI client
   - Initializes console interface

2. **Problem Solving Process**:
   ```
   User Input → AI Reasoning → Function Call → Calculation → Verification → Next Step
   ```

3. **Step-by-Step Flow**:
   - AI shows reasoning for the next step
   - System calculates the result
   - Result is verified
   - Process continues until final answer

4. **Consistency Checking**:
   - Analyzes each calculation step
   - Checks dependencies between steps
   - Verifies mathematical correctness
   - Provides visual feedback

## Features

- **Rich Console Output**: Colorful, formatted output for better readability
- **Step Verification**: Each step is verified for correctness
- **Consistency Analysis**: Checks for logical consistency between steps
- **Timeout Handling**: Prevents infinite loops in calculations
- **Error Handling**: Graceful handling of calculation errors
- **Visual Analysis**: Rich tables and panels for analysis results

## Usage

1. Set up environment variables:
   ```bash
   GEMINI_API_KEY=your_api_key_here
   ```

2. Run the calculator:
   ```bash
   python cot_main.py
   ```

3. The system will:
   - Display the problem
   - Show reasoning steps
   - Calculate results
   - Verify calculations
   - Provide consistency analysis

## Example

For the problem `(23 + 7) * (15 - 8)`:

1. Shows reasoning:
   ```
   Step 1: First, solve inside parentheses: 23 + 7
   Step 2: Then solve second parentheses: 15 - 8
   Step 3: Finally, multiply the results
   ```

2. Calculates each step:
   ```
   23 + 7 = 30
   15 - 8 = 7
   30 * 7 = 210
   ```

3. Verifies each step
4. Provides consistency analysis

## Dependencies

- Python 3.7+
- `google-generativeai`: For AI reasoning
- `rich`: For console formatting
- `mcp`: For tool management
- `python-dotenv`: For environment variables

## Error Handling

The system handles various types of errors:
- Calculation errors
- Timeout errors
- Verification failures
- Consistency issues

Each error is:
- Logged with appropriate context
- Displayed in the console
- Handled gracefully without crashing

## Extensibility

The system can be extended to:
- Add new calculation types
- Implement different verification methods
- Add more analysis features
- Support different output formats

## Best Practices

1. **Type Safety**: All functions use type hints
2. **Documentation**: Comprehensive docstrings
3. **Error Handling**: Graceful error management
4. **Code Organization**: Modular design
5. **Testing**: Each component can be tested independently

## Future Improvements

1. Add support for more complex mathematical operations
2. Implement parallel calculation verification
3. Add support for different AI models
4. Enhance visualization capabilities
5. Add unit testing
6. Implement logging system 