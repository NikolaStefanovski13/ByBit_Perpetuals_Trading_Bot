import numpy as np
from scipy.stats import norm
from typing import Dict, List


class DynamicRiskManagement:
    def __init__(self, config):
        self.initial_risk_per_trade = config['risk_per_trade']
        self.max_risk_per_trade = config['max_risk_per_trade']
        self.lookback_period = config['lookback_period']
        self.risk_per_trade = self.initial_risk_per_trade
        self.trade_history = []
        self.var_confidence = config['var_confidence']
        self.max_position_size = config['max_position_size']

    def update_risk_parameters(self, market_volatility: float) -> None:
        recent_performance = self.calculate_recent_performance()
        volatility_factor = market_volatility / self.average_volatility()

        if recent_performance > 0:
            self.risk_per_trade = min(self.risk_per_trade * 1.1, self.max_risk_per_trade)
        else:
            self.risk_per_trade *= 0.9

        self.risk_per_trade *= volatility_factor

    def calculate_recent_performance(self) -> float:
        recent_trades = self.trade_history[-self.lookback_period:]
        return sum(trade['profit'] for trade in recent_trades)

    def average_volatility(self) -> float:
        if len(self.trade_history) < self.lookback_period:
            return 1  # Default to 1 if not enough history
        return np.std([trade['return'] for trade in self.trade_history[-self.lookback_period:]])

    def calculate_position_size(self, entry_price: float, stop_loss_price: float, current_positions: Dict[str, Dict],
                                volatility: float) -> float:
        risk_amount = self.risk_per_trade
        price_difference = abs(entry_price - stop_loss_price)

        if price_difference == 0:
            return 0

        position_size = risk_amount / price_difference

        volatility_factor = 1 / (1 + volatility)
        position_size *= volatility_factor

        # Adjust for current open positions
        total_exposure = sum(pos['size'] * pos['entry_price'] for pos in current_positions.values())
        available_capital = self.max_position_size - total_exposure
        position_size = min(position_size, available_capital / entry_price)

        return position_size

    def adjust_for_correlation(self, position_size: float, symbol: str, current_positions: Dict[str, Dict],
                               correlation_matrix: Dict[str, Dict[str, float]]) -> float:
        if not current_positions or symbol not in correlation_matrix:
            return position_size

        total_correlation = sum(correlation_matrix[symbol].get(pos_symbol, 0) for pos_symbol in current_positions)
        avg_correlation = total_correlation / len(current_positions)

        correlation_factor = 1 - avg_correlation
        return position_size * correlation_factor

    def calculate_var(self, positions: Dict[str, Dict], volatilities: List[float]) -> float:
        if not positions:
            return 0.0

        portfolio_value = sum(pos['size'] * pos['entry_price'] for pos in positions.values())

        if portfolio_value == 0:
            return 0.0

        weighted_volatility = sum((pos['size'] * pos['entry_price'] * vol) / portfolio_value
                                  for pos, vol in zip(positions.values(), volatilities))

        var = portfolio_value * norm.ppf(1 - self.var_confidence) * weighted_volatility
        return var

    def record_trade(self, trade_result: Dict) -> None:
        self.trade_history.append(trade_result)
        if len(self.trade_history) > self.lookback_period:
            self.trade_history.pop(0)