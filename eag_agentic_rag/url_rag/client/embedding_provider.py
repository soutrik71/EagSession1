from langchain_ollama import OllamaEmbeddings
import os
from langchain_openai import OpenAIEmbeddings
import httpx
from dotenv import load_dotenv

load_dotenv()


class OllamaEmbeddingProvider:
    def __init__(self, model_name: str = "nomic-embed-text:latest"):
        self.model_name = model_name
        self.embeddings = OllamaEmbeddings(model=self.model_name)

    def embed_query(self, text: str):
        """
        Embed a single query string and return the embedding vector.
        """
        return self.embeddings.embed_query(text)

    def embed_documents(self, texts: list):
        """
        Embed a list of documents and return a list of embedding vectors.
        """
        return self.embeddings.embed_documents(texts)


class OpenAIEmbeddingProvider:
    def __init__(
        self,
        model_name: str = "text-embedding-3-small",
        api_key: str = None,
        verify_ssl: bool = False,
    ):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY not set in environment variables or passed to constructor."
            )
        # Create a custom HTTPX client with SSL verification disabled if needed
        if not verify_ssl:
            self.http_client = httpx.Client(verify=False, timeout=120.0)
        else:
            self.http_client = None

        self.embeddings = OpenAIEmbeddings(
            model=self.model_name,
            openai_api_key=self.api_key,
            http_client=self.http_client,
        )

    def embed_query(self, text: str):
        return self.embeddings.embed_query(text)

    def embed_documents(self, texts: list):
        return self.embeddings.embed_documents(texts)
