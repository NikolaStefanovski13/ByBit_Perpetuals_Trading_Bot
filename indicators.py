import pandas as pd

class Indicators:
    @staticmethod
    def calculate_atr(df, period=14):
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr

    @staticmethod
    def chandelier_exit(df, atr, atr_period, multiplier=3.0):
        highest_high = df['high'].rolling(window=atr_period).max()
        return highest_high - (atr * multiplier)

    @staticmethod
    def moving_average(df, window=50):
        return df['close'].rolling(window=window).mean()

    @staticmethod
    def fibonacci_retracement(df):
        high = df['close'].max()
        low = df['close'].min()
        diff = high - low
        return {
            "0%": high,
            "23.6%": high - 0.236 * diff,
            "38.2%": high - 0.382 * diff,
            "50%": high - 0.5 * diff,
            "61.8%": high - 0.618 * diff,
            "78.6%": high - 0.786 * diff,
            "100%": low
        }