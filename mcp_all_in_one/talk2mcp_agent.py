import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
from google import genai
from concurrent.futures import TimeoutError

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
MAX_ITERATIONS = 5  # Increased to allow for Notepad operations
last_response = None
iteration = 0
iteration_response = []


# ===== LLM Generation Functions =====
async def generate_with_timeout(client, prompt, timeout=10):
    """Generate content with a timeout"""
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
    """Format a single tool's description"""
    try:
        params = tool.inputSchema
        desc = getattr(tool, "description", "No description available")
        name = getattr(tool, "name", f"tool_{index}")

        if "properties" in params:
            param_details = []
            for param_name, param_info in params["properties"].items():
                param_type = param_info.get("type", "unknown")
                param_details.append(f"{param_name}: {param_type}")
            params_str = ", ".join(param_details)
        else:
            params_str = "no parameters"

        return f"{index+1}. {name}({params_str}) - {desc}"
    except Exception as e:
        print(f"Error processing tool {index}: {e}")
        return f"{index+1}. Error processing tool"


def create_tools_description(tools):
    """Create a formatted description of all available tools"""
    tools_description = []
    for i, tool in enumerate(tools):
        tool_desc = format_tool_description(tool, i)
        tools_description.append(tool_desc)
        print(f"Added description for tool: {tool_desc}")
    return "\n".join(tools_description)


def create_system_prompt(tools_description):
    """Create the system prompt with available tools"""
    return f"""You are a math agent solving problems and displaying results. You have access to various tools.

Available tools:
{tools_description}

You must respond with EXACTLY ONE line in one of these formats (no additional text):
1. For function calls:
   FUNCTION_CALL: function_name|param1|param2|...
   
2. For final answers:
   FINAL_ANSWER: [number]

Important:
- When a function returns multiple values, you need to process all of them
- For calculations:
  1. First get ASCII values using strings_to_chars_to_int
  2. Then calculate sum of exponentials using int_list_to_exponential_sum
  3. Then either display in Notepad or give FINAL_ANSWER
- If the query specifically asks to show or display the result in Notepad:
  1. First call open_notepad
  2. Then use add_text_in_notepad with a formatted message like "Result: [number]"
  3. Then call close_notepad
  4. Then give FINAL_ANSWER
- Otherwise, just give the FINAL_ANSWER directly
- Do not repeat function calls with the same parameters
- For Notepad operations, you MUST follow this exact sequence:
  FUNCTION_CALL: open_notepad
  FUNCTION_CALL: add_text_in_notepad|Result: [number]
  FUNCTION_CALL: close_notepad
  FINAL_ANSWER: [number]

Examples:
For regular calculations:
- FUNCTION_CALL: strings_to_chars_to_int|INDIA
- FUNCTION_CALL: int_list_to_exponential_sum|73,78,68,73,65
- FINAL_ANSWER: [7.599822246093079e+33]

For displaying in Notepad (only when requested):
- FUNCTION_CALL: strings_to_chars_to_int|INDIA
- FUNCTION_CALL: int_list_to_exponential_sum|73,78,68,73,65
- FUNCTION_CALL: open_notepad
- FUNCTION_CALL: add_text_in_notepad|Result: 7.599822246093079e+33
- FUNCTION_CALL: close_notepad
- FINAL_ANSWER: [7.599822246093079e+33]

DO NOT include any explanations or additional text.
Your entire response should be a single line starting with either FUNCTION_CALL: or FINAL_ANSWER:"""


# ===== Tool Execution Functions =====
def prepare_tool_arguments(tool, params):
    """Prepare arguments for tool execution based on input schema"""
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
    """Extract content from tool execution result"""
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
    """Process a single iteration of the agent"""
    global iteration, last_response, iteration_response

    print(f"\n--- Iteration {iteration + 1} ---")
    prompt = f"{system_prompt}\n\nQuery: {current_query}"

    try:
        response = await generate_with_timeout(client, prompt)
        response_text = response.text.strip()
        print(f"LLM Response: {response_text}")

        # Find the FUNCTION_CALL or FINAL_ANSWER line in the response
        for line in response_text.split("\n"):
            line = line.strip()
            if line.startswith("FUNCTION_CALL:") or line.startswith("FINAL_ANSWER:"):
                response_text = line
                break

    except Exception as e:
        print(f"Failed to get LLM response: {e}")
        return False

    if response_text.startswith("FUNCTION_CALL:"):
        _, function_info = response_text.split(":", 1)
        parts = [p.strip() for p in function_info.split("|")]
        func_name, params = parts[0], parts[1:]

        try:
            tool = next((t for t in tools if t.name == func_name), None)
            if not tool:
                raise ValueError(f"Unknown tool: {func_name}")

            arguments = prepare_tool_arguments(tool, params)
            print(f"Calling tool: {func_name} with arguments: {arguments}")
            result = await session.call_tool(func_name, arguments=arguments)
            iteration_result = get_result_content(result)

            # Format the response based on result type
            if isinstance(iteration_result, list):
                result_str = f"[{', '.join(iteration_result)}]"
            else:
                result_str = str(iteration_result)

            iteration_response.append(
                f"In the {iteration + 1} iteration you called {func_name} with {arguments} parameters, "
                f"and the function returned {result_str}."
            )
            last_response = iteration_result

            # If we just closed Notepad, stop further iterations
            if func_name == "close_notepad":
                print("\n=== Notepad Operations Complete ===")
                return False

            return True

        except Exception as e:
            print(f"Error calling tool: {e}")
            iteration_response.append(f"Error in iteration {iteration + 1}: {str(e)}")
            return False

    elif response_text.startswith("FINAL_ANSWER:"):
        print("\n=== Agent Execution Complete ===")
        # Extract the final answer
        _, final_answer = response_text.split(":", 1)
        final_answer = final_answer.strip()
        print(f"Final Answer: {final_answer}")
        return False

    return True


async def main():
    """Main execution function"""
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

                # Test queries
                queries = [
                    "Find the ASCII values of characters in INDIA, calculate the "
                    "sum of exponentials of those values, and show the result in Notepad.",
                    "Find the ASCII values of characters in INDIA and calculate the "
                    "sum of exponentials of those values.",
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
        import traceback

        traceback.print_exc()
    finally:
        reset_state()  # Reset at the end of main


if __name__ == "__main__":
    asyncio.run(main())
