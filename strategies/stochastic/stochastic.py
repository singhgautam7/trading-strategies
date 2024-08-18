import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from rich.table import Table
from rich.console import Console
import smtplib
from email.mime.text import MIMEText
from ta.momentum import StochasticOscillator
from api.breeze.breeze import BreezeAPI
from strategies.stochastic.historic_data import fetch_banknifty_futures_history, fetch_banknifty_options_history

log = logging.getLogger(__name__)
console = Console()

# Global variable to store crossover data
crossover_df = pd.DataFrame(columns=[
    'Timestamp', 'Futures Price', 'VWAP', 'Option Type', 'Strike Price',
    'Option Open', 'Option High', 'Option Low', 'Option Close', '%K', '%D'
])

def print_valid_trades():
    if crossover_df.empty:
        console.print("[bold red]No valid trades found.[/bold red]")
        return

    table = Table(title="Valid Trades")

    for column in crossover_df.columns:
        table.add_column(column, style="cyan")

    for _, row in crossover_df.iterrows():
        table.add_row(*[str(val) for val in row])

    console.print(table)

def calculate_vwap(df):
    df['VWAP'] = (df['volume'] * df['close']).cumsum() / df['volume'].cumsum()
    return df

def calculate_stochastic_inbuilt(df, k_period=5, d_period=3):
    low_min = df['low'].rolling(window=k_period).min()
    high_max = df['high'].rolling(window=k_period).max()

    df['%K'] = 100 * (df['close'] - low_min) / (high_max - low_min)
    df['%D'] = df['%K'].rolling(window=d_period).mean()

    return df

def calculate_stochastic(df, k_period=5, d_period=3):
    stoch = StochasticOscillator(df['high'], df['low'], df['close'], k_period, d_period)
    df['%K'] = stoch.stoch()
    df['%D'] = stoch.stoch_signal()
    return df

def check_vwap_condition(df):
    above_vwap = (df['close'] > df['VWAP']).rolling(window=6).sum() == 6
    below_vwap = (df['close'] < df['VWAP']).rolling(window=6).sum() == 6
    return above_vwap, below_vwap

def get_nearest_option(current_price, option_type, step=100):
    rounded_price = round(current_price / step) * step
    if option_type == 'Call':
        return rounded_price if rounded_price < current_price else rounded_price - step
    else:  # Put
        return rounded_price if rounded_price > current_price else rounded_price + step

def send_email_alert(subject, body):
    sender_email = "your_email@example.com"
    receiver_email = "receiver_email@example.com"
    password = "your_email_password"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, password)
        server.send_message(msg)

def run_strategy():
    global crossover_df
    breeze = BreezeAPI()
    breeze.connect()

    # Fetch Bank Nifty futures data
    futures_df = fetch_banknifty_futures_history()
    if futures_df is None:
        return

    # Calculate VWAP
    futures_df = calculate_vwap(futures_df)

    # Check VWAP conditions
    above_vwap, below_vwap = check_vwap_condition(futures_df)

    # List to collect new rows
    new_rows = []

    for i in range(len(futures_df)):
        if above_vwap.iloc[i] or below_vwap.iloc[i]:
            current_price = futures_df['close'].iloc[i]
            option_type = 'Call' if above_vwap.iloc[i] else 'Put'
            strike_price = get_nearest_option(current_price, option_type)

            # Fetch option data
            option_df = fetch_banknifty_options_history(strike_price, option_type)
            if option_df is None:
                continue

            # Calculate VWAP and Stochastic for option data
            option_df = calculate_vwap(option_df)
            option_df = calculate_stochastic(option_df)

            # Check for trade conditions
            if (option_df['close'].iloc[-1] > option_df['VWAP'].iloc[-1] and
                option_df['%K'].iloc[-1] > option_df['%D'].iloc[-1] and
                option_df['%K'].iloc[-1] < 70):

                # Append to new_rows list
                new_rows.append({
                    'Timestamp': option_df.index[-1],
                    'Futures Price': current_price,
                    'VWAP': option_df['VWAP'].iloc[-1],
                    'Option Type': option_type,
                    'Strike Price': strike_price,
                    'Option Open': option_df['open'].iloc[-1],
                    'Option High': option_df['high'].iloc[-1],
                    'Option Low': option_df['low'].iloc[-1],
                    'Option Close': option_df['close'].iloc[-1],
                    '%K': option_df['%K'].iloc[-1],
                    '%D': option_df['%D'].iloc[-1]
                })

                # subject = f"Trade Alert: Bank Nifty {option_type} Option"
                # body = f"""
                # Trade possibility detected:
                # Date: {option_df.index[-1]}
                # Option Type: {option_type}
                # Strike Price: {strike_price}
                # Current Price: {option_df['close'].iloc[-1]}
                # VWAP: {option_df['VWAP'].iloc[-1]}
                # %K: {option_df['%K'].iloc[-1]}
                # %D: {option_df['%D'].iloc[-1]}
                # """
                # send_email_alert(subject, body)

    # Add new rows to crossover_df only if there are any
    if new_rows:
        new_df = pd.DataFrame(new_rows)
        crossover_df = pd.concat([crossover_df, new_df], ignore_index=True)

    # Print valid trades at the end
    print_valid_trades()

# if __name__ == "__main__":
#     run_strategy()