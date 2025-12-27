from src.api.kis import KisApi
from src.database.db_manager import DatabaseManager
from src.core.collector import MarketDataCollector
from datetime import datetime, timedelta

def collect_one_year():
    print(">>> Collecting 1 Year Data for Samsung Elec (005930)...")
    kis = KisApi()
    db = DatabaseManager()
    collector = MarketDataCollector(kis, db)
    
    # Collect data month by month to avoid API limits (approx 30 days limit seen?)
    # or just to be safe.
    
    current_date = datetime.now()
    for i in range(12):
        # Define 1 month chunk
        end_dt = current_date
        start_dt = current_date - timedelta(days=30)
        
        end_str = end_dt.strftime("%Y%m%d")
        start_str = start_dt.strftime("%Y%m%d")
        
        print(f"Fetching from {start_str} to {end_str}...")
        collector.collect_daily_price("005930", start_str, end_str)
        
        # Move back
        current_date = start_dt - timedelta(days=1)
        
        # Don't overlap too much, but collector upserts so it's fine.
        import time
        time.sleep(0.5) # Throttle

if __name__ == "__main__":
    collect_one_year()
