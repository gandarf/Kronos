import yfinance as yf
import pandas as pd
import numpy as np

class DremanScreener:
    """
    Implements David Dreman's Contrarian Investing Strategy (Refined).
    
    Step 1: Universe Selection
    - Top 500-1000 Market Cap (Stable, Information Rich)
    - Exclude: Financials, ETFs, REITs (Sector based)

    Step 2: Safety Filters
    - Debt/Equity < 150% (Stability)
    - Current Ratio > 1.0 (Liquidity)
    - Positive Earnings (Profitability)

    Step 3: Ranking (Composite Score)
    - Rank by PER, PBR, PCR (Price/CashFlow), PDR (Price/Dividend)
    - Low Score (Sum of Ranks) is better.
    """
    
    def get_universe(self):
        """
        Returns a list of symbols to screen.
        Expanded list for demo, excluding obvious Financials/ETFs manually for now,
        but the screener will also strictly filter by Sector.
        """
        # Mixed list including some that should be filtered out to test the logic
        return [
            # Tech (Likely Low Yield, High PE)
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "AMD", "CRM", "ADBE",
            # Semi / Hardware (Value-ish?)
            "INTC", "CSCO", "IBM", "QCOM", "TXN", "AVGO", "MU",
            # Healthcare (Defensive, Value)
            "JNJ", "PFE", "UNH", "LLY", "ABBV", "MRK", "BMY", "AMGN", "CVS",
            # Consumer (Stable)
            "PG", "KO", "PEP", "COST", "WMT", "TGT", "MCD", "NKE", "SBUX", "HD", "LOW",
            # Energy (Low PE, High Yield, Cyclical)
            "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX",
            # Auto / Industrial (Cyclical)
            "F", "GM", "BA", "CAT", "MMM", "GE", "HON", "DE",
            # Telecom (High Yield)
            "VZ", "T", "TMUS", "CMCSA",
            # Financials (Should be FILTERED OUT)
            "JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "AXP", "V", "MA" 
        ]

    def fetch_fundamentals(self, symbols):
        print(f"Fetching fundamentals for {len(symbols)} symbols...")
        data = []
        
        for symbol in symbols:
            try:
                t = yf.Ticker(symbol)
                info = t.info
                
                # Basic Info
                sector = info.get('sector', 'Unknown')
                quote_type = info.get('quoteType', 'EQUITY') # EQUITY, ETF, MUTUALFUND
                
                # Metrics
                price = info.get('currentPrice')
                mkt_cap = info.get('marketCap')
                
                # 1. Earnings (PER)
                pe = info.get('trailingPE')
                
                # 2. Book Value (PBR)
                pb = info.get('priceToBook')
                
                # 3. Cash Flow (PCR)
                # OCF per share is not always directly there, calculate: Price / (OCF / Shares)
                # Or use marketCap / totalCashFromOperatingActivities
                ocf = info.get('operatingCashflow')
                pcr = None
                if ocf and mkt_cap:
                    pcr = mkt_cap / ocf
                    
                # 4. Dividend (PDR = 1 / Yield)
                div_yield = info.get('dividendYield') # e.g. 0.05
                pdr = None
                if div_yield and div_yield > 0:
                    pdr = 1 / div_yield
                else:
                    pdr = 9999 # Penalty for no dividend
                    
                # Safety
                debt_to_equity = info.get('debtToEquity') # yfinance returns %, e.g. 154.2
                current_ratio = info.get('currentRatio')
                
                data.append({
                    'symbol': symbol,
                    'name': info.get('shortName', symbol),
                    'sector': sector,
                    'quote_type': quote_type,
                    'price': price,
                    'pe': pe,
                    'pb': pb,
                    'pcr': pcr,
                    'pdr': pdr, # Lower PDR = Higher Yield
                    'dividend_yield': div_yield,
                    'debt_to_equity': debt_to_equity,
                    'current_ratio': current_ratio
                })
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")
                
        return pd.DataFrame(data)

    def screen(self):
        symbols = self.get_universe()
        df = self.fetch_fundamentals(symbols)
        
        if df.empty:
            return []
            
        # --- Step 1: Universe & Sector Filters ---
        # Exclude Financial Services, ETFs
        # Note: yfinance sector 'Financial Services' covers banks.
        mask_sector = (df['sector'] != 'Financial Services') & (df['sector'] != 'Real Estate')
        mask_type = (df['quote_type'] == 'EQUITY')
        
        df_filtered = df[mask_sector & mask_type].copy()
        
        # --- Step 2: Safety Filters ---
        # Debt/Equity < 150 (Note: yfinance uses %, so 150)
        # Current Ratio > 1.0
        # Positive PE
        
        # Handle N/As before filtering (fill with bad values or drop)
        # For Debt, if None, assumed okay? Or drop. Let's drop stricter.
        df_filtered = df_filtered.dropna(subset=['pe', 'debt_to_equity', 'current_ratio'])
        
        mask_safety = (
            (df_filtered['debt_to_equity'] < 150) & 
            (df_filtered['current_ratio'] > 1.0) & 
            (df_filtered['pe'] > 0)
        )
        df_filtered = df_filtered[mask_safety].copy()
        
        if df_filtered.empty:
            return []

        # --- Step 3: Composite Ranking ---
        # We need PER, PBR, PCR, PDR.
        # If any is NaN/None, we can't rank properly.
        # Fill PCR with High Value if missing (assume bad cash flow)
        df_filtered['pcr'] = df_filtered['pcr'].fillna(9999)
        # PDR already handled (9999 if no yield)
        
        # Rank Each (Ascending: Low is better)
        df_filtered['rank_pe'] = df_filtered['pe'].rank(ascending=True)
        df_filtered['rank_pb'] = df_filtered['pb'].rank(ascending=True)
        df_filtered['rank_pcr'] = df_filtered['pcr'].rank(ascending=True)
        df_filtered['rank_pdr'] = df_filtered['pdr'].rank(ascending=True)
        
        # Sum Ranks
        df_filtered['composite_score'] = (
            df_filtered['rank_pe'] + 
            df_filtered['rank_pb'] + 
            df_filtered['rank_pcr'] + 
            df_filtered['rank_pdr']
        )
        
        # Sort by Score
        df_filtered = df_filtered.sort_values(by='composite_score', ascending=True)
        
        # Format for Display
        results = []
        for i, row in df_filtered.iterrows():
             yield_str =  f"{row['dividend_yield']*100:.2f}%" if row['dividend_yield'] else "0%"
             
             results.append({
                 'rank': int(row['composite_score']), # Just using score as rank indicator
                 'symbol': row['symbol'],
                 'name': row['name'],
                 'sector': row['sector'],
                 'price': row['price'],
                 'pe': round(row['pe'], 2),
                 'pb': round(row['pb'], 2) if row['pb'] else "-",
                 'pcr': round(row['pcr'], 2) if row['pcr'] < 1000 else ">1000",
                 'dividend_yield': yield_str,
                 'debt_to_equity': f"{row['debt_to_equity']:.0f}%",
                 'current_ratio': round(row['current_ratio'], 2),
                 'score_text': f"Score: {int(row['composite_score'])}"
             })
             
        # Return Top 20-30
        return results[:30]
