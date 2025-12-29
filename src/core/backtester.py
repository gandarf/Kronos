import pandas as pd
from src.database.db_manager import DatabaseManager
from src.strategies.base import Strategy

class Backtester:
    def __init__(self, db: DatabaseManager, strategy: Strategy, commission_rate=0.000140527, tax_rate=0.002):
        self.db = db
        self.strategy = strategy
        self.commission_rate = commission_rate
        self.tax_rate = tax_rate
        self.results = []
        self.equity_curve = []

    def run(self, symbol, start_date=None, end_date=None, initial_capital=10_000_000):
        print(f"Running Backtest for {symbol} with {self.strategy.__class__.__name__}...", flush=True)
        
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
            
            # --- Execution Logic Correction for Volatility Breakout & General ---
            # Standard Buy: Signal BUY -> Buy at 'current_price' (Close)
            # VB Buy: Signal BUY -> Buy at 'entry_price', Sell at 'exit_price' (Day Trade)
            
            trade_occured = False
            
            if signal == "BUY":
                # Check if it's a Day Trade (VB Strategy)
                if 'exit_price' in signal_res and 'entry_price' in signal_res:
                    # Intraday Trade Logic
                    entry_price = signal_res['entry_price']
                    exit_price = signal_res['exit_price']
                    weight = signal_res.get('weight', 1.0)
                    
                    if cash > 0:
                        amount_investable = cash * weight * (1 - self.commission_rate)
                        qty = int(amount_investable // entry_price)
                        
                        if qty > 0:
                            # Buy
                            cost = qty * entry_price
                            buy_fee = cost * self.commission_rate
                            
                            # Sell (Immediate Exit at Close)
                            revenue = qty * exit_price
                            sell_fee = revenue * self.commission_rate
                            sell_tax = revenue * self.tax_rate
                            
                            profit = revenue - cost - buy_fee - sell_fee - sell_tax
                            cash += profit
                            
                            # Log Buy
                            self.results.append({
                                "date": current_date,
                                "type": "BUY",
                                "price": entry_price,
                                "qty": qty,
                                "fee": buy_fee,
                                "reason": signal_res['reason']
                            })
                            # Log Sell
                            self.results.append({
                                "date": current_date,
                                "type": "SELL",
                                "price": exit_price,
                                "qty": qty,
                                "fee": sell_fee,
                                "tax": sell_tax,
                                "reason": "DayTrade Exit"
                            })
                            trade_occured = True
                            
                else:
                    # Standard Swing Trade Logic (Buy and Hold)
                    if cash > 0:
                        amount_investable = cash * (1 - self.commission_rate)
                        qty = int(amount_investable // current_price)
                        if qty > 0:
                            cost = qty * current_price
                            fee = cost * self.commission_rate
                            cash -= (cost + fee)
                            holdings += qty
                            avg_price = current_price
                            trade_occured = True
                            self.results.append({
                                "date": current_date,
                                "type": "BUY",
                                "price": current_price,
                                "qty": qty,
                                "fee": fee,
                                "reason": signal_res.get('reason', 'Signal')
                            })

            elif signal == "SELL":
                # Standard Sell Logic
                if holdings > 0:
                    qty_to_sell = holdings
                    revenue = qty_to_sell * current_price
                    fee = revenue * self.commission_rate
                    tax = revenue * self.tax_rate
                    cash += (revenue - fee - tax)
                    holdings = 0
                    trade_occured = True
                    self.results.append({
                        "date": current_date,
                        "type": "SELL",
                        "price": current_price,
                        "qty": qty_to_sell,
                        "fee": fee,
                        "tax": tax,
                        "reason": signal_res.get('reason', 'Signal')
                    })

            # Record Equity
            # For Day Trade, holdings is 0 at EOD, so Equity = Cash.
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
