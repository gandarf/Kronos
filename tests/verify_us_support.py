
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.db_manager import DatabaseManager

def verify():
    print(">>> Verifying US Stock Support...")
    db = DatabaseManager()
    
    # 1. Search Tesla
    print("  Searching 'Tesla'...")
    results = db.search_stock("Tesla")
    print(f"  Results: {results}")
    
    found_tsla = any(r['code'] == 'TSLA' for r in results) or any('Tesla' in r['name'] for r in results)
    if found_tsla:
        print("[OK] Tesla found.")
    else:
        print("[FAIL] Tesla NOT found.")
        
    # 2. Search Samsung (Regression)
    print("  Searching '삼성전자'...")
    results_kr = db.search_stock("삼성전자")
    print(f"  Results: {results_kr}")
    
    found_samsung = any(r['code'] == '005930' for r in results_kr)
    if found_samsung:
        print("[OK] Samsung found.")
    else:
        print("[FAIL] Samsung NOT found.")

if __name__ == "__main__":
    verify()
