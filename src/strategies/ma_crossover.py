import pandas as pd
from .base import Strategy
from .utils import calculate_sma, check_crossover

class MovingAverageCrossoverStrategy(Strategy):
    def __init__(self, short_window=5, long_window=20, regime_window=200):
        self.short_window = short_window
        self.long_window = long_window
        self.regime_window = regime_window

    def calculate_signals(self, data: pd.DataFrame) -> dict:
        # Minimum data requirement
        req_len = max(self.long_window, self.regime_window) + 1
        if len(data) < req_len:
            return {
                "signal": "HOLD",
                "reason": "Not enough data",
                "regime": "UNKNOWN"
            }

        # 1. Market Regime (Filter)
        # Using built-in simple 200-day MA logic from base class, or custom here.
        # Let's use custom utilizing utils
        ma_regime = calculate_sma(data['close'], self.regime_window)
        current_price = data['close'].iloc[-1]
        regime = "BULL" if current_price > ma_regime.iloc[-1] else "BEAR"

        # 2. Indicators
        ma_short = calculate_sma(data['close'], self.short_window)
        ma_long = calculate_sma(data['close'], self.long_window)
        
        crossover = check_crossover(ma_short, ma_long)
        
        current_short = ma_short.iloc[-1]
        current_long = ma_long.iloc[-1]

        # 3. Logic
        signal = "HOLD"
        reason = f"Short({current_short:.0f}) vs Long({current_long:.0f})"

        if regime == "BULL":
            if crossover == "GOLDEN":
                signal = "BUY"
                reason = "Golden Cross in Bull Market"
            elif crossover == "DEAD":
                signal = "SELL"
                reason = "Dead Cross"
            elif current_short < current_long:
                 # Optional: Ensure we sell if we are already seeing Dead Cross condition even if it happened earlier?
                 # ideally 'SELL' signal is immediate action. 'HOLD' assumes we maintain position if we bought.
                 # For simplicity, we only trigger on the exact crossover moment.
                 pass
        else: # BEAR Market
             # Strict Defensive: Sell if we hold, or Don't Buy.
             if crossover == "DEAD":
                 signal = "SELL"
                 reason = "Dead Cross (Bear Market)"
             elif crossover == "GOLDEN":
                 signal = "HOLD"
                 reason = "Ignored Golden Cross (Bear Market)"
        
        return {
            "signal": signal,
            "reason": reason,
            "regime": regime
        }
