import os
import sys
import ssl

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


mcp = FastMCP("eag_agentic_rag_basic")


def mcp_log(level: str, message: str) -> None:
    """Log a message to stderr to avoid interfering with JSON communication"""
    sys.stderr.write(f"{level}: {message}\n")
    sys.stderr.flush()


@mcp.tool()
def web_vector_search(query: str, k: int = 1) -> str:
    """
    Perform advanced web search using vector database and return the results.

    Args:
        query: The search query to be used for the vector db search
        k: The number of results to return and default is 1

    Returns:
        A string representation of the results
    """
    if not query:
        raise ValueError("query is required")

    try:
        mcp_log("INFO", f"Received query: {query}")
        k = int(k) if isinstance(k, str) else k
        web_url, page_content = get_retrieved_docs(query, k)
        mcp_log("INFO", f"Returning {len(web_url)} results")
        return f"web_url: {web_url}, page_content: {page_content}"
    except Exception as e:
        mcp_log("ERROR", f"Error in web_vector_search: {e}")
        return "Error: Failed to retrieve documents"


if __name__ == "__main__":
    logger.info(f"Starting MCP server in directory: {os.getcwd()}")
    logger.info(f"Python executable: {sys.executable}")
    mcp.run(transport="stdio")
