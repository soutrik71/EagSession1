from fastmcp import FastMCP, Context
import sys

# Import web tool classes
from tool_utils.web_tools import DuckDuckGoSearcher, WebContentFetcher

# Import Pydantic models from models.py
from models import SearchInput, SearchOutput, UrlFetchInput, UrlFetchOutput

# Initialize FastMCP server
mcp = FastMCP(name="WebToolsServer")

# Initialize web tool instances outside of tool definitions
# This follows the pattern requested - creating class objects outside tool definitions
duckduckgo_searcher = DuckDuckGoSearcher()
web_content_fetcher = WebContentFetcher()


# ================= Web Tools =================


@mcp.tool()
async def search_web(input: SearchInput, ctx: Context) -> SearchOutput:
    """Search the web using DuckDuckGo and return formatted results"""
    await ctx.info("CALLED: search_web(SearchInput) -> SearchOutput")
    await ctx.info(f"Searching for: '{input.query}' (max {input.max_results} results)")
    await ctx.report_progress(0, 100, "Starting web search...")

    try:
        await ctx.report_progress(25, 100, "Performing DuckDuckGo search...")

        # Use the pre-instantiated searcher object
        search_results = await duckduckgo_searcher.search(
            input.query, input.max_results
        )

        await ctx.report_progress(75, 100, "Formatting results...")

        # Format results using the searcher's built-in formatter
        formatted_results = duckduckgo_searcher.format_results_for_llm(search_results)

        await ctx.report_progress(100, 100, "Search completed!")
        await ctx.info(f"Found {len(search_results)} results")

        return SearchOutput(results=formatted_results, success=True, error_message="")
    except Exception as e:
        await ctx.error(f"Web search failed: {str(e)}")
        return SearchOutput(
            results="", success=False, error_message=f"Search failed: {str(e)}"
        )


@mcp.tool()
async def fetch_webpage(input: UrlFetchInput, ctx: Context) -> UrlFetchOutput:
    """Fetch and extract text content from a webpage"""
    await ctx.info("CALLED: fetch_webpage(UrlFetchInput) -> UrlFetchOutput")
    await ctx.info(f"Fetching content from: {input.url}")
    await ctx.report_progress(0, 100, "Starting URL fetch...")

    try:
        await ctx.report_progress(25, 100, "Downloading webpage...")

        # Use the pre-instantiated web content fetcher object
        content = await web_content_fetcher.fetch_and_parse(input.url)

        await ctx.report_progress(75, 100, "Processing content...")

        # Truncate if needed based on input parameter
        if len(content) > input.max_length:
            content = content[: input.max_length] + "... [truncated]"

        await ctx.report_progress(100, 100, "Content fetched successfully!")
        await ctx.info(f"Fetched {len(content)} characters")

        return UrlFetchOutput(content=content, success=True, error_message="")
    except Exception as e:
        await ctx.error(f"URL fetch failed: {str(e)}")
        return UrlFetchOutput(
            content="", success=False, error_message=f"Fetch failed: {str(e)}"
        )


# ================= Server Entry Point =================

if __name__ == "__main__":
    print("FastMCP 2.0 Web Tools Server starting...")
    print("Available tools:")
    print("- search_web: Search the web using DuckDuckGo")
    print("- fetch_webpage: Fetch content from a webpage")

    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        print("Running in development mode")
        mcp.run()  # Run without transport for dev server
    else:
        print("Running with stdio transport")
        mcp.run(transport="stdio")  # Run with stdio for direct execution

    print("\nServer shutting down...")
