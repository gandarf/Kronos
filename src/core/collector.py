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
                # auto_adjust=False to get raw Close (not adjusted for dividends), 
                # so we can simulate dividends separately in backtester.
                hist = ticker.history(period=period, auto_adjust=False)
            else:
                 # Default logic or max?
                 ticker = yf.Ticker(symbol)
                 hist = ticker.history(period="1y", auto_adjust=False)

            if hist.empty:
                print(f"[{symbol}] No data found on yfinance.")
                return 0
            
            # Format/Save logic
            # yfinance returns DataFrame with Index=Date, Columns=Open, High, Low, Close, Volume, Dividends, Stock Splits
            
            db_rows = []
            dividend_rows = []
            
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
                
                # Check for Dividend
                if 'Dividends' in row and row['Dividends'] > 0:
                    dividend_rows.append((symbol, date_str, float(row['Dividends'])))

            # Save to DB
            if db_rows:
                self.db.insert_daily_price(db_rows)
                
                if dividend_rows:
                    self.db.insert_dividends(dividend_rows)
                    
                print(f"[{symbol}] Saved {len(db_rows)} records (and {len(dividend_rows)} dividends) to DB.")
                return len(db_rows)
            
        except Exception as e:
            print(f"Error during collection: {e}")
            raise e
            
        return 0
