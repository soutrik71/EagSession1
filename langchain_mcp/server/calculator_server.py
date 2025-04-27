import sys
import os

# Add the parent directory to the sys.path to find the tools module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.basic_tool import (
    add_numbers,
    subtract_numbers,
    multiply_numbers,
    divide_numbers,
    square_number,
    cube_number,
    is_even,
    is_odd,
    is_prime,
)

from mcp.server.fastmcp import FastMCP
from loguru import logger

mcp = FastMCP("calculator_server")


@mcp.tool()
def add_numbers_tool(a: int, b: int) -> int:
    """
    The objective is to add two numbers.

    Args:
        a: The first number.
        b: The second number.

    Returns:
        The sum of the two numbers.
    """
    return add_numbers(a, b)


@mcp.tool()
def subtract_numbers_tool(a: int, b: int) -> int:
    """
    The objective is to subtract two numbers.

    Args:
        a: The first number.
        b: The second number.

    Returns:
        The difference of the two numbers.
    """
    return subtract_numbers(a, b)


@mcp.tool()
def multiply_numbers_tool(a: int, b: int) -> int:
    """
    The objective is to multiply two numbers.

    Args:
        a: The first number.
        b: The second number.

    Returns:
        The product of the two numbers.
    """
    return multiply_numbers(a, b)


@mcp.tool()
def divide_numbers_tool(a: int, b: int) -> float:
    """
    The objective is to divide two numbers.

    Args:
        a: The first number.
        b: The second number.

    Returns:
        The quotient of the two numbers.
    """
    return divide_numbers(a, b)


@mcp.tool()
def square_number_tool(a: int) -> int:
    """
    The objective is to square a number.

    Args:
        a: The number to square.

    Returns:
        The square of the number.
    """
    return square_number(a)


@mcp.tool()
def cube_number_tool(a: int) -> int:
    """
    The objective is to cube a number.

    Args:
        a: The number to cube.

    Returns:
        The cube of the number.
    """
    return cube_number(a)


@mcp.tool()
def is_even_tool(a: int) -> bool:
    """
    The objective is to check if a number is even.

    Args:
        a: The number to check.

    Returns:
        True if the number is even, False otherwise.
    """
    return is_even(a)


@mcp.tool()
def is_odd_tool(a: int) -> bool:
    """
    The objective is to check if a number is odd.

    Args:
        a: The number to check.

    Returns:
        True if the number is odd, False otherwise.
    """
    return is_odd(a)


@mcp.tool()
def is_prime_tool(a: int) -> bool:
    """
    The objective is to check if a number is prime.

    Args:
        a: The number to check.

    Returns:
        True if the number is prime, False otherwise.
    """
    return is_prime(a)


if __name__ == "__main__":
    logger.info("Starting calculator server")
    mcp.run(transport="stdio")
    # PYTHONPATH=/c/workspace/EagSession1/langchain_mcp uv run server/calculator_server.py
    # uv run -m server.calculator_server
    # python -m server.calculator_server
    # PYTHONPATH=/c/workspace/EagSession1/langchain_mcp python server/calculator_server.py
