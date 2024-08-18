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
    'Expiry', 'Option OHLC', '%K', '%D', 'Open', 'Close'
])

def print_valid_trades():
    if crossover_df.empty:
        console.print("[bold red]No valid trades found.[/bold red]")
        return

    table = Table(title="Valid Trades")

    columns_to_display = [
        'Timestamp', 'Futures Price', 'VWAP', 'Option Type', 'Strike Price',
        'Expiry', 'Option OHLC', '%K', '%D'
    ]

    for column in columns_to_display:
        table.add_column(column, style="cyan")

    for _, row in crossover_df.iterrows():
        row_color = "red" if row['Close'] > row['Open'] else "green"
        table.add_row(
            *[str(row[col]) for col in columns_to_display],
            style=row_color
        )

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

    # Store the options history fetched here
    historic_options_data = {}

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

    flag_stochastic_fulfilled = False

    for i in range(len(futures_df)):
        if above_vwap.iloc[i] or below_vwap.iloc[i]:
            current_price = futures_df['close'].iloc[i]
            option_type = 'Call' if above_vwap.iloc[i] else 'Put'
            strike_price = get_nearest_option(current_price, option_type)
            current_datetime_str = futures_df['datetime'].iloc[i]
            option_history_key = f"{str(strike_price)}-{option_type}"
            log.info(f"Checking at {current_datetime_str=} and {current_price=}")

            # Fetch option data
            if option_history_key in historic_options_data:
                option_df = historic_options_data[option_history_key]
            else:
                option_df = fetch_banknifty_options_history(strike_price, option_type)
                historic_options_data[option_history_key] = option_df

            if option_df is None:
                continue

            # Calculate VWAP and Stochastic for option data
            option_df = calculate_vwap(option_df)
            option_df = calculate_stochastic(option_df)

            # Filter options data based on current timestamp
            option_df = option_df[option_df.datetime == current_datetime_str]

            if option_df.empty:
                continue

            # Check for trade conditions
            if \
                (option_df['close'].iloc[-1] > option_df['VWAP'].iloc[-1] and
                option_df['%K'].iloc[-1] > option_df['%D'].iloc[-1] and
                option_df['%K'].iloc[-1] < 70):

                # Append to new_rows list
                new_rows.append({
                    'Timestamp': option_df['datetime'].iloc[-1],
                    'Futures Price': current_price,
                    'VWAP': round(option_df['VWAP'].iloc[-1], 2),
                    'Option Type': option_type,
                    'Strike Price': strike_price,
                    'Expiry': option_df['expiry_date'].iloc[-1],
                    'Option OHLC': f"O:{option_df['open'].iloc[-1]} H:{option_df['high'].iloc[-1]} L:{option_df['low'].iloc[-1]} C:{option_df['close'].iloc[-1]}",
                    '%K': round(option_df['%K'].iloc[-1], 2),
                    '%D': round(option_df['%D'].iloc[-1], 2),
                })

                flag_stochastic_fulfilled = True

            # If %K goes below the %D, then we wait for the new trade
            elif flag_stochastic_fulfilled and \
                option_df['%K'].iloc[-1] < option_df['%D'].iloc[-1]:
                flag_stochastic_fulfilled = False

    # Add new rows to crossover_df only if there are any
    if new_rows:
        new_df = pd.DataFrame(new_rows)
        crossover_df = pd.concat([crossover_df, new_df], ignore_index=True)

    # Print valid trades at the end
    print_valid_trades()

# if __name__ == "__main__":
#     run_strategy()