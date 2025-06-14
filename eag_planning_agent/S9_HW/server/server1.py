from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError
import math
import sys
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
mcp = FastMCP(name="Calculator")


# ================= Mathematical Operations =================


@mcp.tool()
async def add(input: AddInput, ctx: Context) -> AddOutput:
    """Add two numbers"""
    await ctx.info("CALLED: add(AddInput) -> AddOutput")
    await ctx.info(f"Adding {input.a} + {input.b}")
    result = input.a + input.b
    await ctx.info(f"Result: {result}")
    return AddOutput(result=result)


@mcp.tool()
async def subtract(input: SubtractInput, ctx: Context) -> SubtractOutput:
    """Subtract one number from another"""
    await ctx.info("CALLED: subtract(SubtractInput) -> SubtractOutput")
    await ctx.info(f"Subtracting {input.a} - {input.b}")
    result = input.a - input.b
    await ctx.info(f"Result: {result}")
    return SubtractOutput(result=result)


@mcp.tool()
async def multiply(input: MultiplyInput, ctx: Context) -> MultiplyOutput:
    """Multiply two integers"""
    await ctx.info("CALLED: multiply(MultiplyInput) -> MultiplyOutput")
    await ctx.info(f"Multiplying {input.a} × {input.b}")
    result = input.a * input.b
    await ctx.info(f"Result: {result}")
    return MultiplyOutput(result=result)


@mcp.tool()
async def divide(input: DivideInput, ctx: Context) -> DivideOutput:
    """Divide one number by another"""
    await ctx.info("CALLED: divide(DivideInput) -> DivideOutput")
    await ctx.info(f"Dividing {input.a} ÷ {input.b}")

    if input.b == 0:
        await ctx.error("Division by zero attempted!")
        raise ToolError("Cannot divide by zero")

    result = input.a / input.b
    await ctx.info(f"Result: {result}")
    return DivideOutput(result=result)


@mcp.tool()
async def power(input: PowerInput, ctx: Context) -> PowerOutput:
    """Compute a raised to the power of b"""
    await ctx.info("CALLED: power(PowerInput) -> PowerOutput")
    await ctx.info(f"Computing {input.a} ^ {input.b}")
    result = input.a**input.b
    await ctx.info(f"Result: {result}")
    return PowerOutput(result=result)


@mcp.tool()
async def cbrt(input: CbrtInput, ctx: Context) -> CbrtOutput:
    """Compute the cube root of a number"""
    await ctx.info("CALLED: cbrt(CbrtInput) -> CbrtOutput")
    await ctx.info(f"Computing cube root of {input.a}")
    result = input.a ** (1 / 3)
    await ctx.info(f"Result: {result}")
    return CbrtOutput(result=result)


@mcp.tool()
async def factorial(input: FactorialInput, ctx: Context) -> FactorialOutput:
    """Compute the factorial of a number"""
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
    """Compute the remainder of a divided by b"""
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
    """Compute sine of an angle in radians"""
    await ctx.info("CALLED: sin(SinInput) -> SinOutput")
    await ctx.info(f"Computing sin({input.a} radians)")
    result = math.sin(input.a)
    await ctx.info(f"Result: {result}")
    return SinOutput(result=result)


@mcp.tool()
async def cos(input: CosInput, ctx: Context) -> CosOutput:
    """Compute cosine of an angle in radians"""
    await ctx.info("CALLED: cos(CosInput) -> CosOutput")
    await ctx.info(f"Computing cos({input.a} radians)")
    result = math.cos(input.a)
    await ctx.info(f"Result: {result}")
    return CosOutput(result=result)


@mcp.tool()
async def tan(input: TanInput, ctx: Context) -> TanOutput:
    """Compute tangent of an angle in radians"""
    await ctx.info("CALLED: tan(TanInput) -> TanOutput")
    await ctx.info(f"Computing tan({input.a} radians)")
    result = math.tan(input.a)
    await ctx.info(f"Result: {result}")
    return TanOutput(result=result)


# ================= Special Operations =================


@mcp.tool()
async def mine(input: MineInput, ctx: Context) -> MineOutput:
    """Special mining tool"""
    await ctx.info("CALLED: mine(MineInput) -> MineOutput")
    await ctx.info(f"Mining operation: {input.a} - {input.b} - {input.b}")
    result = input.a - input.b - input.b
    await ctx.info(f"Result: {result}")
    return MineOutput(result=result)


# ================= Image Operations =================


@mcp.tool()
async def create_thumbnail(input: CreateThumbnailInput, ctx: Context) -> ImageOutput:
    """Create a 100x100 thumbnail from image"""
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
    """Convert characters to ASCII values"""
    await ctx.info("CALLED: strings_to_chars_to_int")
    await ctx.info(f"Converting '{input.string}' to ASCII values")
    ascii_values = [ord(char) for char in input.string]
    await ctx.info(f"ASCII values: {ascii_values}")
    return StringsToIntsOutput(result=ascii_values)


# ================= Advanced Mathematical Operations =================


@mcp.tool()
async def int_list_to_exponential_sum(input: ExpSumInput, ctx: Context) -> ExpSumOutput:
    """Sum exponentials of int list"""
    await ctx.info("CALLED: int_list_to_exponential_sum")
    await ctx.info(f"Computing exponential sum for: {input.numbers}")
    result = sum(math.exp(i) for i in input.numbers)
    await ctx.info(f"Result: {result}")
    return ExpSumOutput(result=result)


@mcp.tool()
async def fibonacci_numbers(input: FibonacciInput, ctx: Context) -> FibonacciOutput:
    """Generate first n Fibonacci numbers"""
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
    print("FastMCP 2.0 Calculator Server starting...")

    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        print("Running in development mode")
        mcp.run()  # Run without transport for dev server
    else:
        print("Running with stdio transport")
        mcp.run(transport="stdio")  # Run with stdio for direct execution

    print("\nServer shutting down...")
