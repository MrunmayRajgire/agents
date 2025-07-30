# Design Document: `accounts.py`

**To:** Backend Developer  
**From:** Engineering Lead  
**Date:** 2023-10-27  
**Subject:** Design for Trading Simulation Account Management System

Here is the detailed design for the `accounts.py` module. This module will be a self-contained unit for managing user accounts in our trading simulation platform. It should be implemented as a single Python file, ready for integration with a persistence layer or a simple UI.

## 1. Module Overview: `accounts.py`

This module provides the `Account` class, which encapsulates all the logic and data for a single user's trading account. It handles cash management (deposits, withdrawals), trade execution (buys, sells), and reporting (holdings, value, profit/loss, transaction history). The module is designed to be in-memory and has no external dependencies.

---

## 2. Module-Level Components

### 2.1. Custom Exceptions

To provide clear, specific error feedback, we will define the following custom exceptions at the module level. This allows the calling code (e.g., a UI) to catch specific errors and provide appropriate user feedback.

```python
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
```

### 2.2. Helper Functions

This helper function provides the interface to the "market" for fetching share prices. It includes a test implementation as required.

#### `get_share_price(symbol: str) -> float`

Retrieves the current market price for a given stock symbol.

*   **Parameters:**
    *   `symbol` (`str`): The stock symbol (e.g., 'AAPL').
*   **Returns:**
    *   `float`: The current price per share.
*   **Raises:**
    *   `UnknownSymbolError`: If the symbol is not found in the test data.
*   **Implementation Details:**
    *   The function should be case-insensitive regarding the symbol.
    *   A dictionary will be used for the test implementation.

```python
# Test data for share prices
_test_prices = {
    'AAPL': 150.00,
    'GOOGL': 2750.00,
    'TSLA': 700.50,
}

def get_share_price(symbol: str) -> float:
    # ... implementation here ...
```

---

## 3. Class Design: `Account`

The `Account` class is the core of the module. Each instance represents one user's account.

### 3.1. Class Description

Manages a user's cash balance, share holdings, and transaction history for a simulated trading environment. It enforces trading rules, such as preventing overdrafts or selling unowned shares.

### 3.2. Class Attributes

These attributes represent the internal state of an account. They should be treated as private (by convention, prefixed with an underscore `_`).

*   `_account_id` (`str`): A unique identifier for the account.
*   `_user_name` (`str`): The name of the account holder.
*   `_cash_balance` (`float`): The amount of cash available for trading or withdrawal.
*   `_total_deposits` (`float`): The cumulative sum of all cash deposits. This is the baseline for P/L calculation.
*   `_holdings` (`dict[str, int]`): A dictionary mapping stock symbols to the quantity of shares owned. Example: `{'AAPL': 10, 'TSLA': 5}`.
*   `_transactions` (`list[dict]`): A chronological list of all transactions. Each transaction is a dictionary containing details like `timestamp`, `type`, `symbol`, `quantity`, `price_per_share`, and `total_amount`.

### 3.3. Methods

#### `__init__(self, account_id: str, user_name: str, initial_deposit: float = 0.0)`

Initializes a new `Account` instance.

*   **Parameters:**
    *   `account_id` (`str`): The unique ID for this account.
    *   `user_name` (`str`): The name of the user.
    *   `initial_deposit` (`float`, optional): The starting cash balance. Defaults to `0.0`.
*   **Functionality:**
    *   Sets up the initial state: `_cash_balance`, `_total_deposits`, empty `_holdings`, and an empty `_transactions` list.
    *   If `initial_deposit` is greater than zero, it should be recorded as the first 'DEPOSIT' transaction.

---

#### `deposit(self, amount: float) -> None`

Adds funds to the account's cash balance.

*   **Parameters:**
    *   `amount` (`float`): The amount of cash to deposit. Must be a positive number.
*   **Raises:**
    *   `ValueError`: If `amount` is not a positive number.
*   **Functionality:**
    *   Increases `_cash_balance` by `amount`.
    *   Increases `_total_deposits` by `amount`.
    *   Records a 'DEPOSIT' transaction in `_transactions`.

---

#### `withdraw(self, amount: float) -> None`

Withdraws funds from the account's cash balance.

*   **Parameters:**
    *   `amount` (`float`): The amount of cash to withdraw. Must be a positive number.
*   **Raises:**
    *   `ValueError`: If `amount` is not a positive number.
    *   `InsufficientFundsError`: If `amount` exceeds `_cash_balance`.
*   **Functionality:**
    *   Decreases `_cash_balance` by `amount`.
    *   Records a 'WITHDRAW' transaction in `_transactions`.

---

#### `buy_shares(self, symbol: str, quantity: int) -> None`

Purchases a specified quantity of shares for a given symbol.

*   **Parameters:**
    *   `symbol` (`str`): The stock symbol to buy.
    *   `quantity` (`int`): The number of shares to buy. Must be a positive integer.
*   **Raises:**
    *   `ValueError`: If `quantity` is not a positive integer.
    *   `UnknownSymbolError`: If the symbol price cannot be retrieved.
    *   `InsufficientFundsError`: If the total cost (`price * quantity`) exceeds `_cash_balance`.
*   **Functionality:**
    *   Calls `get_share_price()` to get the current price.
    *   Calculates the total transaction cost.
    *   Verifies sufficient cash balance.
    *   Decreases `_cash_balance` by the total cost.
    *   Updates `_holdings`, adding the shares. If the symbol is new, add it; otherwise, increment the existing count.
    *   Records a 'BUY' transaction in `_transactions`.

---

#### `sell_shares(self, symbol: str, quantity: int) -> None`

Sells a specified quantity of owned shares for a given symbol.

*   **Parameters:**
    *   `symbol` (`str`): The stock symbol to sell.
    *   `quantity` (`int`): The number of shares to sell. Must be a positive integer.
*   **Raises:**
    *   `ValueError`: If `quantity` is not a positive integer.
    *   `UnknownSymbolError`: If the symbol price cannot be retrieved.
    *   `InsufficientSharesError`: If `quantity` exceeds the number of shares owned for that `symbol`.
*   **Functionality:**
    *   Calls `get_share_price()` to get the current price.
    *   Verifies the user owns enough shares to sell.
    *   Calculates the total sale value.
    *   Increases `_cash_balance` by the total value.
    *   Updates `_holdings`, decreasing the share count. If the count becomes zero, the symbol should be removed from the `_holdings` dictionary.
    *   Records a 'SELL' transaction in `_transactions`.

---

### 3.4. Reporting Methods

These methods provide read-only access to the account's state and calculated values.

#### `get_cash_balance(self) -> float`

*   **Returns:** The current cash balance.

#### `get_holdings(self) -> dict[str, int]`

*   **Returns:** A copy of the `_holdings` dictionary.

#### `get_transaction_history(self) -> list[dict]`

*   **Returns:** A copy of the `_transactions` list.

#### `get_portfolio_value(self) -> float`

*   **Functionality:**
    *   Iterates through all symbols in `_holdings`.
    *   For each symbol, calls `get_share_price()` and multiplies by the quantity owned.
    *   Sums the value of all holdings.
    *   Handles potential `UnknownSymbolError` gracefully (e.g., by logging a warning and skipping the symbol, or returning 0 for its value) for delisted stocks, though for this simulation, we can assume all owned stocks have a price.
*   **Returns:** The total current market value of all shares in the portfolio.

#### `get_total_value(self) -> float`

*   **Functionality:**
    *   Calculates the sum of `get_cash_balance()` and `get_portfolio_value()`.
*   **Returns:** The total net worth of the account (cash + shares).

#### `get_profit_loss(self) -> float`

*   **Functionality:**
    *   Calculates `get_total_value() - _total_deposits`. This reflects the overall gain or loss against the total capital invested by the user. Note that withdrawals do not affect this calculation.
*   **Returns:** The total profit or loss of the account.