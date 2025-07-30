# accounts.py
# A self-contained module for a simple trading simulation account management system.

from datetime import datetime
from typing import Dict, List, Union

# 1. Custom Exceptions
# Provides clear, specific error feedback for trading operations.

class TradingError(Exception):
    """Base exception for all trading-related errors."""
    pass

class InsufficientFundsError(TradingError):
    """Raised when an operation cannot be completed due to insufficient cash."""
    pass

class InsufficientSharesError(TradingError):
    """Raised when attempting to sell more shares than are owned."""
    pass

class UnknownSymbolError(TradingError):
    """Raised when a share price is requested for an unknown symbol."""
    pass

# 2. Helper Functions
# This section provides helper functions for the module, like fetching market data.

# Test data for share prices
_test_prices = {
    'AAPL': 150.00,
    'GOOGL': 2750.00,
    'TSLA': 700.50,
}

def get_share_price(symbol: str) -> float:
    """
    Retrieves the current market price for a given stock symbol.
    This is a test implementation using a fixed dictionary.

    Args:
        symbol (str): The stock symbol (e.g., 'AAPL'). Case-insensitive.

    Returns:
        float: The current price per share.

    Raises:
        UnknownSymbolError: If the symbol is not found in the test data.
    """
    normalized_symbol = symbol.upper()
    price = _test_prices.get(normalized_symbol)
    if price is None:
        raise UnknownSymbolError(f"No price data found for symbol: {symbol}")
    return price

# 3. Account Class
# The core class of the module, managing all aspects of a user's account.

class Account:
    """
    Manages a user's cash balance, share holdings, and transaction history
    for a simulated trading environment. It enforces trading rules, such as
    preventing overdrafts or selling unowned shares.
    """
    def __init__(self, account_id: str, user_name: str, initial_deposit: float = 0.0):
        """
        Initializes a new Account instance.

        Args:
            account_id (str): The unique ID for this account.
            user_name (str): The name of the user.
            initial_deposit (float, optional): The starting cash balance. Defaults to 0.0.
        """
        if initial_deposit < 0:
            raise ValueError("Initial deposit cannot be negative.")

        self._account_id: str = account_id
        self._user_name: str = user_name
        self._cash_balance: float = initial_deposit
        self._total_deposits: float = initial_deposit
        self._holdings: Dict[str, int] = {}
        self._transactions: List[Dict[str, Union[str, int, float, None]]] = []

        if initial_deposit > 0:
            self._record_transaction(
                type='DEPOSIT',
                total_amount=initial_deposit
            )

    def _record_transaction(self, *, type: str, symbol: str = None, quantity: int = None,
                           price_per_share: float = None, total_amount: float):
        """A private helper to create and store a transaction record."""
        transaction = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': type,
            'symbol': symbol.upper() if symbol else None,
            'quantity': quantity,
            'price_per_share': price_per_share,
            'total_amount': total_amount
        }
        self._transactions.append(transaction)

    def deposit(self, amount: float) -> None:
        """
        Adds funds to the account's cash balance.

        Args:
            amount (float): The amount of cash to deposit.

        Raises:
            ValueError: If amount is not a positive number.
        """
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Deposit amount must be a positive number.")
        self._cash_balance += amount
        self._total_deposits += amount
        self._record_transaction(type='DEPOSIT', total_amount=amount)

    def withdraw(self, amount: float) -> None:
        """
        Withdraws funds from the account's cash balance.

        Args:
            amount (float): The amount of cash to withdraw.

        Raises:
            ValueError: If amount is not a positive number.
            InsufficientFundsError: If amount exceeds the cash balance.
        """
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Withdrawal amount must be a positive number.")
        if amount > self._cash_balance:
            raise InsufficientFundsError(f"Cannot withdraw ${amount:,.2f}: insufficient funds. "
                                         f"Current balance: ${self._cash_balance:,.2f}")
        self._cash_balance -= amount
        self._record_transaction(type='WITHDRAW', total_amount=amount)

    def buy_shares(self, symbol: str, quantity: int) -> None:
        """
        Purchases a specified quantity of shares for a given symbol.

        Args:
            symbol (str): The stock symbol to buy.
            quantity (int): The number of shares to buy.

        Raises:
            ValueError: If quantity is not a positive integer.
            UnknownSymbolError: If the symbol price cannot be retrieved.
            InsufficientFundsError: If the total cost exceeds the cash balance.
        """
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Quantity to buy must be a positive integer.")

        price = get_share_price(symbol)
        total_cost = price * quantity

        if total_cost > self._cash_balance:
            raise InsufficientFundsError(f"Cannot buy {quantity} of {symbol.upper()} for ${total_cost:,.2f}: "
                                         f"insufficient funds. Current balance: ${self._cash_balance:,.2f}")

        self._cash_balance -= total_cost
        normalized_symbol = symbol.upper()
        self._holdings[normalized_symbol] = self._holdings.get(normalized_symbol, 0) + quantity
        self._record_transaction(
            type='BUY',
            symbol=symbol,
            quantity=quantity,
            price_per_share=price,
            total_amount=total_cost
        )

    def sell_shares(self, symbol: str, quantity: int) -> None:
        """
        Sells a specified quantity of owned shares for a given symbol.

        Args:
            symbol (str): The stock symbol to sell.
            quantity (int): The number of shares to sell.

        Raises:
            ValueError: If quantity is not a positive integer.
            UnknownSymbolError: If the symbol price cannot be retrieved.
            InsufficientSharesError: If quantity exceeds the number of owned shares.
        """
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Quantity to sell must be a positive integer.")

        normalized_symbol = symbol.upper()
        shares_owned = self._holdings.get(normalized_symbol, 0)

        if quantity > shares_owned:
            raise InsufficientSharesError(f"Cannot sell {quantity} shares of {normalized_symbol}. "
                                          f"Only {shares_owned} shares are owned.")

        price = get_share_price(symbol)
        total_value = price * quantity

        self._cash_balance += total_value
        self._holdings[normalized_symbol] -= quantity

        if self._holdings[normalized_symbol] == 0:
            del self._holdings[normalized_symbol]

        self._record_transaction(
            type='SELL',
            symbol=symbol,
            quantity=quantity,
            price_per_share=price,
            total_amount=total_value
        )

    def get_cash_balance(self) -> float:
        """Returns the current cash balance."""
        return self._cash_balance

    def get_holdings(self) -> Dict[str, int]:
        """Returns a copy of the current share holdings."""
        return self._holdings.copy()

    def get_transaction_history(self) -> List[Dict[str, Union[str, int, float, None]]]:
        """Returns a copy of the chronological list of all transactions."""
        return self._transactions.copy()

    def get_portfolio_value(self) -> float:
        """
        Calculates the total current market value of all shares in the portfolio.

        Returns:
            float: The total market value of all owned shares.
        """
        total_value = 0.0
        for symbol, quantity in self._holdings.items():
            try:
                # In a real system, prices can become unavailable. In this simulation,
                # we assume any owned stock will have a price via get_share_price.
                total_value += get_share_price(symbol) * quantity
            except UnknownSymbolError:
                # This case should not be reached if buy_shares is the only
                # way to acquire shares. Log a warning if it ever happens.
                print(f"Warning: Price for owned symbol '{symbol}' not found. It will be valued at $0.")
        return total_value

    def get_total_value(self) -> float:
        """
        Calculates the total net worth of the account (cash + portfolio value).

        Returns:
            float: The total net worth of the account.
        """
        return self.get_cash_balance() + self.get_portfolio_value()

    def get_profit_loss(self) -> float:
        """
        Calculates the total profit or loss against all capital deposited.
        Withdrawals do not affect this calculation.

        Returns:
            float: The total profit or loss of the account.
        """
        return self.get_total_value() - self._total_deposits