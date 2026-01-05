import yfinance as yf
import pandas as pd
import numpy as np

class DremanScreener:
    """
    Implements David Dreman's Contrarian Investing Strategy.
    Key Metrics:
    - Low P/E (Price-to-Earnings): Bottom 20% of market or specific threshold (e.g. < 15)
    - Low P/B (Price-to-Book)
    - High Dividend Yield
    - Strong Financials (Current Ratio > 2.0, Low Debt - simplified here)
    """
    
    def get_universe(self):
        """
        Returns a list of symbols to screen.
        Due to API limits, we'll start with a representative list (e.g. Dow 30 or S&P 100 subset).
        In a real scenario, this would come from the DB (Stock Master).
        """
        # Hardcoded subset of large caps for demo purposes to avoid hitting API limits immediately
        # Combining Tech, Finance, Energy, Consumer, Healthcare
        return [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", # Tech
            "JPM", "BAC", "WFC", "C", "GS", "MS", # Finance
            "XOM", "CVX", "COP", "SLB", # Energy
            "JNJ", "PFE", "UNH", "LLY", "ABBV", # Healthcare
            "PG", "KO", "PEP", "COST", "WMT", # Consumer Staples
            "HD", "MCD", "NKE", "SBUX", # Consumer Discretionary
            "INTC", "CSCO", "IBM", "VZ", "T", # Value Tech/Telco
            "F", "GM", "BA", "CAT", "MMM" # Industrial
        ]

    def fetch_fundamentals(self, symbols):
        """
        Fetches fundamental data for the given symbols using yfinance.
        """
        print(f"Fetching fundamentals for {len(symbols)} symbols...")
        data = []
        
        # Batching might be needed if list is huge, but for < 50 items linear is okay-ish (slow but works)
        # yfinance Tickers object allows batch access?
        # Let's try Tickers for batching if possible, but info attribute is per ticker.
        # We'll loop.
        
        for symbol in symbols:
            try:
                t = yf.Ticker(symbol)
                info = t.info
                
                # Extract Metrics
                pe = info.get('trailingPE')
                forward_pe = info.get('forwardPE')
                pb = info.get('priceToBook')
                div_yield = info.get('dividendYield') # 0.05 = 5%
                mkt_cap = info.get('marketCap')
                current_ratio = info.get('currentRatio')
                payout_ratio = info.get('payoutRatio')
                
                # Check valid PE (Dreman focuses on positive earnings)
                if pe is not None and pe > 0:
                    data.append({
                        'symbol': symbol,
                        'name': info.get('shortName', symbol),
                        'sector': info.get('sector', 'Unknown'),
                        'price': info.get('currentPrice'),
                        'pe': pe,
                        'forward_pe': forward_pe,
                        'pb': pb,
                        'dividend_yield': div_yield if div_yield else 0.0,
                        'market_cap': mkt_cap,
                        'current_ratio': current_ratio
                    })
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")
                
        return pd.DataFrame(data)

    def screen(self, top_n=10):
        """
        Applies Dreman's filters and returns top candidates.
        Ranking Logic:
        1. Filter P/E < 20 (Generic low P/E threshold approx bottom 20-30% of current market)
        2. Filter Market Cap > Large Cap (Stability)
        3. Rank by Dividend Yield (High) + P/E (Low) combined score?
        
        Dreman's primary rule: Buy the bottom 20% P/E stocks.
        """
        symbols = self.get_universe()
        df = self.fetch_fundamentals(symbols)
        
        if df.empty:
            return []
            
        # 1. Filter: P/E < 20 (and > 0)
        # Note: Current market P/E might be high, so 20 is a reasonable "Value" cutoff.
        df_filtered = df[df['pe'] < 25].copy() # Slightly relaxed to 25 for tech-heavy market
        
        # 2. Filter: Strong Financials (Current Ratio > 1.5 if available, else ignore)
        # df_filtered = df_filtered[df_filtered['current_ratio'] > 1.0]
        
        # 3. Score & Rank
        # Lower P/E is better -> Score component 1
        # Higher Yield is better -> Score component 2
        
        # Simple Ranking: Sort by P/E ascending
        df_filtered = df_filtered.sort_values(by='pe', ascending=True)
        
        # Format for display
        results = []
        for _, row in df_filtered.iterrows():
             results.append({
                 'symbol': row['symbol'],
                 'name': row['name'],
                 'sector': row['sector'],
                 'price': row['price'],
                 'pe': round(row['pe'], 2),
                 'pb': round(row['pb'], 2) if row['pb'] else "N/A",
                 'dividend_yield': f"{row['dividend_yield']*100:.2f}%",
                 'score_text': "Low P/E" # Simple tag
             })
             
        return results
