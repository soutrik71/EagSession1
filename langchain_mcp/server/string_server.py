import sys
import os

# Add the parent directory to the sys.path to find the tools module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.basic_tool import (
    reverse_string,
    count_words,
    is_palindrome,
    count_vowels,
    count_consonants,
)
from loguru import logger

from mcp.server.fastmcp import FastMCP


mcp = FastMCP("string_server")


@mcp.tool()
def reverse_string_tool(string: str) -> str:
    """
    The objective is to reverse the string.

    Args:
        string: The string to reverse.

    Returns:
        The reversed string.
    """
    return reverse_string(string)


@mcp.tool()
def count_words_tool(string: str) -> int:
    """
    The objective is to count the number of words in the string.

    Args:
        string: The string to count the words in.

    Returns:
        The number of words in the string.
    """
    return count_words(string)


@mcp.tool()
def is_palindrome_tool(string: str) -> bool:
    """
    The objective is to check if the string is a palindrome.

    Args:
        string: The string to check if it is a palindrome.

    Returns:
        True if the string is a palindrome, False otherwise.
    """
    return is_palindrome(string)


@mcp.tool()
def count_vowels_tool(string: str) -> int:
    """
    The objective is to count the number of vowels in the string.

    Args:
        string: The string to count the vowels in.

    Returns:
        The number of vowels in the string.
    """
    return count_vowels(string)


@mcp.tool()
def count_consonants_tool(string: str) -> int:
    """
    The objective is to count the number of consonants in the string.

    Args:
        string: The string to count the consonants in.

    Returns:
        The number of consonants in the string.
    """
    return count_consonants(string)


if __name__ == "__main__":
    logger.info("Starting string server")
    mcp.run(transport="stdio")
    # PYTHONPATH=/c/workspace/EagSession1/langchain_mcp uv run server/string_server.py
    # uv run -m server.string_server
    # python -m server.string_server
    # PYTHONPATH=/c/workspace/EagSession1/langchain_mcp python server/string_server.py
