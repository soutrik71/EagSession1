from langchain_core.documents import Document
import os
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
import faiss
from client.utils import check_and_reset_index
from dotenv import load_dotenv
import sys

# Add the parent directory (eag_multiserver_mcp) to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)

# Add the current path and project root to the Python path to enable module imports
sys.path.insert(0, current_dir)
sys.path.insert(0, project_root)

# Load environment variables
load_dotenv()

# Clear SSL_CERT_FILE environment variable if set
if "SSL_CERT_FILE" in os.environ:
    del os.environ["SSL_CERT_FILE"]


class ConversationMemory:
    """
    Store and retrieve conversations in a FAISS vector store using conversation IDs.
    Each message is a Document with metadata: conversation_id, sender ('human' or 'ai'), and order.
    """

    def __init__(self, embedder, index_folder="history_index", reset_index=False):
        self.embedder = embedder
        self.index_folder = index_folder
        # Optionally reset the index folder
        check_and_reset_index(self.index_folder, reset_index)
        if not os.path.exists(index_folder):
            sample_embedding = embedder.embed_query("sample text")
            index = faiss.IndexFlatL2(len(sample_embedding))
            self.vector_store = FAISS(
                embedding_function=embedder,
                index=index,
                docstore=InMemoryDocstore(),
                index_to_docstore_id={},
            )
            self.vector_store.save_local(folder_path=index_folder)
        else:
            self.vector_store = FAISS.load_local(
                index_folder, embedder, allow_dangerous_deserialization=True
            )

    def store_conversation(self, conversation_id: str, messages: list[dict]):
        """
        Incrementally store messages for a conversation.
        Each message is a dict: {'sender': 'human'/'ai', 'content': str}
        """
        # Find the current max order for this conversation
        existing_ids = [
            k
            for k in self.vector_store.docstore._dict.keys()
            if k.startswith(conversation_id + "_")
        ]
        if existing_ids:
            # Extract the order numbers and find the max
            existing_orders = [
                int(k.split("_")[-1])
                for k in existing_ids
                if k.split("_")[-1].isdigit()
            ]
            start_order = max(existing_orders) + 1 if existing_orders else 0
        else:
            start_order = 0

        docs = [
            Document(
                page_content=msg["content"],
                metadata={
                    "conversation_id": conversation_id,
                    "sender": msg["sender"],
                    "order": start_order + i,
                },
            )
            for i, msg in enumerate(messages)
        ]
        ids = [f"{conversation_id}_{start_order + i}" for i in range(len(messages))]
        self.vector_store.add_documents(docs, ids=ids)
        self.vector_store.save_local(folder_path=self.index_folder)

    def get_conversation(
        self, conversation_id: str, recency: bool = False
    ) -> list[dict]:
        """
        Retrieve the conversation as a list of dicts with sender and content, ordered.
        """
        # Get all docstore keys for this conversation
        ids = [
            k
            for k in self.vector_store.docstore._dict.keys()
            if k.startswith(conversation_id + "_")
        ]
        docs = self.vector_store.get_by_ids(ids)
        # Sort by order
        docs = sorted(
            [doc for doc in docs if doc is not None],
            key=lambda d: d.metadata.get("order", 0),
        )
        if recency:
            # pass only last 6 messages
            docs = docs[-6:]
        return [
            {"sender": doc.metadata["sender"], "content": doc.page_content}
            for doc in docs
        ]

    def get_conversation_as_lc_messages(
        self, conversation_id: str, recency: bool = False
    ) -> list:
        """
        Return the conversation as a list of LangChain HumanMessage and AIMessage objects, ordered.
        """
        # Get all docstore keys for this conversation
        ids = [
            k
            for k in self.vector_store.docstore._dict.keys()
            if k.startswith(conversation_id + "_")
        ]
        docs = self.vector_store.get_by_ids(ids)
        # Sort by order
        docs = sorted(
            [doc for doc in docs if doc is not None],
            key=lambda d: d.metadata.get("order", 0),
        )
        if recency:
            docs = docs[-6:]
        lc_messages = []
        for doc in docs:
            sender = doc.metadata.get("sender", "human").lower()
            if sender == "human":
                lc_messages.append({"role": "human", "content": doc.page_content})
            elif sender == "ai":
                lc_messages.append({"role": "ai", "content": doc.page_content})
            elif sender == "tool":
                lc_messages.append({"role": "tool", "content": doc.page_content})
            else:
                # fallback: treat as human
                lc_messages.append({"role": "human", "content": doc.page_content})
        return lc_messages

    def count(self) -> int:
        """Return the number of messages stored."""
        return len(self.vector_store.docstore._dict)

    def list_conversation_ids(self) -> list[str]:
        """List all unique conversation IDs stored."""
        ids = self.vector_store.docstore._dict.keys()
        return list(set(k.split("_")[0] for k in ids))


if __name__ == "__main__":
    from client.llm_provider import default_llm
    from client.embedding_provider import OpenAIEmbeddingProvider
    from client.utils import read_yaml_file

    # llm provider
    llm = default_llm.chat_model
    embedder = OpenAIEmbeddingProvider().embeddings

    # read config
    config = read_yaml_file("client/config.yaml")
    print(config)

    history_index_name = config["history_index_name"]
    history_index_name = os.path.join(os.getcwd(), history_index_name)

    memory_store = ConversationMemory(
        embedder, index_folder=history_index_name, reset_index=True
    )

    # test the memory store
    memory_store.store_conversation(
        "test_conversation",
        [
            {"sender": "human", "content": "Hello, how are you?"},
            {"sender": "ai", "content": "I'm good, thank you!"},
            {"sender": "tool", "content": "Tool output"},
        ],
    )

    print(memory_store.get_conversation("test_conversation"))
    print(memory_store.get_conversation_as_lc_messages("test_conversation"))
