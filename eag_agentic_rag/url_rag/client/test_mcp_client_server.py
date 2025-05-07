import os
import sys
import json
import asyncio
from typing import Optional
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

load_dotenv()  # Load environment variables

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack


class MCPTestClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.tools = []

    async def connect_to_server(self, server_script_path: str):
        """Start an MCP server (subprocess) and connect."""
        print(f"Starting server from: {server_script_path}")

        if server_script_path.endswith(".py"):
            command = "python"
        else:
            raise ValueError("Server script must be .py")

        # Start the server process and connect to it via stdio
        server_params = StdioServerParameters(
            command=command, args=[server_script_path], env=None
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
        print(f"Connected to server. Tools: {[t.name for t in tool_list.tools]}")
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

    async def test_web_vector_search(self, query: str, k: int = 1):
        """Test the web_vector_search tool"""
        if not self.session:
            raise RuntimeError("No MCP session found. Did you call connect_to_server?")

        print(f"\nTesting web_vector_search with query: '{query}' and k={k}")

        # Format args for basic_server (direct parameters instead of nested request object)
        tool_args = {"query": query, "k": k}

        try:
            result = await self.session.call_tool("web_vector_search", tool_args)
            print("\nTool Response:")
            print(f"Response type: {type(result.content)}")

            # Handle TextContent error responses
            if isinstance(result.content, list) and len(result.content) > 0:
                # Check if it's a list of TextContent objects (error messages)
                item = result.content[0]
                if (
                    hasattr(item, "type")
                    and item.type == "text"
                    and hasattr(item, "text")
                ):
                    error_message = item.text
                    if "Error executing tool" in error_message:
                        print(f"Server Error: {error_message}")
                        print("\nThis appears to be a server-side error. Please check:")
                        print("1. The vector database is properly initialized")
                        print("2. File paths in the server are correct")
                        print(
                            "3. Server has proper permissions to access required files"
                        )
                        return None

            # For basic server, result is returned as a string
            if isinstance(result.content, str):
                print("Result content:")
                print(result.content)

                # Try to parse the results from the string format
                if "web_url: " in result.content and "page_content: " in result.content:
                    # Extract URLs and content from the string
                    try:
                        # Parse the returned string into a more structured format
                        # The format is "web_url: [...], page_content: [...]"
                        result_str = result.content
                        # Find the separation between web_url and page_content
                        parts_split = result_str.split(", page_content: ")
                        if len(parts_split) == 2:
                            web_url_part = parts_split[0].replace("web_url: ", "")
                            page_content_part = parts_split[1]

                            # Try to evaluate as Python literals
                            web_urls = eval(web_url_part)
                            page_contents = eval(page_content_part)

                            if isinstance(web_urls, list) and isinstance(
                                page_contents, list
                            ):
                                print(f"\nFound {len(web_urls)} results:")
                                for i, (url, content) in enumerate(
                                    zip(web_urls, page_contents)
                                ):
                                    print(f"\nResult {i+1}:")
                                    print(f"URL: {url}")
                                    print(f"Content Preview: {content[:200]}...")
                    except Exception as e:
                        print(f"Could not parse result string: {e}")

                return result.content
            else:
                print(f"Unexpected response format: {result.content}")
                return result.content

        except Exception as e:
            print(f"Error calling web_vector_search: {e}")
            import traceback

            traceback.print_exc()
            return None

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()


async def main():
    """Main function to run the test client"""
    # Get the path to the server script
    server_script_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../server/basic_server.py")
    )

    if not os.path.exists(server_script_path):
        print(f"Error: Server script not found at {server_script_path}")
        sys.exit(1)

    print(f"Server script path: {server_script_path}")

    # Check for potential path issues in the server configuration
    print("\nDiagnosing server configuration:")
    print(f"Current working directory: {os.getcwd()}")

    # Check for YAML config file
    yaml_paths = [
        os.path.join(os.getcwd(), "url_rag", "utility", "config.yaml"),
        os.path.join(
            os.getcwd(), "eag_agentic_rag", "url_rag", "utility", "config.yaml"
        ),
        os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../utility/config.yaml")
        ),
    ]

    print("\nChecking for config.yaml:")
    for path in yaml_paths:
        if os.path.exists(path):
            print(f"✓ Found config.yaml at: {path}")
        else:
            print(f"✗ No config.yaml at: {path}")

    # Check for vector database indexes
    print("\nChecking for vector database index directories:")
    index_paths = [
        os.path.join(os.getcwd(), "url_rag"),
        os.path.join(os.getcwd(), "eag_agentic_rag", "url_rag"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    ]

    for base_path in index_paths:
        if os.path.exists(base_path):
            print(f"Base path exists: {base_path}")
            # List directories that might be indexes
            dirs = [
                d
                for d in os.listdir(base_path)
                if os.path.isdir(os.path.join(base_path, d))
            ]
            for d in dirs:
                # Check if it looks like a FAISS index directory
                index_dir = os.path.join(base_path, d)
                if os.path.exists(
                    os.path.join(index_dir, "index.faiss")
                ) or os.path.exists(os.path.join(index_dir, "index.pkl")):
                    print(f"  ✓ Potential FAISS index found: {index_dir}")
                else:
                    print(f"  - Directory (not a FAISS index): {index_dir}")
        else:
            print(f"Base path doesn't exist: {base_path}")

    client = MCPTestClient()
    try:
        # Connect to the server
        print("\nConnecting to MCP server...")
        await client.connect_to_server(server_script_path)

        # Inspect available tools
        print("\nInspecting available tools:")
        await client.inspect_tools()

        # Test the web_vector_search tool
        test_queries = [
            ("What is vector database", 2),
            ("How does FAISS work", 1),
            ("What is RAG architecture", 3),
        ]

        for query, k in test_queries:
            await client.test_web_vector_search(query, k)
            print("\n" + "-" * 50)

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
