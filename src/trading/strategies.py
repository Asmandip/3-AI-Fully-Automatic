# src/trading/strategies.py
import numpy as np
from src.utils.logger import get_logger

logger = get_logger("Strategies")

class Strategy:
    def __init__(self, name):
        self.name = name
    
    def analyze(self, data):
        raise NotImplementedError

class MeanReversion(Strategy):
    def __init__(self):
        super().__init__("Mean Reversion")
        
    def analyze(self, data):
        if len(data) < 20:
            return 0
            
        closes = np.array([d[4] for d in data])
        sma = np.mean(closes[-20:])
        last_close = closes[-1]
        
        # Buy when price is below SMA
        if last_close < sma * 0.99:
            return 1  # Buy signal
        # Sell when price is above SMA
        elif last_close > sma * 1.01:
            return -1  # Sell signal
        return 0

class Momentum(Strategy):
    def __init__(self):
        super().__init__("Momentum")
        
    def analyze(self, data):
        if len(data) < 10:
            return 0
            
        closes = np.array([d[4] for d in data])
        returns = np.diff(closes) / closes[:-1]
        momentum = np.sum(returns[-5:])
        
        if momentum > 0.01:
            return 1  # Buy signal
        elif momentum < -0.01:
            return -1  # Sell signal
        return 0

class Scalping(Strategy):
    def __init__(self):
        super().__init__("Scalping")
        
    def analyze(self, data):
        if len(data) < 5:
            return 0
            
        # Simple scalping: Buy on quick dip, sell on quick rise
        last_close = data[-1][4]
        prev_close = data[-2][4]
        change = (last_close - prev_close) / prev_close
        
        if change < -0.002:  # Dip of 0.2%
            return 1
        elif change > 0.002:  # Rise of 0.2%
            return -1
        return 0

STRATEGY_MAP = {
    "Mean Reversion": MeanReversion,
    "Momentum": Momentum,
    "Scalping": Scalping
}
