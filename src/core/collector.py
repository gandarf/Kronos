from datetime import datetime
from src.api.kis import KisApi
from src.database.db_manager import DatabaseManager

class MarketDataCollector:
    def __init__(self, kis: KisApi, db: DatabaseManager):
        self.kis = kis
        self.db = db

    def collect_daily_price(self, symbol, start_date, end_date):
        """
        Fetch daily price from KIS and save to DB
        start_date, end_date: YYYYMMDD string
        """
        # print(f"[{symbol}] Collecting data from {start_date} to {end_date}...")
        
        # Fetch from API
        raw_data = self.kis.get_daily_price(symbol, start_date, end_date)
        if not raw_data:
            print(f"[{symbol}] No data returned.")
            return 0

        # Parse and prepare for DB
        db_rows = []
        for row in raw_data:
            # API format: stck_bsop_date, stck_oprc, stck_hgpr, stck_lwpr, stck_clpr, acml_vol
            # DB schema: symbol, date, open, high, low, close, volume
            try:
                item = (
                    symbol,
                    row['stck_bsop_date'],
                    float(row['stck_oprc']),
                    float(row['stck_hgpr']),
                    float(row['stck_lwpr']),
                    float(row['stck_clpr']),
                    int(row['acml_vol'])
                )
                db_rows.append(item)
            except ValueError:
                continue

        # Save to DB
        saved_count = 0
        if db_rows:
            self.db.insert_daily_price(db_rows)
            saved_count = len(db_rows)
            print(f"[{symbol}] Saved {saved_count} records to DB.")
        else:
            print(f"[{symbol}] No valid records to save.")
            
        return saved_count

    def collect_historical_data(self, symbol, years=1):
        """
        Collect historical data for the given symbol for the past 'years'.
        Fetches in 30-day chunks to avoid API limits.
        """
        from datetime import  timedelta
        print(f"[{symbol}] Starting historical data collection for {years} year(s)...")
        end_date = datetime.now()
        start_date_overall = end_date - timedelta(days=365 * years)
        
        current_date = end_date
        
        # Safety limit for iterations (e.g., 12 months + buffer)
        max_months = years * 12 + 2 
        
        total_saved = 0
        try:
            for _ in range(max_months):
                if current_date <= start_date_overall:
                    break
                    
                # Define chunk
                start_chunk = current_date - timedelta(days=30)
                if start_chunk < start_date_overall:
                    start_chunk = start_date_overall
                
                # Ensure date format
                end_str = current_date.strftime("%Y%m%d")
                start_str = start_chunk.strftime("%Y%m%d")
                
                # Fetch
                count = self.collect_daily_price(symbol, start_str, end_str)
                total_saved += count
                
                # Move back
                current_date = start_chunk - timedelta(days=1)
                
                import time
                time.sleep(0.5) # Throttle to be nice
                
        except Exception as e:
            print(f"Error during collection: {e}")
            raise e
            
        print(f"[{symbol}] Historical collection complete. Total saved: {total_saved}")
        return total_saved
