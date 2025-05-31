"""
Simple LLM Utils for LangChain Integration

Provides GPT-4o chat model and text-embedding-3-small embedding model objects.
Handles SSL certificate issues and supports both sync and async methods.
"""

import os
import ssl
import getpass
from typing import Optional
from dotenv import load_dotenv

try:
    import httpx
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
except ImportError as e:
    raise ImportError(
        "Required packages not found. Install with: pip install langchain-openai httpx"
    ) from e


load_dotenv()


def create_ssl_context():
    """Create SSL context that handles certificate issues."""
    try:
        # Try to create default context
        context = ssl.create_default_context()
        return context
    except (FileNotFoundError, ssl.SSLError):
        # If SSL cert file is missing or invalid, create context without verification
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context


def create_http_client():
    """Create httpx client with SSL handling."""
    try:
        # Try with default SSL settings first
        return httpx.Client(timeout=30.0)
    except Exception:
        # If SSL issues, create client with custom SSL context
        ssl_context = create_ssl_context()
        return httpx.Client(timeout=30.0, verify=ssl_context)


def create_async_http_client():
    """Create async httpx client with SSL handling."""
    try:
        # Try with default SSL settings first
        return httpx.AsyncClient(timeout=30.0)
    except Exception:
        # If SSL issues, create client with custom SSL context
        ssl_context = create_ssl_context()
        return httpx.AsyncClient(timeout=30.0, verify=ssl_context)


class LLMUtils:
    """
    Simple utility class that provides LangChain chat and embedding models.
    Handles SSL certificate issues and supports both sync and async operations.

    Attributes:
        chat_model: ChatOpenAI instance configured with GPT-4o
        embedding_model: OpenAIEmbeddings instance configured with text-embedding-3-small
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize with GPT-4o chat model and text-embedding-3-small embedding model.

        Args:
            api_key: OpenAI API key. If None, will try to get from environment or prompt user
        """
        # Setup API key
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        elif "OPENAI_API_KEY" not in os.environ:
            os.environ["OPENAI_API_KEY"] = getpass.getpass(
                "Enter your OpenAI API key: "
            )

        # Clear problematic SSL environment variable if it exists and points to non-existent file
        if "SSL_CERT_FILE" in os.environ:
            cert_file = os.environ["SSL_CERT_FILE"]
            if not os.path.exists(cert_file):
                print(f"Warning: Removing invalid SSL_CERT_FILE: {cert_file}")
                del os.environ["SSL_CERT_FILE"]

        # Create HTTP clients with SSL handling
        http_client = create_http_client()
        async_http_client = create_async_http_client()

        # Initialize models with custom HTTP clients
        try:
            self.chat_model = ChatOpenAI(
                model="gpt-4o",
                http_client=http_client,
                http_async_client=async_http_client,
            )
            self.embedding_model = OpenAIEmbeddings(
                model="text-embedding-3-small",
                http_client=http_client,
                http_async_client=async_http_client,
            )
        except Exception as e:
            # Fallback: try without custom clients
            print(
                f"Warning: Failed to initialize with custom HTTP clients, trying fallback: {e}"
            )
            try:
                self.chat_model = ChatOpenAI(model="gpt-4o")
                self.embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
            except Exception as fallback_error:
                raise RuntimeError(
                    f"Failed to initialize models: {fallback_error}"
                ) from e


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test_async():
        """Test async functionality."""
        # Initialize
        llm_utils = LLMUtils()

        # Test sync methods
        print("Testing sync methods...")
        try:
            response = llm_utils.chat_model.invoke("Hello!")
            print(f"Chat response: {response.content}")
        except Exception as e:
            print(f"Sync chat error: {e}")

        try:
            embeddings = llm_utils.embedding_model.embed_query("Hello world")
            print(f"Embedding dimensions: {len(embeddings)}")
        except Exception as e:
            print(f"Sync embedding error: {e}")

        # Test async methods
        print("\nTesting async methods...")
        try:
            response = await llm_utils.chat_model.ainvoke("Hello async!")
            print(f"Async chat response: {response.content}")
        except Exception as e:
            print(f"Async chat error: {e}")

        try:
            embeddings = await llm_utils.embedding_model.aembed_query(
                "Hello async world"
            )
            print(f"Async embedding dimensions: {len(embeddings)}")
        except Exception as e:
            print(f"Async embedding error: {e}")

    # Run async test
    asyncio.run(test_async())
