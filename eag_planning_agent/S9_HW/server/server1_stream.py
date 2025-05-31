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
    """
    Add two numbers together and return their sum.

    **Use Cases:**
    - Basic arithmetic: adding integers, decimals, negative numbers
    - Sum calculations in financial contexts
    - Combining measurements or quantities
    - Building blocks for complex mathematical operations

    **Examples:**
    - add(15, 25) = 40 (simple addition)
    - add(-10, 5) = -5 (handling negatives)
    - add(3.14, 2.86) = 6.0 (decimal precision)
    - add(1000000, 500000) = 1500000 (large numbers)

    **Best for:** Any situation requiring addition of two numeric values.
    """
    result = input.a + input.b
    await ctx.info(f"ADD: {input.a} + {input.b} = {result}")
    return AddOutput(result=result)


@mcp.tool()
async def subtract(input: SubtractInput, ctx: Context) -> SubtractOutput:
    """
    Subtract the second number from the first number.

    **Use Cases:**
    - Calculating differences between values
    - Finding remaining amounts after deductions
    - Computing changes or deltas
    - Sequential mathematical operations

    **Examples:**
    - subtract(100, 30) = 70 (basic subtraction)
    - subtract(5, 8) = -3 (result can be negative)
    - subtract(45.5, 12.3) = 33.2 (decimal operations)
    - subtract(0, 10) = -10 (subtracting from zero)

    **Best for:** Computing differences, reductions, or remaining quantities.
    """
    result = input.a - input.b
    await ctx.info(f"SUBTRACT: {input.a} - {input.b} = {result}")
    return SubtractOutput(result=result)


@mcp.tool()
async def multiply(input: MultiplyInput, ctx: Context) -> MultiplyOutput:
    """
    Multiply two numbers together to get their product.

    **Use Cases:**
    - Scaling values by factors
    - Calculating areas, volumes
    - Percentage calculations (multiply by decimal)
    - Compound operations and sequences

    **Examples:**
    - multiply(8, 7) = 56 (basic multiplication)
    - multiply(40, 3) = 120 (following up previous calculations)
    - multiply(2.5, 4) = 10.0 (decimal factors)
    - multiply(-3, 5) = -15 (negative numbers)

    **Best for:** Scaling, repeated addition, area calculations, factor operations.
    """
    result = input.a * input.b
    await ctx.info(f"MULTIPLY: {input.a} × {input.b} = {result}")
    return MultiplyOutput(result=result)


@mcp.tool()
async def divide(input: DivideInput, ctx: Context) -> DivideOutput:
    """
    Divide the first number by the second number, returning decimal result.

    **Use Cases:**
    - Splitting quantities into equal parts
    - Calculating rates, ratios, averages
    - Finding unit values from totals
    - Percentage calculations

    **Examples:**
    - divide(64, 8) = 8.0 (exact division)
    - divide(22, 7) ≈ 3.14 (approximations like π)
    - divide(100, 3) ≈ 33.33 (repeating decimals)
    - divide(50, 4) = 12.5 (mixed results)

    **Limitations:** Cannot divide by zero (will raise error).
    **Best for:** Ratios, unit calculations, breaking down totals.
    """
    if input.b == 0:
        await ctx.error(f"DIVIDE ERROR: Cannot divide {input.a} by zero")
        raise ToolError("Cannot divide by zero")

    result = input.a / input.b
    await ctx.info(f"DIVIDE: {input.a} ÷ {input.b} = {result}")
    return DivideOutput(result=result)


@mcp.tool()
async def square(input: SquareInput, ctx: Context) -> SquareOutput:
    """
    Compute the square of a number (multiply number by itself).

    **Use Cases:**
    - Area calculations for squares and circles
    - Quadratic equations and algebra
    - Statistical variance calculations
    - Physics formulas involving squares

    **Examples:**
    - square(7) = 49 (perfect square)
    - square(3.5) = 12.25 (decimal squares)
    - square(-4) = 16 (negative numbers give positive results)
    - square(12) = 144 (larger numbers)

    **Best for:** Area calculations, quadratic operations, mathematical formulas.
    """
    result = input.a * input.a
    await ctx.info(f"SQUARE: {input.a}² = {result}")
    return SquareOutput(result=result)


@mcp.tool()
async def power(input: PowerInput, ctx: Context) -> PowerOutput:
    """
    Raise a number to the power of another number (exponentiation).

    **Use Cases:**
    - Exponential growth calculations
    - Compound interest formulas
    - Scientific notation and large numbers
    - Root calculations (using fractional exponents)

    **Examples:**
    - power(2, 3) = 8 (2³, basic exponentiation)
    - power(4, 0.5) = 2.0 (square root via ½ power)
    - power(10, 6) = 1000000 (powers of 10)
    - power(5, -2) = 0.04 (negative exponents = 1/5²)

    **Best for:** Exponential calculations, roots, scientific computations.
    """
    result = input.a**input.b
    await ctx.info(f"POWER: {input.a}^{input.b} = {result}")
    return PowerOutput(result=result)


@mcp.tool()
async def cbrt(input: CbrtInput, ctx: Context) -> CbrtOutput:
    """
    Compute the cube root of a number (∛x).

    **Use Cases:**
    - Volume calculations (finding side length from volume)
    - Solving cubic equations
    - 3D geometry problems
    - Engineering and physics applications

    **Examples:**
    - cbrt(27) = 3.0 (3³ = 27)
    - cbrt(8) = 2.0 (2³ = 8)
    - cbrt(125) = 5.0 (5³ = 125)
    - cbrt(64) = 4.0 (4³ = 64)

    **Best for:** Volume-related calculations, cubic equation solving.
    """
    result = input.a ** (1 / 3)
    await ctx.info(f"CUBE_ROOT: ∛{input.a} = {result}")
    return CbrtOutput(result=result)


@mcp.tool()
async def factorial(input: FactorialInput, ctx: Context) -> FactorialOutput:
    """
    Compute the factorial of a non-negative integer (n! = n × (n-1) × ... × 1).

    **Use Cases:**
    - Combinatorics and permutations
    - Probability calculations
    - Series expansions in mathematics
    - Statistical distributions

    **Examples:**
    - factorial(5) = 120 (5! = 5×4×3×2×1)
    - factorial(0) = 1 (special case: 0! = 1)
    - factorial(3) = 6 (3! = 3×2×1)
    - factorial(7) = 5040 (larger factorials)

    **Limitations:**
    - Only non-negative integers
    - Maximum input is 170 (larger values overflow)
    **Best for:** Combinatorial problems, probability, statistical calculations.
    """
    if input.a > 170:
        await ctx.error(f"FACTORIAL ERROR: {input.a} too large (max: 170)")
        raise ToolError("Factorial result would be too large")

    result = math.factorial(input.a)
    await ctx.info(f"FACTORIAL: {input.a}! = {result}")
    return FactorialOutput(result=result)


@mcp.tool()
async def remainder(input: RemainderInput, ctx: Context) -> RemainderOutput:
    """
    Compute remainder when dividing first number by second (modulo operation).

    **Use Cases:**
    - Checking divisibility
    - Cyclic calculations (days of week, etc.)
    - Hash functions and algorithms
    - Finding patterns in sequences

    **Examples:**
    - remainder(17, 5) = 2 (17 ÷ 5 = 3 remainder 2)
    - remainder(20, 4) = 0 (perfect division)
    - remainder(7, 3) = 1 (7 ÷ 3 = 2 remainder 1)
    - remainder(100, 7) = 2 (useful for cycles)

    **Limitations:** Cannot use zero as divisor.
    **Best for:** Divisibility tests, cyclic patterns, algorithm implementations.
    """
    if input.b == 0:
        await ctx.error(f"REMAINDER ERROR: Cannot compute {input.a} % 0")
        raise ToolError("Cannot compute remainder with divisor zero")

    result = input.a % input.b
    await ctx.info(f"REMAINDER: {input.a} % {input.b} = {result}")
    return RemainderOutput(result=result)


# ================= Trigonometric Functions =================


@mcp.tool()
async def sin(input: SinInput, ctx: Context) -> SinOutput:
    """
    Compute the sine of an angle given in radians.

    **Use Cases:**
    - Wave calculations and signal processing
    - Geometry and trigonometry problems
    - Physics simulations (oscillations, rotations)
    - Engineering applications

    **Examples:**
    - sin(0) = 0.0 (sine of 0 radians)
    - sin(π/2) ≈ 1.0 (sine of 90 degrees)
    - sin(π) ≈ 0.0 (sine of 180 degrees)
    - sin(3π/2) ≈ -1.0 (sine of 270 degrees)

    **Note:** Input must be in radians. Use π ≈ 3.14159 for common angles.
    **Range:** Output is always between -1 and 1.
    **Best for:** Wave analysis, circular motion, periodic phenomena.
    """
    result = math.sin(input.a)
    await ctx.info(f"SIN: sin({input.a}) = {result}")
    return SinOutput(result=result)


@mcp.tool()
async def cos(input: CosInput, ctx: Context) -> CosOutput:
    """
    Compute the cosine of an angle given in radians.

    **Use Cases:**
    - Component calculations in vectors
    - Wave analysis and signal processing
    - Rotation and transformation matrices
    - Oscillation and harmonic motion

    **Examples:**
    - cos(0) = 1.0 (cosine of 0 radians)
    - cos(π/2) ≈ 0.0 (cosine of 90 degrees)
    - cos(π) ≈ -1.0 (cosine of 180 degrees)
    - cos(2π) ≈ 1.0 (cosine of 360 degrees)

    **Note:** Input must be in radians. Use π ≈ 3.14159 for common angles.
    **Range:** Output is always between -1 and 1.
    **Best for:** Vector projections, wave calculations, harmonic analysis.
    """
    result = math.cos(input.a)
    await ctx.info(f"COS: cos({input.a}) = {result}")
    return CosOutput(result=result)


@mcp.tool()
async def tan(input: TanInput, ctx: Context) -> TanOutput:
    """
    Compute the tangent of an angle given in radians.

    **Use Cases:**
    - Slope calculations in geometry
    - Angle calculations from ratios
    - Navigation and surveying
    - Physics problems involving angles

    **Examples:**
    - tan(0) = 0.0 (tangent of 0 radians)
    - tan(π/4) ≈ 1.0 (tangent of 45 degrees)
    - tan(π/6) ≈ 0.577 (tangent of 30 degrees)
    - tan(π/3) ≈ 1.732 (tangent of 60 degrees)

    **Note:** Input must be in radians. Use π ≈ 3.14159 for common angles.
    **Limitations:** Undefined at π/2 + nπ (90°, 270°, etc.) - will return very large values.
    **Best for:** Slope calculations, angle-to-ratio conversions.
    """
    result = math.tan(input.a)
    await ctx.info(f"TAN: tan({input.a}) = {result}")
    return TanOutput(result=result)


# ================= Special Operations =================


@mcp.tool()
async def mine(input: MineInput, ctx: Context) -> MineOutput:
    """
    Perform special mining operation: a - b - b (subtract second number twice).

    **Use Cases:**
    - Custom mathematical operations
    - Algorithm implementations requiring double subtraction
    - Specialized calculations in certain domains
    - Pattern-based computations

    **Examples:**
    - mine(10, 3) = 4 (10 - 3 - 3 = 4)
    - mine(20, 5) = 10 (20 - 5 - 5 = 10)
    - mine(15, 7) = 1 (15 - 7 - 7 = 1)
    - mine(8, 4) = 0 (8 - 4 - 4 = 0)

    **Formula:** result = a - 2b
    **Best for:** Specialized algorithms, custom mathematical operations.
    """
    result = input.a - input.b - input.b
    await ctx.info(f"MINE: {input.a} - {input.b} - {input.b} = {result}")
    return MineOutput(result=result)


# ================= Image Operations =================


@mcp.tool()
async def create_thumbnail(input: CreateThumbnailInput, ctx: Context) -> ImageOutput:
    """
    Create a 100x100 pixel thumbnail from an image file.

    **Use Cases:**
    - Image processing pipelines
    - Creating preview images for galleries
    - Reducing image file sizes
    - Standardizing image dimensions

    **Supported Formats:**
    - PNG, JPG/JPEG, GIF, BMP, TIFF
    - Most common image formats

    **Examples:**
    - create_thumbnail("/path/photo.jpg") → 100x100 thumbnail
    - create_thumbnail("image.png") → resized PNG thumbnail

    **Output:** Binary image data in PNG format
    **Limitations:** Requires valid, accessible image file path
    **Best for:** Image preprocessing, creating consistent preview sizes.
    """
    try:
        img = PILImage.open(input.image_path)
        img.thumbnail((100, 100))
        await ctx.info(f"THUMBNAIL: Created 100x100 from {input.image_path}")
        return ImageOutput(data=img.tobytes(), format="png")
    except Exception as e:
        await ctx.error(f"THUMBNAIL ERROR: {str(e)}")
        raise ToolError(f"Failed to create thumbnail: {str(e)}")


# ================= String Operations =================


@mcp.tool()
async def strings_to_chars_to_int(
    input: StringsToIntsInput, ctx: Context
) -> StringsToIntsOutput:
    """
    Convert each character in a string to its ASCII integer value.

    **Use Cases:**
    - Text analysis and processing
    - Cryptography and encoding operations
    - Character-based algorithms
    - Data conversion for numerical analysis

    **Examples:**
    - 'ABC' → [65, 66, 67] (uppercase letters)
    - 'hello' → [104, 101, 108, 108, 111] (lowercase letters)
    - '123' → [49, 50, 51] (digit characters)
    - 'A1!' → [65, 49, 33] (mixed characters)

    **Output:** List of integers representing ASCII values
    **Best for:** Text encoding, character analysis, data preprocessing.
    """
    ascii_values = [ord(char) for char in input.string]
    await ctx.info(f"STRING_TO_ASCII: '{input.string}' → {ascii_values}")
    return StringsToIntsOutput(result=ascii_values)


# ================= Advanced Mathematical Operations =================


@mcp.tool()
async def int_list_to_exponential_sum(input: ExpSumInput, ctx: Context) -> ExpSumOutput:
    """
    Calculate sum of exponentials (e^x) for each number in a list.

    **Use Cases:**
    - Statistical analysis (log-likelihood calculations)
    - Machine learning (softmax function components)
    - Physics simulations (exponential processes)
    - Financial modeling (continuous compounding)

    **Mathematical Formula:** Σ(e^xi) for all xi in the list

    **Examples:**
    - [1, 2] → e^1 + e^2 ≈ 2.718 + 7.389 ≈ 10.107
    - [0, 1] → e^0 + e^1 ≈ 1 + 2.718 ≈ 3.718
    - [1, 1, 1] → 3 × e^1 ≈ 3 × 2.718 ≈ 8.154

    **Best for:** Statistical calculations, ML preprocessing, exponential analysis.
    """
    result = sum(math.exp(i) for i in input.numbers)
    await ctx.info(f"EXP_SUM: Σ(e^x) for {input.numbers} = {result}")
    return ExpSumOutput(result=result)


@mcp.tool()
async def fibonacci_numbers(input: FibonacciInput, ctx: Context) -> FibonacciOutput:
    """
    Generate the first n Fibonacci numbers in sequence.

    **Use Cases:**
    - Number theory and mathematical sequences
    - Algorithm demonstrations and testing
    - Pattern recognition in natural phenomena
    - Computer science education and examples

    **Sequence Rule:** Each number = sum of previous two numbers
    **Starting Values:** 0, 1

    **Examples:**
    - fibonacci(5) → [0, 1, 1, 2, 3]
    - fibonacci(8) → [0, 1, 1, 2, 3, 5, 8, 13]
    - fibonacci(1) → [0]
    - fibonacci(2) → [0, 1]

    **Special Cases:** n ≤ 0 returns empty list
    **Best for:** Sequence analysis, mathematical demonstrations, algorithm testing.
    """
    n = input.n
    if n <= 0:
        await ctx.info(f"FIBONACCI: n={n} → []")
        return FibonacciOutput(result=[])

    fib_sequence = [0, 1]
    for _ in range(2, n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])

    result = fib_sequence[:n]
    await ctx.info(f"FIBONACCI: First {n} numbers → {result}")
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
        port=4201,
        log_level="info",  # Reduced from debug to minimize verbosity
    )

    print("\nCalculator Stream Server shutting down...")
