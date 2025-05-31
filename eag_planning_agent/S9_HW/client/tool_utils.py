"""
Utility functions for MCP server and tool management.

Provides helper functions to extract tool information from MCP servers
for use in perception and other modules.
"""

import asyncio
import logging
import yaml
import os
from pathlib import Path
from typing import Dict, List, Any
from core.session import FastMCPSession

# Fix SSL cert issue for local testing
os.environ.pop("SSL_CERT_FILE", None)

# Set up logging
logger = logging.getLogger(__name__)

# Cache for tool information to avoid repeated server connections
_tools_cache = None
_cache_timestamp = 0


async def get_server_tools_info(use_cache: bool = True) -> Dict[str, Dict[str, Any]]:
    """
    Get comprehensive tool information from all live MCP servers with caching.

    Args:
        use_cache: Whether to use cached results if available

    Returns:
        Dictionary mapping server names to their tool information:
        {
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
        ConnectionError: If MCP servers are not available
        ValueError: If no tools are discovered
    """
    global _tools_cache, _cache_timestamp

    # Check cache first (cache valid for 60 seconds)
    import time

    current_time = time.time()
    if use_cache and _tools_cache and (current_time - _cache_timestamp) < 60:
        logger.debug("Using cached tool information")
        return _tools_cache

    server_info = {}

    try:
        # Load configuration - try multiple paths with absolute resolution
        import os

        current_dir = Path(os.getcwd())

        config_paths = [
            current_dir / "profiles.yaml",  # Current working directory
            Path(__file__).parent / "profiles.yaml",  # Same directory as this script
            current_dir / "../config/profiles.yaml",  # Parent config directory
            current_dir / "config/profiles.yaml",  # Local config directory
        ]

        config_path = None
        logger.debug(
            f"Looking for profiles.yaml in paths: {[str(p) for p in config_paths]}"
        )

        for path in config_paths:
            logger.debug(f"Checking path: {path} (exists: {path.exists()})")
            if path.exists():
                config_path = path
                logger.debug(f"Found config at: {config_path}")
                break

        if not config_path:
            raise FileNotFoundError(
                f"profiles.yaml not found in any of these locations: {[str(p) for p in config_paths]}"
            )

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

            # Only log discovery once per session, not every call
            logger.info(
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

            # Only log details once
            logger.info(
                f"✅ Successfully extracted info for {len(server_info)} servers"
            )
            for server, info in server_info.items():
                logger.info(f"   📡 {server}: {len(info['tools'])} tools")

            # Cache the results
            _tools_cache = server_info
            _cache_timestamp = current_time

    except FileNotFoundError as e:
        raise ConnectionError(f"MCP configuration file not found: {e}")
    except Exception as e:
        logger.error(f"❌ Failed to connect to MCP servers: {e}")
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
    server_info = await get_server_tools_info(use_cache=True)
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
    server_info = await get_server_tools_info(use_cache=True)
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
        all_server_info = await get_server_tools_info(use_cache=True)
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
    return {name: all_tools_dict[name] for name in tool_names if name in all_tools_dict}


def format_tools_summary(tools_dict: Dict[str, str]) -> str:
    """
    Format a tools dictionary into a human-readable summary for prompts.

    Args:
        tools_dict: Dictionary mapping tool names to descriptions

    Returns:
        Formatted string suitable for LLM prompts
    """
    if not tools_dict:
        return "No tools available."

    formatted_tools = []
    for tool_name, description in tools_dict.items():
        formatted_tools.append(f"• {tool_name}: {description}")

    return "\n".join(formatted_tools)


async def get_filtered_tools_summary(tool_names: List[str]) -> str:
    """
    Get a formatted summary of specific tools by name.

    Args:
        tool_names: List of tool names to include in the summary

    Returns:
        Formatted string describing the specified tools

    Raises:
        ConnectionError: If unable to fetch tools from MCP servers
    """
    try:
        # Use cached version to avoid repeated server calls
        all_tools_dict = await get_all_tools_dict()
        filtered_tools = filter_tools_dict(all_tools_dict, tool_names)
        return format_tools_summary(filtered_tools)
    except Exception as e:
        logger.error(f"Failed to get filtered tools summary: {e}")
        raise


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
