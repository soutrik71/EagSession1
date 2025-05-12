from mcp.server.fastmcp import FastMCP, Context
from search_tools.websearch import WebSearch, save_search_results
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("web-search")
websearch = WebSearch()


@mcp.tool()
async def search_web(query: str, ctx: Context, max_urls: int = 3) -> str:
    """
    Search the web for the given query and return the best content.

    Args:
        query: The search query string
        ctx: MCP context for logging
        max_urls: Maximum number of URLs to try (default: 3)

    Returns:
        String with search results and path to saved JSON file
    """
    try:
        await ctx.info(f"Starting web search for query: {query}")

        # Perform search and extract content
        await ctx.info(f"Extracting content from up to {max_urls} URLs")
        response = websearch.search_and_extract(query, max_urls)

        # Format output with search result info
        output = []

        if response["result"]:
            result = response["result"]
            url_rank = response["url_rank"]

            await ctx.info(f"Found content in result #{url_rank + 1}")
            output.append(
                f"Search successful! Found content from result #{url_rank + 1}"
            )
            output.append(f"Title: {result.get('title', 'N/A')}")
            output.append(f"Source: {result.get('source', 'N/A')}")
            output.append(f"URL: {result.get('url', 'N/A')}")

            # Save results to file
            await ctx.info("Saving search results to file")
            saved_file = save_search_results(
                query=query,
                text=response["text"],
                tables=response["tables"],
            )

            # Add content preview
            output.append("\nContent Preview:")
            preview = (
                response["text"][:500] + "..."
                if len(response["text"]) > 500
                else response["text"]
            )
            output.append(preview)

            # Add table info
            if response["tables"]:
                table_count = len(response["tables"])
                await ctx.info(f"Found {table_count} tables in the content")
                output.append(f"\nFound {table_count} tables in the content.")

            # Add file path if saved successfully
            if saved_file:
                await ctx.info(f"Results saved to: {saved_file}")
                output.append(f"\nSuccess! Results saved to: {saved_file}")
            else:
                await ctx.warn("Failed to save results to file")
                output.append("\nWarning: Failed to save results to file.")
        else:
            await ctx.warn("No results found for search query")
            output.append("No results found for your search query.")
            output.append(
                "This could be due to no matching content or search API limitations."
            )
            output.append("Please try rephrasing your query or try again later.")

        await ctx.info("Web search completed successfully")
        return "\n".join(output)

    except Exception as e:
        error_msg = f"An error occurred while searching: {str(e)}"
        await ctx.error(f"Search error: {str(e)}")
        return error_msg


if __name__ == "__main__":
    mcp.run(transport="stdio")
