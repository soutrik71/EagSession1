"""
Gathering content from the web has a few components:
Search: Query to url (e.g., using GoogleSearchAPIWrapper).
Loading: Url to HTML (e.g., using AsyncHtmlLoader, AsyncChromiumLoader, etc).
Transforming: HTML to formatted text (e.g., using HTML2Text or Beautiful Soup).
"""

# Loader
# AsyncHtmlLoader
# The AsyncHtmlLoader uses the aiohttp library to make asynchronous HTTP requests, suitable for simpler and lightweight scraping.

from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import Html2TextTransformer

# Load the HTML content from the URLs
urls = ["https://weaviate.io/blog/what-are-agentic-workflows"]
loader = AsyncHtmlLoader(urls)
docs = loader.load()
# HTML2Text
# HTML2Text provides a straightforward conversion of HTML content into plain text (with markdown-like formatting) without any specific tag manipulation.

html2text = Html2TextTransformer()
docs_transformed = html2text.transform_documents(docs)


if __name__ == "__main__":
    # Print the transformed documents
    for doc in docs_transformed:
        print(doc.page_content)
        print("\n" + "=" * 80 + "\n")