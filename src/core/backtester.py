import pandas as pd
from src.database.db_manager import DatabaseManager
from src.strategies.base import Strategy

class Backtester:
    def __init__(self, db: DatabaseManager, strategy: Strategy, commission_rate=0.000140527, tax_rate=0.002, dividend_tax_rate=0.15):
        self.db = db
        self.strategy = strategy
        self.commission_rate = commission_rate
        self.tax_rate = tax_rate
        self.dividend_tax_rate = dividend_tax_rate
        self.results = []
        self.equity_curve = []

    def run(self, symbol, start_date=None, end_date=None, initial_capital=10_000_000, monthly_deposit=0):
        print(f"Running Backtest for {symbol} with {self.strategy.__class__.__name__}...", flush=True)
        
        # 1. Fetch Data
        df = self.db.get_daily_price_optimized(symbol)
        if df.empty:
            print("No data found for backtesting.")
            return

        # Fetch Dividends
        div_map = self.db.get_dividends(symbol) # {date_str: amount}

        # Filter by Date
        if start_date:
            df = df[df.index >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df.index <= pd.to_datetime(end_date)]
            
        if df.empty:
            print(f"No data found for {symbol} between {start_date} and {end_date}.")
            return

        # 2. Initialize State
        cash = initial_capital
        total_invested = initial_capital
        holdings = 0
        avg_price = 0
        
        # 3. Simulation Loop
        dates = df.index
        prev_month = None
        
        for i in range(len(dates)):
            current_date = dates[i]
            
            # --- Monthly Deposit Logic ---
            if monthly_deposit > 0:
                if prev_month is None:
                    prev_month = current_date.month
                elif current_date.month != prev_month:
                    # New month started, add deposit
                    cash += monthly_deposit
                    total_invested += monthly_deposit
                    prev_month = current_date.month
                    # print(f"[{current_date.date()}] Monthly Deposit: {monthly_deposit:,.0f} (Total Invested: {total_invested:,.0f})")

            current_bar = df.iloc[i]
            current_price = current_bar['close']
            
            # --- Dividend Logic ---
            date_str = current_date.strftime("%Y%m%d")
            if date_str in div_map and holdings > 0:
                div_per_share = div_map[date_str]
                gross_div = holdings * div_per_share
                div_tax = gross_div * self.dividend_tax_rate
                net_div = gross_div - div_tax
                
                cash += net_div
                
                self.results.append({
                    "date": current_date,
                    "type": "DIVIDEND",
                    "price": div_per_share,
                    "qty": holdings,
                    "fee": 0,
                    "tax": div_tax,
                    "profit": net_div, # Using profit field for net amount
                    "reason": "Dividend Received"
                })
                # print(f"[{date_str}] Dividend: {gross_div:.2f} (Tax: {div_tax:.2f}) -> +{net_div:.2f}")

            history = df.iloc[:i+1]
            
            # Run Strategy
            signal_res = self.strategy.calculate_signals(history)
            signal = signal_res.get('signal') # Use .get to avoid error if missing
            
            # --- Execution Logic ---
            trade_occured = False
            
            if signal == "BUY":
                # Check for 'weight' or specific 'amount' if strategy provides
                weight = signal_res.get('weight', 1.0)
                
                # Standard Swing/DCA Trade
                if cash > 0:
                    amount_investable = cash * weight * (1 - self.commission_rate)
                    
                    # If weight > 1.0 (e.g. 2.0 for Aggressive DCA), we might not have enough cash.
                    # We simply take min(amount_investable based on weight, actual max cash)
                    # Actually, logic above: cash * weight. 
                    # If weight=2.0, we try to spend 2 * cash. Impossible without margin.
                    # So we must clamp to actual cash.
                    
                    if weight > 1.0:
                        # User wants to buy MORE than current cash (e.g. uses saved cash + new deposit)
                        # But here 'cash' IS the total available. Use all of it.
                        amount_investable = cash * (1 - self.commission_rate)
                    elif weight <= 0:
                         amount_investable = 0

                    qty = int(amount_investable // current_price)
                    
                    if qty > 0:
                        cost = qty * current_price
                        fee = cost * self.commission_rate
                        cash -= (cost + fee)
                        holdings += qty
                        avg_price = current_price
                        trade_occured = True
                        
                        entry_type = "BUY"
                        if weight > 1.0: entry_type = "BUY (Aggressive)"
                        elif weight < 1.0: entry_type = "BUY (Defensive)"

                        self.results.append({
                            "date": current_date,
                            "type": entry_type,
                            "price": current_price,
                            "qty": qty,
                            "fee": fee,
                            "reason": signal_res.get('reason', 'Signal')
                        })
                        
                # VB Strategy (Day Trade) Logic - Kept for compatibility if strategy provides entry/exit
                # VB Strategy (Day Trade) Logic
                if 'exit_price' in signal_res and 'entry_price' in signal_res and cash > 0:
                    # Logic: Buy at 'entry_price', Sell at 'exit_price'
                    # We assume sufficient liquidity/price action to trigger both if Strategy said so.
                    # Usually VB strategy checks High > Target to trigger Buy.
                    
                    entry_price = signal_res['entry_price']
                    exit_price = signal_res['exit_price']
                    
                    # 1. Buy
                    amount_investable = cash * signal_res.get('weight', 0.5) * (1 - self.commission_rate)
                    qty = int(amount_investable // entry_price)
                    
                    if qty > 0:
                        buy_cost = qty * entry_price
                        buy_fee = buy_cost * self.commission_rate
                        
                        # 2. Sell
                        sell_revenue = qty * exit_price
                        sell_fee = sell_revenue * self.commission_rate
                        sell_tax = sell_revenue * self.tax_rate
                        
                        # Net Profit
                        profit = sell_revenue - buy_cost - buy_fee - sell_fee - sell_tax
                        
                        # Update Cash (No holdings change as it is day trade)
                        cash += profit
                        
                        trade_occured = True
                        self.results.append({
                            "date": current_date,
                            "type": "DAY_TRADE",
                            "price": entry_price, # showing entry
                            "exit_price": exit_price,
                            "qty": qty,
                            "profit": profit,
                            "reason": signal_res.get('reason', 'VB Day Trade')
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
            equity = cash + (holdings * current_price)
            self.equity_curve.append({
                "date": current_date,
                "equity": equity,
                "invested": total_invested 
            })
            
        return self.get_summary(initial_capital, total_invested)

    def get_summary(self, initial_capital, total_invested):
        if not self.equity_curve:
            return {}
            
        final_equity = self.equity_curve[-1]['equity']
        
        # Return on Total Invested Capital
        total_return = (final_equity - total_invested) / total_invested * 100
        
        # Max Drawdown
        equity_series = pd.Series([e['equity'] for e in self.equity_curve])
        rolling_max = equity_series.cummax()
        drawdown = (equity_series - rolling_max) / rolling_max * 100
        mdd = drawdown.min()
        
        # Count Trades vs Dividends
        total_trades = 0
        total_dividends = 0
        
        for r in self.results:
            if r['type'] == 'DIVIDEND':
                total_dividends += 1
            else:
                total_trades += 1
        
        return {
            "initial_capital": initial_capital,
            "total_invested": total_invested,
            "final_equity": final_equity,
            "total_return_pct": total_return,
            "mdd_pct": mdd,
            "total_trades": total_trades,
            "total_dividends": total_dividends
        }
