import asyncio
import os
import sys
import json
from typing import List, Optional
from contextlib import AsyncExitStack
from dotenv import load_dotenv
from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from loguru import logger

# Configure logger
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <blue>CLIENT</blue> | <cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)
logger.add("client_logs.log", rotation="10 MB", level="DEBUG")  # Add file logging

# Load environment variables
load_dotenv()

logger.info("Starting Gemini MCP client initialization...")
logger.debug("Loading environment variables and initializing client...")
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    logger.critical("GEMINI_API_KEY not found in environment variables")
    sys.exit(1)


# Test API key with a simple request
def test_api_key():
    logger.info("Testing Gemini API key...")
    try:
        test_client = genai.Client(api_key=api_key)
        test_response = test_client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Hello, this is a test to verify API key is working. Please respond with 'OK'.",
        )
        logger.success(
            f"API key test successful. Response: {test_response.text[:50]}..."
        )
        return True
    except Exception as e:
        logger.error(f"API key test failed: {type(e).__name__}: {e}")
        return False


# Test API key before proceeding
if not test_api_key():
    logger.critical("Exiting due to invalid API key.")
    sys.exit(1)


def clean_schema(schema):
    """
    Recursively removes 'title' fields from the JSON schema.
    """
    if isinstance(schema, dict):
        schema.pop("title", None)  # Remove title if present

        # Recursively clean nested properties
        if "properties" in schema and isinstance(schema["properties"], dict):
            for key in schema["properties"]:
                schema["properties"][key] = clean_schema(schema["properties"][key])

    return schema


class MCPClient:
    def __init__(self):
        """Initialize the MCP client and configure the Gemini API."""
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.genai_client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"
        logger.info(f"Using Gemini model: {self.model}")

    async def connect_to_server(self, server_script_path: str):
        """Connect to the MCP server and list available tools."""
        logger.info(f"Connecting to server at: {server_script_path}")

        if server_script_path.endswith(".py"):
            command = "python"
        elif server_script_path.endswith(".js"):
            command = "node"
        else:
            logger.error(f"Unsupported server script extension: {server_script_path}")
            raise ValueError("Server script must be .py or .js")

        # Define server parameters
        server_params = StdioServerParameters(
            command=command, args=[server_script_path], env=None
        )
        logger.debug(f"Server params: command={command}, args=[{server_script_path}]")

        try:
            # Connect using stdio_client
            logger.debug("Entering stdio_client context...")
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            self.stdio, self.write = stdio_transport
            logger.success("Connected to server process via stdio")

            # Create and initialize session
            logger.debug("Creating ClientSession...")
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.stdio, self.write)
            )
            logger.success("ClientSession created successfully")

            logger.info("Initializing session...")
            await self.session.initialize()
            logger.success("Session initialized successfully")

            # List tools
            logger.info("Fetching available tools from session...")
            tool_list = await self.session.list_tools()
            tool_names = [tool.name for tool in tool_list.tools]
            logger.success(f"Tools fetched successfully: {tool_names}")

            self.tools = tool_list.tools
            return tool_list.tools
        except Exception as e:
            logger.error(f"Error connecting to server: {type(e).__name__}: {e}")
            import traceback

            logger.debug(f"Connection error traceback:\n{traceback.format_exc()}")
            raise

    async def process_query(self, query: str):
        """Process a user query using the Gemini API and tools."""
        if not self.session:
            logger.error("Not connected to MCP server.")
            raise ValueError("Not connected to MCP server.")

        logger.info(f"Processing query: {query}")

        # Convert MCP tools to Gemini format
        function_declarations = []
        for tool in self.tools:
            # Clean the schema
            parameters = clean_schema(tool.inputSchema)
            function_declarations.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": parameters,
                }
            )
        logger.debug(f"Created {len(function_declarations)} function declarations")

        gemini_tools = types.Tool(function_declarations=function_declarations)

        # Format user query
        user_content = types.Content(
            role="user", parts=[types.Part.from_text(text=query)]
        )

        contents = [user_content]

        # Make initial request to Gemini
        logger.info("Making initial API request to Gemini...")
        try:
            response = await self.genai_client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0,
                    tools=[gemini_tools],
                ),
            )
            logger.success("Initial API request successful")
        except Exception as e:
            logger.error(f"Error during initial API request: {type(e).__name__}: {e}")
            raise

        # Append model response to contents
        contents.append(response.candidates[0].content)

        has_function_calls = bool(response.function_calls)
        logger.info(f"Initial response received. Function calls: {has_function_calls}")

        # Tool calling loop
        turn_count = 0
        max_tool_turns = 5

        while response.function_calls and turn_count < max_tool_turns:
            turn_count += 1
            logger.info(f"Tool calling turn {turn_count}/{max_tool_turns}")
            tool_response_parts = []

            # Process all function calls
            for i, fc_part in enumerate(response.function_calls):
                tool_name = fc_part.name
                args = fc_part.args or {}
                logger.info(
                    f"[Tool request] Calling MCP tool: '{tool_name}' with {args}"
                )

                try:
                    # Call the tool
                    logger.debug(f"Sending tool call to server: {tool_name}({args})")
                    tool_result = await self.session.call_tool(tool_name, args)
                    logger.success(f"MCP tool '{tool_name}' executed successfully")

                    if tool_result.isError:
                        error_message = tool_result.content[0].text
                        logger.warning(f"Error from tool execution: {error_message}")
                        tool_response = {"error": error_message}
                    else:
                        result = tool_result.content[0].text
                        logger.debug(
                            f"Tool result: {result[:100]}..."
                            if len(result) > 100
                            else f"Tool result: {result}"
                        )
                        tool_response = {"result": result}

                except Exception as e:
                    error_message = f"Tool execution failed: {type(e).__name__}: {e}"
                    logger.error(error_message)
                    tool_response = {"error": error_message}

                # Create function response part
                logger.debug(f"Creating function response for {tool_name}")
                tool_response_parts.append(
                    types.Part.from_function_response(
                        name=tool_name, response=tool_response
                    )
                )

            # Add tool responses to contents
            contents.append(types.Content(role="user", parts=tool_response_parts))
            logger.debug(
                f"Added {len(tool_response_parts)} tool response parts to history"
            )

            # Make subsequent API call
            logger.info("Making subsequent API call with tool responses...")
            try:
                response = await self.genai_client.aio.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        tools=[gemini_tools],
                    ),
                )
                logger.success(
                    f"Subsequent API call successful. Has function calls: {bool(response.function_calls)}"
                )
            except Exception as e:
                logger.error(
                    f"Error during subsequent API call: {type(e).__name__}: {e}"
                )
                raise

            # Add model response to contents
            contents.append(response.candidates[0].content)

        if turn_count >= max_tool_turns and response.function_calls:
            logger.warning(f"Maximum tool turns ({max_tool_turns}) reached")

        logger.info("Tool calling loop finished. Returning final response")
        return response

    async def chat_loop(self):
        """Run an interactive chat session with the user."""
        logger.info("Starting interactive chat loop")
        print("\nMCP Client Started! Type 'quit' or 'exit' to exit.")

        while True:
            query = input("\nQuery: ").strip()
            if query.lower() in ("quit", "exit"):
                logger.info("Exit command received. Ending chat loop")
                break

            # Process query
            logger.info(f"User query: {query}")
            response = await self.process_query(query)
            print("\nFinal response:")
            print(response.text)
            logger.info("Response delivered to user")

    async def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up resources...")
        await self.exit_stack.aclose()
        logger.success("Resources cleaned up successfully")


async def main():
    """Main function to start the MCP client."""
    if len(sys.argv) < 2:
        logger.error("No server script path provided")
        print("Usage: python gemini_mcp_agent.py <path_to_server_script>")
        sys.exit(1)

    server_path = sys.argv[1]
    logger.info(f"Using server script: {server_path}")

    client = MCPClient()
    try:
        logger.info("Initializing client and connecting to server...")
        await client.connect_to_server(server_path)
        logger.success("Client connected to server successfully")

        logger.info("Starting chat loop...")
        await client.chat_loop()
    except Exception as e:
        logger.critical(f"Application error: {type(e).__name__}: {e}")
        import traceback

        logger.debug(f"Error traceback:\n{traceback.format_exc()}")
    finally:
        logger.info("Cleaning up resources...")
        await client.cleanup()


if __name__ == "__main__":
    logger.info("Starting application...")
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"Application failed with error: {type(e).__name__}: {e}")
        import traceback

        logger.debug(f"Error traceback:\n{traceback.format_exc()}")

# command to call the script: uv run gemini_mcp_agent.py C:/workspace/EagSession1/mcp_full_course/mcp_server/custom_server.py
