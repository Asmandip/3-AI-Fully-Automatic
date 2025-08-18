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
        
        if last_close < sma * 0.99:
            return 1
        elif last_close > sma * 1.01:
            return -1
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
            return 1
        elif momentum < -0.01:
            return -1
        return 0

class Scalping(Strategy):
    def __init__(self):
        super().__init__("Scalping")
        self.threshold = 0.005  # 0.5% প্রাইস মুভমেন্ট
        
    def analyze(self, data):
        if len(data) < 5:
            return 0
            
        # বর্তমান এবং পূর্ববর্তী ক্লোজ প্রাইস
        current_price = data[-1][4]
        previous_price = data[-2][4]
        
        # প্রাইস পরিবর্তনের শতাংশ
        price_change = (current_price - previous_price) / previous_price
        
        # সিগন্যাল জেনারেশন
        if price_change < -0.005:  # 0.5% ডিপ
            return 1  # কিনুন
        elif price_change > 0.005:  # 0.5% রাইজ
            return -1  # বিক্রি করুন
        return 0

STRATEGY_MAP = {
    "Mean Reversion": MeanReversion,
    "Momentum": Momentum,
    "Scalping": Scalping
}