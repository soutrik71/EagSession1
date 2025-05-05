import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables from .env file
load_dotenv()


class LLMProvider:
    """Simple provider for LLM interactions using LangChain's OpenAI implementation."""

    def __init__(self, api_key: str = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not provided and not found in environment variables"
            )
        self.model = model
        self.chat_model = ChatOpenAI(
            model=self.model,
            openai_api_key=self.api_key,
            temperature=0,
        )

    def get_completion(self, system_message: str, user_prompt: str) -> str:
        from langchain.schema import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt),
        ]
        response = self.chat_model.invoke(messages)
        return response.content


# Create a default instance for easy import
default_llm = LLMProvider()
