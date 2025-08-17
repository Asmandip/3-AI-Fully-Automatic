# src/trading/risk_manager.py
import numpy as np
from src.utils.logger import get_logger

logger = get_logger("RiskManager")

class RiskManager:
    def __init__(self, min_vol=0.01):
        self.min_volatility = min_vol

    def calculate_volatility(self, hist_data):
        if not hist_data or len(hist_data) < 2:
            return self.min_volatility
            
        closes = [candle[4] for candle in hist_data]
        returns = np.diff(closes) / closes[:-1]
        volatility = np.std(returns)
        logger.debug(f"Calculated volatility: {volatility:.6f}")
        return max(volatility, self.min_volatility)

    def should_accept_trade(self, size, volatility, balance, max_risk=0.02):
        position_value = size * balance
        risk = volatility * position_value
        max_acceptable_risk = balance * max_risk
        accept = risk <= max_acceptable_risk
        logger.info(f"Risk assessment: {'Accept' if accept else 'Reject'} | "
                    f"Risk: ${risk:.2f}, Max: ${max_acceptable_risk:.2f}")
        return accept