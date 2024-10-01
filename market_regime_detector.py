import numpy as np
from sklearn.mixture import GaussianMixture


class MarketRegimeDetector:
    def __init__(self, n_regimes=3, lookback_period=100):
        self.n_regimes = n_regimes
        self.lookback_period = lookback_period
        self.gmm = GaussianMixture(n_components=n_regimes, random_state=42)

    def detect_regime(self, price_data):
        returns = np.diff(np.log(price_data[-self.lookback_period:]))
        volatility = np.std(returns) * np.sqrt(252)  # Annualized volatility

        features = np.column_stack((returns, volatility))
        self.gmm.fit(features)

        current_features = np.array([[returns[-1], volatility]])
        current_regime = self.gmm.predict(current_features)[0]

        regime_probabilities = self.gmm.predict_proba(current_features)[0]

        return current_regime, regime_probabilities

    def get_regime_parameters(self):
        means = self.gmm.means_
        covariances = self.gmm.covariances_
        weights = self.gmm.weights_
        return means, covariances, weights

    def regime_description(self, regime):
        descriptions = ['Low Volatility', 'Medium Volatility', 'High Volatility']
        return descriptions[regime]