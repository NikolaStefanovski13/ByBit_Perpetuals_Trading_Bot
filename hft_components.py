import numpy as np
from collections import deque


class OrderBookAnalyzer:
    def __init__(self, depth=10):
        self.depth = depth
        self.bid_history = deque(maxlen=100)
        self.ask_history = deque(maxlen=100)

    def analyze_order_book(self, order_book):
        bids = order_book['bids'][:self.depth]
        asks = order_book['asks'][:self.depth]

        bid_liquidity = sum(bid[1] for bid in bids)
        ask_liquidity = sum(ask[1] for ask in asks)

        self.bid_history.append(bids[0][0])
        self.ask_history.append(asks[0][0])

        spread = asks[0][0] - bids[0][0]

        return {
            'bid_liquidity': bid_liquidity,
            'ask_liquidity': ask_liquidity,
            'spread': spread,
            'bid_slope': self.calculate_slope(bids),
            'ask_slope': self.calculate_slope(asks),
            'bid_momentum': self.calculate_momentum(self.bid_history),
            'ask_momentum': self.calculate_momentum(self.ask_history)
        }

    def calculate_slope(self, levels):
        prices = [level[0] for level in levels]
        quantities = [level[1] for level in levels]
        return np.polyfit(prices, quantities, 1)[0]

    def calculate_momentum(self, history):
        if len(history) < 2:
            return 0
        return (history[-1] - history[0]) / len(history)


class LatencyOptimizer:
    def __init__(self, exchange):
        self.exchange = exchange
        self.latencies = deque(maxlen=100)

    async def measure_latency(self):
        start_time = time.time()
        await self.exchange.fetch_ticker('BTC/USDT')
        end_time = time.time()
        latency = end_time - start_time
        self.latencies.append(latency)
        return latency

    def get_average_latency(self):
        return sum(self.latencies) / len(self.latencies) if self.latencies else None

    async def optimize_request_timing(self, target_time):
        avg_latency = self.get_average_latency()
        if avg_latency is None:
            return

        sleep_time = max(0, target_time - avg_latency)
        await asyncio.sleep(sleep_time)