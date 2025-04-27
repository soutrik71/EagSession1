import re
import os
import tiktoken
from bs4 import BeautifulSoup
from langchain_community.document_loaders import RecursiveUrlLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import SKLearnVectorStore
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from langgraph.prebuilt import ToolNode

# Load environment variables
load_dotenv()


def count_tokens(text, model="cl100k_base"):
    """
    Count the number of tokens in the text using tiktoken.

    Args:
        text (str): The text to count tokens for
        model (str): The tokenizer model to use (default: cl100k_base for GPT-4)

    Returns:
        int: Number of tokens in the text
    """
    encoder = tiktoken.get_encoding(model)
    return len(encoder.encode(text))


def bs4_extractor(html: str) -> str:
    """
    Extract text content from HTML using BeautifulSoup.

    Args:
        html (str): Raw HTML content to extract text from

    Returns:
        str: Cleaned text content with excess whitespace removed
    """
    soup = BeautifulSoup(html, "lxml")

    # Target the main article content for LangGraph documentation
    main_content = soup.find("article", class_="md-content__inner")

    # If found, use that, otherwise fall back to the whole document
    content = main_content.get_text() if main_content else soup.text

    # Clean up whitespace
    content = re.sub(r"\n\n+", "\n\n", content).strip()

    return content


def load_langgraph_docs():
    """
    Load LangGraph documentation from the official website.

    This function:
    1. Uses RecursiveUrlLoader to fetch pages from the LangGraph website
    2. Counts the total documents and tokens loaded

    Returns:
        list: A list of Document objects containing the loaded content
        list: A list of tokens per document
    """
    print("Loading LangGraph documentation...")

    # Load the documentation
    urls = [
        "https://langchain-ai.github.io/langgraph/concepts/",
    ]

    docs = []
    for url in urls:
        loader = RecursiveUrlLoader(
            url,
            max_depth=7,
            extractor=bs4_extractor,
        )

        # Load documents using lazy loading (memory efficient)
        docs_lazy = loader.lazy_load()

        # Load documents and track URLs
        for d in docs_lazy:
            docs.append(d)

    print(f"Loaded {len(docs)} documents from LangGraph documentation.")
    print("\nLoaded URLs:")
    for i, doc in enumerate(docs):
        print(f"{i+1}. {doc.metadata.get('source', 'Unknown URL')}")

    # Count total tokens in documents
    total_tokens = 0
    tokens_per_doc = []
    for doc in docs:
        doc_tokens = count_tokens(doc.page_content)
        total_tokens += doc_tokens
        tokens_per_doc.append(doc_tokens)
    print(f"Total tokens in loaded documents: {total_tokens}")

    return docs, tokens_per_doc


def save_llms_full(documents):
    """Save the documents to a file"""

    # Open the output file
    os.makedirs(os.path.join(os.getcwd(), "saved_vector_stores"), exist_ok=True)
    output_filename = os.path.join(
        os.getcwd(), "saved_vector_stores", "saved_llms_full.txt"
    )

    with open(output_filename, "w", encoding="utf-8") as f:
        # Write each document
        for i, doc in enumerate(documents):
            # Get the source (URL) from metadata
            source = doc.metadata.get("source", "Unknown URL")

            # Write the document with proper formatting
            f.write(f"DOCUMENT {i+1}\n")
            f.write(f"SOURCE: {source}\n")
            f.write("CONTENT:\n")
            f.write(doc.page_content)
            f.write("\n\n" + "=" * 80 + "\n\n")

    print(f"Documents concatenated into {output_filename}")


def split_documents(documents):
    """
    Split documents into smaller chunks for improved retrieval.

    This function:
    1. Uses RecursiveCharacterTextSplitter with tiktoken to create semantically meaningful chunks
    2. Ensures chunks are appropriately sized for embedding and retrieval
    3. Counts the resulting chunks and their total tokens

    Args:
        documents (list): List of Document objects to split

    Returns:
        list: A list of split Document objects
    """
    print("Splitting documents...")

    # Initialize text splitter using tiktoken for accurate token counting
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=8000, chunk_overlap=500
    )

    # Split documents into chunks
    split_docs = text_splitter.split_documents(documents)

    print(f"Created {len(split_docs)} chunks from documents.")

    # Count total tokens in split documents
    total_tokens = 0
    for doc in split_docs:
        total_tokens += count_tokens(doc.page_content)

    print(f"Total tokens in split documents: {total_tokens}")

    return split_docs


def create_vectorstore(splits):
    """
    Create a vector store from document chunks using SKLearnVectorStore.

    This function:
    1. Initializes an embedding model to convert text into vector representations
    2. Creates a vector store from the document chunks

    Args:
        splits (list): List of split Document objects to embed

    Returns:
        SKLearnVectorStore: A vector store containing the embedded documents
    """
    print("Creating SKLearnVectorStore...")

    # Initialize OpenAI embeddings
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # Create vector store from documents using SKLearn
    os.makedirs(os.path.join(os.getcwd(), "saved_vector_stores"), exist_ok=True)
    persist_path = os.path.join(
        os.getcwd(), "saved_vector_stores", "sklearn_vectorstore.parquet"
    )

    vectorstore = SKLearnVectorStore.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_path=persist_path,
        serializer="parquet",
    )
    print("SKLearnVectorStore created successfully.")

    vectorstore.persist()
    print("SKLearnVectorStore was persisted to", persist_path)

    return vectorstore


# Add the schema definition for the query tool
class QueryToolInput(BaseModel):
    query: str = Field(
        description="The search query to find relevant information in the LangGraph documentation"
    )


def langgraph_query_tool_impl(query: str):
    """
    Query the LangGraph documentation using a retriever.

    Args:
        query (str): The query to search the documentation with

    Returns:
        str: A str of the retrieved documents
    """
    retriever = SKLearnVectorStore(
        embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
        persist_path=os.path.join(
            os.getcwd(), "saved_vector_stores", "sklearn_vectorstore.parquet"
        ),
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


# Replace the tool wrapper with StructuredTool
langgraph_query_tool = StructuredTool.from_function(
    func=langgraph_query_tool_impl,
    name="langgraph_query_tool",
    description="This tool is used to query the LangGraph documentation using a retriever. This tool can answer questions about the documentation and the concepts of LangGraph.",
    args_schema=QueryToolInput,
    return_direct=True,
)


# def test_structured_tool():
#     """Test the structured tool setup"""
#     print("\nTesting StructuredTool setup:")
#     print(f"Tool name: {langgraph_query_tool.name}")
#     print(f"Tool description: {langgraph_query_tool.description}")
#     print(f"Tool args schema: {langgraph_query_tool.args}")

#     # Test tool invocation
#     result = langgraph_query_tool.invoke({"query": "What is LangGraph?"})
#     print("\nTest query result:")
#     print(result)


def test_tool_node_manual():
    """Test ToolNode with manual tool calls"""
    print(
        "\nTesting ToolNode with manual tool calls by sending a message with a tool call to the LLM"
    )

    # Create ToolNode with our query tool
    tools = [langgraph_query_tool]
    tool_node = ToolNode(tools)

    # Create a manual tool call
    message_with_tool_call = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "langgraph_query_tool",
                "args": {"query": "What is LangGraph?"},
                "id": "tool_call_id",
                "type": "tool_call",
            }
        ],
    )

    # Invoke the tool node
    result = tool_node.invoke({"messages": [message_with_tool_call]})
    print("\nToolNode Manual Result:")
    print(f"Result: {result}")
    return result


def test_tool_node_with_llm():
    """Test ToolNode with LLM integration"""
    print(
        "\nTesting ToolNode with LLM integration by sending a message to the LLM with a tool call"
    )

    # Create tools list
    tools = [langgraph_query_tool]

    # Create LLM with bound tools
    model_with_tools = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(tools)

    # Create ToolNode
    tool_node = ToolNode(tools)

    # Generate AI message with tool calls using the LLM
    ai_message = model_with_tools.invoke("What is LangGraph?")

    # Use the tool node to execute the tool calls
    result = tool_node.invoke({"messages": [ai_message]})
    print("\nToolNode LLM Result:")
    print(f"Result: {result}")
    return result


def main():
    try:
        if not os.path.exists(
            os.path.join(
                os.getcwd(), "saved_vector_stores", "sklearn_vectorstore.parquet"
            )
        ):
            # Load and process documents
            documents, tokens_per_doc = load_langgraph_docs()

            # Save documents to file
            save_llms_full(documents)

            # Split documents into chunks
            split_docs = split_documents(documents)

            # Create vector store
            global vectorstore
            vectorstore = create_vectorstore(split_docs)

        # Test the structured tool setup
        # test_structured_tool()

        # Test manual ToolNode usage
        test_tool_node_manual()

        # Test ToolNode with LLM integration
        test_tool_node_with_llm()

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise


if __name__ == "__main__":
    main()
