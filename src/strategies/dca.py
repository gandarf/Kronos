from .base import Strategy

class BasicDCAStrategy(Strategy):
    """
    Basic Dollar Cost Averaging.
    Buys every month irrespective of price.
    Usually paired with a 'monthly_deposit' in backtester.
    """
    def __init__(self):
        self.last_buy_month = None

    def calculate_signals(self, history):
        if len(history) == 0:
             return {"signal": "HOLD"}
        
        current_date = history.index[-1]
        
        # Simple Logic: Signal BUY every day. 
        # Backtester logic: "if cash > 0 -> Buy".
        # Since DCA adds cash monthly, we just want to invest that cash immediately.
        # So returning BUY always is fine, as long as we have cash.
        
        # However, to be cleaner, we might only signal if we have cash? 
        # Strategy doesn't know cash.
        # Let's just Signal BUY.
        
        return {
            "signal": "BUY",
            "weight": 1.0, # Use all available cash
            "reason": "DCA: Invest Available Cash"
        }

class DynamicDCAStrategy(Strategy):
    """
    Enhanced DCA.
    - Bear Market: Buy 2.0x (Aggressive)
    - Bull Market: Buy 0.5x (Passive, accumulate cash)
    - Sideways (Box): Buy 1.0x (Normal)
    """
    def analyze_market_regime(self, history):
        if len(history) < 60:
            return "SIDEWAYS"
            
        # Logic:
        # Bull: Price > MA60
        # Bear: Price < MA60
        # Sideways: ? Maybe we need 3 zones. 
        # User defined: Bear, Bull, Box.
        # Let's use simple MA20 vs MA60 + Price.
        
        close = history['close']
        ma20 = close.rolling(window=20).mean().iloc[-1]
        ma60 = close.rolling(window=60).mean().iloc[-1]
        price = close.iloc[-1]
        
        # Bull: Price > MA20 and MA20 > MA60 (Strong Uptrend)
        if price > ma20 and ma20 > ma60:
            return "BULL"
        # Bear: Price < MA20 and MA20 < MA60 (Strong Downtrend)
        elif price < ma20 and ma20 < ma60:
            return "BEAR"
        else:
            return "SIDEWAYS"

    def calculate_signals(self, history):
        regime = self.analyze_market_regime(history)
        
        weight = 1.0
        reason = f"DCA (Regime: {regime})"
        
        if regime == "BULL":
            weight = 0.5 # Buy less, save cash
        elif regime == "BEAR":
            weight = 2.0 # Buy double (uses saved cash + new deposit)
        else:
            weight = 1.0 # Buy normal
            
        return {
            "signal": "BUY",
            "weight": weight,
            "reason": reason
        }
