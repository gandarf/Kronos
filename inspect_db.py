import sqlite3
import pandas as pd

def inspect_db():
    conn = sqlite3.connect("data/market_data.db")
    cursor = conn.cursor()
    
    print(">>> Counting rows for 005930...")
    cursor.execute("SELECT COUNT(*) FROM daily_price WHERE symbol='005930'")
    count = cursor.fetchone()[0]
    print(f"Total Rows: {count}")
    
    print("\n>>> First 5 Rows:")
    cursor.execute("SELECT * FROM daily_price WHERE symbol='005930' ORDER BY date ASC LIMIT 5")
    for row in cursor.fetchall():
        print(row)
        
    print("\n>>> Last 5 Rows:")
    cursor.execute("SELECT * FROM daily_price WHERE symbol='005930' ORDER BY date DESC LIMIT 5")
    for row in cursor.fetchall():
        print(row)
        
    conn.close()

if __name__ == "__main__":
    inspect_db()
