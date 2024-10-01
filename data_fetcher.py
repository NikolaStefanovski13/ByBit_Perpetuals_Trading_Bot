import pandas as pd
import asyncio
import logging
from utils import handle_api_error

class DataFetcher:
    def __init__(self, exchange, config):
        self.exchange = exchange
        self.timeframe = config['timeframe']
        self.limit = config['limit']
        self.max_retries = 3
        self.retry_delay = 5

    async def fetch_historical_data(self, symbol):
        for attempt in range(self.max_retries):
            try:
                ohlcv = await self.exchange.fetch_ohlcv(symbol, self.timeframe, limit=self.limit)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                return df
            except Exception as e:
                logging.warning(f"Attempt {attempt + 1} failed to fetch data for {symbol}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    handle_api_error(e)
                    logging.error(f"Failed to fetch data for {symbol} after {self.max_retries} attempts")
        return pd.DataFrame()  # Return an empty DataFrame if all attempts fail

    async def fetch_order_book(self, symbol, depth=10):
        for attempt in range(self.max_retries):
            try:
                order_book = await self.exchange.fetch_order_book(symbol, depth)
                return order_book
            except Exception as e:
                logging.warning(f"Attempt {attempt + 1} failed to fetch order book for {symbol}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    handle_api_error(e)
                    logging.error(f"Failed to fetch order book for {symbol} after {self.max_retries} attempts")
        return None  # Return None if all attempts fail