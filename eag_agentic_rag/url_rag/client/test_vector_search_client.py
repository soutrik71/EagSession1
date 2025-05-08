import os
import sys
import json
import asyncio
from typing import Optional
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack

print(f"Current working directory: {os.getcwd()}")


class MCPVectorSearchClient:
    """Client for testing the vector search functionality of the MCP server."""

    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.tools = []

    async def connect_to_server(self, server_script_path: str):
        """Start an MCP server (subprocess) and connect."""
        print(f"Starting calculator server from: {server_script_path}")

        if server_script_path.endswith(".py"):
            command = "python"
        else:
            raise ValueError("Server script must be .py")

        # Start the server process and connect to it via stdio
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            cwd=os.getcwd(),
        )
        # stdio_transport is a context manager that returns a tuple of (stdio, write)
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )
        # Initialize the session
        await self.session.initialize()

        # Get list of tools
        tool_list = await self.session.list_tools()
        self.tools = tool_list.tools
        print(
            f"Connected to calculator server. Available tools: {[t.name for t in tool_list.tools]}"
        )
        return tool_list.tools

    async def inspect_tools(self):
        """Inspect the tools available from the server"""
        if not self.tools:
            print("No tools available. Did you connect to the server?")
            return

        for tool in self.tools:
            print("\n" + "=" * 50)
            print(f"Tool Name: {tool.name}")
            print(f"Description: {tool.description}")
            print("\nInput Schema:")
            print(json.dumps(tool.inputSchema, indent=2))

            # Check if outputSchema exists before trying to access it
            if hasattr(tool, "outputSchema") and tool.outputSchema:
                print("\nOutput Schema:")
                print(json.dumps(tool.outputSchema, indent=2))
            else:
                print("\nOutput Schema: Not available")

    async def test_web_vector_search(self, query: str, k: int = 3):
        """Test the vector search functionality using web_search_tool"""
        if not self.session:
            raise RuntimeError("No MCP session found. Did you call connect_to_server?")

        print(f"\nTesting web_search_tool with query='{query}', k={k}")
        tool_args = {"input_data": {"query": query, "k": k}}

        try:
            result = await self.session.call_tool("web_search_tool", tool_args)
            print(f"Result: {result.content}")

            # Parse the JSON result for a cleaner display
            try:
                # This exact pattern works in the test_mcp_client_server_basic.py
                content = (
                    result.content[0].text
                    if isinstance(result.content, list)
                    else result.content
                )
                json_result = json.loads(content)

                print("\nRetrieved documents:")
                print(f"Found {json_result['count']} document(s)")

                urls = json_result["urls"]
                contents = json_result["contents"]

                for i in range(len(urls)):
                    print(f"\nDocument {i+1}:")
                    print(f"URL: {urls[i]}")
                    print(f"Content preview: {contents[i][:100]}...")
            except (json.JSONDecodeError, TypeError, IndexError, KeyError) as e:
                # If JSON parsing fails, just use the raw content
                print(f"Error parsing JSON response: {e}")

            return result.content
        except Exception as e:
            print(f"Error calling web_search_tool: {e}")
            import traceback

            traceback.print_exc()
            return None

    async def run_tests(self):
        """Run a series of vector search tests"""
        # Test basic query
        await self.test_web_vector_search("What is Docker?", 2)

        # Test query about Kubernetes
        await self.test_web_vector_search("Explain Kubernetes", 2)

        # Test query about Helm
        await self.test_web_vector_search(
            "What is Helm and how does it relate to Kubernetes?", 3
        )

        # Test technical query
        await self.test_web_vector_search("How to set up a Docker container", 1)

        # Test query with specific technical terms
        await self.test_web_vector_search("Container orchestration benefits", 2)

    async def interactive_mode(self):
        """Run an interactive vector search session"""
        print("\nInteractive Vector Search Mode")
        print("Type 'quit' to exit")

        while True:
            try:
                query = input("\nEnter search query: ").strip()

                if query.lower() == "quit":
                    break

                k = input("Number of results to return (default 3): ").strip()
                k = int(k) if k.isdigit() else 3

                await self.test_web_vector_search(query, k)

            except ValueError as e:
                print(f"Invalid input: {e}")
            except Exception as e:
                print(f"Error: {e}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()


async def main():
    """Main function to run the vector search client"""
    # Get the path to the server script
    server_script_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../server/server.py")
    )

    if not os.path.exists(server_script_path):
        print(f"Error: Server script not found at {server_script_path}")
        sys.exit(1)

    print(f"Server script path: {server_script_path}")

    client = MCPVectorSearchClient()
    try:
        # Connect to the server
        print("\nConnecting to MCP Calculator server...")
        await client.connect_to_server(server_script_path)

        # Inspect available tools
        print("\nInspecting available tools:")
        await client.inspect_tools()

        # Choose testing mode
        mode = input("\nChoose mode (1: Run predefined tests, 2: Interactive search): ")

        if mode == "1":
            # Run all tests
            await client.run_tests()
        else:
            # Run interactive mode
            await client.interactive_mode()

    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Clean up
        print("\nCleaning up...")
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
