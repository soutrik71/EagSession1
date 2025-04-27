"""
Test script for langchain_retriever
"""

import sys
from langchain_retriever import langgraph_query_tool_impl

if __name__ == "__main__":
    try:
        print("Testing langchain_retriever...")
        query = "How do I create a simple LangGraph?"
        result = langgraph_query_tool_impl(query)
        print(f"Success! Retrieved {result.count('==DOCUMENT')} documents")
        print("First few characters of result:", result[:100])
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        import traceback

        traceback.print_exc()
