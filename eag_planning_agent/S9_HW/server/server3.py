from fastmcp import FastMCP, Context
import sys
from pathlib import Path

# Add the tool_utils directory to the path so we can import doc_tools
sys.path.append(str(Path(__file__).parent.parent))

# Import document processor from tool_utils
from tool_utils.doc_tools import DocumentProcessor, ConfigManager

# Import Pydantic models from models.py
from models import DocumentSearchInput, DocumentSearchOutput, DocumentSearchResult

# Initialize FastMCP server
mcp = FastMCP(name="DocumentSearchServer")

# Initialize document processor and config outside of tool definitions
config = ConfigManager()
document_processor = DocumentProcessor()


# ================= Single Document Query Tool =================


@mcp.tool()
async def query_documents(
    input: DocumentSearchInput, ctx: Context
) -> DocumentSearchOutput:
    """Query and retrieve relevant documents using semantic search with automatic index checking"""
    await ctx.info(
        "CALLED: query_documents(DocumentSearchInput) -> DocumentSearchOutput"
    )
    await ctx.info(f"Querying for: '{input.query}' (top {input.top_k} results)")
    await ctx.report_progress(0, 100, "Starting document query...")

    try:
        # Step 1: Check if index exists
        await ctx.report_progress(20, 100, "Checking index availability...")

        index_exists = (
            document_processor.index_file.exists()
            and document_processor.metadata_file.exists()
            and document_processor.cache_file.exists()
        )

        if not index_exists:
            await ctx.warning("Index not found - attempting to create index...")
            await ctx.report_progress(
                30, 100, "Index not found, checking for documents..."
            )

            # Check if documents exist to process
            doc_files = (
                list(document_processor.doc_path.glob("*.*"))
                if document_processor.doc_path.exists()
                else []
            )

            if not doc_files:
                await ctx.error("No documents found and no index available")
                return DocumentSearchOutput(
                    results=[],
                    total_results=0,
                    query=input.query,
                    success=False,
                    error_message="No documents found in documents folder and no existing index. "
                    "Please add documents and run create_index.py",
                )

            await ctx.info(
                f"Found {len(doc_files)} documents - processing to create index..."
            )
            await ctx.report_progress(
                40, 100, "Processing documents to create index..."
            )

            # Process documents to create index
            document_processor.process_documents()
            await ctx.info("Index created successfully")

        # Step 2: Get search configuration from config
        await ctx.report_progress(60, 100, "Reading search configuration...")

        # Use top_k from config if not specified in input, otherwise use input value
        config_top_k = config.get("search.top_k", 5)
        effective_top_k = (
            input.top_k if input.top_k != 5 else config_top_k
        )  # 5 is default in model

        await ctx.info(f"Using top_k: {effective_top_k} (config: {config_top_k})")

        # Step 3: Perform semantic search
        await ctx.report_progress(70, 100, "Performing semantic search...")

        search_results = document_processor.search_documents(input.query)

        await ctx.report_progress(85, 100, "Processing search results...")

        # Limit results to requested top_k
        limited_results = search_results[:effective_top_k]

        # Convert to Pydantic models
        result_models = []
        for result in limited_results:
            result_model = DocumentSearchResult(
                chunk=result.chunk,
                source=result.source,
                chunk_id=result.chunk_id,
                score=result.score,
            )
            result_models.append(result_model)

        await ctx.report_progress(100, 100, "Query completed!")
        await ctx.info(
            f"Found {len(result_models)} results out of {len(search_results)} total matches"
        )

        # Add index status info to success message
        import json

        metadata = json.loads(document_processor.metadata_file.read_text())
        cache_data = json.loads(document_processor.cache_file.read_text())

        status_message = (
            f"Search completed successfully. Index contains {len(metadata)} "
            f"chunks from {len(cache_data)} files."
        )

        return DocumentSearchOutput(
            results=result_models,
            total_results=len(search_results),
            query=input.query,
            success=True,
            error_message=status_message,
        )

    except Exception as e:
        await ctx.error(f"Document query failed: {str(e)}")
        return DocumentSearchOutput(
            results=[],
            total_results=0,
            query=input.query,
            success=False,
            error_message=f"Query failed: {str(e)}",
        )


# ================= Server Entry Point =================

if __name__ == "__main__":
    print("FastMCP 2.0 Document Query Server starting...")
    print("Available tools:")
    print(
        "- query_documents: Query and retrieve relevant documents with automatic index checking"
    )

    print("\nConfiguration:")
    print(f"- Documents folder: {document_processor.doc_path}")
    print(f"- Index cache: {document_processor.index_cache}")
    print(f"- Config file: {config.config_path}")
    print(f"- Default top_k: {config.get('search.top_k', 5)}")

    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        print("Running in development mode")
        mcp.run()  # Run without transport for dev server
    else:
        print("Running with stdio transport")
        mcp.run(transport="stdio")  # Run with stdio for direct execution

    print("Server shutting down...")
