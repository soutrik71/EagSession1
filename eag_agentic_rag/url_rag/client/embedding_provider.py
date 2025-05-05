from langchain_ollama import OllamaEmbeddings


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
