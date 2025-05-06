"""
Web URL Preprocessing module for extracting and embedding content from URLs.

This module processes web URLs by extracting their content, chunking it,
and storing the chunks as embeddings in a FAISS vector store.
"""

import os
import uuid
import yaml
import sys
import time
import shutil
import requests
from requests.exceptions import RequestException
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from loguru import logger

# Fix paths for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

# Import necessary libraries
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import Html2TextTransformer
from langchain_text_splitters import TokenTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_core.documents import Document
import faiss

# Configure loguru logger
LOG_DIR = Path(current_dir) / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "weburl_preprocess.log"

# Remove default logger and set up our custom format
logger.remove()
logger.add(
    sys.stderr,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
    level="INFO",
)
logger.add(
    LOG_FILE,
    rotation="10 MB",
    retention="1 week",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
)

logger.info(f"Starting weburl_preprocess script from {__file__}")

# Fix SSL issues by unsetting SSL_CERT_FILE if it exists
if "SSL_CERT_FILE" in os.environ:
    del os.environ["SSL_CERT_FILE"]
    logger.debug("Removed SSL_CERT_FILE from environment variables")

# Load environment variables
load_dotenv()
logger.debug("Loaded environment variables")


def load_config(config_path: str) -> Optional[Dict[str, Any]]:
    """
    Load configuration from a YAML file

    Args:
        config_path: Path to the configuration file

    Returns:
        Dictionary containing configuration or None if loading failed
    """
    try:
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)
        logger.debug(f"Loaded configuration from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration from {config_path}: {e}")
        return None


def setup_embedding_provider():
    """
    Setup and return an embedding provider

    Returns:
        Embedding function for vector embeddings

    Raises:
        ImportError: If embedding provider cannot be imported
    """
    # Try different import paths to handle various project structures
    import_paths = [
        "client.embedding_provider",
        # Commented out to avoid linter error, will still work at runtime if path exists
        # "url_rag.client.embedding_provider",
    ]

    # Add parent dir to paths for better import resolution
    sys.path.append(str(parent_dir))
    logger.debug(f"Added {parent_dir} to sys.path")

    last_error = None
    for import_path in import_paths:
        try:
            logger.debug(f"Attempting to import from {import_path}")
            module = __import__(import_path, fromlist=["OpenAIEmbeddingProvider"])
            logger.info(
                f"Successfully imported OpenAIEmbeddingProvider from {import_path}"
            )
            return module.OpenAIEmbeddingProvider().embeddings
        except (ImportError, AttributeError) as e:
            last_error = e
            logger.debug(f"Failed to import from {import_path}: {e}")
            continue

    # Manual import attempts as fallback
    try:
        logger.debug("Attempting direct import from client.embedding_provider")
        from utility.embedding_provider import OpenAIEmbeddingProvider

        logger.info("Successfully imported OpenAIEmbeddingProvider directly")
        return OpenAIEmbeddingProvider().embeddings
    except ImportError:
        # The following import is commented out due to linter errors,
        # but it's kept as a fallback for runtime when the path might exist
        # The import error is expected during static analysis
        try:
            logger.debug(
                "Attempting direct import from url_rag.utility.embedding_provider"
            )
            # from url_rag.utility.embedding_provider import OpenAIEmbeddingProvider

            # Use dynamic import to avoid linter errors
            embedding_module = __import__(
                "url_rag.utility.embedding_provider",
                fromlist=["OpenAIEmbeddingProvider"],
            )
            OpenAIEmbeddingProvider = embedding_module.OpenAIEmbeddingProvider

            logger.info(
                "Successfully imported OpenAIEmbeddingProvider from url_rag.utility"
            )
            return OpenAIEmbeddingProvider().embeddings
        except Exception as e:
            last_error = e
            logger.debug(f"Failed direct import attempts: {e}")

    # If we've exhausted all paths, raise the last error
    logger.error(
        f"Could not import OpenAIEmbeddingProvider after multiple attempts: {last_error}"
    )
    raise ImportError(f"Could not import OpenAIEmbeddingProvider: {last_error}")


def extract_text_from_url(url: str) -> List[Document]:
    """
    Extract and return plain text Document(s) from a given URL.
    Uses LangChain's AsyncHtmlLoader and Html2TextTransformer.
    Args:
        url: The URL to extract content from
    Returns:
        A list of Document objects (empty if failed)
    """
    try:
        logger.info(f"Extracting text from URL: {url}")
        # Check if URL is reachable before attempting to load
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            if response.status_code >= 400:
                logger.error(f"URL unreachable (status {response.status_code}): {url}")
                return []
        except RequestException as e:
            logger.error(f"Network error reaching URL {url}: {e}")
            return []
        loader = AsyncHtmlLoader([url])
        docs = loader.load()
        if not docs:
            logger.warning(f"No content fetched from {url}")
            return []
        html2text = Html2TextTransformer()
        docs_transformed = html2text.transform_documents(docs)
        if not docs_transformed or not docs_transformed[0].page_content.strip():
            logger.warning(f"Extracted content is empty or malformed for {url}")
            return []
        logger.success(
            f"Successfully extracted text from {url}, got {len(docs_transformed)} documents"
        )
        return docs_transformed
    except Exception as e:
        logger.error(f"Error extracting text from URL {url}: {e}")
        return []


def chunk_text_documents(
    docs_transformed: List[Document],
    chunk_size: int,
    chunk_overlap: int,
    model_name: str,
) -> List[Document]:
    """
    Split the transformed documents into chunks using TokenTextSplitter.

    Args:
        docs_transformed: List of Document objects
        chunk_size: Maximum size of chunks
        chunk_overlap: Overlap between chunks
        model_name: Model name for tokenization

    Returns:
        A list of chunked Document objects
    """
    if not docs_transformed:
        logger.warning("No documents to chunk")
        return []

    try:
        logger.info(
            f"Chunking {len(docs_transformed)} documents with chunk_size={chunk_size}, chunk_overlap={chunk_overlap}"
        )
        text_splitter = TokenTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap, model_name=model_name
        )
        texts_chunked = text_splitter.split_documents(docs_transformed)
        # Log chunking results
        orig_len = len(docs_transformed)
        chunk_len = len(texts_chunked)
        logger.success(
            f"Chunked documents: {chunk_len} chunks extracted from {orig_len} original documents"
        )
        return texts_chunked
    except Exception as e:
        logger.error(f"Error chunking documents: {e}")
        return []


def add_documents_to_faiss_index(
    documents: List[Document], embedder: Any, index_name: str
) -> List[str]:
    """
    Adds documents to a FAISS vector store with the given index name.
    If the index does not exist, it creates a new one.
    If it exists, it loads and updates it.

    Args:
        documents: List of Document objects to add
        embedder: Embedding function to use
        index_name: Name of the index to use

    Returns:
        List of document IDs
    """
    if not documents:
        logger.warning("No documents to add to index")
        return []

    try:
        # Ensure the index folder exists or not
        if not os.path.exists(index_name):
            logger.info(
                f"Index folder '{index_name}' does not exist. Creating a new index."
            )
            # Create new FAISS index
            # Get embedding size from a sample embedding
            sample_embedding = embedder.embed_query("sample text")
            index = faiss.IndexFlatL2(len(sample_embedding))
            vector_store = FAISS(
                embedding_function=embedder,
                index=index,
                docstore=InMemoryDocstore(),
                index_to_docstore_id={},
            )
            logger.success(f"Created new FAISS index at '{index_name}'")
        else:
            logger.info(f"Index folder '{index_name}' exists. Loading existing index.")
            # Load existing FAISS index
            vector_store = FAISS.load_local(
                index_name, embedder, allow_dangerous_deserialization=True
            )
            logger.success(f"Loaded existing FAISS index from '{index_name}'")

        # Generate unique IDs for each document
        doc_ids = [str(uuid.uuid4()) for _ in documents]
        # Add documents to the vector store
        vector_store.add_documents(documents=documents, ids=doc_ids)
        logger.success(f"Added {len(documents)} documents to the vector store")

        # Save the updated index
        vector_store.save_local(folder_path=index_name)
        logger.success(f"Index saved at '{index_name}'")

        return doc_ids
    except Exception as e:
        logger.error(f"Error adding documents to index: {e}", exc_info=True)
        return []


def check_and_reset_index(index_name: str, reset_index: bool) -> None:
    """
    Check if the index needs to be reset based on configuration

    Args:
        index_name: Path to the index folder
        reset_index: Whether to reset the index
    """
    if reset_index and os.path.exists(index_name):
        logger.warning(
            f"reset_index is set to True. Deleting existing index at '{index_name}'"
        )
        try:
            shutil.rmtree(index_name)
            logger.success(f"Successfully deleted index folder '{index_name}'")
        except Exception as e:
            logger.error(f"Error deleting index folder '{index_name}': {e}")
    elif not reset_index and os.path.exists(index_name):
        logger.info(
            f"reset_index is set to False. Keeping existing index at '{index_name}'"
        )


def process_url(
    url: str, config: Dict[str, Any], embedder: Any, index_name: str
) -> bool:
    """
    Process a URL by extracting content, chunking, and adding to vector store.
    Args:
        url: URL to process
        config: Configuration dictionary
        embedder: Embedding function to use
        index_name: Path to the index directory
    Returns:
        Success status
    """
    try:
        logger.info(f"Processing URL: {url}")
        chunk_size = int(config.get("chunk_size", 500))
        chunk_overlap = int(config.get("chunk_overlap", 50))
        model_name = config.get("model_name", "gpt-4o")
        logger.info(
            f"Using configuration: chunk_size={chunk_size}, "
            f"chunk_overlap={chunk_overlap}, model_name={model_name}, "
            f"index_name={index_name}"
        )
        # Extract text from URL
        raw_docs = extract_text_from_url(url)
        if not raw_docs:
            logger.warning(f"Skipping URL due to extraction failure: {url}")
            return False
        # Chunk the documents
        chunked_docs = chunk_text_documents(
            raw_docs,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            model_name=model_name,
        )
        if not chunked_docs:
            logger.warning(f"Skipping URL due to chunking failure: {url}")
            return False
        # Add to vector store
        doc_ids = add_documents_to_faiss_index(chunked_docs, embedder, index_name)
        if doc_ids:
            logger.success(
                f"Successfully processed URL: {url} and added to index {index_name}"
            )
        return bool(doc_ids)
    except Exception as e:
        logger.error(f"Error processing URL {url}: {e}", exc_info=True)
        return False


def process_single_url(url: str, config_path: str = "config.yaml") -> bool:
    """
    Process a single URL with the given configuration path.

    Args:
        url: URL to process
        config_path: Path to the configuration file

    Returns:
        Success status
    """
    # Resolve config path
    config_path = os.path.join(os.getcwd(), "url_rag", "utility", "config.yaml")

    logger.info(f"Processing single URL {url} with config from {config_path}")

    # Load configuration
    config = load_config(config_path)
    if not config:
        logger.error(f"Failed to load configuration from {config_path}. Exiting.")
        return False

    # Setup embedding provider
    try:
        embedder = setup_embedding_provider()
    except Exception as e:
        logger.error(f"Failed to setup embedding provider: {e}", exc_info=True)
        return False

    # Get index name and reset_index from config
    index_name = config.get("db_index_name", "weburl_index")
    index_name = os.path.join(os.getcwd(), "url_rag", index_name)

    # Process the URL
    return process_url(url, config, embedder, index_name)


def batch_process_urls(urls: List[str], config_path: str = "config.yaml") -> List[bool]:
    """
    Process a batch of URLs with the given configuration path.

    Args:
        urls: List of URLs to process
        config_path: Path to the configuration file

    Returns:
        List of success status for each URL
    """
    logger.info(f"Batch processing {len(urls)} URLs")

    # Load configuration once for all URLs
    config_path = os.path.join(os.getcwd(), "url_rag", "utility", "config.yaml")
    config = load_config(config_path)
    if not config:
        logger.error(f"Failed to load configuration from {config_path}. Exiting.")
        return [False] * len(urls)

    # Setup embedding provider once
    try:
        embedder = setup_embedding_provider()
    except Exception as e:
        logger.error(f"Failed to setup embedding provider: {e}", exc_info=True)
        return [False] * len(urls)

    # Get index name and reset_index from config
    index_name = config.get("db_index_name", "weburl_index")
    index_name = os.path.join(os.getcwd(), "url_rag", index_name)
    reset_index = config.get("reset_index", False)

    # Only reset index once before processing all URLs
    check_and_reset_index(index_name, reset_index)

    results = []
    for i, url in enumerate(urls, 1):
        logger.info(f"Processing URL {i}/{len(urls)}: {url}")
        # Process URL with the already prepared configuration and embedding provider
        success = process_url(url, config, embedder, index_name)
        results.append(success)
        # Sleep to avoid rate limiting
        time.sleep(1)

    logger.info(f"Batch processing complete. Success: {sum(results)}/{len(results)}")
    return results


if __name__ == "__main__":
    # Example usage
    urls = [
        "https://geshan.com.np/blog/2018/11/4-ways-docker-changed-the-way-software-engineers-work-in-past-half-decade",
        "https://www.ibm.com/think/topics/docker",
    ]

    logger.info(f"Processing {len(urls)} URLs...")
    results = batch_process_urls(urls)

    # Summarize results
    successful = sum(1 for r in results if r)
    failed = len(results) - successful
    logger.info(f"Processing complete. Successful: {successful}, Failed: {failed}")

    # Example of checking FAISS index content
    config = load_config(os.path.join(os.getcwd(), "url_rag", "utility", "config.yaml"))
    if config:
        index_name = config.get("db_index_name", "weburl_index")
        index_name = os.path.join(os.getcwd(), "url_rag", index_name)

        if os.path.exists(f"{index_name}/index.pkl"):
            logger.info(f"Index file exists at {index_name}/index.pkl")
            # Example of how to access index details if needed
            import pickle

            with open(f"{index_name}/index.pkl", "rb") as f:
                index = pickle.load(f)
            logger.info(f"Index details: {index}")

    logger.success("Script execution completed")
