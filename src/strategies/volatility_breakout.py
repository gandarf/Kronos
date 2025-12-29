from src.strategies.base import Strategy
from src.strategies.utils import calculate_sma

class VolatilityBreakoutStrategy(Strategy):
    def __init__(self, k=0.5):
        self.k = k
        self.ma_windows = [3, 5, 10, 20]

    def analyze_market_regime(self, history):
        """
        Calculate Market Regime Score (0.0 to 1.0)
        Based on price position relative to MAs.
        """
        if len(history) < max(self.ma_windows):
            return 0.5 # Default neutral if not enough data
        
        current_price = history['close'].iloc[-1]
        score = 0
        
        for window in self.ma_windows:
            sma = history['close'].rolling(window=window).mean().iloc[-1]
            if current_price > sma:
                score += 1
                
        return score / len(self.ma_windows) # 0.0, 0.25, 0.5, 0.75, 1.0

    def calculate_signals(self, history):
        """
        Returns signal dict with 'target_price' and 'weight'.
        """
        if len(history) < 20: 
            return {'signal': 'HOLD', 'reason': 'Insufficient Data'}

        # 1. Calculate Volatility Target
        prev_bar = history.iloc[-2]
        current_bar = history.iloc[-1]
        
        prev_range = prev_bar['high'] - prev_bar['low']
        target_price = current_bar['open'] + (prev_range * self.k)
        
        print(f"Date: {history.index[-1]}, Open: {current_bar['open']}, Target: {target_price}, High: {current_bar['high']}")

        # 2. Check Breakout condition
        # If High > Target, we assume we bought at Target
        if current_bar['high'] >= target_price:
            # 3. Calculate Regime Score (Defensive)
            prev_history = history.iloc[:-1]
            weight = self.analyze_market_regime(prev_history)
            print(f"  -> Breakout! Weight: {weight}")
            
            if weight > 0:
                return {
                    'signal': 'BUY',
                    'entry_price': target_price,
                    'exit_price': current_bar['close'], # Day Trade: Sell at Close
                    'weight': weight,
                    'reason': f"Breakout (Score: {weight})"
                }
        
        return {'signal': 'HOLD', 'reason': 'No Breakout or Low Score'}
