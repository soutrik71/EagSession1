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
    """
    Search the web using DuckDuckGo for current, real-time information.

    **Primary Use Cases:**
    - Finding current news, events, and breaking information
    - Looking up real-time data (stock prices, weather, sports scores)
    - Getting recent information that may not be in training data
    - Fact-checking and verification of current claims
    - Finding specific recent articles, press releases, or announcements

    **When to Use:**
    - Questions about "current", "latest", "recent", "today", "now"
    - Time-sensitive information queries
    - Market data, news events, product launches
    - Verification of contemporary facts or claims
    - Finding specific organizations, people, or recent developments

    **Examples:**
    - "What is the current stock price of Tesla?"
    - "Latest news about climate change policies"
    - "Recent developments in AI technology"
    - "Current weather in New York"
    - "Latest earnings report for Apple"

    **Output Format:**
    - Structured results with titles, URLs, and content snippets
    - Limited to publicly available web content
    - Results ranked by relevance and recency

    **Limitations:**
    - No access to private/password-protected content
    - Results depend on DuckDuckGo's index
    - May not return results for very new information (< few hours)

    **Best for:** Current events, real-time data, recent information, fact verification.
    """
    await ctx.info(f"WEB_SEARCH: '{input.query}' (max {input.max_results} results)")

    try:
        # Use the pre-instantiated searcher object
        search_results = await duckduckgo_searcher.search(
            input.query, input.max_results
        )

        # Format results using the searcher's built-in formatter
        formatted_results = duckduckgo_searcher.format_results_for_llm(search_results)

        await ctx.info(f"WEB_SEARCH RESULT: Found {len(search_results)} results")

        return SearchOutput(results=formatted_results, success=True, error_message="")
    except Exception as e:
        await ctx.error(f"WEB_SEARCH ERROR: {str(e)}")
        return SearchOutput(
            results="", success=False, error_message=f"Search failed: {str(e)}"
        )


@mcp.tool()
async def fetch_webpage(input: UrlFetchInput, ctx: Context) -> UrlFetchOutput:
    """
    Fetch and extract clean text content from any accessible webpage URL.

    **Primary Use Cases:**
    - Reading full articles, blog posts, or detailed content
    - Extracting text from specific web pages for analysis
    - Getting complete content when search results point to relevant pages
    - Following up on URLs found through web search
    - Reading documentation, research papers, or reports online

    **When to Use:**
    - When you have a specific URL and need its content
    - Following links from search results for detailed information
    - Extracting content from news articles, blogs, or research papers
    - Getting full text from pages found via web search
    - Reading online documentation or reference materials

    **Content Processing:**
    - Removes HTML tags, ads, and navigation elements
    - Extracts main text content only
    - Handles various webpage formats and structures
    - Respects content length limits for efficient processing

    **Examples:**
    - fetch_webpage("https://example.com/article") → clean article text
    - Reading a news article found through web search
    - Extracting content from a research paper PDF link
    - Getting full blog post content for analysis

    **Input Requirements:**
    - Valid, accessible URL (http:// or https://)
    - URL must be publicly accessible (no login required)
    - Target page should contain readable text content

    **Output:**
    - Clean, readable text without HTML formatting
    - Trimmed to max_length characters if content is very long
    - Success/failure status with error details if applicable

    **Limitations:**
    - Cannot access password-protected content
    - Some sites may block automated access
    - JavaScript-heavy sites may not render properly
    - File downloads (PDFs, docs) may have limited support

    **Best for:** Reading full articles, extracting detailed content from specific URLs.
    """
    await ctx.info(f"FETCH_WEBPAGE: {input.url} (max {input.max_length} chars)")

    try:
        # Use the pre-instantiated fetcher object
        content = await web_content_fetcher.fetch_webpage_content(
            input.url, input.max_length
        )

        # Clean and format the content
        cleaned_content = web_content_fetcher.clean_content(content)

        await ctx.info(
            f"FETCH_WEBPAGE RESULT: Retrieved {len(cleaned_content)} characters"
        )

        return UrlFetchOutput(content=cleaned_content, success=True, error_message="")
    except Exception as e:
        await ctx.error(f"FETCH_WEBPAGE ERROR: {str(e)}")
        return UrlFetchOutput(
            content="", success=False, error_message=f"Fetch failed: {str(e)}"
        )


# ================= Server Entry Point =================

if __name__ == "__main__":
    print("FastMCP 2.0 Web Tools Stream Server starting...")
    print("Available tools:")
    print("- search_web: Search the web using DuckDuckGo for current information")
    print("- fetch_webpage: Fetch and extract text content from webpage URLs")

    # Run with HTTP streaming transport
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=4202,  # Different port from other servers
        log_level="info",  # Reduced from debug to minimize verbosity
    )

    print("\nWeb Tools Stream Server shutting down...")
