import asyncio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
import os

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
    model="gpt-4o-mini",  # You can also use gpt-3.5-turbo for faster/cheaper processing
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


async def run_interactive_session(agent):
    """Run an interactive session with the multi-server setup."""
    print("\n" + "#" * 80)
    print("#" + " " * 25 + "MULTI-SERVER INTERACTIVE MODE" + " " * 25 + "#")
    print("#" * 80)
    print("\nYou can ask questions about both string operations and calculations.")
    print("Examples:")
    print("  - Reverse the string 'hello world'")
    print("  - What is 42 + 17?")
    print("  - Is 'level' a palindrome?")
    print("  - Is 29 a prime number?")
    print("\nType 'q', 'quit', or 'exit' to exit the program.\n")

    while True:
        user_input = input("\n➤ Enter your query: ")

        if is_exit_command(user_input):
            print("Exiting interactive mode...")
            break

        print("\n" + "=" * 80)
        try:
            res = await agent.ainvoke({"messages": user_input})
            for m in res["messages"]:
                print_message_by_category(m)
        except Exception as e:
            print(f"Error processing request: {e}")
        print("=" * 80)


async def run_examples(agent):
    """Run example queries to demonstrate functionality."""
    print("\n" + "#" * 80)
    print("#" + " " * 30 + "EXAMPLE QUERIES" + " " * 30 + "#")
    print("#" * 80)

    # String examples
    print("\n🔤 STRING OPERATION EXAMPLES:")

    string_examples = [
        "Reverse the string 'hello world'",
        "How many words are in 'The quick brown fox jumps over the lazy dog'?",
        "Is 'racecar' a palindrome?",
    ]

    for i, example in enumerate(string_examples, 1):
        print(f"\nExample {i}: {example}")
        print("-" * 80)
        try:
            res = await agent.ainvoke({"messages": example})
            for m in res["messages"]:
                print_message_by_category(m)
        except Exception as e:
            print(f"Error processing request: {e}")
        print("-" * 80)

    # Calculator examples
    print("\n🔢 CALCULATOR OPERATION EXAMPLES:")

    calc_examples = [
        "What is 42 + 17?",
        "Is 29 a prime number?",
        "What is the square of 8?",
    ]

    for i, example in enumerate(calc_examples, 1):
        print(f"\nExample {i}: {example}")
        print("-" * 80)
        try:
            res = await agent.ainvoke({"messages": example})
            for m in res["messages"]:
                print_message_by_category(m)
        except Exception as e:
            print(f"Error processing request: {e}")
        print("-" * 80)


async def main():
    """Main function to run the multi-server client."""
    print("\n" + "=" * 80)
    print("=" * 23 + " Multi-Server MCP Demo " + "=" * 24)
    print("=" * 80)

    # Initialize multi-server client
    async with MultiServerMCPClient(
        {
            "string_server": {
                "command": "python",
                "args": [
                    "C:/workspace/EagSession1/langchain_mcp/server/string_server.py"
                ],
                "transport": "stdio",
            },
            "calculator_server": {
                "command": "python",
                "args": [
                    "C:/workspace/EagSession1/langchain_mcp/server/calculator_server.py"
                ],
                "transport": "stdio",
            },
        }
    ) as client:
        # Create agent with all tools from both servers
        agent = create_react_agent(llm, client.get_tools())

        # Ask the user if they want to see examples or use interactive mode
        print("\nWhat would you like to do?")
        print("1. Run example queries")
        print("2. Interactive mode")
        print("q. Quit")

        choice = input("\n➤ Enter your choice (1, 2, or q): ")

        if is_exit_command(choice):
            print("Goodbye!")
            return
        elif choice == "1":
            await run_examples(agent)
        elif choice == "2":
            await run_interactive_session(agent)
        else:
            print("Invalid choice. Exiting...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted. Exiting...")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
