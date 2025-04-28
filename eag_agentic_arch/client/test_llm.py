import traceback
import os
from dotenv import load_dotenv
from llm_provider import default_llm

# Load environment variables
load_dotenv()

# Clear SSL_CERT_FILE environment variable if set
if "SSL_CERT_FILE" in os.environ:
    del os.environ["SSL_CERT_FILE"]


def test_llm_provider():
    """Test the LangChain-based LLM provider module."""
    print("Testing LangChain-based LLM provider module...")

    try:
        # Use the default LLM instance
        prompt = "What are the three main components of LangChain?"
        system_message = "You are a helpful assistant that provides concise and accurate information."

        print("\nSystem Message:")
        print(system_message)

        print("\nUser Message:")
        print(prompt)

        # Get completion using the default LLM
        response = default_llm.get_completion(
            prompt=prompt, system_message=system_message
        )

        print("\nAI Response:")
        print(response)

        # Alternative: Create a custom LLM instance
        # custom_llm = get_llm(model="gpt-4o-mini")
        # response = custom_llm.get_completion(prompt, system_message)

        print("\nTest completed successfully!")

    except Exception as e:
        print(f"Error testing LLM provider: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()


if __name__ == "__main__":
    test_llm_provider()
