import pandas as pd
import numpy as np
from src.strategies.ma_crossover import MovingAverageCrossoverStrategy

def test_strategy():
    print(">>> Testing Strategy Module (MA Crossover)...")
    
    # Generate Mock Data (300 days)
    dates = pd.date_range(start='2024-01-01', periods=300)
    
    # Scenario 1: Bull Market, Golden Cross
    # Create price that is generally high (above 200 MA) and has a crossing
    prices = [1000] * 300
    # Make prices rise initially to establish Bull Regime (avg > 1000?)
    # Simple setup: 
    # Days 0-250: Flat 1000
    # Regime Window 200. MA200 = 1000.
    # We need price > 1000.
    
    prices = np.linspace(1000, 1100, 300) # Gradual rise
    
    # Introduce a crossover at the end
    # Short (5) needs to cross Long (20) upwards.
    # Let's manually tweak the last few days.
    # Day -2: Short < Long
    # Day -1: Short > Long
    
    # Let's use a simpler approach: construct DataFrame and tweak
    df = pd.DataFrame({'close': prices}, index=dates)
    
    # Force Bull Regime: Last price 1100 > MA200 (~1050) -> OK
    
    # Force Golden Cross:
    # Set previous 20 days relatively flat/down
    pass 
    
    # Re-generative realistic wave
    # Sine wave + Trend
    t = np.linspace(0, 4*np.pi, 300)
    prices = 1000 + 50*t + 50*np.sin(t) # Uptrend with waves
    # When t increases, 50*t increases.
    
    # --- Test Case 2: Explicit Golden Cross ---
    # Create a small dataset where Short crosses Long upwards
    # Last 5 days avg > Last 20 days avg
    print("\n[Test] Scenario: Bull Market + Golden Cross")
    
    # 200 days of steady rise (Bull Regime)
    base_price = 1000
    prices = [base_price + i for i in range(200)] 
    
    # Add recent prices to trigger Golden Cross
    # Long Window = 20. Short = 5.
    # Day -2: Short < Long
    # Day -1: Short > Long
    
    # To simplify, let's just create a pattern
    # Long Average is lagging. If we spike price, Short will go up faster.
    
    # Append 30 days of sideways
    prices.extend([1200] * 30)
    # Then a sharp drop (Short < Long) -> Dead Cross already happened
    prices.extend([1100] * 10) 
    # Then sharp rise (Short > Long) -> Golden Cross
    prices.extend([1300] * 2)
    
    df = pd.DataFrame({'close': prices}, index=pd.date_range(start='2024-01-01', periods=len(prices)))
    
    # Recalculate indicators to verify manually
    # sma5 = df['close'].rolling(5).mean()
    # sma20 = df['close'].rolling(20).mean()
    # Recalculate indicators to verify manually
    # sma5 = df['close'].rolling(5).mean()
    # sma20 = df['close'].rolling(20).mean()
    # print(sma5.tail(5))
    # print(sma20.tail(5))
    
    strategy = MovingAverageCrossoverStrategy(short_window=5, long_window=20, regime_window=200)
    result = strategy.calculate_signals(df)
    print(f"Signal: {result['signal']} ({result['reason']})")
    
    # --- Test Case 3: Bear Market ---
    print("\n[Test] Scenario: Bear Market")
    # Price dropping below 200MA
    prices_bear = [2000 - i*5 for i in range(250)] # Sharp drop
    df_bear = pd.DataFrame({'close': prices_bear}, index=pd.date_range(start='2024-01-01', periods=len(prices_bear)))
    
    result_bear = strategy.calculate_signals(df_bear)
    print(f"Regime: {result_bear['regime']}")
    print(f"Signal: {result_bear['signal']} ({result_bear['reason']})")

if __name__ == "__main__":
    test_strategy()
