import pandas as pd
import numpy as np
from ta.momentum import StochasticOscillator
import logging

log = logging.getLogger(__name__)

def calculate_vwap(df):
    df['VWAP'] = (df['high'] + df['low'] + df['close']) / 3
    df['VWAP'] = (df['VWAP'] * df['volume']).cumsum() / df['volume'].cumsum()
    return df

def apply_stochastic_strategy(df, k_period=5, d_period=3, smooth_k=3):
    """
    Apply the stochastic strategy to the given dataframe.

    :param df: DataFrame with 'high', 'low', 'close' columns
    :param k_period: %K period
    :param d_period: %D period
    :param smooth_k: %K smoothing period
    :return: DataFrame with stochastic indicators and signals
    """
    # Calculate VWAP
    df = calculate_vwap(df)

    # Calculate Stochastic Oscillator
    stoch = StochasticOscillator(high=df['high'], low=df['low'], close=df['close'],
                                 window=k_period, smooth_window=smooth_k)
    df['%K'] = stoch.stoch()
    df['%D'] = stoch.stoch_signal()

    # Generate signals
    df['above_vwap'] = df['close'] > df['VWAP']
    df['k_above_d'] = df['%K'] > df['%D']
    df['prev_k_above_d'] = df['k_above_d'].shift(1)

    # Crossover signals
    df['stoch_crossover'] = (df['k_above_d'] != df['prev_k_above_d']) & (df['%K'] < 70) & (df['%D'] < 70)

    # Generate buy signals
    df['buy_signal'] = df['above_vwap'] & df['stoch_crossover'] & df['k_above_d']

    return df

def select_option(futures_price, step=100):
    """
    Select the ATM or ITM option based on the futures price.

    :param futures_price: Current futures price
    :param step: Step size for strike prices (default 100 for Bank Nifty)
    :return: Selected strike price
    """
    return round(futures_price / step) * step