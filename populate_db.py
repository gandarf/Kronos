
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.database.db_manager import DatabaseManager
from src.utils.us_stock_loader import UsStockLoader

def populate():
    print(">>> Populating US Stocks...")
    loader = UsStockLoader()
    df = loader.download_and_parse()
    
    if df.empty:
        print("[FAIL] No US stocks fetched.")
        return

    db = DatabaseManager()
    db.save_us_stock_master(df)
    print("[SUCCESS] US Stocks populated.")

if __name__ == "__main__":
    populate()
