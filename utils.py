import yaml
import logging
import ccxt
import time
import aiohttp
import asyncio

def setup_logging(log_level: str) -> None:
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='trading_bot.log',
        filemode='a'
    )
    console = logging.StreamHandler()
    console.setLevel(log_level)
    logging.getLogger('').addHandler(console)

def initialize_exchange(config):
    exchange_id = config['exchange']['id']
    exchange_class = getattr(ccxt, exchange_id)
    return exchange_class({
        'apiKey': config['exchange']['api_key'],
        'secret': config['exchange']['secret'],
        'enableRateLimit': True,
        'options': config['exchange'].get('options', {}),
        'aiohttp_proxy': config.get('proxy_url')  
    })

def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def handle_api_error(error):
    if isinstance(error, ccxt.NetworkError):
        logging.error(f"Network error: {error}")
    elif isinstance(error, ccxt.ExchangeError):
        logging.error(f"Exchange error: {error}")
    elif isinstance(error, ccxt.InsufficientFunds):
        logging.error(f"Insufficient funds: {error}")
    elif isinstance(error, ccxt.InvalidOrder):
        logging.error(f"Invalid order: {error}")
    else:
        logging.error(f"An unexpected error occurred: {error}")
    logging.error(f"Error details: {str(error)}")

async def get_server_time(exchange):
    try:
        response = await exchange.fetch_time()
        return response
    except Exception as e:
        handle_api_error(e)
        return None

async def sync_time(exchange):
    max_attempts = 5
    for attempt in range(max_attempts):
        server_time = await get_server_time(exchange)
        if server_time:
            local_time = int(time.time() * 1000)
            time_offset = server_time - local_time
            logging.info(f"Time offset: {time_offset}ms")
            return time_offset
        logging.warning(f"Time sync attempt {attempt + 1} failed. Retrying...")
        await asyncio.sleep(5)
    logging.error("Failed to synchronize time after multiple attempts")
    return None

async def rate_limit_request(semaphore, callback, *args, **kwargs):
    async with semaphore:
        return await callback(*args, **kwargs)

class APIRateLimiter:
    def __init__(self, rate_limit):
        self.rate_limit = rate_limit
        self.semaphore = asyncio.Semaphore(rate_limit)

    async def execute(self, callback, *args, **kwargs):
        return await rate_limit_request(self.semaphore, callback, *args, **kwargs)
