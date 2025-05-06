#!/usr/bin/env python
"""
Alternative server implementation that directly handles tool calls without Pydantic.
This is a simplified version that may help debug the '[Errno 9] Bad file descriptor' issue.
"""

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
from loguru import logger


# Create a direct mock implementation for testing
# This avoids loading the real vector store during debugging
def mock_get_retrieved_docs(query, k=1):
    """
    Mock implementation for get_retrieved_docs to avoid vector store issues during testing.

    Args:
        query (str): The query string to search for.
        k (int): The number of documents to retrieve.

    Returns:
        web_url (list): List of web URLs of the retrieved documents.
        page_content (list): List of page content of the retrieved documents.
    """
    # Return mock data for testing
    web_url = ["https://example.com/docker"]
    page_content = [
        "Docker is a platform for developing, shipping, and running applications "
        "in containers. Containers are lightweight, portable, and self-sufficient "
        "environments that include everything needed to run an application."
    ]
    print(f"Mock retrieved {len(web_url)} documents for query: {query}")
    return web_url, page_content


# Create the MCP server
mcp = FastMCP("eag_agentic_arch")


# Define the log function
def mcp_log(level: str, message: str) -> None:
    """Log a message to stderr to avoid interfering with JSON communication"""
    sys.stderr.write(f"{level}: {message}\n")
    sys.stderr.flush()


@mcp.tool()
def web_vector_search(query=None, k=1):
    """
    Perform advanced web search using vector database and return the results.

    Args:
        query: The search query to be used for the vector db search
        k: The number of results to return (default: 1)

    Returns:
        Dictionary containing web_url and page_content lists
    """
    mcp_log("INFO", f"Received args - query: {query}, k: {k}")

    if not query:
        error_msg = "query parameter is required"
        mcp_log("ERROR", error_msg)
        return {"error": error_msg, "web_url": [], "page_content": []}

    try:
        # Use mock implementation for testing
        web_url, page_content = mock_get_retrieved_docs(query, k)
        mcp_log("INFO", f"Returning {len(web_url)} results")
        return {"web_url": web_url, "page_content": page_content}
    except Exception as e:
        error_msg = f"Error in web_vector_search: {e}"
        mcp_log("ERROR", error_msg)
        return {"error": error_msg, "web_url": [], "page_content": []}


if __name__ == "__main__":
    logger.info(f"Starting alternative MCP server in directory: {os.getcwd()}")
    logger.info(f"Python executable: {sys.executable}")
    mcp.run(transport="stdio")
