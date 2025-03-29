import os
import finnhub
from typing import Dict, Any, List
import requests
from dotenv import load_dotenv, find_dotenv
from loguru import logger

load_dotenv(find_dotenv())


def get_stock_symbol_alpha_vantage(company_name: str) -> List[Dict[str, str]]:
    """
    Get stock symbol(s) from company name using Alpha Vantage API.

    Args:
        company_name (str): The name of the company (e.g., 'Apple', 'Microsoft')

    Returns:
        List[Dict[str, str]]: List of matching companies with their symbols
            Each dictionary contains:
            - symbol: Stock symbol
            - name: Company name
            - type: Security type
            - region: Region/Exchange
            - currency: Trading currency

    """
    # Get API key from environment variable
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        raise Exception("ALPHA_VANTAGE_API_KEY environment variable not set")

    # Alpha Vantage API endpoint for symbol search
    base_url = "https://www.alphavantage.co/query"
    params = {"function": "SYMBOL_SEARCH", "keywords": company_name, "apikey": api_key}

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes

        data = response.json()
        matches = data.get("bestMatches", [])

        # Format the results
        formatted_matches = []
        for match in matches:
            formatted_matches.append(
                {
                    "symbol": match.get("1. symbol", ""),
                    "name": match.get("2. name", ""),
                    "type": match.get("3. type", ""),
                    "region": match.get("4. region", ""),
                    "currency": match.get("8. currency", ""),
                }
            )

        return formatted_matches
    except Exception as e:
        raise Exception(f"Error looking up symbol for {company_name}: {str(e)}")


def get_company_financials(company_symbol: str) -> Dict[str, Any]:
    """
    Get basic financials for a company using Finnhub API.

    Args:
        company_symbol (str): The symbol of the company (e.g., 'AAPL')

    Returns:
        Dict[str, Any]: Dictionary containing basic financial information

    Raises:
        Exception: If there's an error fetching the data or if the API key is not set
    """
    # Get API key from environment variable
    api_key = os.getenv("FINHUB_API_KEY")
    if not api_key:
        raise Exception("FINHUB_API_KEY environment variable not set")

    # Create a Finnhub client
    finnhub_client = finnhub.Client(api_key=api_key)

    try:
        # Get basic financials
        financials = finnhub_client.company_basic_financials(company_symbol, "all")
        # Convert metrics dictionary to markdown-style string
        metrics = financials["metric"]
        markdown_metrics = "   ".join([f"{k}: {v}" for k, v in metrics.items()])
        return markdown_metrics
    except Exception as e:
        raise Exception(f"Error fetching financials for {company_symbol}: {str(e)}")


from newsapi import NewsApiClient


def get_news_headlines(keyword: str, num_articles: int = 5):
    """
    Get news headlines and descriptions for a keyword search

    Args:
        keyword (str): Search term
        num_articles (int): Number of articles to return (default 3)

    Returns:
        List of tuples containing (title, description) for each article
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        raise Exception("NEWS_API_KEY environment variable not set")

    # Initialize NewsAPI client
    newsapi = NewsApiClient(api_key=api_key)

    try:
        # Get all articles
        all_articles = newsapi.get_everything(
            q=keyword, language="en", sort_by="relevancy"
        )

        logger.info(
            f"No of articles: {len(all_articles['articles'])} and filtered: {len(all_articles['articles'][:num_articles])}"
        )

        # Extract first n articles
        articles = all_articles["articles"][:num_articles]

        # Get title and description pairs
        headlines = [(article["title"], article["description"]) for article in articles]

        # Convert headlines to markdown format
        markdown_headlines = "\n".join(
            [f"**{title}**\n{description}\n\n" for title, description in headlines]
        )

        return markdown_headlines

    except Exception as e:
        raise Exception(f"Error fetching news for {keyword}: {str(e)}")


if __name__ == "__main__":
    company_name = "amazon"
    company_details = get_stock_symbol_alpha_vantage(company_name)
    print(f"Company details: {company_details}\n\n")
    company_symbol = company_details[0]["symbol"]
    print(f"Company symbol: {company_symbol}\n\n")
    company_financials = get_company_financials(company_symbol)
    print(f"Company financials: {company_financials}\n\n")
    company_news = get_news_headlines(company_name)
    print(f"Company news: {company_news}\n\n")
