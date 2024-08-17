import pandas as pd
import numpy as np
from ta.momentum import StochasticOscillator
import logging
from datetime import datetime, timedelta

log = logging.getLogger(__name__)

def calculate_vwap(df):
    df['VWAP'] = (df['high'] + df['low'] + df['close']) / 3
    df['VWAP'] = (df['VWAP'] * df['volume']).cumsum() / df['volume'].cumsum()
    return df

def apply_stochastic_strategy(futures_df, options_df, k_period=5, d_period=3, smooth_k=3):
    """
    Apply the stochastic strategy to the given dataframes.

    :param futures_df: DataFrame with futures data
    :param options_df: DataFrame with options data
    :param k_period: %K period
    :param d_period: %D period
    :param smooth_k: %K smoothing period
    :return: DataFrame with stochastic indicators and signals
    """
    # Calculate VWAP for futures
    futures_df = calculate_vwap(futures_df)

    # Check if last 5 candles are above or below VWAP
    futures_df['above_vwap'] = futures_df['close'] > futures_df['VWAP']
    futures_df['below_vwap'] = futures_df['close'] < futures_df['VWAP']
    futures_df['last_5_above_vwap'] = futures_df['above_vwap'].rolling(window=5).sum() == 5
    futures_df['last_5_below_vwap'] = futures_df['below_vwap'].rolling(window=5).sum() == 5

    # Calculate Stochastic Oscillator for options
    stoch = StochasticOscillator(high=options_df['high'], low=options_df['low'], close=options_df['close'],
                                 window=k_period, smooth_window=smooth_k)
    options_df['%K'] = stoch.stoch()
    options_df['%D'] = stoch.stoch_signal()

    # Generate signals
    options_df['k_above_d'] = options_df['%K'] > options_df['%D']
    options_df['prev_k_above_d'] = options_df['k_above_d'].shift(1)

    # Crossover signals
    options_df['stoch_crossover'] = (options_df['k_above_d'] != options_df['prev_k_above_d']) & (options_df['%K'] < 70) & (options_df['%D'] < 70)

    return futures_df, options_df

def select_option(futures_price, option_type='call', step=100):
    """
    Select the ATM or ITM option based on the futures price.

    :param futures_price: Current futures price
    :param option_type: 'call' or 'put'
    :param step: Step size for strike prices (default 100 for Bank Nifty)
    :return: Selected strike price
    """
    rounded_price = round(futures_price / step) * step
    if option_type == 'call':
        return rounded_price if rounded_price <= futures_price else rounded_price - step
    else:  # put
        return rounded_price if rounded_price >= futures_price else rounded_price + step

def get_next_expiry(current_date):
    """
    Get the next Thursday (expiry day) from the given date.
    """
    days_ahead = 3 - current_date.weekday()  # Thursday is 3
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return current_date + timedelta(days=days_ahead)