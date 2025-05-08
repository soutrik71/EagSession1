import os
import sys
import ssl
import numpy as np
import json

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Disable SSL verification for testing
if hasattr(ssl, "_create_unverified_context"):
    ssl._create_default_https_context = ssl._create_unverified_context

# Import MCP server
from mcp.server.fastmcp import FastMCP
from loguru import logger
from embedding_provider import OpenAIEmbeddingProvider
from tools import get_retrieved_docs
from models import (
    AddInput,
    AddOutput,
    SubtractInput,
    SubtractOutput,
    MultiplyInput,
    MultiplyOutput,
    DivideInput,
    DivideOutput,
    EvaluateExpressionInput,
    EvaluateExpressionOutput,
    CalculatePercentageInput,
    CalculatePercentageOutput,
    SquareRootInput,
    SquareRootOutput,
    CalculateEmbeddingSumInput,
    CalculateEmbeddingSumOutput,
    RetrieveDocumentsInput,
    RetrieveDocumentsOutput,
    Document,
)

# Initialize embedding provider
embedding_provider = OpenAIEmbeddingProvider()

# Create the MCP server with the name "calculator"
mcp = FastMCP("calculator")


# Functions for the calculator operations
@mcp.tool()
def add(input_data: AddInput) -> AddOutput:
    """Add two numbers and return the result.

    Args:
        input_data: The AddInput model containing the numbers to add

    Returns:
        The AddOutput model containing the sum
    """
    result = input_data.a + input_data.b
    return AddOutput(result=result)


@mcp.tool()
def subtract(input_data: SubtractInput) -> SubtractOutput:
    """Subtract the second number from the first number.

    Args:
        input_data: The SubtractInput model containing the numbers to subtract

    Returns:
        The SubtractOutput model containing the result
    """
    result = input_data.a - input_data.b
    return SubtractOutput(result=result)


@mcp.tool()
def multiply(input_data: MultiplyInput) -> MultiplyOutput:
    """Multiply two numbers together.

    Args:
        input_data: The MultiplyInput model containing the numbers to multiply

    Returns:
        The MultiplyOutput model containing the product
    """
    result = input_data.a * input_data.b
    return MultiplyOutput(result=result)


@mcp.tool()
def divide(input_data: DivideInput) -> DivideOutput:
    """Divide the first number by the second number.

    Args:
        input_data: The DivideInput model containing the dividend and divisor

    Returns:
        The DivideOutput model containing the result
    """
    # The validation is already handled by the Pydantic model
    result = input_data.a / input_data.b
    return DivideOutput(result=result)


@mcp.tool()
def evaluate_expression(
    input_data: EvaluateExpressionInput,
) -> EvaluateExpressionOutput:
    """Evaluates a mathematical expression and returns the result.

    Args:
        input_data: The EvaluateExpressionInput model containing the expression to evaluate

    Returns:
        The EvaluateExpressionOutput model containing the result
    """
    try:
        # Warning: eval is unsafe for untrusted input in production
        # For this demo it's fine, but in production use a safer alternative
        restricted_globals = {"__builtins__": {}}
        restricted_locals = {
            "abs": abs,
            "min": min,
            "max": max,
            "round": round,
            "sum": sum,
            "pow": pow,
        }
        result = eval(input_data.expression, restricted_globals, restricted_locals)
        return EvaluateExpressionOutput(result=float(result))
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")


@mcp.tool()
def calculate_percentage(
    input_data: CalculatePercentageInput,
) -> CalculatePercentageOutput:
    """Calculate the percentage of a value.

    Args:
        input_data: The CalculatePercentageInput model containing the value and percentage

    Returns:
        The CalculatePercentageOutput model containing the result
    """
    result = input_data.value * (input_data.percentage / 100)
    return CalculatePercentageOutput(result=result)


@mcp.tool()
def square_root(input_data: SquareRootInput) -> SquareRootOutput:
    """Calculate the square root of a number.

    Args:
        input_data: The SquareRootInput model containing the number to find the square root of

    Returns:
        The SquareRootOutput model containing the result
    """
    # The validation is already handled by the Pydantic model
    result = input_data.number**0.5
    return SquareRootOutput(result=result)


@mcp.tool()
def calculate_embedding_sum(
    input_data: CalculateEmbeddingSumInput,
) -> CalculateEmbeddingSumOutput:
    """Calculate the sum of all values in the embedding vector for the given text.

    Args:
        input_data: The CalculateEmbeddingSumInput model containing the text

    Returns:
        The CalculateEmbeddingSumOutput model containing the result
    """
    try:
        # Generate embedding for the text
        embedding = embedding_provider.embeddings.embed_query(input_data.text)
        # Calculate and return the sum of the embedding vector
        result = float(np.sum(embedding))
        return CalculateEmbeddingSumOutput(result=result)
    except Exception as e:
        raise ValueError(f"Error calculating embedding sum: {e}")


@mcp.tool()
def retrieve_documents(input_data: RetrieveDocumentsInput) -> str:
    """Retrieve documents from the vector store based on the query.

    Args:
        input_data: The RetrieveDocumentsInput model containing the query and k value

    Returns:
        A JSON string containing the retrieved web URLs and page content
    """
    try:
        # Get the retrieved documents using the function from tools.py
        web_urls, page_contents = get_retrieved_docs(input_data.query, input_data.k)

        # Create a list of Document objects
        documents = [
            Document(url=url, content=content)
            for url, content in zip(web_urls, page_contents)
        ]

        # Convert to dictionary first for simple JSON serialization
        response = {
            "urls": web_urls,
            "contents": page_contents,
            "count": len(documents),
        }

        # Return the response as a JSON string
        return json.dumps(response, indent=2)
    except Exception as e:
        logger.error(f"Error retrieving documents: {e}")
        raise ValueError(f"Error retrieving documents: {e}")


def mcp_log(level: str, message: str) -> None:
    """Log a message to stderr to avoid interfering with JSON communication"""
    sys.stderr.write(f"{level}: {message}\n")
    sys.stderr.flush()


if __name__ == "__main__":
    logger.info(f"Starting MCP Calculator server in directory: {os.getcwd()}")
    mcp.run(transport="stdio")
