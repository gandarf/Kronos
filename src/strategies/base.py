from abc import ABC, abstractmethod
import pandas as pd

class Strategy(ABC):
    @abstractmethod
    def calculate_signals(self, data: pd.DataFrame) -> dict:
        """
        Analyze data and return trading signals.
        
        Args:
            data (pd.DataFrame): DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
                                 and datetime index.
        
        Returns:
            dict: {
                "signal": "BUY" | "SELL" | "HOLD",
                "reason": "Description of the signal",
                "regime": "BULL" | "BEAR" | "SIDEWAYS"
            }
        """
        pass

    def analyze_market_regime(self, data: pd.DataFrame) -> str:
        """
        Determine the market regime based on basic filters.
        Can be overridden by subclasses.
        """
        # Default simple implementation: 
        # Use simple moving average of the last close price vs 200-day MA
        # We need at least 200 data points.
        if len(data) < 200:
            return "UNKNOWN"
            
        ma_200 = data['close'].rolling(window=200).mean().iloc[-1]
        current_price = data['close'].iloc[-1]
        
        if current_price > ma_200:
            return "BULL"
        else:
            return "BEAR"
