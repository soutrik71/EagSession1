from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

# Create MCP server instance
mcp = FastMCP("String Reverser")

@mcp.tool()
async def reverse_string(text: str) -> dict:
    """Reverse a given string"""
    return {
        "content": [
            TextContent(
                type="text",
                text=text[::-1] + "amazing"
            )
        ]
    }


if __name__ == "__main__":
    print("Starting MCP String Reverser server...")
    # Check if running with mcp dev command
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
