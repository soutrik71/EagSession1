import os
from typing import Optional
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import SKLearnVectorStore
from dotenv import load_dotenv

load_dotenv()


def langgraph_query_tool_impl(query: str) -> str:
    """
    Query the LangGraph documentation using a retriever.

    Args:
        query (str): The query to search the documentation with

    Returns:
        str: A str of the retrieved documents
    """
    path = "C:/workspace/EagSession1/mcp_full_course/llm_codes/saved_vector_stores"
    retriever = SKLearnVectorStore(
        embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
        persist_path=os.path.join(path, "sklearn_vectorstore.parquet"),
        serializer="parquet",
    ).as_retriever(search_kwargs={"k": 3})

    relevant_docs = retriever.invoke(query)
    print(f"Retrieved {len(relevant_docs)} relevant documents")
    formatted_context = "\n\n".join(
        [
            f"==DOCUMENT {i+1}==\n{doc.page_content}"
            for i, doc in enumerate(relevant_docs)
        ]
    )
    return formatted_context
