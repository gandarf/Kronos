import yfinance as yf
import json

tickers = ["AAPL", "GOOG", "XOM", "JPM"]
results = {}

for t in tickers:
    tick = yf.Ticker(t)
    info = tick.info
    results[t] = {
        "enterpriseValue": info.get("enterpriseValue"),
        "ebitda": info.get("ebitda"),
        "floatShares": info.get("floatShares"),
        "returnOnAssets": info.get("returnOnAssets"),
        "returnOnEquity": info.get("returnOnEquity"),
        "grossProfits": info.get("grossProfits"), # Maybe for ROC?
        "totalCars": None # Just kidding
    } 

print(json.dumps(results, indent=2))
