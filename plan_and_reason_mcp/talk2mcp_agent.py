import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
from google import genai
from concurrent.futures import TimeoutError
import json
import traceback

"""
Code Flow Description:
1. Configuration and Initialization
   - Load environment variables
   - Initialize Gemini client
   - Set up global state

2. LLM Interaction
   - Generate responses with timeout handling
   - Process LLM responses
   - Handle function calls and final answers

3. Tool Management
   - Format tool descriptions
   - Create system prompts
   - Handle tool execution

4. Main Execution Flow
   - Initialize connection
   - Process iterations
   - Handle errors and cleanup
"""


# ===== Configuration and Initialization =====
def load_configuration():
    """Load environment variables and initialize Gemini client"""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    return genai.Client(api_key=api_key)


def reset_state():
    """Reset all global variables to their initial state"""
    global last_response, iteration, iteration_response
    last_response = None
    iteration = 0
    iteration_response = []


# ===== Global Variables =====
MAX_ITERATIONS = 5  # Maximum number of iterations to allow for operations
last_response = None  # Stores the most recent response from tool execution
iteration = 0  # Current iteration counter
iteration_response = []  # List to track responses across iterations


# ===== LLM Generation Functions =====
async def generate_with_timeout(client, prompt, timeout=10):
    """Generate content with a timeout to prevent hanging

    Args:
        client: Gemini client instance
        prompt: Text prompt to send to the LLM
        timeout: Maximum time in seconds to wait for a response

    Returns:
        The LLM response object if successful

    Raises:
        TimeoutError: If generation takes longer than the timeout
        Exception: For other errors during generation
    """
    print("Starting LLM generation...")
    try:
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model="gemini-2.0-flash", contents=prompt
                ),
            ),
            timeout=timeout,
        )
        print("LLM generation completed")
        return response
    except TimeoutError:
        print("LLM generation timed out!")
        raise
    except Exception as e:
        print(f"Error in LLM generation: {e}")
        raise


# ===== Tool Management Functions =====
def format_tool_description(tool, index):
    """Format a single tool's description in JSON structure

    Creates formatted descriptions in both simple function call format
    and JSON format for each available tool.

    Args:
        tool: Tool object containing name and input schema
        index: Index of the tool in the tools list

    Returns:
        Formatted string containing the tool description
    """
    try:
        name = getattr(tool, "name", f"tool_{index}")
        params = tool.inputSchema

        # Create a simple example usage in both formats
        # Format 1: Simple function call format
        params_str = []
        if "properties" in params:
            for param_name, param_info in params["properties"].items():
                param_type = param_info.get("type", "unknown")
                params_str.append(f"{param_name}: <{param_type}>")

        simple_format = f"FUNCTION_CALL: {name}|" + "|".join(params_str)

        # Format 2: JSON format
        json_format = {
            "name": name,
            "args": {
                param_name: f"<{param_info['type']}>"
                for param_name, param_info in params.get("properties", {}).items()
            },
        }

        tool_desc = (
            f"{index+1}. {name}\n"
            f"   Simple format:\n"
            f"   {simple_format}\n"
            f"   JSON format:\n"
            f"   {json.dumps(json_format, indent=3).replace('{', '{{').replace('}', '}}')}\n"
        )

        print(f"Added description for tool: {name}")
        return tool_desc
    except Exception as e:
        print(f"Error processing tool {index}: {e}")
        return f"{index+1}. Error processing tool"


def create_tools_description(tools):
    """Create a formatted description of all available tools

    Combines descriptions of all tools into a single formatted string.

    Args:
        tools: List of tool objects

    Returns:
        A formatted string containing descriptions of all tools
    """
    tools_description = []
    for i, tool in enumerate(tools):
        tool_desc = format_tool_description(tool, i)
        tools_description.append(tool_desc)

    return "\n".join(
        [
            "Available Tools:",
            "Each tool can be called in two formats:",
            "1. Simple format: FUNCTION_CALL: name|param1|param2|...",
            "2. JSON format: {'name': 'function_name', 'args': {'param1': 'value1', ...}}",
            "",
            *tools_description,
        ]
    )


def clean_json_response(response_text):
    """Clean and extract JSON from LLM response

    Uses multiple methods to clean and parse JSON from text responses:
    1. Direct character replacement
    2. Regex-based quote fixing
    3. Python ast.literal_eval for more flexible parsing

    Args:
        response_text: The raw response text from the LLM

    Returns:
        Parsed JSON object or None if parsing fails
    """
    try:
        # Remove markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1]
            if "```" in response_text:
                response_text = response_text.split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1]

        # Clean up any remaining whitespace
        response_text = response_text.strip()

        # Method 1: Try direct replacement of problematic characters
        sanitized_text = response_text

        # Replace all variants of quotes with straight quotes
        quote_replacements = {
            """: '"',  # curly double quote (right)
            """: '"',  # curly double quote (left)
            "'": "'",  # curly single quote (right)
            "'": "'",  # curly single quote (left)
            "′": "'",  # prime
            "‵": "'",  # reversed prime
            "「": '"',  # corner bracket
            "」": '"',  # corner bracket
            "『": '"',  # white corner bracket
            "』": '"',  # white corner bracket
        }
        for old, new in quote_replacements.items():
            sanitized_text = sanitized_text.replace(old, new)

        # Clean up any escaped quotes that might cause issues
        sanitized_text = sanitized_text.replace('\\"', '"')
        sanitized_text = sanitized_text.replace("\\'", "'")

        # Try to parse with direct replacement first
        try:
            return json.loads(sanitized_text)
        except json.JSONDecodeError:
            pass

        # Method 2: Use regex to handle quotes in a more robust way
        import re

        # This regex replaces any quotes (curly or straight) that appear within JSON string values
        # with standard straight double quotes for the JSON structure and escaped straight quotes for string content
        def fix_quotes(match):
            # The matched text is a JSON field with potentially problematic quotes
            field = match.group(0)
            # Replace curly quotes in the value part (after the colon)
            parts = field.split(":", 1)
            if len(parts) == 2:
                key = parts[0]
                value = parts[1].strip()

                # If the value is a string (starts with some kind of quote)
                if (
                    value.startswith('"')
                    or value.startswith('"')
                    or value.startswith("'")
                    or value.startswith("'")
                ):
                    # Extract the string content without the quotes
                    content = (
                        value[1:-1] if value[-1] in ['"', '"', "'", "'"] else value[1:]
                    )
                    # Replace any quotes in content with escaped straight quotes
                    content = (
                        content.replace('"', '\\"')
                        .replace('"', '\\"')
                        .replace('"', '\\"')
                    )
                    # Rebuild with proper JSON formatting
                    return f'{key}: "{content}"'
            return field

        # Apply the regex to fix quotes in the JSON
        pattern = r'"[^"]*":[^,\{\}\[\]]*'  # matches "field": value pairs
        cleaned_text = re.sub(pattern, fix_quotes, response_text)

        # Try parsing again with regex approach
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            pass

        # Method 3: Last resort - use a more forgiving parser
        import ast

        # Convert JSON to Python dict-like string and evaluate
        try:
            # Replace json true/false/null with Python equivalents
            python_dict_str = (
                response_text.replace("true", "True")
                .replace("false", "False")
                .replace("null", "None")
            )
            # Parse using ast.literal_eval which is safer than eval
            return ast.literal_eval(python_dict_str)
        except (SyntaxError, ValueError):
            print(f"All parsing methods failed for: {response_text}")
            return None

    except Exception as e:
        print(f"Error cleaning JSON response: {e}")
        print(f"Original response:\n{response_text}")
        return None


async def evaluate_prompt_with_llm(client, prompt_text):
    """Evaluate a prompt using the LLM based on structured reasoning criteria

    Uses the LLM to evaluate prompts against predefined criteria for
    effective reasoning and structured output.

    Args:
        client: Gemini client instance
        prompt_text: The prompt text to evaluate

    Returns:
        Dictionary containing evaluation scores and feedback
    """
    # Create the JSON schema part without f-string to avoid conflicts
    json_schema = """
{
    "explicit_reasoning": boolean,
    "structured_output": boolean,
    "tool_separation": boolean,
    "conversation_loop": boolean,
    "instructional_framing": boolean,
    "internal_self_checks": boolean,
    "reasoning_type_awareness": boolean,
    "fallbacks": boolean,
    "overall_clarity": "string explanation"
}"""

    evaluation_prompt = (
        "You are a Prompt Evaluation Assistant. Evaluate this prompt for structured reasoning.\n"
        "Respond ONLY with a JSON object containing these fields (no other text):\n"
        f"{json_schema}\n\n"
        "Prompt to evaluate:\n"
        f"{prompt_text}"
    )

    try:
        response = await generate_with_timeout(client, evaluation_prompt)
        evaluation = clean_json_response(response.text)
        if evaluation:
            return evaluation
        return {
            "explicit_reasoning": False,
            "structured_output": False,
            "tool_separation": False,
            "conversation_loop": False,
            "instructional_framing": False,
            "internal_self_checks": False,
            "reasoning_type_awareness": False,
            "fallbacks": False,
            "overall_clarity": "Poor - Error in evaluation",
        }
    except Exception as e:
        print(f"Error in LLM-based prompt evaluation: {e}")
        return {
            "explicit_reasoning": False,
            "structured_output": False,
            "tool_separation": False,
            "conversation_loop": False,
            "instructional_framing": False,
            "internal_self_checks": False,
            "reasoning_type_awareness": False,
            "fallbacks": False,
            "overall_clarity": "Poor - Error in evaluation",
        }


def create_system_prompt(tools_description):
    """Create the system prompt with available tools

    Builds a comprehensive prompt that instructs the LLM how to
    reason through problems and use the available tools.

    Args:
        tools_description: Formatted string describing available tools

    Returns:
        Complete system prompt string
    """
    # Break long line into multiple lines
    base_prompt = (
        "You are a methodical computer agent designed to solve problems through "
        "a sequence of reasoned steps.\n"
        "You have access to a set of tools to interact with the system and gather information.\n\n"
        "**Your Goal:** Accurately fulfill the user's request by breaking it down into "
        "logical steps. At each step, you will first reason about the plan, then "
        "potentially use a tool, or provide the final answer.\n\n"
        f"**Available tools:**\n{tools_description}\n\n"
        "**Operational Cycle (Follow these steps in each turn):**\n\n"
        "1.  **Reasoning Step:**\n"
        "    *   Analyze the current situation and the user's request.\n"
        "    *   Explain your thought process for the *next* action (e.g., "
        '"I need to add two numbers," "I need to check if the file exists," '
        '"The task is complete").\n'
        "    *   Mention the type of reasoning you're using (e.g., arithmetic, "
        "lookup, logic, planning). eg PLANNING : Reasoning about the plan\n"
        "    *   If planning a tool call, state its specific purpose (e.g., "
        "\"Using 'add' tool to calculate the sum\").\n\n"
        "2.  **Self-Correction/Verification Step:**\n"
        "    *   Review your reasoning and the details of your planned action "
        "(especially tool parameters). Does it logically follow? Are the parameters "
        "correct?\n"
        "    *   If you identify an issue, go back to the Reasoning Step to correct it.\n"
        "    *   Verify that all necessary prerequisites are met before proceeding.\n"
        "    *   Double-check parameter types and values against tool requirements.\n\n"
        "3.  **Action Step (Choose ONE):**\n"
        "    Based on your verified reasoning, select *one* of the following output formats:\n\n"
        "    For function calls:\n"
        "    {\n"
        '        "reasoning": "reasoning",\n'
        '        "self_correction": "self_correction",\n'
        '        "function": "function_name",\n'
        '        "parameters": {\n'
        '            "param1": "value1",\n'
        '            "param2": "value2",\n'
        '            "param3": "value3"\n'
        "        }\n"
        "    }\n\n"
        "    if No input is required, use:\n"
        "    {\n"
        '        "reasoning": "reasoning",\n'
        '        "self_correction": "self_correction",\n'
        '        "function": "function_name",\n'
        '        "parameters": ""\n'
        "    }\n\n"
        "    For final answers:\n"
        "    {\n"
        '        "reasoning": "...",\n'
        '        "self_correction": "...",\n'
        '        "answer": "answer"\n'
        "    }\n"
        "    or\n"
        "    {\n"
        '        "reasoning": "...",\n'
        '        "self_correction": "...",\n'
        '        "answer": "DONE"\n'
        "    }\n\n"
        "**Mandatory Guidelines:**\n\n"
        "*   **Structured Responses:** Strictly adhere to the OUTPUT FORMAT, OUTPUT MUST BE A JSON.\n"
        "*   **Step-by-Step Execution:** Process the request iteratively. Wait for the outcome "
        "of a function call before proceeding with the next reasoning step.\n"
        "*   **Tool Prerequisites:** Ensure any necessary applications are open before using "
        "application-specific tools (e.g., call `open_paint` before using paint tools). "
        "Address general tasks first.\n"
        "*   **Error Handling:** If a tool call fails, returns an error, or provides unexpected "
        "results, report this in your next `REASONING:` step and explain your plan to handle "
        "it (e.g., retry, use a different tool, ask for clarification).\n"
        "*   **Uncertainty:** If you are unsure how to proceed or lack necessary information, "
        "state this clearly in the `REASONING:` step and explain what is needed.\n"
        "*   **Parameter Order:** Ensure parameters in `function` are in the exact order "
        "specified by the tool description.\n"
        "*   **Self-Verification:** Always verify your reasoning and actions before proceeding.\n"
        "*   **Context Awareness:** Maintain awareness of the conversation context and previous steps.\n"
        "*   **Type Safety:** Ensure all parameters match their expected types and constraints.\n\n"
        "While using any application, make sure to open the application first before using "
        "application specific tools.\n"
        "Complete the unrelated tasks first and then move on to the application specific tasks.\n"
        "DO NOT PROVIDE INPUTS TO ANY TOOL UNLESS SPECIFIED IN THE QUERY IT SELF. KEEP THE INPUT BLANK\n"
        "DO NOT include multiple responses. Give ONE response at a time.\n"
        "Make sure to provide parameters in the correct order as specified in the function signature."
    )

    return base_prompt


# ===== Tool Execution Functions =====
def prepare_tool_arguments(tool, params):
    """Prepare arguments for tool execution based on input schema

    Transforms and validates parameters according to the tool's schema.

    Args:
        tool: Tool object with input schema
        params: List of parameter values

    Returns:
        Dictionary of prepared arguments

    Raises:
        ValueError: If not enough parameters are provided
    """
    arguments = {}
    schema_properties = tool.inputSchema.get("properties", {})

    for param_name, param_info in schema_properties.items():
        if not params:
            raise ValueError(f"Not enough parameters provided for {tool.name}")

        value = params.pop(0)
        param_type = param_info.get("type", "string")

        if param_type == "integer":
            arguments[param_name] = int(value)
        elif param_type == "number":
            arguments[param_name] = float(value)
        elif param_type == "array":
            if isinstance(value, str):
                value = value.strip("[]").split(",")
            arguments[param_name] = [int(x.strip()) for x in value]
        else:
            arguments[param_name] = str(value)

    return arguments


def get_result_content(result):
    """Extract content from tool execution result

    Normalizes different result formats to a consistent output.

    Args:
        result: Result object from tool execution

    Returns:
        String or list representation of the result content
    """
    if hasattr(result, "content"):
        if isinstance(result.content, list):
            return [
                item.text if hasattr(item, "text") else str(item)
                for item in result.content
            ]
        return str(result.content)
    return str(result)


# ===== Main Execution =====
async def process_iteration(session, tools, current_query, system_prompt):
    """Process a single iteration of the agent

    Handles the full cycle of:
    1. Sending a query to the LLM
    2. Processing the LLM's response
    3. Executing a tool call if needed
    4. Processing the result

    Args:
        session: MCP client session
        tools: List of available tools
        current_query: Current user query with context
        system_prompt: System instructions for the LLM

    Returns:
        Boolean indicating whether to continue iterations
    """
    global iteration, last_response, iteration_response

    print(f"\n--- Iteration {iteration + 1} ---")
    prompt = f"{system_prompt}\n\nQuery: {current_query}"

    try:
        response = await generate_with_timeout(client, prompt)
        response_text = response.text.strip()
        print(f"LLM Response: {response_text}")

        # Parse the JSON response
        response_json = clean_json_response(response_text)
        if not response_json:
            print("Failed to parse JSON response")
            return False

        if "function" in response_json:
            func_name = response_json["function"]

            # Support both parameter formats (object and string)
            params = response_json["parameters"]
            print(f"Raw parameters: {params}")

            try:
                # Find the tool
                tool = next((t for t in tools if t.name == func_name), None)
                if not tool:
                    raise ValueError(f"Unknown tool: {func_name}")
                print(f"Found tool: {func_name}")

                # Handle different parameter formats
                arguments = {}

                # Case 1: params is a string (empty or simple value)
                if isinstance(params, str):
                    if not params.strip():  # Empty string
                        print("Empty parameters string, using empty arguments")
                        arguments = {}
                    else:
                        # Try to parse as JSON if it looks like a JSON object/array
                        if (
                            params.strip().startswith("{")
                            and params.strip().endswith("}")
                        ) or (
                            params.strip().startswith("[")
                            and params.strip().endswith("]")
                        ):
                            try:
                                params = json.loads(params)
                                print(f"Parsed parameters string as JSON: {params}")
                            except json.JSONDecodeError:
                                print(f"Failed to parse parameters as JSON: {params}")
                                # Just use the string as a single parameter if schema requires it
                                if len(tool.inputSchema.get("properties", {})) == 1:
                                    param_name = next(
                                        iter(tool.inputSchema["properties"])
                                    )
                                    arguments[param_name] = params

                # Case 2: params is a dictionary (normal case)
                if isinstance(params, dict):
                    print(f"Parameter schema: {tool.inputSchema}")
                    for param_name, param_info in tool.inputSchema.get(
                        "properties", {}
                    ).items():
                        if param_name in params:
                            value = params[param_name]
                            param_type = param_info.get("type", "string")
                            print(
                                f"Processing parameter {param_name} with value {value} of type {param_type}"
                            )

                            # Handle string that represents a list
                            if param_type == "array" and isinstance(value, str):
                                if value.strip().startswith(
                                    "["
                                ) and value.strip().endswith("]"):
                                    # Convert string representation of list to actual list
                                    try:
                                        value = json.loads(value)
                                        print(
                                            f"Converted string list to actual list: {value}"
                                        )
                                    except json.JSONDecodeError:
                                        # If JSON parsing fails, try eval (safer than direct eval)
                                        import ast

                                        try:
                                            value = ast.literal_eval(value)
                                            print(
                                                f"Converted string list using ast.literal_eval: {value}"
                                            )
                                        except (SyntaxError, ValueError) as e:
                                            print(f"Failed to convert string list: {e}")

                            # Convert types based on schema
                            try:
                                if param_type == "integer":
                                    arguments[param_name] = int(value)
                                elif param_type == "number":
                                    arguments[param_name] = float(value)
                                elif param_type == "array":
                                    if isinstance(value, list):
                                        arguments[param_name] = value
                                    else:
                                        raise ValueError(
                                            f"Expected list for parameter {param_name}, got {type(value)}"
                                        )
                                else:
                                    arguments[param_name] = str(value)
                            except (ValueError, TypeError) as e:
                                print(f"Error converting parameter {param_name}: {e}")
                                raise

                print(f"Calling tool: {func_name} with arguments: {arguments}")
                result = await session.call_tool(func_name, arguments=arguments)
                iteration_result = get_result_content(result)

                # Format the response based on result type
                if isinstance(iteration_result, list):
                    result_str = f"[{', '.join(map(str, iteration_result))}]"
                else:
                    result_str = str(iteration_result)

                iteration_response.append(
                    f"In iteration {iteration + 1}, {func_name} returned: {result_str}"
                )
                last_response = iteration_result

                # If we just closed an application, stop further iterations
                if func_name in ["close_notepad", "close_paint"]:
                    print(f"\n=== {func_name} Operations Complete ===")
                    return False

                return True

            except Exception as e:
                print(f"Error calling tool: {e}")
                traceback.print_exc()  # Print the full traceback for debugging
                iteration_response.append(
                    f"Error in iteration {iteration + 1}: {str(e)}"
                )
                return False

        elif "answer" in response_json:
            print(
                f"Final Reasoning: {response_json.get('reasoning', 'No reasoning provided')}"
            )
            print(
                f"Final Self-Correction: {response_json.get('self_correction', 'No self-correction provided')}"
            )
            print(f"Final answer: {response_json['answer']}")
            print("\n=== Agent Execution Complete ===")
            return False

        return True

    except Exception as e:
        print(f"Failed to get LLM response: {e}")
        traceback.print_exc()  # Print the full traceback for debugging
        return False


async def main():
    """Main execution function

    Orchestrates the entire process:
    1. Initialize client and server connection
    2. Set up the agent with tools and system prompt
    3. Process user queries through iterations
    4. Handle cleanup and errors
    """
    global iteration, last_response, iteration_response
    reset_state()  # Reset at the start of main
    print("Starting main execution...")
    try:
        # Initialize Gemini client
        global client
        client = load_configuration()

        # Create MCP server connection
        print("Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python", args=["example2_improved.py"]
        )

        async with stdio_client(server_params) as (read, write):
            print("Connection established, creating session...")
            async with ClientSession(read, write) as session:
                print("Session created, initializing...")
                await session.initialize()

                # Get available tools
                print("Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                print(f"Successfully retrieved {len(tools)} tools")

                # Create system prompt
                tools_description = create_tools_description(tools)
                system_prompt = create_system_prompt(tools_description)

                # Evaluate the prompt using LLM
                print("\nEvaluating system prompt...")
                evaluation = await evaluate_prompt_with_llm(client, system_prompt)
                print("\nPrompt Evaluation Results:")
                for criterion, value in evaluation.items():
                    if criterion != "overall_clarity":
                        print(f"{criterion}: {'✅' if value else '❌'}")
                print(f"Overall Clarity: {evaluation['overall_clarity']}")

                # Test queries - Split into multiple lines for readability
                queries = [
                    (
                        "Find the ASCII values of characters in INDIA, calculate the "
                        "sum of exponentials of those values, and show the result "
                        "in Notepad."
                    ),
                    # (
                    #     "Find the ASCII values of characters in INDIA and calculate "
                    #     "the sum of exponentials of those values."
                    # ),
                ]

                for query in queries:
                    print(f"\nProcessing query: {query}")
                    print("Starting iteration loop...")

                    # Reset state for each query
                    reset_state()
                    current_query = query

                    # Process iterations until we get a FINAL_ANSWER
                    while iteration < MAX_ITERATIONS:
                        if last_response is not None:
                            current_query = (
                                query + "\n\n" + " ".join(iteration_response)
                            )
                            current_query = current_query + "  What should I do next?"

                        if not await process_iteration(
                            session, tools, current_query, system_prompt
                        ):
                            break

                        iteration += 1

                    print("\n" + "=" * 50 + "\n")

    except Exception as e:
        print(f"Error in main execution: {e}")
        traceback.print_exc()
    finally:
        # Clean up any remaining resources
        reset_state()
        # Give time for pipes to close gracefully
        await asyncio.sleep(0.1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
    finally:
        # Ensure proper cleanup of asyncio resources
        if hasattr(asyncio, "_get_running_loop"):
            try:
                loop = asyncio._get_running_loop()
                if loop and loop.is_running():
                    loop.stop()
                    loop.close()
            except Exception:
                pass
