class AdvancedOrderTypes:
    def __init__(self, exchange):
        self.exchange = exchange

    async def place_trailing_stop(self, symbol, amount, activation_price, trail_percentage):
        params = {
            'triggerPrice': activation_price,
            'trailingStop': trail_percentage
        }
        return await self.exchange.create_order(symbol, 'TRAILING_STOP_MARKET', 'sell', amount, None, params)

    async def place_oco_order(self, symbol, amount, price, stop_price, limit_price):
        params = {
            'stopPrice': stop_price,
            'price': limit_price
        }
        return await self.exchange.create_order(symbol, 'OCO', 'sell', amount, price, params)

    async def place_iceberg_order(self, symbol, side, amount, price, visible_size):
        params = {
            'visibleSize': visible_size
        }
        return await self.exchange.create_order(symbol, 'ICEBERG', side, amount, price, params)

    async def place_twap_order(self, symbol, side, amount, duration):
        params = {
            'duration': duration
        }
        return await self.exchange.create_order(symbol, 'TWAP', side, amount, None, params)