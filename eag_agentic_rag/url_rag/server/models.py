"""
Pydantic models for the MCP calculator server.

This module defines the input and output schemas for each tool in the calculator server.
"""

from typing import List
from pydantic import BaseModel, Field, field_validator


# Add operation
class AddInput(BaseModel):
    """Input schema for the 'add' operation."""

    a: float = Field(..., description="The first number")
    b: float = Field(..., description="The second number")


class AddOutput(BaseModel):
    """Output schema for the 'add' operation."""

    result: float = Field(..., description="The sum of a and b")


# Subtract operation
class SubtractInput(BaseModel):
    """Input schema for the 'subtract' operation."""

    a: float = Field(..., description="The first number")
    b: float = Field(..., description="The second number")


class SubtractOutput(BaseModel):
    """Output schema for the 'subtract' operation."""

    result: float = Field(..., description="The result of a - b")


# Multiply operation
class MultiplyInput(BaseModel):
    """Input schema for the 'multiply' operation."""

    a: float = Field(..., description="The first number")
    b: float = Field(..., description="The second number")


class MultiplyOutput(BaseModel):
    """Output schema for the 'multiply' operation."""

    result: float = Field(..., description="The product of a and b")


# Divide operation
class DivideInput(BaseModel):
    """Input schema for the 'divide' operation."""

    a: float = Field(..., description="The dividend (number to be divided)")
    b: float = Field(..., description="The divisor (number to divide by)")

    @field_validator("b")
    @classmethod
    def b_cannot_be_zero(cls, v):
        """Validate that the divisor is not zero."""
        if v == 0:
            raise ValueError("Cannot divide by zero")
        return v


class DivideOutput(BaseModel):
    """Output schema for the 'divide' operation."""

    result: float = Field(..., description="The result of a / b")


# Evaluate expression operation
class EvaluateExpressionInput(BaseModel):
    """Input schema for the 'evaluate_expression' operation."""

    expression: str = Field(
        ..., description="A string containing a mathematical expression"
    )


class EvaluateExpressionOutput(BaseModel):
    """Output schema for the 'evaluate_expression' operation."""

    result: float = Field(..., description="The result of evaluating the expression")


# Calculate percentage operation
class CalculatePercentageInput(BaseModel):
    """Input schema for the 'calculate_percentage' operation."""

    value: float = Field(..., description="The base value")
    percentage: float = Field(..., description="The percentage to calculate")


class CalculatePercentageOutput(BaseModel):
    """Output schema for the 'calculate_percentage' operation."""

    result: float = Field(..., description="The result of value * (percentage/100)")


# Square root operation
class SquareRootInput(BaseModel):
    """Input schema for the 'square_root' operation."""

    number: float = Field(..., description="The number to calculate the square root of")

    @field_validator("number")
    @classmethod
    def number_cannot_be_negative(cls, v):
        """Validate that the number is not negative."""
        if v < 0:
            raise ValueError("Cannot calculate square root of a negative number")
        return v


class SquareRootOutput(BaseModel):
    """Output schema for the 'square_root' operation."""

    result: float = Field(..., description="The square root of the number")


# Calculate embedding sum operation
class CalculateEmbeddingSumInput(BaseModel):
    """Input schema for the 'calculate_embedding_sum' operation."""

    text: str = Field(..., description="The text to generate embeddings for")


class CalculateEmbeddingSumOutput(BaseModel):
    """Output schema for the 'calculate_embedding_sum' operation."""

    result: float = Field(
        ..., description="The sum of all values in the embedding vector"
    )


# Retrieve documents operation
class RetrieveDocumentsInput(BaseModel):
    """Input schema for the 'retrieve_documents' operation."""

    query: str = Field(..., description="The search query string")
    k: int = Field(3, description="The number of documents to retrieve (default: 3)")


class Document(BaseModel):
    """A document retrieved from the vector store."""

    url: str = Field(..., description="The URL of the document")
    content: str = Field(..., description="The content of the document")


class RetrieveDocumentsOutput(BaseModel):
    """Output schema for the 'retrieve_documents' operation."""

    documents: List[Document] = Field(..., description="The retrieved documents")
    count: int = Field(..., description="The number of documents retrieved")
