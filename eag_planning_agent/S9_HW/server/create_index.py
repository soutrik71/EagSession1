#!/usr/bin/env python3
"""
Simple Document Index Creation Script

This script processes documents in the documents folder and creates a FAISS index.
All configuration is read from server_config.yaml.
"""

import sys
from pathlib import Path

# Add the tool_utils directory to the path so we can import doc_tools
sys.path.append(str(Path(__file__).parent.parent))

try:
    from tool_utils.doc_tools import DocumentProcessor, ConfigManager

    # Initialize config manager to look for config in tool_utils directory
    config = ConfigManager()
except ImportError as e:
    print(f"Error: Could not import doc_tools: {e}")
    print("Make sure you're running this script from the correct directory")
    print("and that all dependencies are installed.")
    sys.exit(1)


def create_index():
    """Create document index based on configuration"""
    try:
        # Initialize processor
        processor = DocumentProcessor()

        # Check if documents folder exists
        if not processor.doc_path.exists():
            print(f"Creating documents folder: {processor.doc_path}")
            processor.doc_path.mkdir(parents=True, exist_ok=True)

        # Check for documents
        doc_files = list(processor.doc_path.glob("*.*"))
        if not doc_files:
            print(f"No documents found in {processor.doc_path}")
            print("Please add documents to process.")
            return False

        print(f"Processing {len(doc_files)} documents...")

        # Process documents and create index
        processor.process_documents()

        print("Index creation completed successfully!")
        return True

    except Exception as e:
        print(f"Index creation failed: {e}")
        return False


def main():
    """Main function"""
    print("Document Index Creation")
    print(f"Config: {config.config_path}")
    print(f"Mode: {config.get('processing.mode', 'process')}")

    mode = config.get("processing.mode", "process")

    if mode == "clear":
        processor = DocumentProcessor()
        processor.clear_index()
        print("Index cleared.")
    elif mode == "process":
        create_index()
    else:
        print(f"Unknown mode: {mode}")
        print("Set processing.mode to 'process' or 'clear' in config file")


if __name__ == "__main__":
    main()
