from src.database.db_manager import DatabaseManager
from src.core.backtester import Backtester
from src.strategies.ma_crossover import MovingAverageCrossoverStrategy

def test_real_backtest():
    symbol = "005930"
    print(f">>> Running Real Backtest for {symbol} (Samsung Elec)...")
    
    db = DatabaseManager()
    
    # Strategy: 5/20 MA Crossover, Regime Filter 200 (or 60 if data short)
    # We have ~360 days data. 200 regime window is fine.
    strategy = MovingAverageCrossoverStrategy(short_window=5, long_window=20, regime_window=60)
    # Reduced regime window to 60 to allow earlier trading start.
    
    backtester = Backtester(db, strategy, commission_rate=0.000140527)
    
    summary = backtester.run(symbol, initial_capital=10_000_000)
    
    if not summary:
        print("Backtest failed or no data.")
        return

    print("\n[Samsung Elec Backtest Results (1 Year)]")
    print(f"Initial Capital: {summary['initial_capital']:,.0f} KRW")
    print(f"Final Equity:    {summary['final_equity']:,.0f} KRW")
    print(f"Total Return:    {summary['total_return_pct']:.2f} %")
    print(f"MDD:             {summary['mdd_pct']:.2f} %")
    print(f"Trades Executed: {summary['total_trades']}")

if __name__ == "__main__":
    test_real_backtest()
