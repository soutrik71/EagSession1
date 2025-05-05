import sys
from mcp.server.fastmcp import FastMCP
from models import WebsearchRequest, WebsearchResponse
from tools import get_retrieved_docs
from loguru import logger


def mcp_log(level: str, message: str) -> None:
    """Log a message to stderr to avoid interfering with JSON communication"""
    sys.stderr.write(f"{level}: {message}\n")
    sys.stderr.flush()


mcp = FastMCP("eag_agentic_arch")


@mcp.tool()
def websearch_tool(request: WebsearchRequest) -> WebsearchResponse:
    """
    Perform a web search and return the results.

    Args:
        request: The search parameters in the format of WebsearchRequest pydantic model
    Returns:
        A list of URLs and their corresponding page content in the format of WebsearchResponse pydantic model
    """
    try:
        mcp_log("INFO", f"Received query: {request.query}")
        web_url, page_content = get_retrieved_docs(request.query, request.k)
        mcp_log("INFO", f"Returning {len(web_url)} results")
        return WebsearchResponse(web_url=web_url, page_content=page_content)
    except Exception as e:
        mcp_log("ERROR", f"Failed to retrieve docs: {e}")
        return WebsearchResponse(web_url=[], page_content=[])


if __name__ == "__main__":
    logger.info("Starting MCP server...")
    mcp.run(transport="stdio")
