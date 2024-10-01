import numpy as np
import pandas as pd


class PerformanceAnalytics:
    def __init__(self):
        self.equity_curve = []
        self.trades = []

    def update(self, current_positions, latest_prices):
        portfolio_value = sum(pos['size'] * latest_prices[symbol]['close'] for symbol, pos in current_positions.items())
        self.equity_curve.append(portfolio_value)

    def calculate_metrics(self):
        returns = pd.Series(self.equity_curve).pct_change()
        total_return = (self.equity_curve[-1] / self.equity_curve[0]) - 1
        sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std()
        max_drawdown = (pd.Series(self.equity_curve).cummax() - self.equity_curve).max() / pd.Series(
            self.equity_curve).cummax()

        win_rate = len([t for t in self.trades if t['profit'] > 0]) / len(self.trades) if self.trades else 0

        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate
        }

    def record_trade(self, trade):
        self.trades.append(trade)

    def get_equity_curve(self):
        return self.equity_curve

    def get_trades(self):
        return self.trades