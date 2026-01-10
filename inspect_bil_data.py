
import sys
import os
sys.path.append(os.getcwd())
from src.database.db_manager import DatabaseManager
import pandas as pd

def inspect_data():
    db = DatabaseManager()
    symbol = "BIL"
    
    # Get Prices
    prices = db.get_daily_price_optimized(symbol)
    if prices.empty:
        print("No price data found.")
        return

    # Filter for the relevant period
    mask = (prices.index >= "2025-01-01") & (prices.index <= "2026-01-01")
    df = prices[mask]
    
    print(f"Price Data ({len(df)} rows):")
    print(f"Columns: {df.columns.tolist()}")
    print(df[['close']].head())
    print(df[['close']].tail())
    
    start_price = df.iloc[0]['close']
    end_price = df.iloc[-1]['close']
    print(f"\nStart Price (2025-01-01): {start_price}")
    print(f"End Price (2026-01-01): {end_price}")
    print(f"Price Change: {end_price - start_price} ({ (end_price - start_price)/start_price * 100 :.2f}%)")

    # Inspect Dividends directly from DB file since we can't import db methods easily locally if we don't know the exact path setup or db is locked.
    # Actually, we can use the db object we created.
    
    # We need to know how to get dividends. 
    # Let's try to infer table name 'dividends' and use raw sql.
    import sqlite3
    conn = sqlite3.connect("data/kronos.db")
    cursor = conn.cursor()
    
    print(f"\nDividends Query:")
    cursor.execute(f"SELECT date, dividend FROM dividends WHERE symbol='{symbol}' AND date BETWEEN '2025-01-01' AND '2026-01-01' ORDER BY date")
    rows = cursor.fetchall()
    
    total_div = 0
    for r in rows:
        print(r)
        total_div += r[1]
        
    print(f"Total Dividends Sum: {total_div}")
    conn.close()

if __name__ == "__main__":
    inspect_data()
