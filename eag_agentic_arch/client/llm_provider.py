import os
from dotenv import load_dotenv
from typing import Optional, List, Dict
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage

# Load environment variables from .env file when module is imported
load_dotenv()

# Clear SSL_CERT_FILE environment variable if set
if "SSL_CERT_FILE" in os.environ:
    del os.environ["SSL_CERT_FILE"]


class LLMProvider:
    """Provider for LLM interactions using LangChain's OpenAI implementation."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize the LLM provider.

        Args:
            api_key: OpenAI API key. If None, it will be read from environment variable.
            model: The model to use for completions.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not provided and not found in environment variables"
            )

        self.model = model

        # Initialize LangChain's ChatOpenAI
        self.chat_model = ChatOpenAI(
            model=self.model, openai_api_key=self.api_key, temperature=0
        )

    def get_completion(
        self,
        prompt: str,
        system_message: str = "You are a helpful assistant that provides concise and accurate information.",
        temperature: float = 0.0,
    ) -> str:
        """
        Get a completion from the LLM.

        Args:
            prompt: The user prompt to send to the model ie the human message
            system_message: The system message to set the context.
            temperature: Controls randomness. Lower is more deterministic.

        Returns:
            The model's response text.
        """
        # Create message objects
        messages = [SystemMessage(content=system_message), HumanMessage(content=prompt)]

        # Override temperature if needed
        if temperature != 0.0:
            self.chat_model.temperature = temperature

        # Get response from the model
        response = self.chat_model.invoke(messages)

        return response.content

    def get_completion_with_messages(
        self, messages: List[Dict[str, str]], temperature: float = 0.0
    ) -> str:
        """
        Get a completion from the LLM with custom message format.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
            temperature: Controls randomness. Lower is more deterministic.

        Returns:
            The model's response text.
        """
        # Convert dict messages to LangChain message objects
        langchain_messages = []
        for msg in messages:
            if msg["role"] == "system":
                langchain_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                langchain_messages.append(AIMessage(content=msg["content"]))

        # Override temperature if needed
        if temperature != 0.0:
            self.chat_model.temperature = temperature

        # Get response from the model
        response = self.chat_model.invoke(langchain_messages)

        return response.content


# Create a default instance for easy import
default_llm = LLMProvider()


def get_llm(api_key: Optional[str] = None, model: str = "gpt-4o-mini") -> LLMProvider:
    """
    Get an LLM provider instance.

    Args:
        api_key: OpenAI API key. If None, it will be read from environment variable.
        model: The model to use for completions.

    Returns:
        An LLMProvider instance.
    """
    return LLMProvider(api_key=api_key, model=model)
