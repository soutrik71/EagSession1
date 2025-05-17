import asyncio
import os
import sys
import json
from typing import Optional
from contextlib import AsyncExitStack
import ssl
import warnings
import traceback
import httpx

from mcp import ClientSession
from mcp.client.sse import sse_client
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

# --- SSL PATCHING START ---
if "SSL_CERT_FILE" in os.environ:
    print(f"Removing SSL_CERT_FILE: {os.environ.get('SSL_CERT_FILE')}")
    del os.environ["SSL_CERT_FILE"]

os.environ["PYTHONHTTPSVERIFY"] = "0"
os.environ["OPENAI_VERIFY_SSL_CERTS"] = "false"
os.environ["OPENAI_API_SKIP_VERIFY_SSL"] = "true"
os.environ["REQUESTS_CA_BUNDLE"] = ""
os.environ["NODE_TLS_REJECT_UNAUTHORIZED"] = "0"
os.environ["SSL_CERT_FILE"] = ""

ssl._create_default_https_context = ssl._create_unverified_context

warnings.filterwarnings("ignore", ".*SSL.*")
warnings.filterwarnings("ignore", ".*Certificate.*")
warnings.filterwarnings("ignore", ".*Unverified.*")
# --- SSL PATCHING END ---

# Patch httpx.AsyncClient to always use verify=False
_original_async_client = httpx.AsyncClient


class InsecureAsyncClient(_original_async_client):
    def __init__(self, *args, **kwargs):
        kwargs["verify"] = False
        super().__init__(*args, **kwargs)


httpx.AsyncClient = InsecureAsyncClient

# (Optional) Patch httpx transport for even lower-level SSL bypass
if hasattr(httpx, "_transports") and hasattr(httpx._transports, "default"):
    original_httpx_transport = httpx._transports.default.AsyncHTTPTransport

    class InsecureAsyncHTTPTransport(original_httpx_transport):
        def __init__(self, *args, **kwargs):
            kwargs["verify"] = False
            super().__init__(*args, **kwargs)

    httpx._transports.default.AsyncHTTPTransport = InsecureAsyncHTTPTransport

from openai import AsyncOpenAI


class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.openai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"

    async def connect_to_sse_server(self, server_url: str):
        """Connect to an MCP server running with SSE transport"""
        # Store the context managers so they stay alive
        self._streams_context = sse_client(url=server_url)
        streams = await self._streams_context.__aenter__()

        self._session_context = ClientSession(*streams)
        self.session: ClientSession = await self._session_context.__aenter__()

        # Initialize
        await self.session.initialize()

        # List available tools to verify connection
        print("Initialized SSE client...")
        print("Listing tools...")
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def cleanup(self):
        """Properly clean up the session and streams"""
        if hasattr(self, "_session_context") and self._session_context:
            await self._session_context.__aexit__(None, None, None)
        if hasattr(self, "_streams_context") and self._streams_context:
            await self._streams_context.__aexit__(None, None, None)

    async def _get_openai_functions(self):
        """Convert MCP tools to OpenAI function-calling format."""
        tool_list = await self.session.list_tools()
        functions = []
        for tool in tool_list.tools:
            fn_schema = {
                "name": tool.name,
                "description": tool.description or tool.name,
                "parameters": {"type": "object", "properties": {}},
                "required": [],
            }
            if tool.inputSchema and tool.inputSchema.get("type") == "object":
                fn_schema["parameters"] = tool.inputSchema
            functions.append(fn_schema)
        return functions

    async def process_query(self, query: str) -> str:
        """Process a query using GPT-4o and available tools"""
        if not self.session:
            raise RuntimeError(
                "No MCP session found. Did you call connect_to_sse_server?"
            )

        functions = await self._get_openai_functions()
        print("Calling OpenAI with functions:", functions)
        # First call to GPT: provide user's message + available functions
        response = await self.openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": query}],
            functions=functions,
            function_call="auto",
        )
        print("OpenAI response:", response)
        assistant_message = response.choices[0].message

        if (
            hasattr(assistant_message, "function_call")
            and assistant_message.function_call
        ):
            fn_name = assistant_message.function_call.name
            fn_args_json = assistant_message.function_call.arguments
            try:
                fn_args = json.loads(fn_args_json) if fn_args_json else {}
            except json.JSONDecodeError:
                return "[Error] GPT produced invalid JSON arguments."

            print(f"\n[Tool request] GPT wants to call {fn_name} with {fn_args}")
            # tool call with MCP server
            tool_result = await self.session.call_tool(fn_name, fn_args)
            print(f"[Tool response] {tool_result.content}")

            # Second call to GPT: provide the tool's result
            followup = await self.openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": query},
                    assistant_message.to_dict(),
                    {
                        "role": "function",
                        "name": fn_name,
                        "content": tool_result.content,
                    },
                ],
            )
            return followup.choices[0].message.content
        else:
            # GPT didn't request a function
            return assistant_message.content

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == "quit":
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")
                traceback.print_exc()


async def main():
    # Hardcoded server URL
    server_url = "http://localhost:8080/sse"
    client = MCPClient()
    try:
        await client.connect_to_sse_server(server_url=server_url)
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
