from indicators import Indicators
import logging

class DataAnalyzer:
    def __init__(self, data):
        self.data = data

    def analyze_fibonacci_retracement(self):
        levels = Indicators.fibonacci_retracement(self.data)
        current_price = self.data['close'].iloc[-1]

        for level, price in levels.items():
            logging.info(f"{level} Level: {price:.2f}")

        if current_price >= levels["23.6%"]:
            logging.info(f"Current price is above the 23.6% level ({levels['23.6%']:.2f}). Considered bullish.")
        elif current_price >= levels["38.2%"]:
            logging.info(f"Current price is above the 38.2% level ({levels['38.2%']:.2f}). Considered neutral.")
        elif current_price >= levels["61.8%"]:
            logging.info(f"Current price is above the 61.8% level ({levels['61.8%']:.2f}). Considered bearish.")
        else:
            logging.info(f"Current price is below the 61.8% level ({levels['61.8%']:.2f}). Considered strongly bearish.")