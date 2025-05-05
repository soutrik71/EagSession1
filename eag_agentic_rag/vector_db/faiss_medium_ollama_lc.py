from langchain_ollama import OllamaEmbeddings
import faiss
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
import os
import pickle
import json

# Original Corpus of jokes with metadata
jokes = [
    {
        "id": 1,
        "category": "animals",
        "text": "Why don't cows have any money? Because farmers milk them dry.",
    },
    {
        "id": 2,
        "category": "tech",
        "text": "Why do programmers prefer dark mode? Because light attracts bugs.",
    },
    {
        "id": 3,
        "category": "school",
        "text": "Why did the student eat his homework? Because the teacher said it was a piece of cake.",
    },
    {
        "id": 4,
        "category": "classic",
        "text": "I told my wife she was drawing her eyebrows too high. She looked surprised.",
    },
    {
        "id": 5,
        "category": "tech",
        "text": "How do you comfort a JavaScript bug? You console it.",
    },
]

# convert each into a Document class
lc_docs = [
    Document(page_content=j["text"], metadata={"category": j["category"]})
    for j in jokes
]
# create a list of ids
lc_ids = [str(j["id"]) for j in jokes]
# embedding function
embeddings = OllamaEmbeddings(model="nomic-embed-text:latest")
op = embeddings.embed_query("Hello, world!")
# Check the length of the embedding
print(f"🔢 Vector length: {len(op)}")

# create a FAISS index and add documents
index = faiss.IndexFlatL2(len(op))
vector_store = FAISS(
    embedding_function=embeddings,
    index=index,
    docstore=InMemoryDocstore(),
    index_to_docstore_id={},
)
# add documents to the vector store
ids = vector_store.add_documents(documents=lc_docs, ids=lc_ids)
print(f"Added {len(ids)} documents to the vector store.")

# create a folder to store the index
os.makedirs("faiss_index", exist_ok=True)
# You can also save and load a FAISS index
vector_store.save_local(folder_path="faiss_index")
# Load the FAISS index
vector_store2 = FAISS.load_local(
    "faiss_index", embeddings, allow_dangerous_deserialization=True
)

# add one more document to the vector store
new_doc = Document(
    page_content="Why did the computer go to the doctor? Because it had a virus.",
    metadata={"category": "tech"},
)
new_id = "6"
vector_store2.add_documents(documents=[new_doc], ids=[new_id])
print(f"Added {len([new_doc])} documents to the vector store.")

# Save the updated index
vector_store2.save_local(folder_path="faiss_index")


if __name__ == "__main__":
    query = "Something about software engineers and debugging."

    results = vector_store.similarity_search(query, k=3)
    print("Results from the original vector store:")
    for result in results:
        print(f"category: {result.metadata['category']}")
        print(f"Text: {result.page_content}")
        print("\n\n")

    results2 = vector_store2.similarity_search(query, k=3)
    print("Results from the loaded vector store:")
    for result in results2:
        print(f"category: {result.metadata['category']}")
        print(f"Text: {result.page_content}")
        print("\n\n")
