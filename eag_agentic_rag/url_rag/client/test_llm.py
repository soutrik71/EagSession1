import os
import ssl
import warnings
import asyncio
import traceback
from eag_agentic_rag.url_rag.client.llm_provider import (
    default_llm,
    test_ssl_config,
    create_insecure_http_client,
    create_insecure_async_http_client,
)
from embedding_provider import OpenAIEmbeddingProvider

# ======== TEST SETUP ========
# Ensure we're suppressing any SSL warnings to avoid cluttering output
warnings.filterwarnings("ignore", ".*SSL.*")
warnings.filterwarnings("ignore", ".*Certificate.*")
warnings.filterwarnings("ignore", ".*Unverified.*")


def print_ssl_debug_info():
    """Print detailed information about the current SSL configuration."""
    print("\n========== SSL CONFIGURATION INFO ==========")
    print(
        f"SSL Default Context Verify Mode: {ssl._create_default_https_context().verify_mode}"
    )
    print(f"SSL CERT_NONE Value: {ssl.CERT_NONE}")

    # Check environment variables
    print("\nEnvironment Variables:")
    print(f"  - PYTHONHTTPSVERIFY={os.environ.get('PYTHONHTTPSVERIFY')}")
    print(f"  - OPENAI_VERIFY_SSL_CERTS={os.environ.get('OPENAI_VERIFY_SSL_CERTS')}")
    print(
        f"  - OPENAI_API_SKIP_VERIFY_SSL={os.environ.get('OPENAI_API_SKIP_VERIFY_SSL')}"
    )
    print(f"  - REQUESTS_CA_BUNDLE={os.environ.get('REQUESTS_CA_BUNDLE')}")
    print(
        f"  - NODE_TLS_REJECT_UNAUTHORIZED={os.environ.get('NODE_TLS_REJECT_UNAUTHORIZED')}"
    )
    print(f"  - SSL_CERT_FILE={os.environ.get('SSL_CERT_FILE')}")

    # Test creating SSL context
    ctx = ssl.create_default_context()
    print("\nSSL Context Properties:")
    print(f"  - check_hostname: {ctx.check_hostname}")
    print(f"  - verify_mode: {ctx.verify_mode}")

    print("========== END SSL INFO ==========\n")


async def test_sync_http_request():
    """Test a direct synchronous HTTP request using our helper."""
    print("\n========== TESTING SYNC HTTP REQUEST ==========")
    try:
        client = create_insecure_http_client()
        response = client.get("https://api.openai.com/v1/models")
        print(
            f"✅ Direct sync HTTP request successful (Status: {response.status_code})"
        )
        client.close()
        return True
    except Exception as e:
        print(f"❌ Direct sync HTTP request failed: {e}")
        traceback.print_exc()
        return False


async def test_async_http_request():
    """Test a direct asynchronous HTTP request using our helper."""
    print("\n========== TESTING ASYNC HTTP REQUEST ==========")
    try:
        client = create_insecure_async_http_client()
        response = await client.get("https://api.openai.com/v1/models")
        print(
            f"✅ Direct async HTTP request successful (Status: {response.status_code})"
        )
        await client.aclose()
        return True
    except Exception as e:
        print(f"❌ Direct async HTTP request failed: {e}")
        traceback.print_exc()
        return False


async def test_llm_sync():
    """Test the synchronous LLM capabilities"""
    print("\n========== TESTING SYNCHRONOUS LLM ==========")
    try:
        query = "What is retrieval-augmented generation in one sentence?"
        print(f"Query: {query}")
        response = default_llm.get_completion(
            system_message="You are a helpful AI assistant. Keep your responses concise.",
            user_prompt=query,
        )
        print(f"✅ Sync Response: {response}")
        return True
    except Exception as e:
        print(f"❌ Synchronous LLM test failed: {e}")
        traceback.print_exc()
        return False


async def test_llm_async():
    """Test the asynchronous LLM capabilities"""
    print("\n========== TESTING ASYNCHRONOUS LLM ==========")
    try:
        query = "Explain the concept of vector databases in one sentence."
        print(f"Query: {query}")
        response = await default_llm.get_completion_async(
            system_message="You are a helpful AI assistant. Keep your responses concise.",
            user_prompt=query,
        )
        print(f"✅ Async Response: {response}")
        return True
    except Exception as e:
        print(f"❌ Asynchronous LLM test failed: {e}")
        traceback.print_exc()
        return False


async def test_embeddings():
    """Test the OpenAI embedding provider."""
    print("\n========== TESTING OPENAI EMBEDDINGS ==========")
    try:
        # Create embedding provider with SSL verification disabled
        embedding_provider = OpenAIEmbeddingProvider(verify_ssl=False)

        # Test single text embedding
        test_text = "This is a test for embedding generation."
        embedding = embedding_provider.embed_query(test_text)

        # Verify embedding dimensions
        print(f"✅ Embedding generated successfully. Dimensions: {len(embedding)}")

        # Test multiple document embeddings
        test_docs = ["Document 1 for testing.", "Document 2 for testing."]
        embeddings = embedding_provider.embed_documents(test_docs)

        print(f"✅ Multiple embeddings generated. Count: {len(embeddings)}")
        return True
    except Exception as e:
        print(f"❌ Embedding test failed: {e}")
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all the tests asynchronously"""
    print("\n========== STARTING COMPREHENSIVE TESTS ==========")

    # Print detailed SSL configuration
    print_ssl_debug_info()

    # Run basic SSL test
    test_ssl_config()

    # Run direct HTTP client tests
    await test_sync_http_request()
    await test_async_http_request()

    # Run LLM tests
    await test_llm_sync()
    await test_llm_async()

    # Run embedding test
    await test_embeddings()

    print("\n========== ALL TESTS COMPLETED ==========")


if __name__ == "__main__":
    # Execute all tests
    asyncio.run(run_all_tests())
