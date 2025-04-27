import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
import os

# First, ensure we've installed the required packages
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    import sys
    import subprocess

    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "langchain-openai"])
    from langchain_openai import ChatOpenAI

# Disable SSL verification for development (not recommended for production)
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

# Disable SSL verification for OpenAI client
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
os.environ["SSL_CERT_FILE"] = ""

load_dotenv()

# Configure API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Initialize the OpenAI model
llm = ChatOpenAI(
    model="gpt-4o-mini",
    openai_api_key=OPENAI_API_KEY,
    temperature=0,
    max_tokens=1024,
    timeout=None,
    max_retries=2,
)


def print_message_by_category(message):
    """Print message with clear category labels and formatting."""
    if message.type == "human":
        print("=" * 32 + " Human Message " + "=" * 33)
        print(f"\n{message.content}\n")
    elif message.type == "ai":
        print("=" * 34 + " AI Message " + "=" * 34)

        # Handle tool calls in AI messages
        if hasattr(message, "tool_calls") and message.tool_calls:
            print("Tool Calls:")
            for tool_call in message.tool_calls:
                # Handle tool_call as a dictionary
                if isinstance(tool_call, dict):
                    tool_id = tool_call.get("id", "unknown")
                    tool_name = tool_call.get("name", "unknown")
                    print(f"  {tool_name} ({tool_id})")
                    print(f"  Call ID: {tool_id}")

                    # Handle args if they exist
                    args = tool_call.get("args", {})
                    if args:
                        print("  Args:")
                        for key, value in args.items():
                            print(f"    {key}: {value}")
                # Handle tool_call as an object (keeping this as fallback)
                elif hasattr(tool_call, "name") and hasattr(tool_call, "id"):
                    print(f"  {tool_call.name} ({tool_call.id})")
                    print(f"  Call ID: {tool_call.id}")

                    # Handle args if they exist
                    if hasattr(tool_call, "args"):
                        print("  Args:")
                        for key, value in tool_call.args.items():
                            print(f"    {key}: {value}")
                else:
                    print(f"  Unknown tool call format: {tool_call}")

        # Print the actual AI response
        if message.content:
            print(f"\n{message.content}\n")
    elif message.type == "tool":
        print("=" * 33 + " Tool Message " + "=" * 33)
        print(f"Name: {message.name}\n")
        print(f"{message.content}\n")
    else:
        print("=" * 30 + f" {message.type.capitalize()} Message " + "=" * 30)
        print(f"\n{message.content}\n")


def is_exit_command(user_input):
    """Check if user input is an exit command."""
    exit_commands = ["q", "quit", "exit", "bye", "goodbye", "stop"]
    return user_input.lower().strip() in exit_commands


async def run_interactive_string_session():
    """Run an interactive session with the string server."""
    print("\n" + "#" * 80)
    print("#" + " " * 25 + "STRING SERVER INTERACTIVE MODE" + " " * 25 + "#")
    print("#" * 80)
    print("\nYou can ask questions about string operations.")
    print("Examples:")
    print("  - Reverse the string 'hello world'")
    print("  - How many words are in 'This is a test sentence'?")
    print("  - Is 'level' a palindrome?")
    print("  - Count the vowels in 'beautiful'")
    print("\nType 'q', 'quit', or 'exit' to go back to server selection.\n")

    server_parameters = StdioServerParameters(
        command="python",
        args=["C:/workspace/EagSession1/langchain_mcp/server/string_server.py"],
    )
    async with stdio_client(server_parameters) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(llm, tools)

            while True:
                user_input = input("\n➤ Enter your string query: ")

                if is_exit_command(user_input):
                    print("Exiting string server mode...")
                    break

                print("\n" + "=" * 80)
                try:
                    res = await agent.ainvoke({"messages": user_input})
                    for m in res["messages"]:
                        print_message_by_category(m)
                except Exception as e:
                    print(f"Error processing request: {e}")
                print("=" * 80)


async def run_interactive_calculator_session():
    """Run an interactive session with the calculator server."""
    print("\n" + "#" * 80)
    print("#" + " " * 23 + "CALCULATOR SERVER INTERACTIVE MODE" + " " * 23 + "#")
    print("#" * 80)
    print("\nYou can ask questions about mathematical operations.")
    print("Examples:")
    print("  - What is 42 + 17?")
    print("  - Is 29 a prime number?")
    print("  - What's the square of 8?")
    print("  - Multiply 12 by 5")
    print("\nType 'q', 'quit', or 'exit' to go back to server selection.\n")

    server_parameters = StdioServerParameters(
        command="python",
        args=["C:/workspace/EagSession1/langchain_mcp/server/calculator_server.py"],
    )
    async with stdio_client(server_parameters) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(llm, tools)

            while True:
                user_input = input("\n➤ Enter your math query: ")

                if is_exit_command(user_input):
                    print("Exiting calculator server mode...")
                    break

                print("\n" + "=" * 80)
                try:
                    res = await agent.ainvoke({"messages": user_input})
                    for m in res["messages"]:
                        print_message_by_category(m)
                except Exception as e:
                    print(f"Error processing request: {e}")
                print("=" * 80)


async def agent_main():
    """Main function to provide a server selection menu."""
    print("\n" + "=" * 80)
    print("=" * 23 + " Model Context Protocol Demo " + "=" * 23)
    print("=" * 80)

    while True:
        print("\nSelect a server to interact with:")
        print("1. String Server (string operations)")
        print("2. Calculator Server (math operations)")
        print("q. Quit")

        choice = input("\n➤ Enter your choice (1, 2, or q): ")

        if is_exit_command(choice):
            print("Goodbye!")
            break
        elif choice == "1":
            await run_interactive_string_session()
        elif choice == "2":
            await run_interactive_calculator_session()
        else:
            print("Invalid choice. Please select 1, 2, or q.")


if __name__ == "__main__":
    try:
        asyncio.run(agent_main())
    except KeyboardInterrupt:
        print("\nProgram interrupted. Exiting...")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
