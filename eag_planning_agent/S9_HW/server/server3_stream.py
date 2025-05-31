from fastmcp import FastMCP, Context
from pathlib import Path
import sys

# Add the tool_utils directory to the path so we can import doc_tools
sys.path.append(str(Path(__file__).parent.parent))

# Import document processor from tool_utils
from tool_utils.doc_tools import DocumentProcessor, ConfigManager

# Import Pydantic models from models.py
from models import DocumentSearchInput, DocumentSearchOutput, DocumentSearchResult

# Initialize FastMCP server
mcp = FastMCP(name="DocumentSearchStreamServer")

# Initialize document processor and config outside of tool definitions
config = ConfigManager()
document_processor = DocumentProcessor()


# ================= Document Query Tool =================


@mcp.tool()
async def query_documents(
    input: DocumentSearchInput, ctx: Context
) -> DocumentSearchOutput:
    """
    Query and retrieve relevant documents using semantic search from indexed knowledge base.

    **Primary Use Cases:**
    - Finding information from processed documents and knowledge base
    - Searching through previously uploaded PDFs, documents, and files
    - Getting specific information from organizational knowledge
    - Retrieving context-relevant content from document collections
    - Answering questions based on indexed document content

    **Available Document Topics & Collections:**
    - **Sports & Cricket:** Player statistics, match data, cricket history and analysis
    - **DLF Constructions:** Company information, project details, construction industry data
    - **Economics:** Economic theories, market analysis, financial concepts and data
    - **Indian Policies & Government Schemes:** Policy documents, government programs,
      regulations, and administrative information
    - **Tesla Motors & Carbon Crisis:** Tesla's intellectual property, carbon emission reports,
      environmental impact studies, and related technological information

    **When to Use:**
    - Questions about specific topics covered in the knowledge base
    - Looking for detailed information from uploaded documents
    - Need for authoritative content from processed files
    - Searching for specific facts, figures, or concepts from documents
    - When web search might not have specialized/internal information

    **Search Capabilities:**
    - **Semantic Search:** Understands context and meaning, not just keywords
    - **Relevance Ranking:** Results ordered by similarity and relevance scores
    - **Multi-document Search:** Searches across entire indexed collection
    - **Chunk-based Results:** Returns specific relevant sections with source information

    **Examples of Effective Queries:**
    - "What are the key features of the Pradhan Mantri Awas Yojana scheme?"
    - "Tesla's approach to reducing carbon emissions in manufacturing"
    - "DLF's major construction projects in Delhi NCR"
    - "Economic impact of inflation on Indian markets"
    - "Top cricket players' performance statistics"
    - "Government policies for rural development in India"

    **Output Format:**
    - Ranked document chunks with relevance scores
    - Source file information for each result
    - Specific content sections most relevant to query
    - Success/failure status with detailed error information

    **Search Parameters:**
    - **top_k:** Number of most relevant results to return (default: 5)
    - Automatic index checking and creation if needed
    - Configurable search parameters through system config

    **Performance Features:**
    - Automatic index creation if documents exist but no index found
    - Intelligent caching for faster repeated searches
    - Error recovery and helpful diagnostic messages

    **Limitations:**
    - Only searches indexed documents (not real-time web content)
    - Requires documents to be pre-processed and indexed
    - Results limited to content quality and coverage of indexed files
    - No access to documents outside the indexed collection

    **Best for:** Knowledge base queries, document research, finding specific information
    from organizational/uploaded content, policy and technical documentation searches.
    """
    await ctx.info(f"DOC_SEARCH: '{input.query}' (top {input.top_k} results)")

    try:
        # Step 1: Check if index exists
        index_exists = (
            document_processor.index_file.exists()
            and document_processor.metadata_file.exists()
            and document_processor.cache_file.exists()
        )

        if not index_exists:
            await ctx.warning("DOC_SEARCH: Index not found, checking for documents...")

            # Check if documents exist to process
            doc_files = (
                list(document_processor.doc_path.glob("*.*"))
                if document_processor.doc_path.exists()
                else []
            )

            if not doc_files:
                await ctx.error(
                    "DOC_SEARCH ERROR: No documents found and no index available"
                )
                return DocumentSearchOutput(
                    results=[],
                    total_results=0,
                    query=input.query,
                    success=False,
                    error_message="No documents found in documents folder and no existing index. "
                    "Please add documents and run create_index.py",
                )

            await ctx.info(
                f"DOC_SEARCH: Found {len(doc_files)} documents, creating index..."
            )

            # Process documents to create index
            document_processor.process_documents()
            await ctx.info("DOC_SEARCH: Index created successfully")

        # Step 2: Get search configuration
        config_top_k = config.get("search.top_k", 5)
        effective_top_k = (
            input.top_k if input.top_k != 5 else config_top_k
        )  # 5 is default in model

        # Step 3: Perform semantic search
        search_results = document_processor.search_documents(input.query)

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

        await ctx.info(
            f"DOC_SEARCH RESULT: Found {len(result_models)} relevant chunks from {len(search_results)} total matches"
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
        await ctx.error(f"DOC_SEARCH ERROR: {str(e)}")
        return DocumentSearchOutput(
            results=[],
            total_results=0,
            query=input.query,
            success=False,
            error_message=f"Query failed: {str(e)}",
        )


# ================= Server Entry Point =================

if __name__ == "__main__":
    print("FastMCP 2.0 Document Search Stream Server starting...")
    print("Available tools:")
    print(
        "- query_documents: Semantic search through indexed knowledge base with automatic index management"
    )

    print("\nConfiguration:")
    print(f"- Documents folder: {document_processor.doc_path}")
    print(f"- Index cache: {document_processor.index_cache}")
    print(f"- Config file: {config.config_path}")
    print(f"- Default top_k: {config.get('search.top_k', 5)}")

    # Run with HTTP streaming transport
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=4203,  # Different port from other servers
        log_level="info",  # Reduced from debug to minimize verbosity
    )

    print("\nDocument Search Stream Server shutting down...")
