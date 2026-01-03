
import sys
import os
import json
import requests
import yaml

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.api.kis import KisApi

def test_us_endpoints():
    print(">>> Initializing KIS API for US Stock Test...")
    kis = KisApi()
    kis._ensure_token()
    
    # Try to find US Stock Search Endpoint
    # Common guesses for URL
    # /uapi/overseas-stock/v1/quotations/search-info
    # TR_ID usually differs. 
    # For US Stock Price:
    # Path: /uapi/overseas-price/v1/quotations/price
    # TR_ID: HHDFS00000300 (Real), HHDFS76200200 (Paper/Virtual)?
    # Let's try to get price for TSLA first.
    
    print("\n[1] Testing US Stock Price (TSLA)...")
    
    url = f"{kis.url_base}/uapi/overseas-price/v1/quotations/price"
    
    # Determine TR_ID for Overseas Price
    # Reference: KIS API Docs (General Knowledge)
    # Real: HHDFS00000300
    # Virtual: HHDFS76200200
    
    is_virtual = "openapivts" in kis.url_base
    tr_id = "HHDFS76200200" if is_virtual else "HHDFS00000300"
    
    print(f"    Using URL: {url}")
    print(f"    Using TR_ID: {tr_id}")
    
    headers = kis._get_headers(tr_id=tr_id)
    
    # NASDAQ: NAS, NYSE: NYS, AMEX: AMS
    params = {
        "AUTH": "",
        "EXCD": "NAS",
        "SYMB": "TSLA"
    }
    
    res = requests.get(url, headers=headers, params=params)
    print(f"    Status Code: {res.status_code}")
    if res.status_code == 200:
        print(f"    Response: {json.dumps(res.json(), indent=2, ensure_ascii=False)}")
    else:
        print(f"    Error: {res.text}")


    print("\n[2] Testing US Stock Search (Info)...")
    # Trying search-info
    # /uapi/overseas-stock/v1/quotations/search-info
    # TR_ID: HHKDB669102C0 ? (Guessing based on some docs online)
    # Or maybe simpler: just search "Tesla"?
    
    # Actually, KIS API usually doesn't have a "search by name" for overseas.
    # It has "search stock info" which fetches details for a specific symbol.
    # Let's try to fetch info for AAPL
    
    url_info = f"{kis.url_base}/uapi/overseas-stock/v1/quotations/search-info"
    # TR_ID might be CTPF1604R (from some sources) or similar.
    # Let's try a common one or look for documentation later if this fails.
    # But for now, let's see if we can just get price, which confirms US Support is possible.
    
if __name__ == "__main__":
    test_us_endpoints()
