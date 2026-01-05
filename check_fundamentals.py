import yfinance as yf
import json

tickers = ["AAPL", "JPM", "XOM", "INTC"]
data = {}

for t in tickers:
    tick = yf.Ticker(t)
    info = tick.info
    data[t] = {
        "trailingPE": info.get("trailingPE"),
        "forwardPE": info.get("forwardPE"),
        "priceToBook": info.get("priceToBook"),
        "dividendYield": info.get("dividendYield"),
        "marketCap": info.get("marketCap"),
        "currentRatio": info.get("currentRatio")
    }

print(json.dumps(data, indent=2))
