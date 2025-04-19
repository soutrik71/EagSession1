# basic import
from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from PIL import Image as PILImage
import math
import sys
from pywinauto.keyboard import send_keys
import time
import subprocess

"""
Available Tools:
1. Basic Math Operations:
   - add(a: int, b: int) -> int: Add two numbers
   - add_list(numbers: list) -> int: Add all numbers in a list
   - subtract(a: int, b: int) -> int: Subtract two numbers
   - multiply(a: int, b: int) -> int: Multiply two numbers
   - divide(a: int, b: int) -> float: Divide two numbers
   - power(a: int, b: int) -> int: Power of two numbers
   - remainder(a: int, b: int) -> int: Remainder of two numbers division

2. Advanced Math Operations:
   - sqrt(a: int) -> float: Square root of a number
   - cbrt(a: int) -> float: Cube root of a number
   - factorial(a: int) -> int: Factorial of a number
   - log(a: int) -> float: Log of a number
   - sin(a: int) -> float: Sin of a number
   - cos(a: int) -> float: Cos of a number
   - tan(a: int) -> float: Tan of a number

3. Special Operations:
   - mine(a: int, b: int) -> int: Special mining tool
   - fibonacci_numbers(n: int) -> list: Return first n Fibonacci Numbers
   - int_list_to_exponential_sum(numbers: list) -> float: Sum of exponentials of numbers
   - strings_to_chars_to_int(string: str) -> list[int]: Return ASCII values of characters

4. Image Operations:
   - create_thumbnail(image_path: str) -> Image: Create a thumbnail from an image

5. Notepad Operations:
   - open_notepad() -> dict: Open Notepad maximized
   - add_text_in_notepad(text: str) -> dict: Add text in Notepad
   - close_notepad() -> dict: Close Notepad
"""

# Global variables
word_app = None
notepad_app = None

# Initialize MCP server
mcp = FastMCP("Calculator")


def log_tool_call(func_name: str, params: str) -> None:
    """Helper function to log tool calls"""
    print(f"CALLED: {func_name}({params})")


# ===== Basic Math Operations =====
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    log_tool_call("add", "a: int, b: int")
    return int(a + b)


@mcp.tool()
def add_list(numbers: list) -> int:
    """Add all numbers in a list"""
    log_tool_call("add_list", "numbers: list")
    return sum(numbers)


@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    log_tool_call("subtract", "a: int, b: int")
    return int(a - b)


@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    log_tool_call("multiply", "a: int, b: int")
    return int(a * b)


@mcp.tool()
def divide(a: int, b: int) -> float:
    """Divide two numbers"""
    log_tool_call("divide", "a: int, b: int")
    return float(a / b)


@mcp.tool()
def power(a: int, b: int) -> int:
    """Power of two numbers"""
    log_tool_call("power", "a: int, b: int")
    return int(a**b)


@mcp.tool()
def remainder(a: int, b: int) -> int:
    """Remainder of two numbers division"""
    log_tool_call("remainder", "a: int, b: int")
    return int(a % b)


# ===== Advanced Math Operations =====
@mcp.tool()
def sqrt(a: int) -> float:
    """Square root of a number"""
    log_tool_call("sqrt", "a: int")
    return float(a**0.5)


@mcp.tool()
def cbrt(a: int) -> float:
    """Cube root of a number"""
    log_tool_call("cbrt", "a: int")
    return float(a ** (1 / 3))


@mcp.tool()
def factorial(a: int) -> int:
    """Factorial of a number"""
    log_tool_call("factorial", "a: int")
    return int(math.factorial(a))


@mcp.tool()
def log(a: int) -> float:
    """Log of a number"""
    log_tool_call("log", "a: int")
    return float(math.log(a))


@mcp.tool()
def sin(a: int) -> float:
    """Sin of a number"""
    log_tool_call("sin", "a: int")
    return float(math.sin(a))


@mcp.tool()
def cos(a: int) -> float:
    """Cos of a number"""
    log_tool_call("cos", "a: int")
    return float(math.cos(a))


@mcp.tool()
def tan(a: int) -> float:
    """Tan of a number"""
    log_tool_call("tan", "a: int")
    return float(math.tan(a))


# ===== Special Operations =====
@mcp.tool()
def mine(a: int, b: int) -> int:
    """Special mining tool"""
    log_tool_call("mine", "a: int, b: int")
    return int(a - b - b)


@mcp.tool()
def fibonacci_numbers(n: int) -> list:
    """Return the first n Fibonacci Numbers"""
    log_tool_call("fibonacci_numbers", "n: int")
    if n <= 0:
        return []
    fib_sequence = [0, 1]
    for _ in range(2, n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    return fib_sequence[:n]


@mcp.tool()
def int_list_to_exponential_sum(numbers: list) -> float:
    """Return sum of exponentials of numbers in a list"""
    log_tool_call("int_list_to_exponential_sum", "numbers: list")
    return sum(math.exp(i) for i in numbers)


@mcp.tool()
def strings_to_chars_to_int(string: str) -> list[int]:
    """Return the ASCII values of the characters in a word"""
    log_tool_call("strings_to_chars_to_int", "string: str")
    return [int(ord(char)) for char in string]


# ===== Image Operations =====
@mcp.tool()
def create_thumbnail(image_path: str) -> Image:
    """Create a thumbnail from an image"""
    log_tool_call("create_thumbnail", "image_path: str")
    img = PILImage.open(image_path)
    img.thumbnail((100, 100))
    return Image(data=img.tobytes(), format="png")


# ===== Notepad Operations =====
@mcp.tool()
async def open_notepad() -> dict:
    """Open Notepad"""
    try:
        # Kill any existing notepad
        subprocess.run(
            ["taskkill", "/F", "/IM", "notepad.exe"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        time.sleep(1)

        # Start notepad
        subprocess.Popen(
            ["notepad.exe"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        time.sleep(1)

        return {
            "content": [
                TextContent(
                    type="text",
                    text="Notepad opened successfully",
                )
            ]
        }
    except Exception as e:
        return {"content": [TextContent(type="text", text=str(e))]}


@mcp.tool()
async def add_text_in_notepad(text: str) -> dict:
    """Add text in Notepad"""
    try:
        # Wait a bit for Notepad to be ready
        time.sleep(1)

        # Use keyboard module for more reliable text input
        send_keys

        # Press Alt+Space, x to maximize (in case it's not)
        send_keys("%{SPACE}x")
        time.sleep(0.5)

        # Type the text
        send_keys(text, with_spaces=True, pause=0.1)
        time.sleep(0.5)

        return {
            "content": [
                TextContent(type="text", text=f"Text:'{text}' added successfully")
            ]
        }
    except Exception as e:
        return {"content": [TextContent(type="text", text=str(e))]}


@mcp.tool()
async def close_notepad() -> dict:
    """Close Notepad"""
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "notepad.exe"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        time.sleep(1)
        return {
            "content": [
                TextContent(
                    type="text",
                    text="Notepad closed successfully",
                )
            ]
        }
    except Exception as e:
        return {"content": [TextContent(type="text", text=str(e))]}


# ===== Resources =====
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    log_tool_call("get_greeting", "name: str")
    return f"Hello, {name}!"


# ===== Prompts =====
@mcp.prompt()
def review_code(code: str) -> str:
    """Review code"""
    return f"Please review this code:\n\n{code}"


@mcp.prompt()
def debug_error(error: str) -> list[base.Message]:
    """Debug error"""
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]


if __name__ == "__main__":
    print("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
