import unittest
from unittest.mock import patch, ANY
from datetime import datetime

# Assuming accounts.py is in the same directory
from accounts import (
    Account,
    get_share_price,
    InsufficientFundsError,
    InsufficientSharesError,
    UnknownSymbolError,
)

# A fixed timestamp for predictable transaction records
MOCK_TIMESTAMP = datetime(2023, 10, 27, 10, 0, 0)
MOCK_ISO_TIMESTAMP = MOCK_TIMESTAMP.isoformat()


class TestGetSharePrice(unittest.TestCase):
    """Tests for the get_share_price helper function."""

    def test_get_price_known_symbol(self):
        """Test retrieving the price for a known symbol."""
        self.assertEqual(get_share_price('AAPL'), 150.00)
        self.assertEqual(get_share_price('GOOGL'), 2750.00)

    def test_get_price_case_insensitive(self):
        """Test that symbol lookup is case-insensitive."""
        self.assertEqual(get_share_price('aapl'), 150.00)
        self.assertEqual(get_share_price('gOOgl'), 2750.00)

    def test_get_price_unknown_symbol(self):
        """Test that an unknown symbol raises UnknownSymbolError."""
        with self.assertRaises(UnknownSymbolError):
            get_share_price('UNKNOWN')
        with self.assertRaisesRegex(UnknownSymbolError, "No price data found for symbol: FAKE"):
            get_share_price('FAKE')


@patch('accounts.datetime')
class TestAccount(unittest.TestCase):
    """Tests for the Account class."""

    def setUp(self):
        """Set up a fresh account instance for each test."""
        # This setup is used by tests that need a pre-funded account.
        # Tests for initialization will create their own instances.
        self.account = Account("acc123", "Test User", initial_deposit=10000.0)

    # === Initialization Tests ===
    def test_account_initialization_with_deposit(self, mock_dt):
        """Test creating an account with a positive initial deposit."""
        mock_dt.utcnow.return_value = MOCK_TIMESTAMP
        acc = Account("id_init", "Init User", initial_deposit=5000.0)
        self.assertEqual(acc.get_cash_balance(), 5000.0)
        self.assertEqual(acc._total_deposits, 5000.0)
        self.assertEqual(acc.get_holdings(), {})
        
        history = acc.get_transaction_history()
        self.assertEqual(len(history), 1)
        self.assertDictEqual(history[0], {
            'timestamp': MOCK_ISO_TIMESTAMP, 'type': 'DEPOSIT', 'symbol': None,
            'quantity': None, 'price_per_share': None, 'total_amount': 5000.0
        })

    def test_account_initialization_no_deposit(self, mock_dt):
        """Test creating an account with zero initial deposit."""
        acc = Account("id_zero", "Zero User", initial_deposit=0.0)
        self.assertEqual(acc.get_cash_balance(), 0.0)
        self.assertEqual(acc._total_deposits, 0.0)
        self.assertEqual(len(acc.get_transaction_history()), 0)

    def test_account_initialization_negative_deposit(self, mock_dt):
        """Test that a negative initial deposit raises ValueError."""
        with self.assertRaisesRegex(ValueError, "Initial deposit cannot be negative."):
            Account("id_neg", "Neg User", initial_deposit=-100.0)

    # === Deposit and Withdraw Tests ===
    def test_deposit_positive_amount(self, mock_dt):
        """Test a valid deposit increases balance and is recorded."""
        mock_dt.utcnow.return_value = MOCK_TIMESTAMP
        self.account.deposit(500.0)
        self.assertEqual(self.account.get_cash_balance(), 10500.0)
        self.assertEqual(self.account._total_deposits, 10500.0)
        
        history = self.account.get_transaction_history()
        self.assertEqual(len(history), 1) # No initial deposit tx in setUp
        self.assertDictEqual(history[-1], {
            'timestamp': MOCK_ISO_TIMESTAMP, 'type': 'DEPOSIT', 'symbol': None,
            'quantity': None, 'price_per_share': None, 'total_amount': 500.0
        })

    def test_deposit_non_positive_amount(self, mock_dt):
        """Test that depositing zero or a negative amount raises ValueError."""
        with self.assertRaisesRegex(ValueError, "Deposit amount must be a positive number."):
            self.account.deposit(0)
        with self.assertRaisesRegex(ValueError, "Deposit amount must be a positive number."):
            self.account.deposit(-50.0)
        with self.assertRaises(ValueError):
            self.account.deposit("not a number")

    def test_withdraw_valid_amount(self, mock_dt):
        """Test a valid withdrawal decreases balance and is recorded."""
        mock_dt.utcnow.return_value = MOCK_TIMESTAMP
        self.account.withdraw(1000.0)
        self.assertEqual(self.account.get_cash_balance(), 9000.0)
        # Total deposits should not change on withdrawal
        self.assertEqual(self.account._total_deposits, 10000.0)

        history = self.account.get_transaction_history()
        self.assertDictEqual(history[-1], {
            'timestamp': MOCK_ISO_TIMESTAMP, 'type': 'WITHDRAW', 'symbol': None,
            'quantity': None, 'price_per_share': None, 'total_amount': 1000.0
        })

    def test_withdraw_insufficient_funds(self, mock_dt):
        """Test withdrawing more than the available balance raises InsufficientFundsError."""
        with self.assertRaises(InsufficientFundsError):
            self.account.withdraw(10000.01)
        with self.assertRaisesRegex(InsufficientFundsError, "insufficient funds"):
            self.account.withdraw(20000.0)

    def test_withdraw_non_positive_amount(self, mock_dt):
        """Test that withdrawing zero or a negative amount raises ValueError."""
        with self.assertRaisesRegex(ValueError, "Withdrawal amount must be a positive number."):
            self.account.withdraw(0)
        with self.assertRaisesRegex(ValueError, "Withdrawal amount must be a positive number."):
            self.account.withdraw(-50.0)
        with self.assertRaises(ValueError):
            self.account.withdraw("not a number")

    # === Share Trading Tests ===
    def test_buy_shares_success(self, mock_dt):
        """Test a successful share purchase."""
        mock_dt.utcnow.return_value = MOCK_TIMESTAMP
        self.account.buy_shares('AAPL', 10)  # Cost: 10 * 150 = 1500
        self.assertAlmostEqual(self.account.get_cash_balance(), 8500.0)
        self.assertDictEqual(self.account.get_holdings(), {'AAPL': 10})
        
        history = self.account.get_transaction_history()
        self.assertDictEqual(history[-1], {
            'timestamp': MOCK_ISO_TIMESTAMP, 'type': 'BUY', 'symbol': 'AAPL',
            'quantity': 10, 'price_per_share': 150.0, 'total_amount': 1500.0
        })

    def test_buy_shares_insufficient_funds(self, mock_dt):
        """Test buying shares with not enough cash."""
        with self.assertRaises(InsufficientFundsError):
            self.account.buy_shares('GOOGL', 4)  # Cost: 4 * 2750 = 11000
        self.assertEqual(self.account.get_cash_balance(), 10000.0)
        self.assertEqual(self.account.get_holdings(), {})

    def test_buy_shares_unknown_symbol(self, mock_dt):
        """Test buying shares of an unknown symbol."""
        with self.assertRaises(UnknownSymbolError):
            self.account.buy_shares('FAKE', 10)

    def test_buy_shares_invalid_quantity(self, mock_dt):
        """Test buying shares with an invalid quantity."""
        with self.assertRaisesRegex(ValueError, "Quantity to buy must be a positive integer."):
            self.account.buy_shares('TSLA', 0)
        with self.assertRaisesRegex(ValueError, "Quantity to buy must be a positive integer."):
            self.account.buy_shares('TSLA', -5)
        with self.assertRaisesRegex(ValueError, "Quantity to buy must be a positive integer."):
            self.account.buy_shares('TSLA', 2.5)

    def test_sell_shares_success_partial(self, mock_dt):
        """Test a successful partial sale of owned shares."""
        mock_dt.utcnow.return_value = MOCK_TIMESTAMP
        self.account.buy_shares('TSLA', 10) # Balance: 10000 - (700.50 * 10) = 2995.0
        self.assertAlmostEqual(self.account.get_cash_balance(), 2995.0)

        # Now sell 4 shares
        self.account.sell_shares('tsla', 4) # Gain: 4 * 700.50 = 2802.0
        self.assertAlmostEqual(self.account.get_cash_balance(), 2995.0 + 2802.0)
        self.assertDictEqual(self.account.get_holdings(), {'TSLA': 6})
        
        history = self.account.get_transaction_history()
        self.assertDictEqual(history[-1], {
            'timestamp': ANY, 'type': 'SELL', 'symbol': 'TSLA',
            'quantity': 4, 'price_per_share': 700.50, 'total_amount': 2802.0
        })

    def test_sell_shares_success_all(self, mock_dt):
        """Test selling all shares of a symbol removes it from holdings."""
        self.account.buy_shares('AAPL', 5) # Holdings: {'AAPL': 5}
        self.account.sell_shares('AAPL', 5)
        self.assertDictEqual(self.account.get_holdings(), {})

    def test_sell_shares_insufficient_shares(self, mock_dt):
        """Test selling more shares than owned."""
        self.account.buy_shares('AAPL', 5)
        with self.assertRaises(InsufficientSharesError):
            self.account.sell_shares('AAPL', 6)
        with self.assertRaisesRegex(InsufficientSharesError, "Only 5 shares are owned"):
            self.account.sell_shares('AAPL', 6)

    def test_sell_shares_not_owned(self, mock_dt):
        """Test selling shares of a symbol that is not owned."""
        with self.assertRaises(InsufficientSharesError):
            self.account.sell_shares('GOOGL', 1)
        with self.assertRaisesRegex(InsufficientSharesError, "Only 0 shares are owned"):
            self.account.sell_shares('GOOGL', 1)
    
    def test_sell_shares_invalid_quantity(self, mock_dt):
        """Test selling shares with an invalid quantity."""
        self.account.buy_shares('AAPL', 5)
        with self.assertRaisesRegex(ValueError, "Quantity to sell must be a positive integer."):
            self.account.sell_shares('AAPL', 0)
        with self.assertRaisesRegex(ValueError, "Quantity to sell must be a positive integer."):
            self.account.sell_shares('AAPL', -1)
        with self.assertRaisesRegex(ValueError, "Quantity to sell must be a positive integer."):
            self.account.sell_shares('AAPL', 1.5)

    # === Getter and Calculation Tests ===
    def test_getters_return_copies(self, mock_dt):
        """Test that getter methods for holdings and history return copies."""
        self.account.buy_shares('AAPL', 1)
        
        holdings_copy = self.account.get_holdings()
        holdings_copy['AAPL'] = 99
        self.assertEqual(self.account.get_holdings()['AAPL'], 1)

        history_copy = self.account.get_transaction_history()
        history_copy.append("malicious entry")
        self.assertEqual(len(self.account.get_transaction_history()), 1)

    def test_get_portfolio_value(self, mock_dt):
        """Test calculation of total portfolio value."""
        self.assertEqual(self.account.get_portfolio_value(), 0.0)
        self.account.buy_shares('AAPL', 10)  # 1500
        self.account.buy_shares('TSLA', 2)   # 1401
        expected_value = (150.0 * 10) + (700.50 * 2)
        self.assertAlmostEqual(self.account.get_portfolio_value(), expected_value)
    
    def test_get_total_value(self, mock_dt):
        """Test calculation of total account value (cash + portfolio)."""
        # Initial state: 10000 cash, 0 portfolio
        self.assertAlmostEqual(self.account.get_total_value(), 10000.0)
        # After buying, total value should be unchanged (value moved from cash to shares)
        self.account.buy_shares('AAPL', 10) # Cost 1500
        self.assertAlmostEqual(self.account.get_total_value(), 10000.0)
        self.assertAlmostEqual(self.account.get_cash_balance(), 8500.0)
        self.assertAlmostEqual(self.account.get_portfolio_value(), 1500.0)
    
    def test_get_profit_loss(self, mock_dt):
        """Test calculation of profit and loss."""
        # Initial P/L is 0
        self.assertAlmostEqual(self.account.get_profit_loss(), 0.0)
        
        # Buying shares doesn't change P/L if price is stable
        self.account.buy_shares('AAPL', 10) # cost 1500
        self.assertAlmostEqual(self.account.get_profit_loss(), 0.0)

        # A withdrawal should not affect P/L calculation
        self.account.withdraw(500)
        self.assertAlmostEqual(self.account.get_cash_balance(), 8000.0)
        self.assertAlmostEqual(self.account._total_deposits, 10000.0)
        self.assertAlmostEqual(self.account.get_profit_loss(), 0.0)

        # Simulate a price change to check P/L
        with patch('accounts.get_share_price') as mock_get_price:
            mock_get_price.return_value = 160.0  # AAPL price goes up by $10
            # P/L = (current_value - deposits)
            # current_value = cash + portfolio_value = 8000 + (10 * 160) = 9600
            # deposits = 10000
            # P/L = 9600 - 10000 = -400.0
            self.assertAlmostEqual(self.account.get_profit_loss(), -400.0)

            # Selling at a profit
            self.account.sell_shares('AAPL', 10) # Sells for 10 * 160 = 1600
            # cash = 8000 + 1600 = 9600
            # holdings value = 0
            # total value = 9600
            # P/L = 9600 - 10000 = -400
            self.assertAlmostEqual(self.account.get_profit_loss(), -400.0)
            

if __name__ == '__main__':
    unittest.main(verbosity=2)