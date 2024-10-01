import asyncio
import logging
from typing import Dict, List
import aiohttp
from data_fetcher import DataFetcher
from strategy import MultiStrategyManager
from risk_management import DynamicRiskManagement
from execution import Execution
from advanced_order_types import AdvancedOrderTypes
from utils import setup_logging, initialize_exchange, load_config, sync_time
from ml_predictor import EnhancedMLPredictor
from hft_components import OrderBookAnalyzer, LatencyOptimizer
from market_regime_detector import MarketRegimeDetector
from smart_execution import SmartExecutionAlgorithm
from performance_analytics import PerformanceAnalytics


async def process_symbol(
        symbol: str,
        data_fetcher: DataFetcher,
        multi_strategy_manager: MultiStrategyManager,
        risk_management: DynamicRiskManagement,
        execution: Execution,
        advanced_order_types: AdvancedOrderTypes,
        ml_predictor: EnhancedMLPredictor,
        order_book_analyzer: OrderBookAnalyzer,
        market_regime_detector: MarketRegimeDetector,
        performance_analytics: PerformanceAnalytics,
        current_positions: Dict[str, Dict],
        correlation_matrix: Dict[str, Dict[str, float]]
) -> None:
    try:
        df = await data_fetcher.fetch_historical_data(symbol)
        if df.empty:
            logging.warning(f"No data available for {symbol}, skipping...")
            return

        regime, regime_probs = market_regime_detector.detect_regime(df['close'])
        logging.info(f"Current market regime for {symbol}: {market_regime_detector.regime_description(regime)}")

        order_book = await data_fetcher.exchange.fetch_order_book(symbol)
        order_book_analysis = order_book_analyzer.analyze_order_book(order_book)

        ml_predictor.train(df)
        ml_prediction = ml_predictor.predict(df)

        signals = multi_strategy_manager.get_signals(df, order_book_analysis, ml_prediction, regime)

        for strategy, signal in signals.items():
            if signal['action'] in ['buy', 'sell']:
                entry_price = df['close'].iloc[-1]
                stop_loss_price = signal['stop_loss']
                take_profit_price = signal['take_profit']

                position_size = risk_management.calculate_position_size(entry_price, stop_loss_price,
                                                                        current_positions,
                                                                        df['close'].pct_change().std())
                position_size = risk_management.adjust_for_correlation(position_size, symbol, current_positions,
                                                                       correlation_matrix)

                if position_size > 0:
                    smart_execution = SmartExecutionAlgorithm(data_fetcher.exchange, symbol, position_size, 300)
                    order = await smart_execution.adaptive_execution(signal['action'], entry_price, stop_loss_price,
                                                                     take_profit_price)

                    if order:
                        current_positions[symbol] = {
                            'strategy': strategy,
                            'size': position_size,
                            'entry_price': entry_price,
                            'stop_loss': stop_loss_price,
                            'take_profit': take_profit_price
                        }

                        logging.info(
                            f"New {signal['action'].upper()} order placed for {symbol} - Entry: {entry_price}, Stop Loss: {stop_loss_price}, Take Profit: {take_profit_price}")

            elif signal['action'] == 'close' and symbol in current_positions:
                close_execution = SmartExecutionAlgorithm(data_fetcher.exchange, symbol,
                                                          current_positions[symbol]['size'], 300)
                await close_execution.adaptive_execution('close')
                del current_positions[symbol]
                logging.info(f"Position closed for {symbol}")

        performance_analytics.update(current_positions, df)
        risk_management.update_risk_parameters(df['close'].pct_change().std())

        volatility_list = [df['close'].pct_change().std() for _ in current_positions]
        var = risk_management.calculate_var(current_positions, volatility_list)
        logging.info(f"Current Value at Risk for {symbol}: {var}")

    except Exception as e:
        logging.error(f"Error processing {symbol}: {e}", exc_info=True)


async def main():
    config = load_config('config.yaml')
    setup_logging(config['logging']['level'])

    exchange = initialize_exchange(config)
    max_sync_attempts = 5
    for attempt in range(max_sync_attempts):
        time_offset = sync_time(exchange)
        if time_offset is not None:
            exchange.options['adjustForTimeDifference'] = True
            break
        logging.warning(f"Time sync attempt {attempt + 1} failed. Retrying...")
        await asyncio.sleep(5)

    if time_offset is None:
        logging.error("Failed to synchronize time with the exchange. Exiting.")
        return

    data_fetcher = DataFetcher(exchange, config['data_fetcher'])
    multi_strategy_manager = MultiStrategyManager(config['strategy'])
    risk_management = DynamicRiskManagement(config['risk_management'])
    execution = Execution(exchange, config)
    advanced_order_types = AdvancedOrderTypes(exchange)
    ml_predictor = EnhancedMLPredictor()
    order_book_analyzer = OrderBookAnalyzer()
    latency_optimizer = LatencyOptimizer(exchange)
    market_regime_detector = MarketRegimeDetector()
    performance_analytics = PerformanceAnalytics()

    current_positions = {}
    correlation_matrix = {}  
    symbols = config['trading']['symbols']
    iteration_interval = config['trading']['iteration_interval']

    while True:
        try:
            await latency_optimizer.optimize_request_timing(iteration_interval)

            tasks = [process_symbol(symbol, data_fetcher, multi_strategy_manager, risk_management, execution,
                                    advanced_order_types, ml_predictor, order_book_analyzer, market_regime_detector,
                                    performance_analytics, current_positions, correlation_matrix)
                     for symbol in symbols]

            await asyncio.gather(*tasks)
            metrics = performance_analytics.calculate_metrics()
            logging.info(f"Performance Summary:\n{metrics}")

        except Exception as e:
            logging.error(f"Error in main loop: {e}", exc_info=True)
        await asyncio.sleep(iteration_interval)


if __name__ == "__main__":
    asyncio.run(main())
