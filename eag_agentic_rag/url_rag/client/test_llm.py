import os

# Clear SSL_CERT_FILE environment variable if set, before any other imports
if "SSL_CERT_FILE" in os.environ:
    del os.environ["SSL_CERT_FILE"]

from dotenv import load_dotenv

load_dotenv()

import traceback
from llm_provider import default_llm
from embedding_provider import OpenAIEmbeddingProvider


def test_llm_provider():
    """Test the simplified LLM provider module."""
    print("Testing simplified LLM provider module...")

    try:
        # Use the default LLM instance
        prompt = "What are the three main components of LangChain?"
        system_message = "You are a helpful assistant that provides concise and accurate information."

        print("\nSystem Message:")
        print(system_message)

        print("\nUser Message:")
        print(prompt)

        # Get completion using the default LLM (new interface)
        response = default_llm.get_completion(
            system_message=system_message, user_prompt=prompt
        )

        print("\nAI Response:")
        print(response)

        print("\nTest completed successfully!")

    except Exception as e:
        print(f"Error testing LLM provider: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()


def test_embedding_provider():
    """Test the  embedding provider."""
    print("\nTesting embedding provider...")
    try:
        provider = OpenAIEmbeddingProvider()
        sentences = [
            "How does AlphaFold work?",
            "How do proteins fold?",
            "What is the capital of France?",
            "Explain how neural networks learn.",
        ]
        embeddings = [provider.embed_query(s) for s in sentences]
        print(f"\nEmbedding vector length: {len(embeddings[0])}")
        print(f"First 5 values: {embeddings[0][:5]}")
        print("\nEmbedding test completed successfully!")
    except Exception as e:
        print(f"Error testing embedding provider: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()


if __name__ == "__main__":
    test_llm_provider()
    test_embedding_provider()
