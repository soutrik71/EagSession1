import os
from dotenv import load_dotenv
from llm_provider import default_llm, get_llm

# Load environment variables
load_dotenv()

# Clear SSL_CERT_FILE environment variable if set
if "SSL_CERT_FILE" in os.environ:
    del os.environ["SSL_CERT_FILE"]


def main():
    """Example usage of the LangChain-based LLM provider."""
    print("LangChain-based LLM Provider Examples\n" + "=" * 35)

    # Example 1: Using the default LLM instance
    print("\nExample 1: Using the default LLM instance")
    question = "What is the capital of France?"
    response = default_llm.get_completion(question)
    print(f"Question: {question}")
    print(f"Answer: {response}\n")

    # Example 2: Using a custom system message
    print("Example 2: Using a custom system message")
    question = "Explain the concept of machine learning in one sentence."
    system_message = (
        "You are a technical expert who explains complex concepts concisely."
    )
    response = default_llm.get_completion(
        prompt=question, system_message=system_message
    )
    print(f"System: {system_message}")
    print(f"Question: {question}")
    print(f"Answer: {response}\n")

    # Example 3: Using custom messages format
    print("Example 3: Using custom messages format")
    messages = [
        {"role": "system", "content": "You are a helpful travel assistant."},
        {"role": "user", "content": "I want to visit Paris."},
        {
            "role": "assistant",
            "content": "Paris is a beautiful city! What would you like to know about it?",
        },
        {"role": "user", "content": "What are the top 3 attractions I should visit?"},
    ]
    response = default_llm.get_completion_with_messages(messages)
    print("Chat history:")
    for msg in messages:
        print(f"  {msg['role'].capitalize()}: {msg['content']}")
    print(f"Response: {response}\n")

    # Example 4: Creating a custom LLM instance with temperature
    print("Example 4: Creating a custom LLM instance")
    custom_llm = get_llm(model="gpt-4o-mini")
    response = custom_llm.get_completion(
        "Tell me a short joke about programming.",
        temperature=0.7,  # Higher temperature for more creativity
    )
    print(f"Response from custom model (temperature=0.7): {response}")


if __name__ == "__main__":
    main()
