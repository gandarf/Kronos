from src.api.kis import KisApi
from src.database.db_manager import DatabaseManager
from src.core.collector import MarketDataCollector
from datetime import datetime, timedelta
import sys

def test_collector():
    # Redirect output to file
    # sys.stdout = open('collector_debug.log', 'w')
    # sys.stderr = sys.stdout
    # print(">>> Testing Market Data Collector...")

    # 1. Init Components
    try:
        kis = KisApi()
        db = DatabaseManager() # Will create DB and Tables if missing
        collector = MarketDataCollector(kis, db)
        # print("[OK] Components Initialized")
    except Exception as e:
        print(f"[FAIL] Initialization failed: {e}")
        return

    # 2. Define Period (Last 30 days)
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
    
    symbol = "005930" # Samsung Electronics

    # 3. Run Collection
    print(f"Collecting {symbol} ({start_date} ~ {end_date})...")
    collector.collect_daily_price(symbol, start_date, end_date)

    # 4. Verify DB
    rows = db.get_daily_price(symbol) # Fetch all for symbol
    if rows:
        print(f"[OK] Data verified in DB. Total rows: {len(rows)}")
        print(f"     Last Record: {rows[-1]}")
    else:
        print("[FAIL] No data found in DB")

if __name__ == "__main__":
    test_collector()
