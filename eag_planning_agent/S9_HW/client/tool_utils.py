"""
Utility functions for MCP server and tool management.

Provides helper functions to extract tool information from MCP servers
for use in perception and other modules.
"""

import asyncio
import yaml
import os
from pathlib import Path
from typing import Dict, List, Any
from core.session import FastMCPSession

# Fix SSL cert issue for local testing
os.environ.pop("SSL_CERT_FILE", None)


async def get_server_tools_info() -> Dict[str, Dict[str, Any]]:
    """
    Get comprehensive tool information from all MCP servers dynamically.

    This function connects to live MCP servers and extracts their tool information.
    If servers are unavailable, it will raise an exception rather than using fallback data.

    Returns:
        Dict mapping server names to their tool information
        Format: {
            "server_name": {
                "description": "Server description",
                "tools": [
                    {
                        "name": "tool_name",
                        "description": "Tool description",
                        "schema": {...}
                    }
                ]
            }
        }

    Raises:
        ConnectionError: If unable to connect to MCP servers
        ValueError: If no tools are discovered from any server
    """
    server_info = {}

    try:
        # Load MCP configuration
        config_path = Path(__file__).parent / "profiles.yaml"
        with open(config_path, "r") as f:
            profiles_config = yaml.safe_load(f)

        mcp_config = profiles_config["mcp_client_config"]

        # Connect to MCP session and get tools
        async with FastMCPSession(mcp_config) as session:
            # Get all tools dynamically
            all_tools = session.available_tools
            server_tool_mapping = session.get_server_info()

            if not all_tools:
                raise ValueError("No tools discovered from any MCP server")

            print(
                f"🔍 Discovered {len(all_tools)} tools from {len(server_tool_mapping)} server categories"
            )

            # Build detailed server info dynamically
            for server_name, tool_names in server_tool_mapping.items():
                if not tool_names or server_name == "other":
                    continue

                # Create dynamic server description based on tools
                server_description = f"MCP server providing {len(tool_names)} tools"
                if server_name == "calculator":
                    server_description = "Mathematical operations and calculations"
                elif server_name == "web_tools":
                    server_description = "Web search and content fetching capabilities"
                elif server_name == "doc_search":
                    server_description = "Document search and retrieval"

                server_info[server_name] = {
                    "description": server_description,
                    "tools": [],
                }

                # Get detailed tool information dynamically
                for tool_name in tool_names:
                    # Find the tool object
                    tool_obj = next(
                        (tool for tool in all_tools if tool.name == tool_name), None
                    )
                    if tool_obj:
                        tool_info = {
                            "name": tool_name,
                            "description": tool_obj.description or f"Tool: {tool_name}",
                            "schema": (
                                tool_obj.inputSchema
                                if hasattr(tool_obj, "inputSchema")
                                else {}
                            ),
                        }
                        server_info[server_name]["tools"].append(tool_info)

            if not server_info:
                raise ValueError("No valid server information could be extracted")

            print(f"✅ Successfully extracted info for {len(server_info)} servers")
            for server, info in server_info.items():
                print(f"   📡 {server}: {len(info['tools'])} tools")

    except FileNotFoundError as e:
        raise ConnectionError(f"MCP configuration file not found: {e}")
    except Exception as e:
        print(f"❌ Failed to connect to MCP servers: {e}")
        raise ConnectionError(f"Unable to connect to MCP servers: {e}")

    return server_info


def get_fallback_server_info() -> Dict[str, Dict[str, Any]]:
    """
    DEPRECATED: This function is no longer used.

    The system now requires live MCP servers to be available.
    Use get_server_tools_info() instead which connects to actual servers.

    Raises:
        NotImplementedError: Always, as fallback is no longer supported
    """
    raise NotImplementedError(
        "Fallback server info is deprecated. "
        "Please ensure MCP servers are running and use get_server_tools_info() instead."
    )


def format_tools_for_prompt(server_info: Dict[str, Dict[str, Any]]) -> str:
    """
    Format server and tool information for use in prompts in server:tool:desc format.

    Args:
        server_info: Server information from get_server_tools_info()

    Returns:
        Formatted string for prompt injection in server:tool:desc format
    """
    formatted_lines = []

    for server_name, info in server_info.items():
        for tool in info["tools"]:
            # Format as server:tool:description
            formatted_lines.append(
                f"{server_name}:{tool['name']}:{tool['description']}"
            )

    return "\n".join(formatted_lines)


async def get_tools_for_prompt() -> str:
    """
    Get formatted tool information for prompt injection.

    Returns:
        Formatted string ready for use in prompts
    """
    server_info = await get_server_tools_info()
    return format_tools_for_prompt(server_info)


def get_all_server_names(server_info: Dict[str, Dict[str, Any]]) -> List[str]:
    """
    Get list of all available server names.

    Args:
        server_info: Server information dictionary

    Returns:
        List of server names
    """
    return list(server_info.keys())


def get_all_tool_names(server_info: Dict[str, Dict[str, Any]]) -> List[str]:
    """
    Get list of all available tool names across all servers.

    Args:
        server_info: Server information dictionary

    Returns:
        List of all tool names
    """
    all_tools = []
    for server_data in server_info.values():
        for tool in server_data["tools"]:
            all_tools.append(tool["name"])
    return all_tools


async def get_server_tools_tuples() -> List[tuple]:
    """
    Get server tool information as a list of tuples for compatibility.

    Returns:
        List of tuples in format (server_name, tool_name, tool_description)
    """
    server_info = await get_server_tools_info()
    tool_tuples = []

    for server_name, info in server_info.items():
        for tool in info["tools"]:
            tool_tuples.append((server_name, tool["name"], tool["description"]))

    return tool_tuples


async def get_all_tools_dict() -> Dict[str, str]:
    """
    Extract all tools and descriptions into a single dictionary across all servers.

    Returns:
        Dict mapping tool_name to description: {"tool_name": "description", ...}
    """
    try:
        all_server_info = await get_server_tools_info()
    except Exception as e:
        raise ConnectionError(f"Failed to fetch tools from MCP servers: {e}")

    tools_dict = {}
    for server_name, server_data in all_server_info.items():
        for tool in server_data["tools"]:
            tools_dict[tool["name"]] = tool["description"]

    return tools_dict


def filter_tools_dict(
    all_tools_dict: Dict[str, str], tool_names: List[str]
) -> Dict[str, str]:
    """
    Filter the tools dictionary by a list of tool names.

    Args:
        all_tools_dict: Dictionary of all tools {name: description}
        tool_names: List of tool names to include

    Returns:
        Filtered dictionary containing only specified tools
    """
    return {name: desc for name, desc in all_tools_dict.items() if name in tool_names}


def format_tools_summary(tools_dict: Dict[str, str]) -> str:
    """
    Create a formatted string summary of tools.

    Args:
        tools_dict: Dictionary of tools {name: description}

    Returns:
        Formatted string with tool names and descriptions
    """
    return "\n".join(
        f"- {tool_name}: {description if description else 'No description provided.'}"
        for tool_name, description in tools_dict.items()
    )


async def get_filtered_tools_summary(tool_names: List[str]) -> str:
    """
    Simple function to get filtered tools summary in one call.

    Steps:
    1. Extract all tools and descriptions to dict
    2. Filter dict by tool names list
    3. Format as string summary

    Args:
        tool_names: List of tool names to include

    Returns:
        Formatted string summary of specified tools
    """
    # Step 1: Get all tools dict
    all_tools = await get_all_tools_dict()

    # Step 2: Filter by tool names
    filtered_tools = filter_tools_dict(all_tools, tool_names)

    # Step 3: Format as string
    return format_tools_summary(filtered_tools)


# Test function
async def test_utils():
    """Test utility functions"""
    print("🧪 Testing MCP Utils")
    print("=" * 40)

    try:
        # Test basic server info
        server_info = await get_server_tools_info()
        print(f"✅ Found {len(server_info)} servers")

        # Test all tools dict
        all_tools = await get_all_tools_dict()
        print(f"✅ Extracted {len(all_tools)} tools total")
        print(f" the tool names are {all_tools.keys()}")

        # Test filtering with some example tools
        example_tools = [
            "calculator_add",
            "web_tools_search_web",
            "doc_search_query_documents",
        ]
        filtered_summary = await get_filtered_tools_summary(example_tools)
        print(f"\n📋 Filtered summary for {example_tools}:")
        print(filtered_summary)

        # Test formatted tools for prompt
        formatted = format_tools_for_prompt(server_info)
        print("\n🔧 First 3 lines of formatted tools:")
        print("\n".join(formatted.split("\n")[:3]))

    except Exception as e:
        print(f"❌ Error testing utils: {e}")


if __name__ == "__main__":
    asyncio.run(test_utils())
