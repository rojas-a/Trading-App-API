import logging
import os
import time

from sqlalchemy.exc import SQLAlchemyError
from trading.models.stock_model import Stocks
from trading.utils.api_utils import get_current_price
from trading.utils.logger import configure_logger

logger = logging.getLogger(__name__)
configure_logger(logger)


class PortfolioModel:
    """
    A class to manage a portfolio of stocks.

    """

    def __init__(self):
        """Initializes the PortfolioModel with an empty portfolio.

        portfolio (dict[str, dict[str, int]]) - A dictionary mapping usernames to their holdings,
        where each holding maps a stock ticker to the number of shares owned.
        The TTL (Time To Live) for stock caching is set to a default value from the environment variable "TTL",
        which defaults to 60 seconds if not set.
        """
        self.portfolio: dict[str, dict[str, int]] = {}  # username -> {ticker -> shares}
        self._stock_cache: dict[str, Stocks] = {}
        self._ttl: dict[str, float] = {}
        self.ttl_seconds = int(os.getenv("TTL", 60))


    ##################################################
    # Stock Management Functions
    ##################################################

    def calculate_portfolio_value(self, username: str) -> float:
        """Calculates the full value of a user's portfolio.

        Args:
            username (str): The username of the portfolio owner.

        Returns:
            float: the full value of the user's portfolio in USD

        Raises:
            ValueError: If the portfolio is empty or there is an issue finding the stock price
        """
        logger.info("Received request to calculate portfolio value")
        self.check_if_empty(username)

        user_portfolio = self.portfolio[username]
        total = 0.0
        for ticker, quantity in user_portfolio.items():
            try:
                logger.info(f"Fetching price for {ticker}")
                price = get_current_price(ticker)
                subtotal = price * quantity
                total += subtotal
                logger.info(f"{quantity} shares of {ticker} at ${price:.2f} each: ${subtotal:.2f}")
            except ValueError as e:
                logger.error(f"Failed to find price for stock {ticker}: {e}")
                raise

        logger.info(f"Successfully computed total portfolio value: ${total:.2f}")
        return total


    def _get_stock_from_cache_or_db(self, ticker: str) -> Stocks:
        """
        Retrieves a stock by ticker, using the internal cache if possible.

        Args:
            ticker (str): The ticker of the stock to retrieve.

        Returns:
            Stocks: The stock object corresponding to the given ticker.

        Raises:
            ValueError: If the stock cannot be found in the database.
        """
        now = time.time()

        if ticker in self._stock_cache and self._ttl.get(ticker, 0) > now:
            logger.debug(f"Stock {ticker} retrieved from cache")
            return self._stock_cache[ticker]

        try:
            stock = Stocks.get_stock_by_ticker(ticker)
            logger.info(f"Stock {ticker} loaded from DB")
        except ValueError as e:
            logger.error(f"Stock {ticker} not found in DB: {e}")
            raise ValueError(f"Stock {ticker} not found in database") from e

        self._stock_cache[ticker] = stock
        self._ttl[ticker] = now + self.ttl_seconds
        return stock

    def get_user_portfolio(self, username: str) -> dict:
        """
        Retrieves and summarizes the user's portfolio.

        Args:
            username (str): Username of the portfolio owner.

        Returns:
            dict: Portfolio summary with holdings and total value.
        """
        try:
            self.check_if_empty(username)

            user_portfolio = self.portfolio[username]
            result = []
            total_value = self.calculate_portfolio_value(username)

            for ticker, quantity in user_portfolio.items():
                price = get_current_price(ticker)
                holding_value = quantity * price

                result.append({
                    "ticker": ticker,
                    "quantity": quantity,
                    "current_price": price,
                    "total_value": holding_value
                })

            return {
                "total_value": round(total_value, 2),
                "holdings": result
            }

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving portfolio: {e}")
            raise


    ##################################################
    # Buy / Sell Functions
    ##################################################


    def buy_stock(self, username: str, stock_symbol: str, shares: int) -> dict:
        """
        Enables users to purchase shares of a specified stock.

        Args:
            username (str): The username of the buyer.
            stock_symbol (str): The symbol of the stock to buy.
            shares (int): The number of shares to purchase.

        Returns:
            Dict: Transaction details including stock symbol, shares purchased, price per share,
                  total cost, and timestamp.

        Raises:
            ValueError: If the stock symbol is invalid, shares value is invalid, or the transaction fails.
        """
        logger.info(f"Attempting to buy {shares} shares of {stock_symbol}")

        stock_symbol = self.validate_stock_ticker(stock_symbol, check_in_portfolio=False, username=username)
        shares = self.validate_shares_count(shares)

        if username not in self.portfolio:
            self.portfolio[username] = {}

        try:
            price_per_share = get_current_price(stock_symbol)
        except ValueError as e:
            logger.error(f"Failed to buy stock {stock_symbol}: {e}")
            raise

        if stock_symbol in self.portfolio[username]:
            self.portfolio[username][stock_symbol] += shares
        else:
            self.portfolio[username][stock_symbol] = shares

        total_cost = price_per_share * shares

        transaction_details = {
            "transaction_type": "BUY",
            "stock_symbol": stock_symbol,
            "shares": shares,
            "price_per_share": price_per_share,
            "total_cost": total_cost,
            "timestamp": time.time()
        }

        logger.info(f"Successfully bought {shares} shares of {stock_symbol} at ${price_per_share:.2f} per share")
        return transaction_details

    def sell_stock(self, username: str, stock_symbol: str, shares: int) -> dict:
        """
        Allows users to sell shares of a stock they currently hold.

        Args:
            username (str): The username of the seller.
            stock_symbol (str): The symbol of the stock to sell.
            shares (int): The number of shares to sell.

        Returns:
            Dict: Transaction details including stock symbol, shares sold, price per share,
                  total proceeds, and timestamp.

        Raises:
            ValueError: If the stock symbol is invalid, shares value is invalid,
                        the user doesn't own the stock, or owns insufficient shares.
        """
        logger.info(f"Attempting to sell {shares} shares of {stock_symbol}")

        self.check_if_empty(username)

        stock_symbol = self.validate_stock_ticker(stock_symbol, username=username)
        shares = self.validate_shares_count(shares)

        user_portfolio = self.portfolio.get(username, {})

        if stock_symbol not in user_portfolio:
            logger.error(f"Stock {stock_symbol} not found in portfolio")
            raise ValueError(f"You don't own any shares of {stock_symbol}")

        if user_portfolio[stock_symbol] < shares:
            logger.error(f"Insufficient shares of {stock_symbol} in portfolio")
            raise ValueError(f"You only have {user_portfolio[stock_symbol]} shares of {stock_symbol}, but attempted to sell {shares}")

        try:
            price_per_share = get_current_price(stock_symbol)
        except ValueError as e:
            logger.error(f"Failed to sell stock {stock_symbol}: {e}")
            raise

        self.portfolio[username][stock_symbol] -= shares

        if self.portfolio[username][stock_symbol] == 0:
            del self.portfolio[username][stock_symbol]

        total = price_per_share * shares

        transaction_details = {
            "transaction_type": "SELL",
            "stock_symbol": stock_symbol,
            "shares": shares,
            "price_per_share": price_per_share,
            "total_proceeds": total,
            "timestamp": time.time()
        }

        logger.info(f"Successfully sold {shares} shares of {stock_symbol} at ${price_per_share:.2f} per share")
        return transaction_details


    ##################################################
    # Utility Functions
    ##################################################

    def validate_stock_ticker(self, ticker: str, check_in_portfolio: bool = True, username: str = "") -> str:
        """
        Validates the given stock ticker.

        Args:
            ticker (str): The stock ticker to validate.
            check_in_portfolio (bool, optional): If True, verifies the ticker is present in the user's portfolio.
            username (str): The username to check against when check_in_portfolio is True.

        Returns:
            str: The validated stock ticker.

        Raises:
            ValueError: If stock ticker is not found in the portfolio (when check_in_portfolio=True),
                        or not found in the database.
        """
        if check_in_portfolio:
            user_portfolio = self.portfolio.get(username, {})
            if ticker not in user_portfolio:
                logger.error(f"Stock {ticker} not found in portfolio")
                raise ValueError(f"Stock {ticker} not found in portfolio")

        try:
            self._get_stock_from_cache_or_db(ticker)
        except Exception as e:
            logger.error(f"Stock {ticker} not found in database: {e}")
            raise ValueError(f"Stock {ticker} not found in database")

        return ticker

    def validate_shares_count(self, shares: int) -> int:
        """
        Validates that the number of shares is a positive integer.

        Args:
            shares: The number of shares to validate.

        Returns:
            int: The validated number of shares.

        Raises:
            ValueError: If the shares count is not a positive integer.
        """
        try:
            shares = int(shares)
            if shares <= 0:
                raise ValueError
        except (ValueError, TypeError):
            logger.error(f"Invalid number of shares: {shares}")
            raise ValueError(f"Number of shares must be a positive integer: {shares}")

        return shares

    def check_if_empty(self, username: str) -> None:
        """
        Checks if the user's portfolio is empty and raises a ValueError if it is.

        Args:
            username (str): The username whose portfolio to check.

        Raises:
            ValueError: If the portfolio is empty.
        """
        user_portfolio = self.portfolio.get(username, {})
        if not user_portfolio:
            logger.error("Portfolio is empty")
            raise ValueError("Portfolio is empty")
