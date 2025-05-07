import os
import sys
import ssl

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Disable SSL verification for the server process
if hasattr(ssl, "_create_unverified_context"):
    ssl._create_default_https_context = ssl._create_unverified_context

# Handle the SSL_CERT_FILE environment variable
if "SSL_CERT_FILE" in os.environ:
    print(f"Server removing SSL_CERT_FILE: {os.environ.get('SSL_CERT_FILE')}")
    del os.environ["SSL_CERT_FILE"]

# Import after path setup
from mcp.server.fastmcp import FastMCP
from tools import get_retrieved_docs
from loguru import logger
from pydantic import BaseModel, Field
from typing import List

mcp = FastMCP("eag_agentic_rag")


class WebsearchRequest(BaseModel):
    """Request model for web search."""

    query: str = Field(
        description="The search query to be used for the vector db search"
    )
    k: int = Field(description="The number of results to return", default=1)


class WebsearchResponse(BaseModel):
    """Response model for web search."""

    web_url: List[str] = Field(..., description="List of URLs from the search results")
    page_content: List[str] = Field(
        ..., description="List of page content from the search results"
    )


def mcp_log(level: str, message: str) -> None:
    """Log a message to stderr to avoid interfering with JSON communication"""
    sys.stderr.write(f"{level}: {message}\n")
    sys.stderr.flush()


@mcp.tool()
def web_vector_search(request: WebsearchRequest) -> WebsearchResponse:
    """
    Perform advanced web search using vector database and return the results.

    Args:
        request: The search parameters with query and k (number of results)
                in the format of WebsearchRequest pydantic model
    Returns:
        WebsearchResponse with web_url and page_content lists in the format of WebsearchResponse pydantic model
    """
    if not all([request.query, request.k]):
        raise ValueError("query and k are required")
    try:
        mcp_log("INFO", f"Received query: {request.query}")
        web_url, page_content = get_retrieved_docs(request.query, request.k)
        mcp_log("INFO", f"Returning {len(web_url)} results")
        return WebsearchResponse(web_url=web_url, page_content=page_content)
    except Exception as e:
        mcp_log("ERROR", f"Error in web_vector_search: {e}")
        return WebsearchResponse(web_url=[], page_content=[])


if __name__ == "__main__":
    logger.info(f"Starting MCP server in directory: {os.getcwd()}")
    logger.info(f"Python executable: {sys.executable}")
    mcp.run(transport="stdio")
