# core/session.py

import os
import sys
from typing import Optional, Any, List, Dict
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCP:
    """
    Lightweight wrapper for one-time MCP tool calls using stdio transport.
    Each call spins up a new subprocess and terminates cleanly.
    """

    def __init__(
        self,
        server_script: str = "mcp_server_2.py",
        working_dir: Optional[str] = None,
        server_command: Optional[str] = None,
    ):
        self.server_script = server_script
        self.working_dir = working_dir or os.getcwd()
        self.server_command = server_command or sys.executable

    async def list_tools(self):
        server_params = StdioServerParameters(
            command=self.server_command, args=[self.server_script], cwd=self.working_dir
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                return tools_result.tools

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        server_params = StdioServerParameters(
            command=self.server_command, args=[self.server_script], cwd=self.working_dir
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await session.call_tool(tool_name, arguments=arguments)


class MultiMCP:
    """
    Stateless version: discovers tools from multiple MCP servers, but reconnects per tool call.
    Each call_tool() uses a fresh session based on tool-to-server mapping.
    """

    def __init__(self, server_configs: List[dict]):
        self.server_configs = server_configs
        self.tool_map: Dict[str, Dict[str, Any]] = {}  # tool_name → {config, tool}
        self.server_tools: Dict[str, List[Any]] = {}  # server_name -> list of tools

    async def initialize(self):
        print("in MultiMCP initialize")
        for config in self.server_configs:
            try:
                params = StdioServerParameters(
                    command=sys.executable,
                    args=[config["script"]],
                    cwd=config.get("cwd", os.getcwd()),
                )
                print(f"→ Scanning tools from: {config['script']} in {params.cwd}")
                async with stdio_client(params) as (read, write):
                    print("Connection established, creating session...")
                    try:
                        async with ClientSession(read, write) as session:
                            print("[agent] Session created, initializing...")
                            await session.initialize()
                            print("[agent] MCP session initialized")
                            tools = await session.list_tools()
                            print(
                                f"→ Tools received: {[tool.name for tool in tools.tools]}"
                            )
                            for tool in tools.tools:
                                self.tool_map[tool.name] = {
                                    "config": config,
                                    "tool": tool,
                                }
                                server_key = config[
                                    "id"
                                ]  # fallback to script name if no key
                                if server_key not in self.server_tools:
                                    self.server_tools[server_key] = []
                                self.server_tools[server_key].append(tool)
                    except Exception as se:
                        print(f"❌ Session error: {se}")
            except Exception as e:
                print(f"❌ Error initializing MCP server {config['script']}: {e}")

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        entry = self.tool_map.get(tool_name)
        if not entry:
            raise ValueError(f"Tool '{tool_name}' not found on any server.")

        config = entry["config"]
        params = StdioServerParameters(
            command=sys.executable,
            args=[config["script"]],
            cwd=config.get("cwd", os.getcwd()),
        )

        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await session.call_tool(tool_name, arguments)

    async def list_all_tools(self) -> List[str]:
        return list(self.tool_map.keys())

    def get_all_tools(self) -> List[Any]:
        return [entry["tool"] for entry in self.tool_map.values()]

    def get_tools_from_servers(self, selected_servers: List[str]) -> List[Any]:
        tools = []
        for server in selected_servers:
            if server in self.server_tools:
                tools.extend(self.server_tools[server])
        return tools

    async def shutdown(self):
        pass  # no persistent sessions to close
