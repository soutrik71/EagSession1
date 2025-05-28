import httpx
from bs4 import BeautifulSoup
from typing import List
from dataclasses import dataclass
import urllib.parse
import asyncio
from datetime import datetime, timedelta
import re
import ssl


@dataclass
class SearchResult:
    """Data class to represent a search result"""

    title: str
    link: str
    snippet: str
    position: int


class RateLimiter:
    """Simple rate limiter to avoid overwhelming web services"""

    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.requests = []

    async def acquire(self):
        """Wait if necessary to respect rate limits"""
        now = datetime.now()
        # Remove requests older than 1 minute
        self.requests = [
            req for req in self.requests if now - req < timedelta(minutes=1)
        ]

        if len(self.requests) >= self.requests_per_minute:
            # Wait until we can make another request
            wait_time = 60 - (now - self.requests[0]).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)

        self.requests.append(now)


class DuckDuckGoSearcher:
    """DuckDuckGo search functionality without MCP dependencies"""

    BASE_URL = "https://html.duckduckgo.com/html"
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    def __init__(self):
        self.rate_limiter = RateLimiter()

    def format_results_for_llm(self, results: List[SearchResult]) -> str:
        """Format results in a natural language style that's easier for LLMs to process"""
        if not results:
            return (
                "No results were found for your search query. This could be due to "
                "DuckDuckGo's bot detection or the query returned no matches. "
                "Please try rephrasing your search or try again in a few minutes."
            )

        output = [f"Found {len(results)} search results:\n"]

        for result in results:
            output.extend(
                [
                    f"{result.position}. {result.title}",
                    f"   URL: {result.link}",
                    f"   Summary: {result.snippet}",
                    "",  # Empty line between results
                ]
            )

        return "\n".join(output)

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Search DuckDuckGo for the given query

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of SearchResult objects
        """
        try:
            # Apply rate limiting
            await self.rate_limiter.acquire()

            # Create form data for POST request
            data = {
                "q": query,
                "b": "",
                "kl": "",
            }

            # Create SSL context that's more permissive for Windows environments
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            async with httpx.AsyncClient(verify=False) as client:
                result = await client.post(
                    self.BASE_URL, data=data, headers=self.HEADERS, timeout=30.0
                )
                result.raise_for_status()

            # Parse HTML result
            soup = BeautifulSoup(result.text, "html.parser")
            if not soup:
                return []

            results = []
            for result in soup.select(".result"):
                title_elem = result.select_one(".result__title")
                if not title_elem:
                    continue

                link_elem = title_elem.find("a")
                if not link_elem:
                    continue

                title = link_elem.get_text(strip=True)
                link = link_elem.get("href", "")

                # Skip ad results
                if "y.js" in link:
                    continue

                # Clean up DuckDuckGo redirect URLs
                if link.startswith("//duckduckgo.com/l/?uddg="):
                    link = urllib.parse.unquote(link.split("uddg=")[1].split("&")[0])

                snippet_elem = result.select_one(".result__snippet")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                results.append(
                    SearchResult(
                        title=title,
                        link=link,
                        snippet=snippet,
                        position=len(results) + 1,
                    )
                )

                if len(results) >= max_results:
                    break

            return results

        except httpx.TimeoutException:
            print("Search request timed out")
            return []
        except httpx.HTTPError as e:
            print(f"HTTP error occurred: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error during search: {str(e)}")
            return []


class WebContentFetcher:
    """Web content fetching functionality without MCP dependencies"""

    def __init__(self):
        self.rate_limiter = RateLimiter(requests_per_minute=20)

    async def fetch_and_parse(self, url: str) -> str:
        """
        Fetch and parse content from a webpage

        Args:
            url: URL to fetch content from

        Returns:
            Cleaned text content from the webpage
        """
        try:
            await self.rate_limiter.acquire()

            # Create SSL context that's more permissive for Windows environments
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            async with httpx.AsyncClient(verify=False) as client:
                result = await client.get(
                    url,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36"
                        )
                    },
                    follow_redirects=True,
                    timeout=30.0,
                )
                result.raise_for_status()

            # Parse the HTML
            soup = BeautifulSoup(result.text, "html.parser")

            # Remove script and style elements
            for element in soup(["script", "style", "nav", "header", "footer"]):
                element.decompose()

            # Get the text content
            text = soup.get_text()

            # Clean up the text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)

            # Remove extra whitespace
            text = re.sub(r"\s+", " ", text).strip()

            # Truncate if too long
            if len(text) > 8000:
                text = text[:8000] + "... [content truncated]"

            return text

        except httpx.TimeoutException:
            error_msg = f"Request timed out for URL: {url}"
            print(error_msg)
            return "Error: The request timed out while trying to fetch the webpage."
        except httpx.HTTPError as e:
            error_msg = f"HTTP error occurred while fetching {url}: {str(e)}"
            print(error_msg)
            return f"Error: Could not access the webpage ({str(e)})"
        except Exception as e:
            error_msg = f"Error fetching content from {url}: {str(e)}"
            print(error_msg)
            return f"Error: An unexpected error occurred while fetching the webpage ({str(e)})"


# Convenience functions for easy usage
async def search_duckduckgo(query: str, max_results: int = 10) -> str:
    """
    Convenience function to search DuckDuckGo and get formatted results

    Args:
        query: Search query string
        max_results: Maximum number of results to return

    Returns:
        Formatted search results as a string
    """
    searcher = DuckDuckGoSearcher()
    results = await searcher.search(query, max_results)
    return searcher.format_results_for_llm(results)


async def fetch_webpage_content(url: str) -> str:
    """
    Convenience function to fetch and parse webpage content

    Args:
        url: URL to fetch content from

    Returns:
        Cleaned text content from the webpage
    """
    fetcher = WebContentFetcher()
    return await fetcher.fetch_and_parse(url)


def main():
    """Main function for testing the web tools"""
    print("Testing DuckDuckGo Search...")
    try:
        result = asyncio.run(search_duckduckgo("What is the capital of France?", 3))
        print(result)
        print("\n" + "=" * 50 + "\n")
    except Exception as e:
        print(f"Search test failed: {e}")

    print("Testing Web Content Fetching...")
    try:
        result = asyncio.run(fetch_webpage_content("https://httpbin.org/html"))
        print(result[:500] + "..." if len(result) > 500 else result)
    except Exception as e:
        print(f"Fetch test failed: {e}")


if __name__ == "__main__":
    main()
