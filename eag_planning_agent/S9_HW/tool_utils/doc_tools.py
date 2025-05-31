"""
Document Processing Pipeline with OpenAI Integration

Recreated from original mcp_server_2.py to use OpenAI models instead of Ollama.
Provides document extraction, semantic chunking, FAISS indexing, and search functionality.
All configuration is handled through server_config.yaml file.
"""

import sys
import os
import json
import faiss
import numpy as np
from pathlib import Path
from tqdm import tqdm
import hashlib
import re
from typing import List, Dict, Any
from dataclasses import dataclass
import yaml

# Import our LLM utilities
from .llm_utils import LLMUtils

# External libraries for document processing
try:
    from markitdown import MarkItDown
    import trafilatura
    import pymupdf4llm
except ImportError as e:
    print(f"Warning: Some optional dependencies not found: {e}")
    print("Install with: pip install markitdown trafilatura pymupdf4llm pillow PyYAML")


class ConfigManager:
    """Manages configuration loading and access"""

    def __init__(self, config_path: str = "server_config.yaml"):
        # Look for config file in the same directory as this file
        self.config_path = Path(__file__).parent / config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            print(f"Warning: Config file {self.config_path} not found. Using defaults.")
            return self._get_default_config()
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}. Using defaults.")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration if file is not found"""
        return {
            "paths": {
                "root_dir": ".",
                "documents_dir": "documents",
                "index_cache_dir": "faiss_index",
                "images_dir": "images",
                "files": {
                    "index_file": "index.bin",
                    "metadata_file": "metadata.json",
                    "cache_file": "doc_index_cache.json",
                },
            },
            "text_processing": {
                "chunk_size": 256,
                "chunk_overlap": 40,
                "semantic_word_limit": 512,
                "min_words_for_semantic": 10,
                "supported_extensions": {
                    "pdf": [".pdf"],
                    "web": [".html", ".htm", ".url"],
                },
            },
            "search": {"top_k": 5},
            "extraction": {
                "pdf": {"write_images": True},
                "webpage": {"output_format": "markdown"},
                "images": {"delete_after_caption": True, "caption_placeholder": True},
            },
            "logging": {"level": "INFO", "output": "stderr"},
            "processing": {
                "mode": "process",
                "force_rebuild": False,
                "skip_unchanged": True,
                "show_progress": True,
                "continue_on_error": True,
                "search_query": "",
            },
        }

    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation"""
        keys = key_path.split(".")
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value


# Global configuration instance
config = ConfigManager()
ROOT = Path(__file__).parent.parent.resolve() / config.get("paths.root_dir", ".")


@dataclass
class SearchResult:
    """Result from document search"""

    chunk: str
    source: str
    chunk_id: str
    score: float


class DocumentProcessor:
    """Main document processing class using OpenAI models"""

    def __init__(self):
        """Initialize with OpenAI models and configuration"""
        try:
            self.llm_utils = LLMUtils()
            self.chat_model = self.llm_utils.chat_model
            self.embedding_model = self.llm_utils.embedding_model
        except Exception as e:
            print(f"Error initializing LLM models: {e}")
            raise

        # Setup paths from configuration
        self.doc_path = ROOT / config.get("paths.documents_dir", "documents")
        self.index_cache = ROOT / config.get("paths.index_cache_dir", "faiss_index")
        self.index_cache.mkdir(exist_ok=True)

        # File paths
        self.index_file = self.index_cache / config.get(
            "paths.files.index_file", "index.bin"
        )
        self.metadata_file = self.index_cache / config.get(
            "paths.files.metadata_file", "metadata.json"
        )
        self.cache_file = self.index_cache / config.get(
            "paths.files.cache_file", "doc_index_cache.json"
        )

    def _log(self, level: str, message: str) -> None:
        """Helper function for logging"""
        log_level = config.get("logging.level", "INFO")
        if self._should_log(level, log_level):
            output = config.get("logging.output", "stderr")
            if output == "stderr":
                sys.stderr.write(f"{level}: {message}\n")
                sys.stderr.flush()
            else:
                print(f"{level}: {message}")

    def _should_log(self, level: str, config_level: str) -> bool:
        """Check if message should be logged based on level"""
        levels = {"DEBUG": 0, "INFO": 1, "WARN": 2, "ERROR": 3}
        return levels.get(level, 1) >= levels.get(config_level, 1)

    def _file_hash(self, path: Path) -> str:
        """Helper function to compute file hash"""
        return hashlib.md5(path.read_bytes()).hexdigest()

    def _get_embedding(self, text: str) -> np.ndarray:
        """Helper function to get embeddings using OpenAI"""
        try:
            embedding = self.embedding_model.embed_query(text)
            return np.array(embedding, dtype=np.float32)
        except Exception as e:
            self._log("ERROR", f"Failed to get embedding: {e}")
            raise

    def _chunk_text(self, text: str) -> List[str]:
        """Helper function for basic text chunking"""
        size = config.get("text_processing.chunk_size", 256)
        overlap = config.get("text_processing.chunk_overlap", 40)

        words = text.split()
        chunks = []
        for i in range(0, len(words), size - overlap):
            chunk = " ".join(words[i : i + size])
            chunks.append(chunk)
        return chunks

    def _caption_image(self, img_path: str) -> str:
        """Helper function to caption images"""
        full_path = self.doc_path / img_path

        if not full_path.exists():
            self._log("ERROR", f"Image file not found: {full_path}")
            return f"[Image file not found: {img_path}]"

        try:
            if config.get("extraction.images.caption_placeholder", True):
                self._log("INFO", f"Image captioning placeholder for: {img_path}")
                return f"[Image: {img_path.split('/')[-1]}]"
        except Exception as e:
            self._log("ERROR", f"Failed to caption image {img_path}: {e}")
            return f"[Image could not be processed: {img_path}]"

    def _replace_images_with_captions(self, markdown: str) -> str:
        """Helper function to replace image references with captions"""

        def replace(match):
            alt, src = match.group(1), match.group(2)
            try:
                caption = self._caption_image(src)
                if config.get(
                    "extraction.images.delete_after_caption", True
                ) and not src.startswith("http"):
                    img_path = self.doc_path / src
                    if img_path.exists():
                        img_path.unlink()
                        self._log("INFO", f"Deleted image after captioning: {img_path}")
                return f"**Image:** {caption}"
            except Exception as e:
                self._log("WARN", f"Image processing failed: {e}")
                return f"[Image could not be processed: {src}]"

        return re.sub(r"!\[(.*?)\]\((.*?)\)", replace, markdown)

    def _semantic_merge(self, text: str) -> List[str]:
        """Helper function for semantic text chunking using OpenAI"""
        word_limit = config.get("text_processing.semantic_word_limit", 512)
        words = text.split()
        i = 0
        final_chunks = []

        while i < len(words):
            chunk_words = words[i : i + word_limit]
            chunk_text = " ".join(chunk_words).strip()

            prompt = f"""
You are a markdown document segmenter.

Here is a portion of a markdown document:

---
{chunk_text}
---

If this chunk clearly contains **more than one distinct topic or section**,
reply ONLY with the **second part**, starting from the first sentence or
heading of the new topic.

If it's only one topic, reply with NOTHING.

Keep markdown formatting intact.
"""

            try:
                response = self.chat_model.invoke(prompt)
                reply = response.content.strip()

                if reply:
                    split_point = chunk_text.find(reply)
                    if split_point != -1:
                        first_part = chunk_text[:split_point].strip()
                        second_part = reply.strip()
                        final_chunks.append(first_part)

                        leftover_words = second_part.split()
                        words = leftover_words + words[i + word_limit :]
                        i = 0
                        continue
                    else:
                        final_chunks.append(chunk_text)
                else:
                    final_chunks.append(chunk_text)

            except Exception as e:
                self._log("ERROR", f"Semantic chunking LLM error: {e}")
                final_chunks.append(chunk_text)

            i += word_limit

        return final_chunks

    def extract_pdf(self, file_path: str) -> str:
        """Extract PDF content to markdown"""
        if not os.path.exists(file_path):
            return f"File not found: {file_path}"

        images_dir = config.get("paths.images_dir", "images")
        global_image_dir = self.doc_path / images_dir
        global_image_dir.mkdir(parents=True, exist_ok=True)

        try:
            pdf_config = config.get("extraction.pdf", {})
            markdown = pymupdf4llm.to_markdown(
                file_path,
                write_images=pdf_config.get("write_images", True),
                image_path=str(global_image_dir),
            )

            # Re-point image links
            markdown = re.sub(
                rf"!\[\]\((.*?/{images_dir}/)([^)]+)\)",
                rf"![]({images_dir}/\2)",
                markdown.replace("\\", "/"),
            )

            return self._replace_images_with_captions(markdown)
        except Exception as e:
            self._log("ERROR", f"Failed to extract PDF {file_path}: {e}")
            return f"Error extracting PDF: {e}"

    def extract_webpage(self, url: str) -> str:
        """Extract webpage content to markdown"""
        try:
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return "Failed to download the webpage."

            webpage_config = config.get("extraction.webpage", {})
            markdown = (
                trafilatura.extract(
                    downloaded,
                    include_comments=webpage_config.get("include_comments", False),
                    include_tables=webpage_config.get("include_tables", True),
                    include_images=webpage_config.get("include_images", True),
                    output_format=webpage_config.get("output_format", "markdown"),
                )
                or ""
            )

            return self._replace_images_with_captions(markdown)
        except Exception as e:
            self._log("ERROR", f"Failed to extract webpage {url}: {e}")
            return f"Error extracting webpage: {e}"

    def clear_index(self) -> None:
        """Clear existing FAISS index and cache files"""
        try:
            files_to_remove = [self.index_file, self.metadata_file, self.cache_file]
            for file_path in files_to_remove:
                if file_path.exists():
                    file_path.unlink()
                    self._log("INFO", f"Deleted {file_path.name}")
            self._log("INFO", "Index cleared successfully")
        except Exception as e:
            self._log("ERROR", f"Failed to clear index: {e}")

    def process_documents(self) -> None:
        """Process documents and create FAISS index"""
        force_rebuild = config.get("processing.force_rebuild", False)

        if force_rebuild:
            self._log("INFO", "Force rebuild requested - clearing existing index")
            self.clear_index()

        self._log("INFO", "Indexing documents with OpenAI models...")
        self.doc_path.mkdir(exist_ok=True)

        # Load existing data
        cache_meta = (
            json.loads(self.cache_file.read_text()) if self.cache_file.exists() else {}
        )
        metadata = (
            json.loads(self.metadata_file.read_text())
            if self.metadata_file.exists()
            else []
        )
        index = (
            faiss.read_index(str(self.index_file)) if self.index_file.exists() else None
        )

        files = list(self.doc_path.glob("*.*"))
        if not files:
            self._log("WARN", f"No files found in {self.doc_path}")
            return

        # Get configuration
        pdf_extensions = config.get(
            "text_processing.supported_extensions.pdf", [".pdf"]
        )
        web_extensions = config.get(
            "text_processing.supported_extensions.web", [".html", ".htm", ".url"]
        )
        min_words = config.get("text_processing.min_words_for_semantic", 10)
        skip_unchanged = config.get("processing.skip_unchanged", True)
        show_progress = config.get("processing.show_progress", True)

        for file in files:
            fhash = self._file_hash(file)

            if (
                not force_rebuild
                and skip_unchanged
                and file.name in cache_meta
                and cache_meta[file.name] == fhash
            ):
                self._log("SKIP", f"Skipping unchanged file: {file.name}")
                continue

            self._log("PROC", f"Processing: {file.name}")
            try:
                ext = file.suffix.lower()
                markdown = ""

                if ext in pdf_extensions:
                    self._log("INFO", f"Using PyMuPDF4LLM to extract {file.name}")
                    markdown = self.extract_pdf(str(file))
                elif ext in web_extensions:
                    self._log("INFO", f"Using Trafilatura to extract {file.name}")
                    url = file.read_text().strip()
                    markdown = self.extract_webpage(url)
                else:
                    try:
                        converter = MarkItDown()
                        self._log("INFO", f"Using MarkItDown fallback for {file.name}")
                        markdown = converter.convert(str(file)).text_content
                    except Exception as e:
                        self._log("WARN", f"MarkItDown failed for {file.name}: {e}")
                        if not config.get("processing.continue_on_error", True):
                            raise
                        continue

                if not markdown.strip():
                    self._log("WARN", f"No content extracted from {file.name}")
                    continue

                # Chunk the content
                if len(markdown.split()) < min_words:
                    self._log(
                        "WARN", f"Content too short for semantic merge in {file.name}"
                    )
                    chunks = [markdown.strip()]
                else:
                    self._log("INFO", f"Running semantic merge on {file.name}")
                    chunks = self._semantic_merge(markdown)

                # Generate embeddings
                embeddings_for_file = []
                new_metadata = []

                chunk_iter = enumerate(chunks)
                if show_progress:
                    chunk_iter = enumerate(tqdm(chunks, desc=f"Embedding {file.name}"))

                for i, chunk in chunk_iter:
                    if not chunk.strip():
                        continue
                    embedding = self._get_embedding(chunk)
                    embeddings_for_file.append(embedding)
                    new_metadata.append(
                        {
                            "doc": file.name,
                            "chunk": chunk,
                            "chunk_id": f"{file.stem}_{i}",
                        }
                    )

                if embeddings_for_file:
                    if index is None:
                        dim = len(embeddings_for_file[0])
                        index = faiss.IndexFlatL2(dim)
                    index.add(np.stack(embeddings_for_file))
                    metadata.extend(new_metadata)
                    cache_meta[file.name] = fhash

                    # Save everything
                    self.cache_file.write_text(json.dumps(cache_meta, indent=2))
                    self.metadata_file.write_text(json.dumps(metadata, indent=2))
                    faiss.write_index(index, str(self.index_file))
                    self._log("SAVE", f"Saved index after processing {file.name}")

            except Exception as e:
                self._log("ERROR", f"Failed to process {file.name}: {e}")
                if not config.get("processing.continue_on_error", True):
                    raise

    def search_documents(self, query: str) -> List[SearchResult]:
        """Search documents using FAISS index"""
        top_k = config.get("search.top_k", 5)
        self._ensure_faiss_ready()

        self._log("SEARCH", f"Query: {query}")
        try:
            index = faiss.read_index(str(self.index_file))
            metadata = json.loads(self.metadata_file.read_text())

            query_vec = self._get_embedding(query).reshape(1, -1)
            distances, indices = index.search(query_vec, k=top_k)

            results = []
            for i, idx in enumerate(indices[0]):
                if idx != -1:
                    data = metadata[idx]
                    results.append(
                        SearchResult(
                            chunk=data["chunk"],
                            source=data["doc"],
                            chunk_id=data["chunk_id"],
                            score=float(distances[0][i]),
                        )
                    )
            return results
        except Exception as e:
            self._log("ERROR", f"Failed to search: {e}")
            return []

    def _ensure_faiss_ready(self) -> None:
        """Helper function to ensure FAISS index is ready"""
        if not (self.index_file.exists() and self.metadata_file.exists()):
            self._log("INFO", "Index not found — running process_documents()...")
            self.process_documents()
        else:
            self._log("INFO", "Index already exists.")


def main():
    """Main function that runs based on configuration"""
    print("Document Processing Pipeline with OpenAI models")
    print(f"Configuration loaded from: {config.config_path}")

    processor = DocumentProcessor()
    mode = config.get("processing.mode", "process")

    if mode == "clear":
        print("Clearing existing index...")
        processor.clear_index()
        print("Index cleared successfully.")

    elif mode == "search":
        query = config.get("processing.search_query", "")
        if not query:
            print("Error: No search query specified in config file.")
            print("Set 'processing.search_query' in server_config.yaml")
            return

        print(f"Searching for: {query}")
        results = processor.search_documents(query)

        for i, result in enumerate(results, 1):
            print(f"\n--- Result {i} ---")
            print(f"{result.chunk}")
            print(
                f"[Source: {result.source}, ID: {result.chunk_id}, Score: {result.score:.4f}]"
            )

    else:  # mode == 'process' or default
        print("Processing documents...")
        processor.process_documents()
        print("Documents processed successfully!")


if __name__ == "__main__":
    main()
