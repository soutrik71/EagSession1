from pydantic import BaseModel, Field
from typing import Optional, List


class WebsearchRequest(BaseModel):
    """Request model for web search."""

    query: str = Field(..., description="The search query")
    k: int = Field(1, description="The number of results to return")


class WebsearchResponse(BaseModel):
    """Response model for web search."""

    web_url: List[str] = Field(..., description="List of URLs from the search results")
    page_content: List[str] = Field(
        ..., description="List of page content from the search results"
    )
