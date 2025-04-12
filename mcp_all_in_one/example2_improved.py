# basic import
from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from PIL import Image as PILImage
import math
import sys
from pywinauto.application import Application
import win32gui
import win32con
import time
from win32api import GetSystemMetrics

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

5. Paint Operations:
   - open_paint() -> dict: Open Microsoft Paint maximized on secondary monitor
   - draw_rectangle(x1: int, y1: int, x2: int, y2: int) -> dict: Draw rectangle in Paint
   - add_text_in_paint(text: str) -> dict: Add text in Paint
"""

# Global variables
paint_app = None

# Initialize MCP server
mcp = FastMCP("Calculator")


def log_tool_call(func_name: str, params: str) -> None:
    """Helper function to log tool calls"""
    print(f"CALLED: {func_name}({params})")


# ===== Basic Math Operations =====
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    log_tool_call("add", f"a: int, b: int")
    return int(a + b)


@mcp.tool()
def add_list(numbers: list) -> int:
    """Add all numbers in a list"""
    log_tool_call("add_list", "numbers: list")
    return sum(numbers)


@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    log_tool_call("subtract", f"a: int, b: int")
    return int(a - b)


@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    log_tool_call("multiply", f"a: int, b: int")
    return int(a * b)


@mcp.tool()
def divide(a: int, b: int) -> float:
    """Divide two numbers"""
    log_tool_call("divide", f"a: int, b: int")
    return float(a / b)


@mcp.tool()
def power(a: int, b: int) -> int:
    """Power of two numbers"""
    log_tool_call("power", f"a: int, b: int")
    return int(a**b)


@mcp.tool()
def remainder(a: int, b: int) -> int:
    """Remainder of two numbers division"""
    log_tool_call("remainder", f"a: int, b: int")
    return int(a % b)


# ===== Advanced Math Operations =====
@mcp.tool()
def sqrt(a: int) -> float:
    """Square root of a number"""
    log_tool_call("sqrt", f"a: int")
    return float(a**0.5)


@mcp.tool()
def cbrt(a: int) -> float:
    """Cube root of a number"""
    log_tool_call("cbrt", f"a: int")
    return float(a ** (1 / 3))


@mcp.tool()
def factorial(a: int) -> int:
    """Factorial of a number"""
    log_tool_call("factorial", f"a: int")
    return int(math.factorial(a))


@mcp.tool()
def log(a: int) -> float:
    """Log of a number"""
    log_tool_call("log", f"a: int")
    return float(math.log(a))


@mcp.tool()
def sin(a: int) -> float:
    """Sin of a number"""
    log_tool_call("sin", f"a: int")
    return float(math.sin(a))


@mcp.tool()
def cos(a: int) -> float:
    """Cos of a number"""
    log_tool_call("cos", f"a: int")
    return float(math.cos(a))


@mcp.tool()
def tan(a: int) -> float:
    """Tan of a number"""
    log_tool_call("tan", f"a: int")
    return float(math.tan(a))


# ===== Special Operations =====
@mcp.tool()
def mine(a: int, b: int) -> int:
    """Special mining tool"""
    log_tool_call("mine", f"a: int, b: int")
    return int(a - b - b)


@mcp.tool()
def fibonacci_numbers(n: int) -> list:
    """Return the first n Fibonacci Numbers"""
    log_tool_call("fibonacci_numbers", f"n: int")
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


# ===== Paint Operations =====
def get_paint_window():
    """Helper function to get the Paint window"""
    global paint_app
    if not paint_app:
        return None
    return paint_app.window(class_name="MSPaintApp")


def ensure_paint_open():
    """Helper function to ensure Paint is open"""
    return {
        "content": [
            TextContent(
                type="text", text="Paint is not open. Please call open_paint first."
            )
        ]
    }


@mcp.tool()
async def open_paint() -> dict:
    """Open Microsoft Paint maximized on secondary monitor"""
    global paint_app
    try:
        # Start Paint with a longer timeout
        paint_app = Application().start("mspaint.exe", timeout=10)
        time.sleep(2)  # Give more time for Paint to start

        paint_window = get_paint_window()
        if not paint_window:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Failed to get Paint window handle. Please ensure Paint is installed and accessible.",
                    )
                ]
            }

        # Get primary monitor width
        try:
            primary_width = GetSystemMetrics(0)
        except Exception:
            primary_width = (
                1920  # Default to common resolution if GetSystemMetrics fails
            )

        # Move to secondary monitor with error handling
        try:
            win32gui.SetWindowPos(
                paint_window.handle,
                win32con.HWND_TOP,
                primary_width + 1,
                0,
                0,
                0,
                win32con.SWP_NOSIZE,
            )
        except Exception as e:
            print(f"Warning: Could not move window: {e}")

        # Maximize window with error handling
        try:
            win32gui.ShowWindow(paint_window.handle, win32con.SW_MAXIMIZE)
            time.sleep(1)  # Give time for maximize to complete
        except Exception as e:
            print(f"Warning: Could not maximize window: {e}")

        return {
            "content": [
                TextContent(
                    type="text",
                    text="Paint opened successfully on secondary monitor and maximized",
                )
            ]
        }
    except Exception as e:
        return {
            "content": [TextContent(type="text", text=f"Error opening Paint: {str(e)}")]
        }


@mcp.tool()
async def draw_rectangle(x1: int, y1: int, x2: int, y2: int) -> dict:
    """Draw a rectangle in Paint from (x1,y1) to (x2,y2)"""
    paint_window = get_paint_window()
    if not paint_window:
        return ensure_paint_open()

    try:
        if not paint_window.has_focus():
            paint_window.set_focus()
            time.sleep(1)  # Give more time for focus

        # Click on the Rectangle tool with retry
        for _ in range(3):  # Try up to 3 times
            try:
                paint_window.click_input(coords=(530, 82))
                time.sleep(1)
                break
            except Exception:
                time.sleep(1)
                continue

        # Get the canvas area
        canvas = paint_window.child_window(class_name="MSPaintView")
        if not canvas.exists():
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Could not find Paint canvas. Please ensure Paint is open and visible.",
                    )
                ]
            }

        # Draw rectangle with error handling
        try:
            canvas.press_mouse_input(coords=(x1 + 2560, y1))
            time.sleep(0.5)
            canvas.move_mouse_input(coords=(x2 + 2560, y2))
            time.sleep(0.5)
            canvas.release_mouse_input(coords=(x2 + 2560, y2))
            time.sleep(1)
        except Exception as e:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text=f"Error drawing rectangle: {str(e)}. Please ensure Paint is open and visible.",
                    )
                ]
            }

        return {
            "content": [
                TextContent(
                    type="text", text=f"Rectangle drawn from ({x1},{y1}) to ({x2},{y2})"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(type="text", text=f"Error drawing rectangle: {str(e)}")
            ]
        }


@mcp.tool()
async def add_text_in_paint(text: str) -> dict:
    """Add text in Paint"""
    paint_window = get_paint_window()
    if not paint_window:
        return ensure_paint_open()

    try:
        if not paint_window.has_focus():
            paint_window.set_focus()
            time.sleep(1)

        # Click on the Text tool with retry
        for _ in range(3):
            try:
                paint_window.click_input(coords=(528, 92))
                time.sleep(1)
                break
            except Exception:
                time.sleep(1)
                continue

        # Get the canvas area
        canvas = paint_window.child_window(class_name="MSPaintView")
        if not canvas.exists():
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Could not find Paint canvas. Please ensure Paint is open and visible.",
                    )
                ]
            }

        # Select text tool with retry
        for _ in range(3):
            try:
                paint_window.type_keys("t")
                time.sleep(0.5)
                paint_window.type_keys("x")
                time.sleep(0.5)
                break
            except Exception:
                time.sleep(1)
                continue

        # Click where to start typing
        try:
            canvas.click_input(coords=(810, 533))
            time.sleep(1)
        except Exception as e:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text=f"Error positioning cursor: {str(e)}. Please ensure Paint is open and visible.",
                    )
                ]
            }

        # Type the text
        try:
            paint_window.type_keys(text)
            time.sleep(1)
        except Exception as e:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text=f"Error typing text: {str(e)}. Please ensure Paint is open and visible.",
                    )
                ]
            }

        # Click to exit text mode
        try:
            canvas.click_input(coords=(1050, 800))
            time.sleep(1)
        except Exception:
            pass  # Ignore error on exit text mode

        return {
            "content": [
                TextContent(type="text", text=f"Text:'{text}' added successfully")
            ]
        }
    except Exception as e:
        return {"content": [TextContent(type="text", text=f"Error: {str(e)}")]}


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
