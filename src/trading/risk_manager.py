# src/trading/risk_manager.py
import numpy as np

class RiskManager:
    def __init__(self, min_vol=0.01):
        self.min_volatility = min_vol

    def calculate_volatility(self, hist_data):
        if not hist_data:
            return self.min_volatility
        # Insert real volatility calc here
        return self.min_volatility  # Placeholder

    def should_accept_trade(self, size, volatility):
        max_pos = 1 / (volatility + 1e-8)
        return size <= max_pos
