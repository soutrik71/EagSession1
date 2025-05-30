from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError
import math
from PIL import Image as PILImage

# Import our Pydantic models (only the ones from original mcp_server_1.py)
from models import (
    AddInput,
    AddOutput,
    SubtractInput,
    SubtractOutput,
    MultiplyInput,
    MultiplyOutput,
    DivideInput,
    DivideOutput,
    SquareInput,
    SquareOutput,
    PowerInput,
    PowerOutput,
    CbrtInput,
    CbrtOutput,
    FactorialInput,
    FactorialOutput,
    RemainderInput,
    RemainderOutput,
    SinInput,
    SinOutput,
    CosInput,
    CosOutput,
    TanInput,
    TanOutput,
    MineInput,
    MineOutput,
    CreateThumbnailInput,
    ImageOutput,
    StringsToIntsInput,
    StringsToIntsOutput,
    ExpSumInput,
    ExpSumOutput,
    FibonacciInput,
    FibonacciOutput,
)

# Initialize FastMCP server
mcp = FastMCP(name="CalculatorStreamServer")


# ================= Mathematical Operations =================


@mcp.tool()
async def add(input: AddInput, ctx: Context) -> AddOutput:
    """Add two numbers together and return the sum. Handles integers, floats, and negative numbers. Example: add(5, 3) = 8"""
    await ctx.info("CALLED: add(AddInput) -> AddOutput")
    await ctx.info(f"Adding {input.a} + {input.b}")
    result = input.a + input.b
    await ctx.info(f"Result: {result}")
    return AddOutput(result=result)


@mcp.tool()
async def subtract(input: SubtractInput, ctx: Context) -> SubtractOutput:
    """Subtract the second number from the first number. Handles integers, floats, and negative numbers. Example: subtract(10, 4) = 6"""
    await ctx.info("CALLED: subtract(SubtractInput) -> SubtractOutput")
    await ctx.info(f"Subtracting {input.a} - {input.b}")
    result = input.a - input.b
    await ctx.info(f"Result: {result}")
    return SubtractOutput(result=result)


@mcp.tool()
async def multiply(input: MultiplyInput, ctx: Context) -> MultiplyOutput:
    """Multiply two numbers together. Handles integers, floats, and negative numbers. Example: multiply(6, 7) = 42"""
    await ctx.info("CALLED: multiply(MultiplyInput) -> MultiplyOutput")
    await ctx.info(f"Multiplying {input.a} × {input.b}")
    result = input.a * input.b
    await ctx.info(f"Result: {result}")
    return MultiplyOutput(result=result)


@mcp.tool()
async def divide(input: DivideInput, ctx: Context) -> DivideOutput:
    """Divide the first number by the second number. Returns decimal result. Cannot divide by zero. Example: divide(15, 3) = 5.0"""
    await ctx.info("CALLED: divide(DivideInput) -> DivideOutput")
    await ctx.info(f"Dividing {input.a} ÷ {input.b}")

    if input.b == 0:
        await ctx.error("Division by zero attempted!")
        raise ToolError("Cannot divide by zero")

    result = input.a / input.b
    await ctx.info(f"Result: {result}")
    return DivideOutput(result=result)


@mcp.tool()
async def square(input: SquareInput, ctx: Context) -> SquareOutput:
    """Compute the square of a number (a²). Multiplies the number by itself. Example: square(7) = 49, square(3.5) = 12.25"""
    await ctx.info("CALLED: square(SquareInput) -> SquareOutput")
    await ctx.info(f"Computing {input.a}²")
    result = input.a * input.a
    await ctx.info(f"Result: {result}")
    return SquareOutput(result=result)


@mcp.tool()
async def power(input: PowerInput, ctx: Context) -> PowerOutput:
    """Compute a number raised to the power of another number. Handles negative exponents. Example: power(2, 3) = 8, power(4, 0.5) = 2.0"""
    await ctx.info("CALLED: power(PowerInput) -> PowerOutput")
    await ctx.info(f"Computing {input.a} ^ {input.b}")
    result = input.a**input.b
    await ctx.info(f"Result: {result}")
    return PowerOutput(result=result)


@mcp.tool()
async def cbrt(input: CbrtInput, ctx: Context) -> CbrtOutput:
    """Compute the cube root of a number. Returns the number that when cubed gives the input. Example: cbrt(27) = 3.0, cbrt(8) = 2.0"""
    await ctx.info("CALLED: cbrt(CbrtInput) -> CbrtOutput")
    await ctx.info(f"Computing cube root of {input.a}")
    result = input.a ** (1 / 3)
    await ctx.info(f"Result: {result}")
    return CbrtOutput(result=result)


@mcp.tool()
async def factorial(input: FactorialInput, ctx: Context) -> FactorialOutput:
    """Compute the factorial of a non-negative integer. Factorial of n is n! = n × (n-1) × ... × 1. Maximum input is 170. Example: factorial(5) = 120"""
    await ctx.info("CALLED: factorial(FactorialInput) -> FactorialOutput")
    await ctx.info(f"Computing factorial of {input.a}")

    if input.a > 170:  # Factorial becomes too large
        await ctx.error("Number too large for factorial calculation")
        raise ToolError("Factorial result would be too large")

    result = math.factorial(input.a)
    await ctx.info(f"Result: {result}")
    return FactorialOutput(result=result)


@mcp.tool()
async def remainder(input: RemainderInput, ctx: Context) -> RemainderOutput:
    """Compute the remainder when dividing the first number by the second (modulo operation). Cannot use zero as divisor. Example: remainder(17, 5) = 2"""
    await ctx.info("CALLED: remainder(RemainderInput) -> RemainderOutput")
    await ctx.info(f"Computing {input.a} % {input.b}")

    if input.b == 0:
        await ctx.error("Division by zero in remainder operation!")
        raise ToolError("Cannot compute remainder with divisor zero")

    result = input.a % input.b
    await ctx.info(f"Result: {result}")
    return RemainderOutput(result=result)


# ================= Trigonometric Functions =================


@mcp.tool()
async def sin(input: SinInput, ctx: Context) -> SinOutput:
    """Compute the sine of an angle given in radians. Returns value between -1 and 1. Example: sin(π/2) ≈ 1.0, sin(0) = 0.0"""
    await ctx.info("CALLED: sin(SinInput) -> SinOutput")
    await ctx.info(f"Computing sin({input.a} radians)")
    result = math.sin(input.a)
    await ctx.info(f"Result: {result}")
    return SinOutput(result=result)


@mcp.tool()
async def cos(input: CosInput, ctx: Context) -> CosOutput:
    """Compute the cosine of an angle given in radians. Returns value between -1 and 1. Example: cos(0) = 1.0, cos(π) = -1.0"""
    await ctx.info("CALLED: cos(CosInput) -> CosOutput")
    await ctx.info(f"Computing cos({input.a} radians)")
    result = math.cos(input.a)
    await ctx.info(f"Result: {result}")
    return CosOutput(result=result)


@mcp.tool()
async def tan(input: TanInput, ctx: Context) -> TanOutput:
    """Compute the tangent of an angle given in radians. Undefined at π/2 + nπ. Example: tan(π/4) ≈ 1.0, tan(0) = 0.0"""
    await ctx.info("CALLED: tan(TanInput) -> TanOutput")
    await ctx.info(f"Computing tan({input.a} radians)")
    result = math.tan(input.a)
    await ctx.info(f"Result: {result}")
    return TanOutput(result=result)


# ================= Special Operations =================


@mcp.tool()
async def mine(input: MineInput, ctx: Context) -> MineOutput:
    """Perform a special mining operation: a - b - b. Subtracts the second number twice from the first. Example: mine(10, 3) = 4"""
    await ctx.info("CALLED: mine(MineInput) -> MineOutput")
    await ctx.info(f"Mining operation: {input.a} - {input.b} - {input.b}")
    result = input.a - input.b - input.b
    await ctx.info(f"Result: {result}")
    return MineOutput(result=result)


# ================= Image Operations =================


@mcp.tool()
async def create_thumbnail(input: CreateThumbnailInput, ctx: Context) -> ImageOutput:
    """Create a 100x100 pixel thumbnail from an image file. Requires valid image path. Supports common formats (PNG, JPG, GIF). Returns binary image data."""
    await ctx.info("CALLED: create_thumbnail(CreateThumbnailInput) -> ImageOutput")
    await ctx.info(f"Creating thumbnail for: {input.image_path}")

    try:
        img = PILImage.open(input.image_path)
        img.thumbnail((100, 100))
        await ctx.info("Thumbnail created successfully")
        return ImageOutput(data=img.tobytes(), format="png")
    except Exception as e:
        await ctx.error(f"Error creating thumbnail: {str(e)}")
        raise ToolError(f"Failed to create thumbnail: {str(e)}")


# ================= String Operations =================


@mcp.tool()
async def strings_to_chars_to_int(
    input: StringsToIntsInput, ctx: Context
) -> StringsToIntsOutput:
    """Convert each character in a string to its ASCII integer value. Returns list of integers. Example: 'ABC' → [65, 66, 67]"""
    await ctx.info("CALLED: strings_to_chars_to_int")
    await ctx.info(f"Converting '{input.string}' to ASCII values")
    ascii_values = [ord(char) for char in input.string]
    await ctx.info(f"ASCII values: {ascii_values}")
    return StringsToIntsOutput(result=ascii_values)


# ================= Advanced Mathematical Operations =================


@mcp.tool()
async def int_list_to_exponential_sum(input: ExpSumInput, ctx: Context) -> ExpSumOutput:
    """Calculate the sum of exponentials (e^x) for each number in a list. Example: [1, 2] → e^1 + e^2 ≈ 10.39. Useful for complex mathematical sequences."""
    await ctx.info("CALLED: int_list_to_exponential_sum")
    await ctx.info(f"Computing exponential sum for: {input.numbers}")
    result = sum(math.exp(i) for i in input.numbers)
    await ctx.info(f"Result: {result}")
    return ExpSumOutput(result=result)


@mcp.tool()
async def fibonacci_numbers(input: FibonacciInput, ctx: Context) -> FibonacciOutput:
    """Generate the first n Fibonacci numbers in sequence. Each number is sum of previous two. Example: n=5 → [0, 1, 1, 2, 3]"""
    await ctx.info("CALLED: fibonacci_numbers(FibonacciInput) -> FibonacciOutput")
    await ctx.info(f"Generating {input.n} Fibonacci numbers")

    n = input.n
    if n <= 0:
        return FibonacciOutput(result=[])

    fib_sequence = [0, 1]
    for _ in range(2, n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])

    result = fib_sequence[:n]
    await ctx.info(f"Generated sequence: {result}")
    return FibonacciOutput(result=result)


# ================= Server Entry Point =================

if __name__ == "__main__":
    print("FastMCP 2.0 Calculator Stream Server starting...")
    print("Available tools:")
    print(
        "- Mathematical: add, subtract, multiply, divide, square, power, cbrt, factorial, remainder"
    )
    print("- Trigonometric: sin, cos, tan")
    print("- Special: mine, create_thumbnail, strings_to_chars_to_int")
    print("- Advanced: int_list_to_exponential_sum, fibonacci_numbers")

    # Run with HTTP streaming transport
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=4201,  # Different port from tools_server_stream.py
        log_level="debug",
    )

    print("\nCalculator Stream Server shutting down...")
