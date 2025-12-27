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
            return

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
        if db_rows:
            self.db.insert_daily_price(db_rows)
            print(f"[{symbol}] Saved {len(db_rows)} records to DB.")
        else:
            print(f"[{symbol}] No valid records to save.")
