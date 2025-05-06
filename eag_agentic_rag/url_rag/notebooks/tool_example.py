import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import LangChain tool components
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List


# Define a schema for the web search tool
class WebSearchRequest(BaseModel):
    query: str = Field(description="The query to search the web for")
    k: int = Field(description="The number of results to return", default=1)


class WebSearchResponse(BaseModel):
    results: List[str] = Field(description="The results of the web search")


# # Method 1: Define a tool using direct parameters
# @tool
# def web_search(query: str, k: int = 1) -> str:
#     """Search the web for information on any topic.

#     This tool must be used for ANY information retrieval task.
#     Always use this tool when asked about facts, information, or explanations about anything.

#     Args:
#         query: The search query to find information about
#         k: The number of results to return
#     """
#     return (
#         f"Found {k} results for: {query}. "
#         f"The search results indicate that {query} is related to Kubernetes package management, "
#         f"which helps simplify deploying, upgrading and managing applications."
#     )


# Method 2: Define a tool with a schema - CORRECTED VERSION
@tool("web_vector_search")
def web_vector_search(request: WebSearchRequest) -> WebSearchResponse:
    """Search the knowledge base for information on any topic.

    This tool must be used for ANY request requiring factual information.

    Args:
        request: The WebSearchRequest containing query and k parameters
    """
    # Extract values from the request
    query = request.query
    k = request.k

    return WebSearchResponse(
        results=[
            f"Found {k} results for: {query} (schema validated). "
            f"The knowledge base indicates {query} is a package manager for Kubernetes "
            f"that simplifies application deployment and management."
        ]
    )


if __name__ == "__main__":
    try:
        from url_rag.utility.llm_provider import default_llm

        llm = default_llm.chat_model
    except ImportError:
        # Fallback to OpenAI if the custom provider isn't available
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(temperature=0)

    print("Testing tool invocation...")

    # Method 1: Use invoke directly with the correct format
    print("\nMethod 1: Using .invoke() with correct format")
    result1 = web_vector_search.invoke(
        {"request": WebSearchRequest(query="What is the capital of Germany?", k=2)}
    )
    print(f"Result: {result1}")

    # Method 2: Using the invoke method with dictionary format
    print("\nMethod 2: Using .invoke() with nested dictionary")
    result2 = web_vector_search.invoke(
        {"request": {"query": "What is the capital of France?", "k": 3}}
    )
    print(f"Result: {result2}")

    print("\nTesting LLM with tools:")
    # Bind the tools to the language model
    llm_with_tools = llm.bind_tools(
        [web_vector_search], tool_choice="any"  # Force tool usage
    )

    # Use a string query
    response = llm_with_tools.invoke("What is use of helm in kubernetes?")
    print(f"LLM response: {response}")

    # Print tool calls specifically
    if hasattr(response, "tool_calls") and response.tool_calls:
        print("\nTool calls made:")
        for tool_call in response.tool_calls:
            print(f"- Tool: {tool_call['name']}")
            print(f"  Args: {tool_call['args']}")

            # Execute the tool call correctly
            if tool_call["name"] == "web_vector_search":
                print("\nExecuting the tool call:")

                # Handle the correct structure of args
                args = tool_call["args"]

                # Check if 'request' is in args (nested structure)
                if "request" in args:
                    # Extract the inner request
                    inner_request = args["request"]
                    # Create a WebSearchRequest from the inner request
                    request_obj = WebSearchRequest(**inner_request)
                else:
                    # If not nested, use args directly
                    request_obj = WebSearchRequest(**args)

                # Call invoke with the correct format
                tool_result = web_vector_search.invoke({"request": request_obj})
                print(f"Tool execution result: {tool_result}")
    else:
        print("\nNo tool calls were made by the LLM!")
