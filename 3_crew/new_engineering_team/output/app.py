import gradio as gr
import pandas as pd
from accounts import Account, TradingError, get_share_price

# --- 1. Initial Setup: Create the single account instance for the demo ---
# We instantiate the account globally to maintain its state throughout the app's life.
# This approach is suitable for a simple, single-user demonstration.
try:
    # Initialize with a starting deposit to make the demo more interactive
    trading_account = Account(
        account_id="gradio_demo_001",
        user_name="Demo User",
        initial_deposit=10000.00
    )
except Exception as e:
    # Handle potential init errors, though unlikely with this setup
    print(f"FATAL: Failed to initialize account: {e}")
    trading_account = None

# --- 2. Helper Functions for UI updates ---

def format_holdings_to_df(holdings_dict: dict) -> pd.DataFrame:
    """Converts the holdings dictionary to a pandas DataFrame for display."""
    if not holdings_dict:
        return pd.DataFrame(columns=["Symbol", "Quantity"])
    
    # Add current price and value for a richer display
    data = []
    for symbol, quantity in holdings_dict.items():
        try:
            price = get_share_price(symbol)
            value = price * quantity
            data.append([symbol, quantity, f"${price:,.2f}", f"${value:,.2f}"])
        except TradingError:
            data.append([symbol, quantity, "N/A", "N/A"])

    return pd.DataFrame(data, columns=["Symbol", "Quantity", "Current Price", "Current Value"])

def format_transactions_to_df(transactions_list: list) -> pd.DataFrame:
    """Converts the transaction list to a pandas DataFrame for display."""
    if not transactions_list:
        return pd.DataFrame(columns=['Timestamp', 'Type', 'Symbol', 'Quantity', 'Price/Share', 'Total Amount'])
    
    df = pd.DataFrame(transactions_list)
    # Format and rename columns for presentation
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    df['total_amount'] = df['total_amount'].apply(lambda x: f"${x:,.2f}")
    df['price_per_share'] = df['price_per_share'].apply(lambda p: f"${p:,.2f}" if p is not None else "N/A")
    df.rename(columns={
        'timestamp': 'Timestamp',
        'type': 'Type',
        'symbol': 'Symbol',
        'quantity': 'Quantity',
        'price_per_share': 'Price/Share',
        'total_amount': 'Total Amount'
    }, inplace=True)
    
    return df[['Timestamp', 'Type', 'Symbol', 'Quantity', 'Price/Share', 'Total Amount']]

def get_all_metrics(account: Account):
    """Gathers all key metrics from the account object for a UI refresh."""
    if not account:
        # Return default empty values if account initialization failed
        empty_holdings = format_holdings_to_df({})
        empty_tx = format_transactions_to_df([])
        return "$0.00", "$0.00", "$0.00", "$0.00", empty_holdings, empty_tx

    cash = f"${account.get_cash_balance():,.2f}"
    portfolio_val = f"${account.get_portfolio_value():,.2f}"
    total_val = f"${account.get_total_value():,.2f}"
    pnl = f"${account.get_profit_loss():,.2f}"
    holdings_df = format_holdings_to_df(account.get_holdings())
    transactions_df = format_transactions_to_df(account.get_transaction_history())
    return cash, portfolio_val, total_val, pnl, holdings_df, transactions_df

# --- 3. Gradio Event Handler Functions ---

def handle_deposit(amount):
    """Processes a deposit request and returns all updated metrics."""
    if not trading_account:
        return "ERROR: Account not initialized.", *get_all_metrics(None)
    try:
        trading_account.deposit(float(amount))
        message = f"Success: Deposited ${amount:,.2f}."
    except (ValueError, TradingError) as e:
        message = f"Error: {e}"
    
    return message, *get_all_metrics(trading_account)

def handle_withdraw(amount):
    """Processes a withdrawal request and returns all updated metrics."""
    if not trading_account:
        return "ERROR: Account not initialized.", *get_all_metrics(None)
    try:
        trading_account.withdraw(float(amount))
        message = f"Success: Withdrew ${amount:,.2f}."
    except (ValueError, TradingError) as e:
        message = f"Error: {e}"
        
    return message, *get_all_metrics(trading_account)

def handle_buy(symbol, quantity):
    """Processes a buy shares request and returns all updated metrics."""
    if not trading_account:
        return "ERROR: Account not initialized.", *get_all_metrics(None)
    if not symbol or not quantity or int(quantity) <= 0:
        message = "Error: Please provide a valid symbol and a positive quantity."
        return message, *get_all_metrics(trading_account)
    try:
        trading_account.buy_shares(symbol, int(quantity))
        message = f"Success: Bought {int(quantity)} shares of {symbol}."
    except (ValueError, TradingError) as e:
        message = f"Error: {e}"
        
    return message, *get_all_metrics(trading_account)

def handle_sell(symbol, quantity):
    """Processes a sell shares request and returns all updated metrics."""
    if not trading_account:
        return "ERROR: Account not initialized.", *get_all_metrics(None)
    if not symbol or not quantity or int(quantity) <= 0:
        message = "Error: Please provide a valid symbol and a positive quantity."
        return message, *get_all_metrics(trading_account)
    try:
        trading_account.sell_shares(symbol, int(quantity))
        message = f"Success: Sold {int(quantity)} shares of {symbol}."
    except (ValueError, TradingError) as e:
        message = f"Error: {e}"
        
    return message, *get_all_metrics(trading_account)

# --- 4. Gradio UI Definition ---

with gr.Blocks(theme=gr.themes.Soft(), title="Trading Account Demo") as demo:
    gr.Markdown("# Simple Trading Account Demo")
    gr.Markdown("A prototype interface to demonstrate the features of the `Account` backend class. All values are in USD.")

    with gr.Row():
        cash_balance_out = gr.Textbox(label="Cash Balance", interactive=False)
        portfolio_value_out = gr.Textbox(label="Portfolio Value (Current)", interactive=False)
        total_value_out = gr.Textbox(label="Total Account Value", interactive=False)
        pnl_out = gr.Textbox(label="Profit / Loss", interactive=False)

    status_message_out = gr.Textbox(label="Status / Message Log", interactive=False, lines=1)

    with gr.Tabs():
        with gr.TabItem("Portfolio & Actions"):
            with gr.Row():
                with gr.Column(scale=2):
                    gr.Markdown("### Current Holdings")
                    holdings_out = gr.DataFrame(
                        interactive=False, 
                        row_count=(4, "dynamic")
                    )
                with gr.Column(scale=1):
                    with gr.Group():
                        gr.Markdown("#### Cash Actions")
                        cash_amount_in = gr.Number(label="Amount ($)", minimum=0.01, value=1000)
                        with gr.Row():
                            deposit_btn = gr.Button("Deposit", variant="primary")
                            withdraw_btn = gr.Button("Withdraw")
                    with gr.Group():
                        gr.Markdown("#### Trade Actions")
                        trade_symbol_in = gr.Dropdown(label="Stock Symbol", choices=['AAPL', 'GOOGL', 'TSLA'], value='AAPL')
                        trade_quantity_in = gr.Number(label="Quantity", minimum=1, precision=0, value=10)
                        with gr.Row():
                            buy_btn = gr.Button("Buy Shares", variant="primary")
                            sell_btn = gr.Button("Sell Shares")
        
        with gr.TabItem("Transaction History"):
            gr.Markdown("A log of all deposits, withdrawals, and trades.")
            transactions_out = gr.DataFrame(
                interactive=False,
                row_count=(10, "dynamic"),
                wrap=True
            )

    # List of all output components to be updated by actions
    outputs = [
        status_message_out,
        cash_balance_out,
        portfolio_value_out,
        total_value_out,
        pnl_out,
        holdings_out,
        transactions_out
    ]

    # --- 5. Connect UI components to functions ---

    deposit_btn.click(fn=handle_deposit, inputs=[cash_amount_in], outputs=outputs)
    withdraw_btn.click(fn=handle_withdraw, inputs=[cash_amount_in], outputs=outputs)
    buy_btn.click(fn=handle_buy, inputs=[trade_symbol_in, trade_quantity_in], outputs=outputs)
    sell_btn.click(fn=handle_sell, inputs=[trade_symbol_in, trade_quantity_in], outputs=outputs)

    # Initial load of data when the app starts
    def initial_load():
        initial_message = "Account loaded successfully with initial deposit." if trading_account else "ERROR: Account failed to load."
        metrics = get_all_metrics(trading_account)
        return initial_message, *metrics

    demo.load(fn=initial_load, inputs=None, outputs=outputs)

if __name__ == "__main__":
    if trading_account:
        print("Launching Gradio Demo...")
        demo.launch()
    else:
        print("Could not start the Gradio application because the account failed to initialize.")
