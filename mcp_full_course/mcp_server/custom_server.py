import asyncio
from dotenv import load_dotenv, find_dotenv
from linkup import LinkupClient
from mcp.server.fastmcp import FastMCP
import operator
import os
import sys
from loguru import logger

# Configure logger
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)
logger.add("server_logs.log", rotation="10 MB", level="DEBUG")  # Add file logging

logger.info("Starting custom_server.py initialization...")

# Load environment variables
logger.debug("Loading environment variables...")
load_dotenv(find_dotenv())
logger.debug("Environment variables loaded")

# Check for linkup_api_key
linkup_key = os.getenv("linkup_api_key")
if not linkup_key:
    logger.warning("linkup_api_key not found in environment variables")
else:
    logger.success("Found linkup_api_key in environment variables")

# Initialize FastMCP
logger.info("Initializing FastMCP server...")
mcp = FastMCP("linkup-server")
logger.success("FastMCP server initialized successfully")

# Initialize LinkupClient
logger.info("Initializing LinkupClient...")
try:
    client = LinkupClient(linkup_key)
    logger.success("LinkupClient initialized successfully")
except Exception as e:
    logger.error(f"Error initializing LinkupClient: {type(e).__name__}: {e}")
    # Continue execution anyway, errors will be handled in the tool functions

# Dictionary of supported operations
OPERATIONS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "**": operator.pow,
    "%": operator.mod,
}
logger.info(f"Registered {len(OPERATIONS)} mathematical operations")


@mcp.tool()
def web_search(query: str) -> str:
    """Search the web for the given query."""
    logger.info(f"Executing web_search tool with query: '{query}'")
    try:
        search_response = client.search(
            query=query,
            depth="standard",  # "standard" or "deep"
            output_type="sourcedAnswer",  # "searchResults" or "sourcedAnswer" or "structured"
            structured_output_schema=None,  # must be filled if output_type is "structured"
        )
        logger.success("web_search completed successfully")
        return search_response
    except Exception as e:
        error_msg = f"Error in web_search: {type(e).__name__}: {e}"
        logger.error(error_msg)
        return error_msg


@mcp.tool()
def calculate(expression: str) -> str:
    """
    Perform basic mathematical calculations.
    Input format: "number1 operator number2" (e.g., "5 + 3", "10 * 2")
    Supported operators: +, -, *, /, **, %
    """
    logger.info(f"Executing calculate tool with expression: '{expression}'")
    try:
        # Split the expression into parts
        parts = expression.strip().split()
        if len(parts) != 3:
            logger.warning("Invalid format in expression")
            return "Error: Please provide expression in format 'number operator number'"

        num1 = float(parts[0])
        operator_symbol = parts[1]
        num2 = float(parts[2])

        if operator_symbol not in OPERATIONS:
            logger.warning(f"Unsupported operator '{operator_symbol}'")
            return f"Error: Unsupported operator. Supported operators are: {', '.join(OPERATIONS.keys())}"

        # Handle division by zero
        if operator_symbol == "/" and num2 == 0:
            logger.warning("Division by zero attempted")
            return "Error: Division by zero"

        result = OPERATIONS[operator_symbol](num1, num2)

        # Format the result to remove trailing zeros for whole numbers
        if result.is_integer():
            result_str = str(int(result))
        else:
            result_str = str(result)

        logger.success(f"Calculation result: {result_str}")
        return result_str

    except ValueError:
        logger.error("Invalid numbers provided")
        return "Error: Invalid numbers provided"
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.error(error_msg)
        return error_msg


if __name__ == "__main__":
    logger.info("Server ready, registering MCP tools...")
    logger.info(f"Registered tools: web_search, calculate")
    logger.info("Starting MCP server with stdio transport...")

    try:
        # Add a special debug note about stdio blocking
        logger.debug(
            "About to call mcp.run() - this will block and handle stdio communication"
        )
        mcp.run(transport="stdio")
        # This won't be reached in normal execution
        logger.success("MCP server exited normally")
    except Exception as e:
        logger.critical(f"ERROR starting MCP server: {type(e).__name__}: {e}")
        sys.exit(1)
