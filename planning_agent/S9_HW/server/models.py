from pydantic import BaseModel, Field
from typing import List


# ================= Mathematical Operations =================


class AddInput(BaseModel):
    """Input model for addition operation"""

    a: float = Field(description="First number to add")
    b: float = Field(description="Second number to add")


class AddOutput(BaseModel):
    """Output model for addition operation"""

    result: float = Field(description="Sum of the two numbers")


class SubtractInput(BaseModel):
    """Input model for subtraction operation"""

    a: float = Field(description="Number to subtract from")
    b: float = Field(description="Number to subtract")


class SubtractOutput(BaseModel):
    """Output model for subtraction operation"""

    result: float = Field(description="Difference of the two numbers")


class MultiplyInput(BaseModel):
    """Input model for multiplication operation"""

    a: float = Field(description="First number to multiply")
    b: float = Field(description="Second number to multiply")


class MultiplyOutput(BaseModel):
    """Output model for multiplication operation"""

    result: float = Field(description="Product of the two numbers")


class DivideInput(BaseModel):
    """Input model for division operation"""

    a: float = Field(description="Dividend (number to be divided)")
    b: float = Field(description="Divisor (number to divide by)")


class DivideOutput(BaseModel):
    """Output model for division operation"""

    result: float = Field(description="Quotient of the division")


class SquareInput(BaseModel):
    """Input model for square operation"""

    a: float = Field(description="Number to square")


class SquareOutput(BaseModel):
    """Output model for square operation"""

    result: float = Field(description="Square of the number (a²)")


class PowerInput(BaseModel):
    """Input model for power operation"""

    a: float = Field(description="Base number")
    b: float = Field(description="Exponent")


class PowerOutput(BaseModel):
    """Output model for power operation"""

    result: float = Field(description="Result of base raised to the power of exponent")


class CbrtInput(BaseModel):
    """Input model for cube root operation"""

    a: float = Field(description="Number to find cube root of")


class CbrtOutput(BaseModel):
    """Output model for cube root operation"""

    result: float = Field(description="Cube root of the number")


class FactorialInput(BaseModel):
    """Input model for factorial operation"""

    a: int = Field(description="Non-negative integer to find factorial of", ge=0)


class FactorialOutput(BaseModel):
    """Output model for factorial operation"""

    result: int = Field(description="Factorial of the number")


class RemainderInput(BaseModel):
    """Input model for remainder operation"""

    a: int = Field(description="Dividend")
    b: int = Field(description="Divisor")


class RemainderOutput(BaseModel):
    """Output model for remainder operation"""

    result: int = Field(description="Remainder of a divided by b")


# ================= Trigonometric Functions =================


class SinInput(BaseModel):
    """Input model for sine function"""

    a: float = Field(description="Angle in radians")


class SinOutput(BaseModel):
    """Output model for sine function"""

    result: float = Field(description="Sine of the angle")


class CosInput(BaseModel):
    """Input model for cosine function"""

    a: float = Field(description="Angle in radians")


class CosOutput(BaseModel):
    """Output model for cosine function"""

    result: float = Field(description="Cosine of the angle")


class TanInput(BaseModel):
    """Input model for tangent function"""

    a: float = Field(description="Angle in radians")


class TanOutput(BaseModel):
    """Output model for tangent function"""

    result: float = Field(description="Tangent of the angle")


# ================= Special Operations =================


class MineInput(BaseModel):
    """Input model for mine operation"""

    a: float = Field(description="First number")
    b: float = Field(description="Second number")


class MineOutput(BaseModel):
    """Output model for mine operation"""

    result: float = Field(description="Result of mining operation: a - b - b")


# ================= Image Operations =================


class CreateThumbnailInput(BaseModel):
    """Input model for thumbnail creation"""

    image_path: str = Field(description="Path to the image file")


class ImageOutput(BaseModel):
    """Output model for image operations"""

    data: bytes = Field(description="Image data as bytes")
    format: str = Field(description="Image format (e.g., 'png', 'jpg')")


# ================= String Operations =================


class StringsToIntsInput(BaseModel):
    """Input model for string to ASCII conversion"""

    string: str = Field(description="String to convert to ASCII values")


class StringsToIntsOutput(BaseModel):
    """Output model for string to ASCII conversion"""

    result: List[int] = Field(description="List of ASCII values")


# ================= Advanced Mathematical Operations =================


class ExpSumInput(BaseModel):
    """Input model for exponential sum operation"""

    numbers: List[int] = Field(description="List of numbers to compute exponential sum")


class ExpSumOutput(BaseModel):
    """Output model for exponential sum operation"""

    result: float = Field(description="Sum of exponentials of the input numbers")


class FibonacciInput(BaseModel):
    """Input model for Fibonacci sequence generation"""

    n: int = Field(description="Number of Fibonacci numbers to generate", ge=0)


class FibonacciOutput(BaseModel):
    """Output model for Fibonacci sequence"""

    result: List[int] = Field(description="List of Fibonacci numbers")


# ================= Code Execution (commented out in original) =================


class PythonCodeInput(BaseModel):
    """Input model for Python code execution"""

    code: str = Field(description="Python code to execute")


class PythonCodeOutput(BaseModel):
    """Output model for Python code execution"""

    result: str = Field(description="Execution result or output")


class ShellCommandInput(BaseModel):
    """Input model for shell command execution"""

    command: str = Field(description="Shell command to execute")


# ================= Web Operations =================


class SearchInput(BaseModel):
    """Input model for web search operations"""

    query: str = Field(description="Search query string")
    max_results: int = Field(
        description="Maximum number of results", default=10, ge=1, le=50
    )


class SearchOutput(BaseModel):
    """Output model for web search operations"""

    results: str = Field(description="Formatted search results")
    success: bool = Field(description="Whether the search was successful")
    error_message: str = Field(description="Error message if search failed", default="")


class UrlFetchInput(BaseModel):
    """Input model for URL content fetching"""

    url: str = Field(description="URL to fetch content from")
    max_length: int = Field(description="Maximum content length", default=8000, ge=100)


class UrlFetchOutput(BaseModel):
    """Output model for URL content fetching"""

    content: str = Field(description="Extracted text content from the webpage")
    success: bool = Field(description="Whether the fetch was successful")
    error_message: str = Field(description="Error message if fetch failed", default="")


# ================= Document Search Operations =================


class DocumentSearchInput(BaseModel):
    """Input model for document search operations"""

    query: str = Field(description="Search query to find relevant documents")
    top_k: int = Field(
        description="Number of top results to return", default=5, ge=1, le=20
    )


class DocumentSearchResult(BaseModel):
    """Individual search result from document search"""

    chunk: str = Field(description="Text chunk that matched the query")
    source: str = Field(description="Source document filename")
    chunk_id: str = Field(description="Unique identifier for this chunk")
    score: float = Field(description="Similarity score (lower is better)")


class DocumentSearchOutput(BaseModel):
    """Output model for document search operations"""

    results: List[DocumentSearchResult] = Field(description="List of search results")
    total_results: int = Field(description="Total number of results found")
    query: str = Field(description="Original search query")
    success: bool = Field(description="Whether the search was successful")
    error_message: str = Field(description="Error message if search failed", default="")
