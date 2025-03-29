"""
Common US company stock symbols mapping.
This serves as a fallback when the Alpha Vantage API doesn't return results.
"""

COMMON_COMPANY_SYMBOLS = {
    # Tech Companies
    "microsoft": "MSFT",
    "apple": "AAPL",
    "amazon": "AMZN",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "meta": "META",
    "facebook": "META",
    "netflix": "NFLX",
    "tesla": "TSLA",
    "nvidia": "NVDA",
    "intel": "INTC",
    "adobe": "ADBE",
    "salesforce": "CRM",
    "oracle": "ORCL",
    # Retail Companies
    "walmart": "WMT",
    "target": "TGT",
    "costco": "COST",
    "home depot": "HD",
    "nike": "NKE",
    "starbucks": "SBUX",
    "mcdonalds": "MCD",
    # Financial Companies
    "jpmorgan": "JPM",
    "jp morgan": "JPM",
    "bank of america": "BAC",
    "goldman sachs": "GS",
    "visa": "V",
    "mastercard": "MA",
    "american express": "AXP",
    # Healthcare Companies
    "johnson & johnson": "JNJ",
    "johnson and johnson": "JNJ",
    "unitedhealth": "UNH",
    "pfizer": "PFE",
    "merck": "MRK",
    # Industrial Companies
    "boeing": "BA",
    "caterpillar": "CAT",
    "general electric": "GE",
    "3m": "MMM",
    # Telecommunications
    "at&t": "T",
    "verizon": "VZ",
    "t-mobile": "TMUS",
    # Entertainment
    "disney": "DIS",
    "walt disney": "DIS",
    # Energy Companies
    "exxon mobil": "XOM",
    "exxonmobil": "XOM",
    "chevron": "CVX",
    # Automotive
    "ford": "F",
    "general motors": "GM",
    # Others
    "coca cola": "KO",
    "coca-cola": "KO",
    "pepsi": "PEP",
    "pepsico": "PEP",
    "procter & gamble": "PG",
    "procter and gamble": "PG",
}


def get_symbol_from_mapping(company_name: str) -> str:
    """
    Get the stock symbol for a company from the mapping.

    Args:
        company_name: The name of the company to look up

    Returns:
        The stock symbol if found, None otherwise
    """
    # Clean and standardize the company name
    clean_name = company_name.lower().strip()

    # Direct lookup
    if clean_name in COMMON_COMPANY_SYMBOLS:
        return COMMON_COMPANY_SYMBOLS[clean_name]

    # Try partial matches
    for name, symbol in COMMON_COMPANY_SYMBOLS.items():
        if clean_name in name or name in clean_name:
            return symbol

    return None
