from src.api.kis import KisApi

def debug_kis():
    kis = KisApi()
    
    # Try to fetch Jan 2025 data (System time is Dec 2025)
    start_date = "20250101"
    end_date = "20250131"
    
    print(f"Requesting data for: {start_date} ~ {end_date}")
    data = kis.get_daily_price("005930", start_date, end_date)
    
    if not data:
        print("No data returned.")
        return

    print(f"Returned {len(data)} rows.")
    if len(data) > 0:
        print("First Row:", data[0])
        print("Last Row:", data[-1])

        # Check dates
        # Typically KIS returns data sorted?
        # output2 usually has 'stck_bsop_date' (business operation date)
        
        first_date = data[0]['stck_bsop_date']
        last_date = data[-1]['stck_bsop_date']
        print(f"Date Range in response: {last_date} ~ {first_date} (Note: often desc)")

if __name__ == "__main__":
    debug_kis()
