from mcp.server.fastmcp import FastMCP
import sys
import os
from typing import Optional, List, Dict, Any
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import SKLearnVectorStore
from dotenv import load_dotenv
from loguru import logger

# Configure loguru
logger.remove()

# Load environment variables for OpenAI API key
load_dotenv()

logger.info("Starting LangChain Retriever MCP Server")

mcp = FastMCP(
    "langchain_retriever",
)

path = "C:/workspace/EagSession1/mcp_full_course/llm_codes/saved_vector_stores"


@mcp.tool()
def langgraph_query_tool(query: str) -> str:
    """
    Query the LangGraph documentation using a retriever from a local file and a vector store.
    """
    logger.debug(f"Querying LangGraph documentation: {query}")

    # Implementation moved from langchain_retriever.py
    retriever = SKLearnVectorStore(
        embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
        persist_path=os.path.join(path, "sklearn_vectorstore.parquet"),
        serializer="parquet",
    ).as_retriever(search_kwargs={"k": 3})

    relevant_docs = retriever.invoke(query)
    logger.debug(f"Retrieved {len(relevant_docs)} documents")

    formatted_context = "\n\n".join(
        [
            f"==DOCUMENT {i+1}==\n{doc.page_content}"
            for i, doc in enumerate(relevant_docs)
        ]
    )

    return formatted_context


@mcp.resource("docs://langgraph/full")
def get_all_langgraph_docs() -> str:
    """
    Get all the LangGraph documentation. Returns the contents of the file llms_full.txt,
    which contains a curated set of LangGraph documentation (~300k tokens). This is useful
    for a comprehensive response to questions about LangGraph.
    """
    logger.debug("Retrieving full LangGraph documentation")
    # Local path to the LangGraph documentation
    with open(os.path.join(path, "saved_llms_full.txt"), "r", encoding="utf-8") as file:
        content = file.read()
        logger.debug(
            f"Successfully read documentation file ({len(content)} characters)"
        )
        return content


if __name__ == "__main__":
    print("Starting MCP String Reverser server...")
    # Check if running with mcp dev command
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
