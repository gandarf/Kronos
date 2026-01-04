
import argparse
import sys
from datetime import datetime

# Path setup if run from root
import os
sys.path.append(os.getcwd())

from src.database.db_manager import DatabaseManager
from src.core.collector import MarketDataCollector
from src.core.backtester import Backtester

from src.strategies.buy_and_hold import BuyAndHoldStrategy
from src.strategies.dca import BasicDCAStrategy, DynamicDCAStrategy
from src.strategies.volatility_breakout import VolatilityBreakoutStrategy
from src.strategies.ma_crossover import MovingAverageCrossoverStrategy

def main():
    parser = argparse.ArgumentParser(description="Kronos Backtester Runner")
    parser.add_argument("--mode", type=str, required=True, choices=["lump", "dca", "algo"], help="Backtest mode")
    parser.add_argument("--symbol", type=str, required=True, help="Stock Symbol (e.g., AAPL)")
    parser.add_argument("--strategy", type=str, default="vb", choices=["vb", "ma", "bh"], help="Strategy (only for algo mode)")
    parser.add_argument("--deposit", type=int, default=100_000, help="Monthly deposit (for DCA)")
    parser.add_argument("--capital", type=int, default=10_000_000, help="Initial Capital")
    parser.add_argument("--years", type=int, default=1, help="Years of data to fetch if missing")
    parser.add_argument("--start-date", type=str, help="Start Date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End Date (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    # 1. Setup
    db = DatabaseManager()
    
    import pandas as pd
    from datetime import timedelta
    
    # Check Data
    df = db.get_daily_price_optimized(args.symbol)
    
    # data sufficiency check
    should_fetch = False
    years_needed = args.years
    
    if args.start_date:
        # Calculate years needed to cover start_date
        start_dt = pd.to_datetime(args.start_date)
        days_needed = (datetime.now() - start_dt).days + 10 # buffer
        years_needed = max(1, int(days_needed / 365) + 1)
        
    if df.empty:
        should_fetch = True
    else:
        # Check if we have enough history
        # Approximating years to days.
        required_days = years_needed * 365
        first_date = df.index.min()
        available_days = (datetime.now() - first_date).days
        
        # Buffer of 10 days
        if available_days < (required_days - 10):
            print(f"[{args.symbol}] Existing data ({available_days} days) is less than requested ({required_days} days).")
            should_fetch = True
            
    if should_fetch:
        print(f"[{args.symbol}] Fetching {years_needed} years of historical data via yfinance...")
        
        # Simple Mock for KIS
        class MockKis: pass
        
        collector = MarketDataCollector(MockKis(), db)
        collector.collect_historical_data(args.symbol, years=years_needed)
        
        # Reload after fetch
        df = db.get_daily_price_optimized(args.symbol)
        
    if df.empty:
        print(f"Failed to load data for {args.symbol}")
        return
        
    # 2. Select Strategy
    strategy = None
    monthly_deposit = 0
    
    if args.mode == "lump":
        strategy = BuyAndHoldStrategy()
        print("Model: Lump-sum Buy & Hold")
        
    elif args.mode == "dca":
        strategy = BasicDCAStrategy()
        monthly_deposit = args.deposit
        print(f"Mode: DCA (Monthly Deposit: {monthly_deposit:,.0f})")
        
    elif args.mode == "algo":
        if args.strategy == "vb":
            strategy = VolatilityBreakoutStrategy()
        elif args.strategy == "ma":
            strategy = MovingAverageCrossoverStrategy()
        elif args.strategy == "bh":
            strategy = BuyAndHoldStrategy()
        print(f"Mode: Algo Trading ({strategy.__class__.__name__})")

    # 3. Run Backtest
    backtester = Backtester(db, strategy)
    res = backtester.run(
        args.symbol, 
        initial_capital=args.capital, 
        monthly_deposit=monthly_deposit,
        start_date=args.start_date,
        end_date=args.end_date
    )
    
    # 4. Report
    if res:
        print("="*40)
        print(f" FINAL RESULT ({args.symbol})")
        print("="*40)
        print(f" Initial Capital : {res['initial_capital']:,.0f}")
        print(f" Total Invested  : {res['total_invested']:,.0f}")
        print(f" Final Equity    : {res['final_equity']:,.0f}")
        print(f" Total Return    : {res['total_return_pct']:.2f}%")
        print(f" MDD             : {res['mdd_pct']:.2f}%")
        print(f" Trades          : {res['total_trades']}")
        print(f" Dividends       : {res['total_dividends']}")
        print("="*40)
    else:
        print("Backtest failed or returned no results.")

if __name__ == "__main__":
    main()
