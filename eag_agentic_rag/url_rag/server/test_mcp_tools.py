#!/usr/bin/env python
# Testing script for MCP tools in the server

import os
import sys

# Add parent directory to path for imports
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# Import server modules directly since we're in the same directory
from tools import get_retrieved_docs
from server import WebsearchRequest, web_vector_search


def test_direct_search():
    """Test the get_retrieved_docs function directly."""
    print("Testing direct web search...")

    # Test with simple query
    query = "What is Helm in Kubernetes?"
    k = 1

    try:
        # Call the function directly
        web_urls, page_contents = get_retrieved_docs(query, k)
        print(f"Direct search successful: {len(web_urls)} results found")
        print(f"First URL: {web_urls[0] if web_urls else 'None'}")
        print(
            f"Content preview: {page_contents[0][:100]}..."
            if page_contents
            else "No content"
        )
    except Exception as e:
        print(f"Direct search failed: {str(e)}")


def test_tool_search():
    """Test the web_vector_search tool function."""
    print("Testing web_vector_search tool...")

    # Create a search request
    request = WebsearchRequest(query="What is Docker?", k=1)

    try:
        # Call the web search tool
        result = web_vector_search(request)
        print(f"Tool search successful: {len(result.web_url)} results found")
        print(f"First URL: {result.web_url[0] if result.web_url else 'None'}")
        print(
            f"Content preview: {result.page_content[0][:100]}..."
            if result.page_content
            else "No content"
        )
    except Exception as e:
        print(f"Tool search failed: {str(e)}")


def test_tool_search_with_request_format():
    """Test the web_vector_search tool function with the exact request format used by the LLM."""
    print("Testing web_vector_search tool with exact request format...")

    # Create the exact format used by LLM tool calls
    request_data = {
        "request": {
            "query": "What is the purpose and benefits of using Helm in software development or Kubernetes?",
            "k": 1,
        }
    }

    try:
        # Extract the request from the nested structure
        inner_request = request_data["request"]

        # Convert to WebsearchRequest object
        request_obj = WebsearchRequest(**inner_request)

        # Call the web search tool
        result = web_vector_search(request_obj)

        print(f"Tool search successful: {len(result.web_url)} results found")
        print(f"First URL: {result.web_url[0] if result.web_url else 'None'}")
        print(
            f"Content preview: {result.page_content[0][:100]}..."
            if result.page_content
            else "No content"
        )

        # Print the full content for first result
        if result.page_content:
            print("\nFull content of first result:")
            print("-" * 50)
            print(result.page_content[0])
            print("-" * 50)
    except Exception as e:
        print(f"Tool search failed: {str(e)}")
        import traceback

        traceback.print_exc()


def test_multiple_queries():
    """Test the web_vector_search tool with multiple queries."""
    print("Testing multiple queries...")

    queries = [
        "What is Kubernetes?",
        "What is Docker container?",
        "How does Helm work?",
    ]

    for query in queries:
        print(f"\nTesting query: {query}")
        request = WebsearchRequest(query=query, k=1)

        try:
            result = web_vector_search(request)
            print(f"Search successful: {len(result.web_url)} results")
            if result.web_url:
                print(f"URL: {result.web_url[0]}")
                print(f"Content preview: {result.page_content[0][:100]}...")
        except Exception as e:
            print(f"Search failed: {str(e)}")


if __name__ == "__main__":
    # test_direct_search()
    print("\n" + "-" * 50 + "\n")
    test_tool_search_with_request_format()  # Run the new test first
    print("\n" + "-" * 50 + "\n")
    test_tool_search()
    print("\n" + "-" * 50 + "\n")
    test_multiple_queries()
