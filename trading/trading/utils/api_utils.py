import os
import requests
import logging

logger = logging.getLogger(__name__)

BASE_URL = "https://alpha-vantage.p.rapidapi.com/query"
API_HOST = "alpha-vantage.p.rapidapi.com"
API_KEY = os.getenv("RAPIDAPI_KEY")


def get_current_price(ticker: str) -> float:
    """Fetch the current stock price via RapidAPI.

    Args:
        ticker (str): The stock ticker symbol.

    Returns:
        float: The current price of the stock.

    Raises:
        ValueError: If the price cannot be fetched.
    """
    logger.info(f"Attempting to fetch price for ticker: {ticker}")

    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": ticker.upper(),
        "datatype": "json"
    }

    headers = {
        "x-rapidapi-host": API_HOST,
        "x-rapidapi-key": API_KEY
    }

    try:
        logger.debug(f"Sending request to Alpha Vantage with params: {params}")
        response = requests.get(BASE_URL, headers=headers, params=params, timeout=5)
        response.raise_for_status()
        logger.debug("Received response from Alpha Vantage")

        data = response.json()
        logger.debug(f"Response JSON: {data}")

        price_str = data["Global Quote"]["05. price"]
        price = float(price_str)
        logger.info(f"Fetched price for {ticker}: {price}")
        return price

    except Exception as e:
        logger.error(f"Failed to get price for {ticker}: {e}", exc_info=True)
        raise ValueError(f"Could not fetch price for {ticker}")


def is_valid_ticker(ticker: str) -> bool:
    """Check whether a ticker symbol is valid via Alpha Vantage symbol search.

    Args:
        ticker (str): The ticker symbol to validate.

    Returns:
        bool: True if the ticker is valid, False otherwise.
    """
    params = {
        "function": "SYMBOL_SEARCH",
        "keywords": ticker.upper(),
        "apikey": API_KEY
    }

    try:
        response = requests.get("https://www.alphavantage.co/query", params=params, timeout=5)
        response.raise_for_status()
        matches = response.json().get("bestMatches", [])
        return any(match.get("1. symbol", "").upper() == ticker.upper() for match in matches)

    except Exception as e:
        logger.error(f"Error validating ticker {ticker}: {e}")
        return False