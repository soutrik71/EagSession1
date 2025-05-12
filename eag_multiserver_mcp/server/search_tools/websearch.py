from typing import List, Dict, Optional, Tuple, Any
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import (
    DuckDuckGoSearchException,
    RatelimitException,
    TimeoutException,
)
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
import os
from datetime import datetime
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def save_search_results(
    query: str, text: str, tables: List[Dict], output_dir: str = "./server/outputs"
) -> str:
    """
    Save search results to a JSON file in the specified directory.

    Args:
        query (str): The search query used
        text (str): The extracted text content
        tables (List[Dict]): List of tables as dictionaries
        output_dir (str): Directory to save the output file

    Returns:
        str: Path to the saved file
    """
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Create a sanitized filename from the query and timestamp
    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_query = "".join(c if c.isalnum() else "_" for c in query)
    # filename = f"{sanitized_query}_{timestamp}.json"
    filename = f"{sanitized_query}.json"
    filepath = os.path.join(output_dir, filename)

    # Prepare the data
    data = {
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "url_text": text,
        "url_tables": tables,
    }

    # Save to file
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Search results saved to {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Error saving search results: {str(e)}")
        return ""


class WebSearch:
    """
    A class to perform web searches using DuckDuckGo search API and extract content from URLs.
    """

    def __init__(self):
        """Initialize the WebSearch class with DuckDuckGo search client."""
        self.ddgs = DDGS()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    @retry(
        retry=(
            retry_if_exception_type(RatelimitException)
            | retry_if_exception_type(TimeoutException)
            | retry_if_exception_type(DuckDuckGoSearchException)
        ),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(5),
        before_sleep=before_sleep_log(logger, logging.INFO),
    )
    def news_search(
        self,
        query: str,
        max_results: int = 5,
        region: str = "wt-wt",
        safesearch: str = "moderate",
    ) -> List[Dict]:
        """
        Perform a news search using DuckDuckGo with retry logic for rate limits.

        Args:
            query (str): The search query string
            max_results (int): Maximum number of results to return (default: 5)
            region (str): Region for search results (default: "wt-wt" for worldwide)
            safesearch (str): Safe search level - "on", "moderate", or "off" (default: "moderate")

        Returns:
            List[Dict]: List of news results, each containing:
                - title: Title of the news article
                - url: URL of the article
                - body: Brief description of the article
                - date: Publication date
                - source: Source website
                - image: Image URL (if available)
        """
        try:
            logger.info(f"Performing news search for: {query}")
            results = self.ddgs.news(
                query,
                max_results=max_results,
                region=region,
                safesearch=safesearch,
            )
            results_list = list(results)
            logger.info(f"Found {len(results_list)} news results")
            return results_list
        except (RatelimitException, TimeoutException, DuckDuckGoSearchException) as e:
            logger.warning(f"DuckDuckGo search error: {str(e)}")
            # These exceptions will be caught by the retry decorator
            raise
        except Exception as e:
            logger.error(f"Error performing news search: {str(e)}")
            return []

    def get_first_news(self, query: str, **kwargs) -> Optional[Dict]:
        """
        Get only the first news search result.

        Args:
            query (str): The search query string
            **kwargs: Additional parameters to pass to news_search

        Returns:
            Optional[Dict]: First news result or None if no results found
        """
        results = self.news_search(query, max_results=1, **kwargs)
        return results[0] if results else None

    @retry(
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, logging.INFO),
    )
    def extract_content_from_url(self, url: str) -> Tuple[str, List[pd.DataFrame]]:
        """
        Extract text content and tables from a URL with retry logic.

        Args:
            url (str): The URL to extract content from

        Returns:
            Tuple[str, List[pd.DataFrame]]: A tuple containing:
                - Extracted text content as a string
                - List of pandas DataFrames representing tables found on the page
        """
        try:
            logger.info(f"Extracting content from URL: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()

            # Extract text
            text = soup.get_text(separator="\n")
            text = "\n".join(
                [line.strip() for line in text.split("\n") if line.strip()]
            )

            # Extract tables
            tables = []
            for table in soup.find_all("table"):
                df = self._parse_html_table(table)
                if (
                    not df.empty and df.shape[1] > 1
                ):  # Only include tables with multiple columns
                    # Clean the dataframe
                    df = self._clean_dataframe(df)
                    if not df.empty:
                        tables.append(df)

            logger.info(f"Extracted {len(text)} chars of text and {len(tables)} tables")
            return text, tables

        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error for URL {url}: {str(e)}")
            # This will be caught by the retry decorator
            raise
        except Exception as e:
            logger.error(f"Error extracting content from URL {url}: {str(e)}")
            return "", []

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean a pandas DataFrame by removing duplicate rows and fixing headers.

        Args:
            df: DataFrame to clean

        Returns:
            pd.DataFrame: Cleaned DataFrame
        """
        # If first row duplicates the column names, drop it
        if df.shape[0] > 0:
            first_row = df.iloc[0].astype(str).tolist()
            column_names = df.columns.astype(str).tolist()

            if first_row == column_names:
                df = df.iloc[1:].reset_index(drop=True)

            # Remove any rows that are identical to the header
            df = df[
                ~df.astype(str).apply(tuple, axis=1).isin([tuple(column_names)])
            ].reset_index(drop=True)

            # Drop duplicate rows
            df = df.drop_duplicates().reset_index(drop=True)

            # Replace empty strings with NaN and drop all-NaN rows and columns
            df = df.replace("", pd.NA).dropna(how="all").dropna(axis=1, how="all")

        return df

    def _parse_html_table(self, table_element: Any) -> pd.DataFrame:
        """
        Parse an HTML table element into a pandas DataFrame.

        Args:
            table_element: BeautifulSoup table element

        Returns:
            pd.DataFrame: Pandas DataFrame containing the table data
        """
        try:
            rows = []

            # Extract headers
            headers = []
            header_row = table_element.find("thead")
            if header_row:
                headers = [
                    th.get_text().strip() for th in header_row.find_all(["th", "td"])
                ]

            # If no headers found in thead, check first tr
            if not headers:
                first_row = table_element.find("tr")
                if first_row:
                    headers = [
                        th.get_text().strip() for th in first_row.find_all(["th", "td"])
                    ]

            # Process table body
            for row in table_element.find_all("tr"):
                if (
                    row.find_parent("thead") is None
                ):  # Skip header row if we already have headers
                    cols = [td.get_text().strip() for td in row.find_all(["td", "th"])]
                    if cols and (len(cols) >= len(headers) if headers else True):
                        rows.append(cols)

            # Create DataFrame
            if headers and rows and any(len(row) == len(headers) for row in rows):
                # Filter rows to only those matching header length
                valid_rows = [row for row in rows if len(row) == len(headers)]
                return pd.DataFrame(valid_rows, columns=headers)
            elif rows:
                # Get the most common row length if no headers
                row_lengths = [len(row) for row in rows]
                if not row_lengths:
                    return pd.DataFrame()

                most_common_length = max(set(row_lengths), key=row_lengths.count)
                valid_rows = [row for row in rows if len(row) == most_common_length]
                return pd.DataFrame(valid_rows)
            else:
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error parsing HTML table: {str(e)}")
            return pd.DataFrame()

    def extract_best_content(self, query: str, max_urls: int = 3) -> Dict:
        """
        Try multiple search results and extract content from the best one.

        Args:
            query (str): The search query string
            max_urls (int): Maximum number of URLs to try

        Returns:
            Dict: Dictionary containing:
                - result: The original search result
                - text: Extracted text from the URL
                - tables: List of extracted tables
                - url_rank: Which URL in the results was used (0-indexed)
        """
        results = self.news_search(query, max_results=max_urls)

        if not results:
            logger.warning(f"No search results found for query: {query}")
            return {"result": None, "text": "", "tables": [], "url_rank": -1}

        best_result = None
        best_text = ""
        best_tables = []
        best_rank = -1
        best_score = -1

        # Try each result until we find one with good content
        for i, result in enumerate(results):
            url = result.get("url", "")
            if not url:
                continue

            logger.info(f"Trying URL {i+1}/{len(results)}: {url}")
            try:
                text, tables = self.extract_content_from_url(url)

                # Evaluate the quality of the content
                content_score = self._evaluate_content(text, tables)
                logger.info(f"Content score for URL {i+1}: {content_score}/10")

                # If this is the first result or it's better than what we have
                if best_rank == -1 or content_score > best_score:
                    best_result = result
                    best_text = text
                    best_tables = tables
                    best_rank = i
                    best_score = content_score

                    # If we found good content, we can stop searching
                    if content_score >= 7:  # Threshold for "good enough" content
                        logger.info(
                            f"Found good content at URL rank {i+1} with score {content_score}/10"
                        )
                        break

            except Exception as e:
                logger.error(f"Error processing URL {url}: {str(e)}")
                # Continue to the next URL
                continue

        # Convert tables to dict for serialization, handle NaN values
        table_dicts = []
        for table in best_tables:
            table_dict = table.fillna("").to_dict()
            table_dicts.append(table_dict)

        logger.info(
            f"Selected best content from URL rank {best_rank + 1 if best_rank >= 0 else 'None'}"
        )

        return {
            "result": best_result,
            "text": best_text,
            "tables": table_dicts,
            "url_rank": best_rank,
        }

    def _evaluate_content(self, text: str, tables: List[pd.DataFrame]) -> int:
        """
        Evaluate the quality of extracted content.

        Args:
            text (str): Extracted text
            tables (List[pd.DataFrame]): Extracted tables

        Returns:
            int: Score from 0-10 indicating content quality
        """
        score = 0

        # Text quality
        if len(text) > 2000:
            score += 3
        elif len(text) > 500:
            score += 2
        elif len(text) > 100:
            score += 1

        # Table quality
        if tables:
            # Bonus for having tables
            score += 2

            # Bonus for tables with reasonable dimensions
            good_tables = 0
            for table in tables:
                if table.shape[0] >= 3 and table.shape[1] >= 2:
                    good_tables += 1

            if good_tables >= 2:
                score += 3
            elif good_tables == 1:
                score += 2

        return score

    def search_and_extract(self, query: str, max_urls: int = 3) -> Dict:
        """
        Perform a search and extract content from multiple results to find the best one.

        Args:
            query (str): The search query string
            max_urls (int): Maximum number of URLs to try

        Returns:
            Dict: Dictionary containing search result and extracted content:
                - result: The best search result
                - text: Extracted text from the URL
                - tables: List of extracted tables
                - url_rank: Which URL in the results was used (0-indexed)
        """
        logger.info(f"Starting search and extract for query: {query}")
        # Add some random delay to avoid rate limiting
        time.sleep(0.5 + (time.time() % 2))
        return self.extract_best_content(query, max_urls)


if __name__ == "__main__":
    websearch = WebSearch()

    # Example search with error handling
    try:
        # Search for F1 standings and extract content from the best source
        print("Searching for Formula 1 2025 driver standings...")
        response = websearch.search_and_extract("formula 1 2025 driver standings")

        if response["result"]:
            print("\nBest Search Result (Rank #{0}):".format(response["url_rank"] + 1))
            print(f"Title: {response['result'].get('title', 'N/A')}")
            print(f"Source: {response['result'].get('source', 'N/A')}")
            print(f"URL: {response['result'].get('url', 'N/A')}")

            print("\nExtracted Text (first 500 chars):")
            print(
                response["text"][:500] + "..."
                if len(response["text"]) > 500
                else response["text"]
            )

            if response.get("tables"):
                print(f"\nFound {len(response['tables'])} tables on the page.")
                for i, table_dict in enumerate(response["tables"], 1):
                    print(f"\nTable {i}:")
                    # Convert back to DataFrame for display
                    df = pd.DataFrame.from_dict(table_dict)
                    print(df)

            # Save the results to a file using the standalone function
            saved_file = save_search_results(
                query="formula 1 2025 driver standings",
                text=response["text"],
                tables=response["tables"],
            )

            if saved_file:
                print(f"\nResults saved to: {saved_file}")
        else:
            print("No results found.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
