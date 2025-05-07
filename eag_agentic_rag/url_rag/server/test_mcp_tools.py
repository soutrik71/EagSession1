#!/usr/bin/env python
# Testing script for MCP tools in the server

import os
import sys

# Import server modules directly since we're in the same directory
from tools import get_retrieved_docs
from basic_server import web_vector_search  # Changed to import from basic_server


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

    # Call with direct parameters (no WebsearchRequest)
    query = "What is Docker?"
    k = 1

    try:
        # Call the web search tool directly with parameters
        result = web_vector_search(query, k)
        print("Tool search successful")
        print(f"Result: {result}")

        # Parse the string result
        if "web_url: " in result and "page_content: " in result:
            parts = result.split(", page_content: ")
            if len(parts) == 2:
                web_url_part = parts[0].replace("web_url: ", "")
                page_content_part = parts[1]

                # Eval to convert string representation to Python objects
                web_urls = eval(web_url_part)
                page_contents = eval(page_content_part)

                print(f"Parsed {len(web_urls)} results")
                print(f"First URL: {web_urls[0] if web_urls else 'None'}")
                print(
                    f"Content preview: {page_contents[0][:100]}..."
                    if page_contents
                    else "No content"
                )
    except Exception as e:
        print(f"Tool search failed: {str(e)}")
        import traceback

        traceback.print_exc()


def test_tool_search_with_request_format():
    """Test the web_vector_search tool function with the exact request format used by the LLM."""
    print("Testing web_vector_search tool with exact request format...")

    # Create the exact format used by LLM tool calls - simple parameters for basic_server
    query = "What is the purpose and benefits of using Helm in software development or Kubernetes?"
    k = 1

    try:
        # Call the web search tool
        result = web_vector_search(query, k)
        print("Tool search successful")
        print(f"Result: {result}")

        # Parse the string result
        if "web_url: " in result and "page_content: " in result:
            parts = result.split(", page_content: ")
            if len(parts) == 2:
                web_url_part = parts[0].replace("web_url: ", "")
                page_content_part = parts[1]

                # Eval to convert string representation to Python objects
                web_urls = eval(web_url_part)
                page_contents = eval(page_content_part)

                print(f"Parsed {len(web_urls)} results")
                print(f"First URL: {web_urls[0] if web_urls else 'None'}")
                print(
                    f"Content preview: {page_contents[0][:100]}..."
                    if page_contents
                    else "No content"
                )

                # Print the full content for first result
                if page_contents:
                    print("\nFull content of first result:")
                    print("-" * 50)
                    print(page_contents[0])
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
        k = 1

        try:
            result = web_vector_search(query, k)
            print("Search successful")

            # Parse the string result
            if "web_url: " in result and "page_content: " in result:
                parts = result.split(", page_content: ")
                if len(parts) == 2:
                    web_url_part = parts[0].replace("web_url: ", "")
                    page_content_part = parts[1]

                    # Eval to convert string representation to Python objects
                    web_urls = eval(web_url_part)
                    page_contents = eval(page_content_part)

                    print(f"Parsed {len(web_urls)} results")
                    if web_urls:
                        print(f"URL: {web_urls[0]}")
                        print(f"Content preview: {page_contents[0][:100]}...")
        except Exception as e:
            print(f"Search failed: {str(e)}")
            import traceback

            traceback.print_exc()


def parse_string_result(result):
    """Helper function to parse the string result from basic_server."""
    if (
        not isinstance(result, str)
        or "web_url: " not in result
        or "page_content: " not in result
    ):
        print(f"Can't parse result: {result}")
        return None, None

    parts = result.split(", page_content: ")
    if len(parts) != 2:
        print(f"Invalid format in result: {result}")
        return None, None

    web_url_part = parts[0].replace("web_url: ", "")
    page_content_part = parts[1]

    try:
        web_urls = eval(web_url_part)
        page_contents = eval(page_content_part)
        return web_urls, page_contents
    except Exception as e:
        print(f"Error evaluating result parts: {e}")
        return None, None


if __name__ == "__main__":
    test_direct_search()
    print("\n" + "-" * 50 + "\n")
    test_tool_search_with_request_format()  # Run the new test first
    print("\n" + "-" * 50 + "\n")
    test_tool_search()
    print("\n" + "-" * 50 + "\n")
    test_multiple_queries()
