from fastmcp import FastMCP

mcp = FastMCP("basic_server")


@mcp.tool()
async def add(a: int, b: int) -> int:
    """Add two numbers together

    Args:
        a: The first number
        b: The second number

    Returns:
        The sum of the two numbers
    """
    return a + b


@mcp.tool()
async def subtract(a: int, b: int) -> int:
    """Subtract two numbers

    Args:
        a: The first number
        b: The second number

    Returns:
        The difference of the two numbers
    """
    return a - b


@mcp.tool()
async def multiply(a: int, b: int) -> int:
    """Multiply two numbers

    Args:
        a: The first number
        b: The second number

    Returns:
        The product of the two numbers
    """
    return a * b


@mcp.tool()
async def divide(a: int, b: int) -> float:
    """Divide two numbers

    Args:
        a: The first number
        b: The second number

    Returns:
        The quotient of the two numbers
    """
    return a / b


# Static resource
@mcp.resource("config://version")
def get_version():
    return "2.0.1"


# Dynamic resource template
@mcp.resource("users://{user_id}/profile")
def get_profile(user_id: int):
    # Fetch profile for user_id...
    return {"name": f"User {user_id}", "status": "active"}


@mcp.prompt()
def summarize_request(text: str) -> str:
    """Generate a prompt asking for a summary."""
    return f"Please summarize the following text:\n\n{text}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
