from fastmcp import FastMCP, Context
import sys
from pathlib import Path

# Add the tool_utils directory to the path so we can import web_tools
sys.path.append(str(Path(__file__).parent.parent))

# Import web tool classes
from tool_utils.web_tools import DuckDuckGoSearcher, WebContentFetcher

# Import Pydantic models from models.py
from models import SearchInput, SearchOutput, UrlFetchInput, UrlFetchOutput

# Initialize FastMCP server
mcp = FastMCP(name="WebToolsStreamServer")

# Initialize web tool instances outside of tool definitions
# This follows the pattern requested - creating class objects outside tool definitions
duckduckgo_searcher = DuckDuckGoSearcher()
web_content_fetcher = WebContentFetcher()


# ================= Web Tools =================


@mcp.tool()
async def search_web(input: SearchInput, ctx: Context) -> SearchOutput:
    """Search the web using DuckDuckGo for current information. Returns formatted search results with titles, URLs, and snippets. Good for finding current facts, news, or real-time information. Limited to publicly available content."""
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
    """Fetch and extract text content from a webpage URL. Returns clean text content without HTML tags. Good for getting full article content or detailed information from specific pages. Requires valid, accessible URL."""
    await ctx.info("CALLED: fetch_webpage(UrlFetchInput) -> UrlFetchOutput")
    await ctx.info(f"Fetching content from: {input.url} (max {input.max_length} chars)")
    await ctx.report_progress(0, 100, "Starting webpage fetch...")

    try:
        await ctx.report_progress(25, 100, "Downloading webpage...")

        # Use the pre-instantiated fetcher object
        content = await web_content_fetcher.fetch_webpage_content(
            input.url, input.max_length
        )

        await ctx.report_progress(75, 100, "Processing content...")

        # Clean and format the content
        cleaned_content = web_content_fetcher.clean_content(content)

        await ctx.report_progress(100, 100, "Webpage fetch completed!")
        await ctx.info(f"Retrieved {len(cleaned_content)} characters")

        return UrlFetchOutput(content=cleaned_content, success=True, error_message="")
    except Exception as e:
        await ctx.error(f"Webpage fetch failed: {str(e)}")
        return UrlFetchOutput(
            content="", success=False, error_message=f"Fetch failed: {str(e)}"
        )


# ================= Server Entry Point =================

if __name__ == "__main__":
    print("FastMCP 2.0 Web Tools Stream Server starting...")
    print("Available tools:")
    print("- search_web: Search the web using DuckDuckGo")
    print("- fetch_webpage: Fetch content from a webpage")

    # Run with HTTP streaming transport
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=4202,  # Different port from other servers
        log_level="debug",
    )

    print("\nWeb Tools Stream Server shutting down...")
