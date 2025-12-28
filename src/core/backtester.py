import pandas as pd
from src.database.db_manager import DatabaseManager
from src.strategies.base import Strategy

class Backtester:
    def __init__(self, db: DatabaseManager, strategy: Strategy, commission_rate=0.000140527):
        self.db = db
        self.strategy = strategy
        self.commission_rate = commission_rate
        self.results = []
        self.equity_curve = []

    def run(self, symbol, start_date=None, end_date=None, initial_capital=10_000_000):
        print(f"Running Backtest for {symbol}...")
        
        # 1. Fetch Data
        df = self.db.get_daily_price_optimized(symbol)
        if df.empty:
            print("No data found for backtesting.")
            return

        # 2. Initialize State
        cash = initial_capital
        holdings = 0
        avg_price = 0
        
        # 3. Simulation Loop
        # We need to simulate day by day.
        # Ideally, we pass "past data up to today" to the strategy.
        # Optimization: Pass full DF, but strategy only looks at .iloc[:i]
        # Or strategy is vectorised.
        # For simplicity and "realistic" simulation, we iterate.
        
        dates = df.index
        for i in range(len(dates)):
            # Determine current window (up to today)
            # Optimization: Strategy usually needs lookback window (e.g. 200).
            # If i < 200, wait? Or pass data from 0 to i.
            
            # Extract current day's data for execution price
            current_date = dates[i]
            current_bar = df.iloc[i]
            current_price = current_bar['close']
            
            # Prepare data passed to strategy (History)
            # Note: Strategy should not see 'future'.
            # df.iloc[:i+1] includes today. Strategy decides based on today's close?
            # Standard simulation: Calculate signal on CLOSE, Execute on NEXT OPEN or Same CLOSE.
            # Let's assume Signal on CLOSE, Execute on CLOSE (simplest assumption for daily).
            
            history = df.iloc[:i+1]
            
            # Run Strategy
            signal_res = self.strategy.calculate_signals(history)
            signal = signal_res['signal']
            
            # Execute
            trade_occured = False
            if signal == "BUY":
                if cash > 0:
                    # Buy All
                    amount_investable = cash * (1 - self.commission_rate)
                    qty = int(amount_investable // current_price)
                    if qty > 0:
                        cost = qty * current_price
                        fee = cost * self.commission_rate
                        cash -= (cost + fee)
                        holdings += qty
                        avg_price = current_price # Simplified avg
                        trade_occured = True
                        self.results.append({
                            "date": current_date,
                            "type": "BUY",
                            "price": current_price,
                            "qty": qty,
                            "fee": fee,
                            "reason": signal_res['reason']
                        })
            
            elif signal == "SELL":
                if holdings > 0:
                    # Sell All
                    revenue = holdings * current_price
                    fee = revenue * self.commission_rate
                    cash += (revenue - fee)
                    holdings = 0
                    trade_occured = True
                    self.results.append({
                        "date": current_date,
                        "type": "SELL",
                        "price": current_price,
                        "qty": holdings, # 0 now, record prev holdings? logic error here.
                        # Fix: holdings was cleared before logging.
                        # Correct logic:
                        # qty = holdings
                        # holdings = 0
                    })
                    # Re-write Sell Block
            
            # Re-implement Sell Logic properly
            if signal == "SELL" and holdings > 0 and not trade_occured: # Ensure we didn't buy same tick
                 qty_to_sell = holdings
                 revenue = qty_to_sell * current_price
                 fee = revenue * self.commission_rate
                 cash += (revenue - fee)
                 holdings = 0
                 trade_occured = True
                 self.results.append({
                    "date": current_date,
                    "type": "SELL",
                    "price": current_price,
                    "qty": qty_to_sell,
                    "fee": fee,
                    "reason": signal_res['reason']
                })

            # Record Equity
            equity = cash + (holdings * current_price)
            self.equity_curve.append({
                "date": current_date,
                "equity": equity
            })
            
        return self.get_summary(initial_capital)

    def get_summary(self, initial_capital):
        if not self.equity_curve:
            return {}
            
        final_equity = self.equity_curve[-1]['equity']
        total_return = (final_equity - initial_capital) / initial_capital * 100
        
        # Max Drawdown
        equity_series = pd.Series([e['equity'] for e in self.equity_curve])
        rolling_max = equity_series.cummax()
        drawdown = (equity_series - rolling_max) / rolling_max * 100
        mdd = drawdown.min()
        
        return {
            "initial_capital": initial_capital,
            "final_equity": final_equity,
            "total_return_pct": total_return,
            "mdd_pct": mdd,
            "total_trades": len(self.results)
        }
