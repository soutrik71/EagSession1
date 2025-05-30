"""
FastMCP 2.0 Session Management

Provides a simplified interface for managing multiple MCP servers using HTTP transport.
Based on the FastMCP 2.0 Client architecture for streamable-http connections.
"""

import logging
from typing import Dict, List, Any
from fastmcp import Client


class FastMCPSession:
    """
    FastMCP 2.0 session manager for multiple HTTP-based MCP servers.

    Replaces the old stdio-based MultiMCP with a single HTTP client
    that can connect to multiple servers simultaneously.
    """

    def __init__(self, mcp_config: Dict[str, Any]):
        """
        Initialize with mcp_client_config from profiles.yaml

        Args:
            mcp_config: The mcp_client_config section from profiles.yaml
        """
        self.config = mcp_config
        self.client = Client(mcp_config)
        self.available_tools = []
        self.server_info = {}

        # Set up logging
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        """Async context manager entry - mimics test_server_all.py pattern"""
        try:
            # Use the client exactly like test_server_all.py does
            await self.client.__aenter__()

            self.logger.info(
                f"✅ Multi-server client connected: {self.client.is_connected()}"
            )

            # List all available tools from all servers
            self.available_tools = await self.client.list_tools()

            # Group tools by server for analysis
            self._categorize_tools()

            self.logger.info(
                f"📋 Discovered {len(self.available_tools)} tools from all servers"
            )

            return self

        except Exception as e:
            self.logger.error(f"❌ FastMCP session initialization failed: {e}")
            # Clean up if initialization fails
            try:
                await self.client.__aexit__(None, None, None)
            except Exception:
                pass
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        try:
            self.logger.info("FastMCP session shutting down...")
            await self.client.__aexit__(exc_type, exc_val, exc_tb)
        except Exception as e:
            self.logger.warning(f"Error during client shutdown: {e}")

    def _categorize_tools(self):
        """Categorize tools by server based on naming convention"""
        server_tools = {
            "calculator": [],
            "web_tools": [],
            "doc_search": [],
            "other": [],
        }

        for tool in self.available_tools:
            if tool.name.startswith("calculator_"):
                server_tools["calculator"].append(tool.name)
            elif tool.name.startswith("web_tools_"):
                server_tools["web_tools"].append(tool.name)
            elif tool.name.startswith("doc_search_"):
                server_tools["doc_search"].append(tool.name)
            else:
                server_tools["other"].append(tool.name)

        self.server_info = server_tools

        # Log server tool counts
        for server, tools in server_tools.items():
            if tools:
                self.logger.info(f"   {server}: {len(tools)} tools")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool on the appropriate server.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found
            Exception: If tool execution fails
        """
        # Check if tool exists
        tool_names = [tool.name for tool in self.available_tools]
        if tool_name not in tool_names:
            raise ValueError(
                f"Tool '{tool_name}' not found. Available tools: {tool_names}"
            )

        try:
            self.logger.debug(f"Calling tool: {tool_name} with args: {arguments}")
            # Use the client directly - it's already connected in the context
            result = await self.client.call_tool(tool_name, arguments)
            return result

        except Exception as e:
            self.logger.error(f"❌ Tool call failed for {tool_name}: {e}")
            raise

    async def list_tools(self) -> List[str]:
        """
        Get list of all available tool names.

        Returns:
            List of tool names
        """
        return [tool.name for tool in self.available_tools]

    def get_tools_by_server(self, server_name: str) -> List[str]:
        """
        Get tools available from a specific server.

        Args:
            server_name: Name of the server ('calculator', 'web_tools', 'doc_search')

        Returns:
            List of tool names from that server
        """
        return self.server_info.get(server_name, [])

    def get_server_info(self) -> Dict[str, List[str]]:
        """
        Get information about tools grouped by server.

        Returns:
            Dictionary mapping server names to their tool lists
        """
        return self.server_info.copy()

    async def health_check(self) -> Dict[str, bool]:
        """
        Check health of all configured servers.

        Returns:
            Dictionary mapping server names to their health status
        """
        health_status = {}

        try:
            # Check each server based on available tools
            for server_name in ["calculator", "web_tools", "doc_search"]:
                server_tools = self.get_tools_by_server(server_name)
                health_status[server_name] = len(server_tools) > 0

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            # Mark all servers as unhealthy
            for server_name in ["calculator", "web_tools", "doc_search"]:
                health_status[server_name] = False

        return health_status


class MultiMCP:
    """
    Compatibility wrapper to maintain API compatibility with original MultiMCP.

    This provides a bridge between the old MultiMCP interface and the new
    FastMCPSession for easier migration.
    """

    def __init__(
        self,
        server_configs: List[Dict[str, Any]] = None,
        mcp_config: Dict[str, Any] = None,
    ):
        """
        Initialize MultiMCP wrapper.

        Args:
            server_configs: Legacy server configs (ignored in new implementation)
            mcp_config: New FastMCP 2.0 config (preferred)
        """
        if mcp_config:
            self.mcp_config = mcp_config
        else:
            # Default config if none provided
            self.mcp_config = {
                "mcpServers": {
                    "calculator": {
                        "url": "http://127.0.0.1:4201/mcp/",
                        "transport": "streamable-http",
                    },
                    "web_tools": {
                        "url": "http://127.0.0.1:4202/mcp/",
                        "transport": "streamable-http",
                    },
                    "doc_search": {
                        "url": "http://127.0.0.1:4203/mcp/",
                        "transport": "streamable-http",
                    },
                }
            }
        self.session = None

    async def initialize(self):
        """Initialize the session"""
        self.session = FastMCPSession(self.mcp_config)
        await self.session.__aenter__()
        return True

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        """Call a tool (compatibility method)"""
        if not self.session:
            raise RuntimeError("Session not initialized. Call initialize() first.")
        return await self.session.call_tool(tool_name, arguments)

    async def list_all_tools(self) -> List[str]:
        """List all available tools (compatibility method)"""
        if not self.session:
            raise RuntimeError("Session not initialized. Call initialize() first.")
        return await self.session.list_tools()

    def get_all_tools(self) -> List[Any]:
        """Get all tool objects (compatibility method)"""
        if not self.session:
            raise RuntimeError("Session not initialized. Call initialize() first.")
        return self.session.available_tools

    async def shutdown(self):
        """Shutdown the session"""
        if self.session:
            await self.session.__aexit__(None, None, None)
            self.session = None
