import pytest

from trading.models.portfolio_model import PortfolioModel, PortfolioHolding
from trading.models.stock_model import Stocks


@pytest.fixture()
def portfolio_model():
    """Fixture to provide a new PortfolioModel instance for each test."""
    return PortfolioModel()


@pytest.fixture
def stock_apple(session):
    """Fixture for Apple stock."""
    stock = Stocks(ticker="AAPL", current_price=174.35)
    session.add(stock)
    session.commit()
    return stock


@pytest.fixture
def stock_google(session):
    """Fixture for Google stock."""
    stock = Stocks(ticker="GOOGL", current_price=2805.67)
    session.add(stock)
    session.commit()
    return stock


def _add_holding(session, username, ticker, shares):
    holding = PortfolioHolding(username=username, ticker=ticker, shares=shares)
    session.add(holding)
    session.commit()
    return holding


##################################################
# Buy Stock Test Cases
##################################################

def test_buy_new_stock_success(portfolio_model, session, stock_apple, mocker):
    """Test buying a stock not currently in the portfolio."""
    mocker.patch.object(portfolio_model, 'validate_stock_ticker', return_value="AAPL")
    mocker.patch.object(portfolio_model, 'validate_shares_count', return_value=10)
    mocker.patch('trading.models.portfolio_model.get_current_price', return_value=174.35)

    result = portfolio_model.buy_stock("alice", "AAPL", 10)

    holding = PortfolioHolding.query.filter_by(username="alice", ticker="AAPL").first()
    assert holding is not None
    assert holding.shares == 10

    assert result["transaction_type"] == "BUY"
    assert result["stock_symbol"] == "AAPL"
    assert result["shares"] == 10
    assert result["price_per_share"] == 174.35
    assert result["total_cost"] == 174.35 * 10
    assert "timestamp" in result


def test_buy_existing_stock(portfolio_model, session, stock_apple, mocker):
    """Test buying more shares of a stock already in the portfolio."""
    _add_holding(session, "alice", "AAPL", 5)

    mocker.patch.object(portfolio_model, 'validate_stock_ticker', return_value="AAPL")
    mocker.patch.object(portfolio_model, 'validate_shares_count', return_value=5)
    mocker.patch('trading.models.portfolio_model.get_current_price', return_value=180.00)

    result = portfolio_model.buy_stock("alice", "AAPL", 5)

    holding = PortfolioHolding.query.filter_by(username="alice", ticker="AAPL").first()
    assert holding.shares == 10
    assert result["shares"] == 5
    assert result["price_per_share"] == 180.00
    assert result["total_cost"] == 900.00


def test_buy_stock_validation_error(portfolio_model, session, mocker):
    """Test buying stock with an invalid ticker."""
    mocker.patch.object(portfolio_model, 'validate_stock_ticker', side_effect=ValueError("Invalid stock ticker"))

    with pytest.raises(ValueError, match="Invalid stock ticker"):
        portfolio_model.buy_stock("alice", "INVALID", 10)

    holding = PortfolioHolding.query.filter_by(username="alice").first()
    assert holding is None


def test_buy_stock_api_error(portfolio_model, session, mocker):
    """Test handling error when the price API fails during buy."""
    mocker.patch.object(portfolio_model, 'validate_stock_ticker', return_value="AAPL")
    mocker.patch.object(portfolio_model, 'validate_shares_count', return_value=10)
    mocker.patch('trading.models.portfolio_model.get_current_price', side_effect=ValueError("API error"))

    with pytest.raises(ValueError, match="API error"):
        portfolio_model.buy_stock("alice", "AAPL", 10)

    holding = PortfolioHolding.query.filter_by(username="alice", ticker="AAPL").first()
    assert holding is None


##################################################
# Sell Stock Test Cases
##################################################

def test_sell_stock_success(portfolio_model, session, mocker):
    """Test successfully selling shares of a stock."""
    _add_holding(session, "alice", "AAPL", 20)

    mocker.patch.object(portfolio_model, 'validate_stock_ticker', return_value="AAPL")
    mocker.patch.object(portfolio_model, 'validate_shares_count', return_value=10)
    mocker.patch.object(portfolio_model, 'check_if_empty')
    mocker.patch('trading.models.portfolio_model.get_current_price', return_value=190.00)

    result = portfolio_model.sell_stock("alice", "AAPL", 10)

    holding = PortfolioHolding.query.filter_by(username="alice", ticker="AAPL").first()
    assert holding.shares == 10

    assert result["transaction_type"] == "SELL"
    assert result["stock_symbol"] == "AAPL"
    assert result["shares"] == 10
    assert result["price_per_share"] == 190.00
    assert result["total_proceeds"] == 190.00 * 10
    assert "timestamp" in result


def test_sell_all_shares(portfolio_model, session, mocker):
    """Test selling all shares removes the holding row from the DB."""
    _add_holding(session, "alice", "GOOGL", 5)

    mocker.patch.object(portfolio_model, 'validate_stock_ticker', return_value="GOOGL")
    mocker.patch.object(portfolio_model, 'validate_shares_count', return_value=5)
    mocker.patch.object(portfolio_model, 'check_if_empty')
    mocker.patch('trading.models.portfolio_model.get_current_price', return_value=2800.00)

    result = portfolio_model.sell_stock("alice", "GOOGL", 5)

    holding = PortfolioHolding.query.filter_by(username="alice", ticker="GOOGL").first()
    assert holding is None
    assert result["shares"] == 5
    assert result["price_per_share"] == 2800.00
    assert result["total_proceeds"] == 14000.00


def test_sell_stock_not_owned(portfolio_model, session, mocker):
    """Test error when trying to sell a stock not in the portfolio."""
    mocker.patch.object(portfolio_model, 'validate_stock_ticker', return_value="TSLA")
    mocker.patch.object(portfolio_model, 'validate_shares_count', return_value=5)
    mocker.patch.object(portfolio_model, 'check_if_empty')

    with pytest.raises(ValueError, match="You don't own any shares of TSLA"):
        portfolio_model.sell_stock("alice", "TSLA", 5)


def test_sell_more_shares_than_owned(portfolio_model, session, mocker):
    """Test error when trying to sell more shares than owned."""
    _add_holding(session, "alice", "GOOGL", 3)

    mocker.patch.object(portfolio_model, 'validate_stock_ticker', return_value="GOOGL")
    mocker.patch.object(portfolio_model, 'validate_shares_count', return_value=5)
    mocker.patch.object(portfolio_model, 'check_if_empty')

    with pytest.raises(ValueError, match="You only have 3 shares of GOOGL, but attempted to sell 5"):
        portfolio_model.sell_stock("alice", "GOOGL", 5)

    holding = PortfolioHolding.query.filter_by(username="alice", ticker="GOOGL").first()
    assert holding.shares == 3


def test_sell_stock_empty_portfolio(portfolio_model, session, mocker):
    """Test error when trying to sell from an empty portfolio."""
    mocker.patch.object(portfolio_model, 'check_if_empty', side_effect=ValueError("Portfolio is empty"))

    with pytest.raises(ValueError, match="Portfolio is empty"):
        portfolio_model.sell_stock("alice", "AAPL", 5)


def test_sell_stock_api_error(portfolio_model, session, mocker):
    """Test that a price API failure during sell leaves holdings unchanged."""
    _add_holding(session, "alice", "AAPL", 10)

    mocker.patch.object(portfolio_model, 'validate_stock_ticker', return_value="AAPL")
    mocker.patch.object(portfolio_model, 'validate_shares_count', return_value=5)
    mocker.patch.object(portfolio_model, 'check_if_empty')
    mocker.patch('trading.models.portfolio_model.get_current_price', side_effect=ValueError("API error"))

    with pytest.raises(ValueError, match="API error"):
        portfolio_model.sell_stock("alice", "AAPL", 5)

    holding = PortfolioHolding.query.filter_by(username="alice", ticker="AAPL").first()
    assert holding.shares == 10
