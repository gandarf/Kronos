from src.database.db_manager import DatabaseManager
from src.core.backtester import Backtester
from src.strategies.ma_crossover import MovingAverageCrossoverStrategy
import pandas as pd
import os

def test_backtester():
    print(">>> Testing Backtester Engine...")
    
    # 1. Setup Mock Data in DB
    db = DatabaseManager()
    
    # Create artificial price data
    # 0-199: Flat 1000 (To build MA200)
    # 200-250: Rise to 1100 (Bull Market)
    # 251-260: Short Drop (Golden Cross Setup if we recover?) 
    # Let's use the Pattern we used in Strategy Test:
    # 200 rising -> 30 sideways -> 10 drop -> 5 rise
    
    # Actually, let's use the real DB data if available, but for unit test, inserting known data is safer.
    symbol = "TEST_STOCK"
    dates = pd.date_range(start='2024-01-01', periods=300)
    prices = [1000 + i for i in range(200)] # 1000 to 1199
    prices.extend([1200] * 30)
    prices.extend([1100] * 10) # Drop
    prices.extend([1300] * 60) # Sharp Rise (Golden Cross should trigger)
    
    db_rows = []
    for i, date in enumerate(dates):
        d_str = date.strftime("%Y%m%d")
        item = (symbol, d_str, prices[i], prices[i], prices[i], prices[i], 1000)
        db_rows.append(item)
        
    db.insert_daily_price(db_rows)
    
    # 2. Run Backtest
    strategy = MovingAverageCrossoverStrategy(short_window=5, long_window=20, regime_window=50)
    backtester = Backtester(db, strategy, commission_rate=0.000140527)
    
    summary = backtester.run(symbol, initial_capital=10_000_000)
    
    print("\n[Backtest Results]")
    print(f"Initial Capital: {summary['initial_capital']:,.0f} KRW")
    print(f"Final Equity:    {summary['final_equity']:,.0f} KRW")
    print(f"Total Return:    {summary['total_return_pct']:.2f} %")
    print(f"MDD:             {summary['mdd_pct']:.2f} %")
    print(f"Trades Executed: {summary['total_trades']}")
    
    if summary['total_trades'] > 0:
        print("[OK] Backtest executed trades.")
    else:
        print("[WARN] No trades executed. Check strategy logic.")

if __name__ == "__main__":
    test_backtester()
