import time
import logging
from typing import Dict, Any
from utils import handle_api_error, get_server_time

class Execution:
    def __init__(self, exchange, config):
        self.exchange = exchange
        self.config = config
        self.max_retries = 5
        self.retry_delay = 60

    async def place_order(self, symbol: str, side: str, qty: float, price: float, stop_loss: float, take_profit: float) -> Dict[str, Any]:
        for attempt in range(self.max_retries):
            try:
                server_time = get_server_time(self.exchange)
                if not server_time:
                    logging.warning(f"Attempt {attempt + 1}: Failed to get server time. Retrying...")
                    time.sleep(self.retry_delay)
                    continue

                #  leverage
                leverage = self.config['risk_management']['leverage']
                await self.exchange.set_leverage(leverage, symbol)

                #  main order
                order = await self.exchange.create_order(symbol, 'market', side, qty)
                logging.info(f"Main order placed successfully: {order}")

                # stop loss order
                stop_loss_order = await self.exchange.create_order(
                    symbol, 'stop', 'sell' if side == 'buy' else 'buy', qty,
                    None, {'stopPrice': stop_loss}
                )
                logging.info(f"Stop loss order placed: {stop_loss_order}")

                #  take profit order
                take_profit_order = await self.exchange.create_order(
                    symbol, 'limit', 'sell' if side == 'buy' else 'buy', qty,
                    take_profit, {'type': 'takeProfit'}
                )
                logging.info(f"Take profit order placed: {take_profit_order}")

                # delay to allow order processing
                time.sleep(5)  # delay if necessary

                # fetch the order status
                order_status = await self._fetch_order_status(order['id'], symbol)
                logging.info(f"Fetched order status: {order_status}")

                return {
                    'main_order': order_status,
                    'stop_loss_order': stop_loss_order,
                    'take_profit_order': take_profit_order
                }

            except Exception as e:
                handle_api_error(e)
                logging.error(f"Attempt {attempt + 1}: Error placing order for {symbol}. Error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logging.critical("Max retries reached. Raising exception.")
                    raise

    async def _fetch_order_status(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Fetch the complete status of the order using the appropriate method."""
        try:
            # fetch open orders and check if the order is among them
            open_orders = await self.exchange.fetch_open_orders(symbol)
            logging.debug(f"Open orders: {open_orders}")
            order_status = next((order for order in open_orders if order['id'] == order_id), None)

            # if not found in open orders, fetch closed orders
            if not order_status:
                closed_orders = await self.exchange.fetch_closed_orders(symbol)
                logging.debug(f"Closed orders: {closed_orders}")
                order_status = next((order for order in closed_orders if order['id'] == order_id), None)

            if not order_status:
                logging.warning(f"Order ID {order_id} not found in open or closed orders.")
            else:
                logging.debug(f"Order status details - ID: {order_status.get('id')}, Symbol: {order_status.get('symbol')}, "
                              f"Price: {order_status.get('price')}, Amount: {order_status.get('amount')}, "
                              f"Status: {order_status.get('status')}")

            return order_status

        except Exception as e:
            logging.error(f"Error fetching order status for ID {order_id}: {e}")
            raise

    async def close_position(self, symbol: str, position_size: float) -> Dict[str, Any]:
        """Close an existing position."""
        try:
            close_order = await self.exchange.create_market_sell_order(symbol, position_size)
            logging.info(f"Position closed for {symbol}: {close_order}")
            return close_order
        except Exception as e:
            logging.error(f"Error closing position for {symbol}: {e}")
            raise
