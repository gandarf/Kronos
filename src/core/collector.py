from datetime import datetime
import yfinance as yf
from src.api.kis import KisApi
from src.database.db_manager import DatabaseManager

class MarketDataCollector:
    def __init__(self, kis: KisApi, db: DatabaseManager):
        self.kis = kis
        self.db = db

    def collect_historical_data(self, symbol, years=1):
        """
        Collect historical data using yfinance.
        Fetches data and saves to DB.
        """
        print(f"[{symbol}] Starting historical data collection via yfinance...")
        try:
            # yfinance download
            start_date = None
            if years > 0:
                ticker = yf.Ticker(symbol)
                # period="1y", "2y", "max" etc
                period = f"{years}y"
                hist = ticker.history(period=period)
            else:
                 # Default logic or max?
                 ticker = yf.Ticker(symbol)
                 hist = ticker.history(period="1y")

            if hist.empty:
                print(f"[{symbol}] No data found on yfinance.")
                return 0
            
            # Format/Save logic
            # yfinance returns DataFrame with Index=Date, Columns=Open, High, Low, Close, Volume, Dividends, Stock Splits
            # DB schema expects: symbol, date(YYYYMMDD), open, high, low, close, volume
            
            db_rows = []
            for date, row in hist.iterrows():
                date_str = date.strftime("%Y%m%d")
                item = (
                    symbol,
                    date_str,
                    float(row['Open']),
                    float(row['High']),
                    float(row['Low']),
                    float(row['Close']),
                    int(row['Volume'])
                )
                db_rows.append(item)
                
            # Save to DB
            if db_rows:
                self.db.insert_daily_price(db_rows)
                print(f"[{symbol}] Saved {len(db_rows)} records to DB.")
                return len(db_rows)
            
        except Exception as e:
            print(f"Error during collection: {e}")
            raise e
            
        return 0
