import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# Clear SSL_CERT_FILE environment variable if set
if "SSL_CERT_FILE" in os.environ:
    del os.environ["SSL_CERT_FILE"]

from utility.utils import read_yaml_file
from utility.embedding_provider import OpenAIEmbeddingProvider
from langchain_community.vectorstores import FAISS


print("Current working directory:", os.getcwd())

yaml_file_path = os.path.join(os.getcwd(), "url_rag", "utility", "config.yaml")
yaml_data = read_yaml_file(yaml_file_path)
embedder = OpenAIEmbeddingProvider().embeddings


index_name = yaml_data["db_index_name"]
index_path = os.path.join(os.getcwd(), "url_rag", index_name)


def get_vector_store(index_name=index_name, embedder=embedder):
    """
    Load a FAISS vector store from the specified index name.

    Args:
        index_name (str): The name of the index to load.
        embedder: The embedding provider to use.

    Returns:
        vector_store: The loaded FAISS vector store.
    """
    path = f"url_rag/{index_name}"
    if not os.path.exists(path):
        print(f"Index folder '{index_name}' does not exist. Creating a new index.")
        raise FileNotFoundError(
            f"Index folder '{index_name}' does not exist and cannot be loaded."
        )
    # Load existing FAISS index
    vector_store = FAISS.load_local(
        path, embedder, allow_dangerous_deserialization=True
    )
    print(f"Loaded existing FAISS index from {index_name} successfully from {path}.")
    return vector_store


def get_retrieved_docs(query, k):
    """
    Retrieve documents from the vector store based on the query and filters.

    Args:
        query (str): The query string to search for.
        k (int): The number of documents to retrieve.

    Returns:
        web_url (list): List of web URLs of the retrieved documents.
        page_content (list): List of page content of the retrieved documents.
    """
    vector_store = get_vector_store()
    docs = vector_store.similarity_search(query=query, k=k)
    web_url = [d.metadata["source"] for d in docs]
    print(f"Retrieved {len(web_url)} documents from the vector store.")
    page_content = [d.page_content for d in docs]
    print(f"Retrieved {len(page_content)} documents from the vector store.")
    return web_url, page_content


if __name__ == "__main__":
    # Example usage
    query = "What is Helm"
    k = 1
    web_url, page_content = get_retrieved_docs(query, k)
    print("Web URLs:", web_url)
    print("Page Content:", page_content)
