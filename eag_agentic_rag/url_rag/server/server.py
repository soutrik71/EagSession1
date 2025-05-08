import os
import sys
import ssl
import json

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
from models import (
    RetrieveDocumentsInput,
)

# Set the server name
mcp = FastMCP("WebVectorSearch")


def mcp_log(level: str, message: str) -> None:
    """Log a message to stderr to avoid interfering with JSON communication"""
    sys.stderr.write(f"{level}: {message}\n")
    sys.stderr.flush()


@mcp.tool()
def web_search_tool(input_data: RetrieveDocumentsInput) -> str:
    """Retrieve documents from the web using vector search based on the query.

    Args:
        input_data: The RetrieveDocumentsInput model containing the query and k value

    Returns:
        A JSON string containing the retrieved web URLs and page content
    """
    try:
        # Get the retrieved documents using the function from tools.py
        web_urls, page_contents = get_retrieved_docs(input_data.query, input_data.k)

        # Create response
        response = {"urls": web_urls, "contents": page_contents, "count": len(web_urls)}

        # Return the response as a JSON string
        return json.dumps(response, indent=2)
    except Exception as e:
        logger.error(f"Error retrieving documents: {e}")
        raise ValueError(f"Error retrieving documents: {e}")


if __name__ == "__main__":
    logger.info(f"Starting MCP server in directory: {os.getcwd()}")
    logger.info(f"Python executable: {sys.executable}")
    logger.info(f"Server script path: {__file__}")

    # Log the current directory structure to help debug path issues
    try:
        server_dir = os.path.dirname(os.path.abspath(__file__))
        logger.info(f"Server directory: {server_dir}")

        # Check if vector store exists
        from tools import yaml_data, index_path

        logger.info(f"Index name from config: {yaml_data['db_index_name']}")
        logger.info(f"Index path: {index_path}")
        logger.info(f"Index exists: {os.path.exists(index_path)}")
    except Exception as e:
        logger.error(f"Error checking vector store: {e}")

    # Run the server
    mcp.run(transport="stdio")
