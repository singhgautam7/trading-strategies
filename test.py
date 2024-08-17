import pandas as pd
import numpy as np
import requests
import smtplib
from email.mime.text import MIMEText
from ta import add_all_ta_features
from ta.volume import VolumeWeightedAveragePrice
from ta.momentum import StochasticOscillator
import schedule
import time
from dotenv import load_dotenv
import os

# Load environment variables from the .env file (if present)
load_dotenv()

def get_futures_data(symbol, interval='5min'):
    """
    Generic function to fetch futures data for a given symbol.

    Args:
    symbol (str): The symbol to fetch data for (e.g., 'BANKNIFTY', 'NIFTY')
    interval (str): The time interval for the data (default: '5min')

    Returns:
    pandas.DataFrame: DataFrame containing the futures data
    """
    # Placeholder for API call
    # You'll need to implement the actual API call based on your data provider
    url = f"https://api.example.com/futures/{symbol}?interval={interval}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        data = response.json()

        # Convert the JSON data to a pandas DataFrame
        df = pd.DataFrame(data)

        # Ensure the DataFrame has the required columns
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"Missing required columns. Expected: {required_columns}")

        # Convert timestamp to datetime and set as index
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)

        return df

    except requests.RequestException as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

def get_option_data(symbol, strike_price, option_type, interval='5min'):
    """
    Generic function to fetch option data for a given symbol, strike price, and option type.

    Args:
    symbol (str): The underlying symbol (e.g., 'BANKNIFTY', 'NIFTY')
    strike_price (float): The strike price of the option
    option_type (str): The type of option ('CALL' or 'PUT')
    interval (str): The time interval for the data (default: '5min')

    Returns:
    pandas.DataFrame: DataFrame containing the option data
    """
    # Placeholder for API call
    # You'll need to implement the actual API call based on your data provider
    url = f"https://api.example.com/options/{symbol}?strike={strike_price}&type={option_type}&interval={interval}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        df = pd.DataFrame(data)

        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"Missing required columns. Expected: {required_columns}")

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)

        return df

    except requests.RequestException as e:
        print(f"Error fetching option data for {symbol} {strike_price} {option_type}: {e}")
        return None

def calculate_indicators(df):
    # Ensure the dataframe has the required columns
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"Missing required columns. Expected: {required_columns}")

    # Calculate VWAP
    vwap = VolumeWeightedAveragePrice(high=df['high'], low=df['low'], close=df['close'], volume=df['volume'], window=14)
    df['VWAP'] = vwap.volume_weighted_average_price()

    # Calculate Stochastic Oscillator
    stoch = StochasticOscillator(high=df['high'], low=df['low'], close=df['close'], window=5, smooth_window=3)
    df['%K'] = stoch.stoch()
    df['%D'] = stoch.stoch_signal()

    return df

def check_conditions(futures_df, options_df):
    # Check if conditions are met for generating a signal
    last_candle = options_df.iloc[-1]
    prev_candle = options_df.iloc[-2]

    # Check if price is above VWAP
    price_above_vwap = last_candle['close'] > last_candle['VWAP']

    # Check if %K just crossed above %D below the upper band of 70
    stoch_crossover = (prev_candle['%K'] <= prev_candle['%D']) and (last_candle['%K'] > last_candle['%D'])
    below_upper_band = last_candle['%K'] < 70 and last_candle['%D'] < 70

    return price_above_vwap and stoch_crossover and below_upper_band

def send_email(subject, body):
    # Function to send email alerts
    sender = "your_email@gmail.com"
    recipient = "recipient@example.com"
    password = "your_email_password"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
        smtp_server.login(sender, password)
        smtp_server.sendmail(sender, recipient, msg.as_string())


def main():
    symbol = "BANKNIFTY"  # This can be changed to "NIFTY" or any other symbol
    futures_df = get_futures_data(symbol)

    if futures_df is not None:
        futures_df = calculate_indicators(futures_df)

        # Determine ATM/ITM option based on futures price
        current_price = futures_df['close'].iloc[-1]
        strike_price = round(current_price / 100) * 100  # Round to nearest 100

        call_options_df = get_option_data(symbol, strike_price, 'CALL')
        put_options_df = get_option_data(symbol, strike_price, 'PUT')

        if call_options_df is not None:
            call_options_df = calculate_indicators(call_options_df)
            if check_conditions(futures_df, call_options_df):
                send_email("Trade Alert", f"Potential {symbol} CALL trade opportunity")

        if put_options_df is not None:
            put_options_df = calculate_indicators(put_options_df)
            if check_conditions(futures_df, put_options_df):
                send_email("Trade Alert", f"Potential {symbol} PUT trade opportunity")
    else:
        print(f"Failed to fetch futures data for {symbol}")


if __name__ == "__main__":
    BREEZE_API_KEY = os.getenv("BREEZE_API_KEY")
    print(f"{BREEZE_API_KEY = }")
    # # Run the script every 5 minutes
    # schedule.every(5).minutes.do(main)

    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)
