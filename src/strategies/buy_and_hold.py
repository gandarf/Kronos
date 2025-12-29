from .base import Strategy

class BuyAndHoldStrategy(Strategy):
    """
    Simple Buy and Hold Strategy.
    Buys on the first available opportunity and holds until the end.
    Used primarily as a benchmark.
    """
    def __init__(self):
        self.bought = False

    def calculate_signals(self, history):
        """
        Signals BUY if not bought yet. otherwise HOLD.
        """
        if not self.bought:
            if len(history) > 0:
                current_price = history['close'].iloc[-1]
                self.bought = True
                return {
                    "signal": "BUY",
                    "entry_price": current_price, # Buy at Close (or Open of next day? Backtester logic dependent)
                    # Ideally Buy and Hold buys at Open of Day 1. 
                    # But calculate_signals usually runs on Day N to decide for Day N+1 or immediate action.
                    # If we return BUY here, Backtester executes.
                    "reason": "Buy and Hold: Initial Entry",
                    "weight": 1.0
                }
        
        # Otherwise hold (do nothing)
        return {"signal": "HOLD", "reason": "Holding"}
