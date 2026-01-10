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
    
    
    def get_universe(self, universe_type='large_cap'):
        """
        Returns a list of symbols to screen based on universe_type.
        - large_cap: Top 50-100 mega cap stocks.
        - mid_cap: Rank ~250-750 (Approx $2B - $20B Market Cap).
        """
        
        large_caps = [
            # Tech
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "AMD", "CRM", "ADBE",
            # Semi / Hardware
            "INTC", "CSCO", "IBM", "QCOM", "TXN", "AVGO", "MU",
            # Healthcare
            "JNJ", "PFE", "UNH", "LLY", "ABBV", "MRK", "BMY", "AMGN", "CVS",
            # Consumer
            "PG", "KO", "PEP", "COST", "WMT", "TGT", "MCD", "NKE", "SBUX", "HD", "LOW",
            # Energy
            "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX",
            # Auto / Industrial
            "F", "GM", "BA", "CAT", "MMM", "GE", "HON", "DE",
            # Telecom
            "VZ", "T", "TMUS", "CMCSA",
            # Financials (Should be FILTERED OUT by Screener, but good to have in universe to test filters)
            "JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "AXP", "V", "MA" 
        ]
        
        mid_caps = [
            # Consumer / Retail
            "M", "KSS", "GPS", "JWN", "CROX", "SKX", "YETI", "WWW", 
            # Tech / Software (Mid)
            "DBX", "DOCU", "TWLO", "OKTA", "NET", "ESTC", "ZM",
            # Industrial / Cyclical
            "AAL", "UAL", "LUV", "ALK", "CAR", "HTZ",
            # Healthcare (Mid)
            "TDOC", "EXAS", "NVAX",
            # Energy (Mid/Small)
            "MRO", "APA", "OVV", "MTDR", "CHX",
            # Real Estate / REITs (Often Mid cap)
            "O", "SPG", "VICS", "PK",
            # Others
            "WU", "BEN", "IVZ", "HBI", "UAA"
        ]
        
        if universe_type == 'mid_cap':
             return mid_caps
             
        return large_caps

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

    def screen(self, universe_type='large_cap'):
        symbols = self.get_universe(universe_type)
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


class MagicFormulaScreener(DremanScreener):
    """
    Implements Joel Greenblatt's Magic Formula.
    Rank companies by:
    1. Earnings Yield = EBIT / Enterprise Value (High is Better)
    2. Return on Capital = EBIT / (Net Fixed Assets + Working Capital)
       -> Proxy: ROA (Return on Assets) or ROCE if available. High is Better.
    
    Composite Score = Rank(EY) + Rank(ROC)
    """
    
    def fetch_magic_metrics(self, symbols):
        print(f"[MagicFormula] Fetching for {len(symbols)} symbols...")
        data = []
        
        for symbol in symbols:
            try:
                t = yf.Ticker(symbol)
                info = t.info
                
                # Basic
                sector = info.get('sector', 'Unknown')
                quote_type = info.get('quoteType', 'EQUITY')
                price = info.get('currentPrice')
                mkt_cap = info.get('marketCap') # Minimum size check usually
                
                # Magic Metrics
                # 1. Earnings Yield
                # Greenblatt: EBIT / Enterprise Value.
                # yfinance usually has 'enterpriseValue'. EBIT is sometimes 'earningsBeforeInterestAndTaxes',
                # or we can use EBITDA as proxy if EBIT missing?
                # Actually info keys often: 'ebitda', 'enterpriseValue'. 
                # Let's try to get them.
                
                ev = info.get('enterpriseValue')
                ebitda = info.get('ebitda') 
                
                earnings_yield = 0.0
                if ev and ebitda and ev > 0:
                    earnings_yield = ebitda / ev
                    
                # 2. Return on Capital
                # Choosing ROA as proxy for screen simplicity
                roa = info.get('returnOnAssets')
                roe = info.get('returnOnEquity')
                
                if roa is None: roa = 0.0
                
                data.append({
                    'symbol': symbol,
                    'name': info.get('shortName', symbol),
                    'sector': sector,
                    'quote_type': quote_type,
                    'price': price,
                    'earnings_yield': earnings_yield,
                    'roa': roa,
                    'ev': ev,
                    'ebitda': ebitda
                })
                
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")
                
        return pd.DataFrame(data)

    def screen(self, universe_type='large_cap'):
        symbols = self.get_universe(universe_type) # Use same large cap universe
        df = self.fetch_magic_metrics(symbols)
        
        if df.empty:
            return []
            
        # 1. Filters (Universe)
        # Exclude Financials & Utilities (Greenblatt rule)
        # Exclude ADRs (usually).
        mask_sector = (~df['sector'].isin(['Financial Services', 'Real Estate', 'Utilities']))
        mask_type = (df['quote_type'] == 'EQUITY')
        
        df_filtered = df[mask_sector & mask_type].copy()
        
        # 2. Minimum Yield Check (Optional, e.g. EY > 0)
        df_filtered = df_filtered[df_filtered['earnings_yield'] > 0].copy()
        
        if df_filtered.empty:
            return []
            
        # 3. Ranking
        # Earnings Yield: High is Better (Descending) -> Rank 1 is best
        df_filtered['rank_ey'] = df_filtered['earnings_yield'].rank(ascending=False)
        
        # ROA: High is Better (Descending)
        df_filtered['rank_roa'] = df_filtered['roa'].rank(ascending=False)
        
        # Composite
        df_filtered['composite_score'] = df_filtered['rank_ey'] + df_filtered['rank_roa']
        
        # Sort
        df_filtered = df_filtered.sort_values(by='composite_score', ascending=True)
        
        results = []
        for i, row in df_filtered.iterrows():
            ey_str = f"{row['earnings_yield']*100:.2f}%"
            roa_str = f"{row['roa']*100:.2f}%"
            
            # Format EV/EBITDA
            ev_ebitda = "-"
            if row['ebitda'] and row['ebitda'] > 0 and row['ev']:
                ev_ebitda = f"{row['ev']/row['ebitda']:.2f}x"

            results.append({
                 'rank': int(row['composite_score']),
                 'symbol': row['symbol'],
                 'name': row['name'],
                 'sector': row['sector'],
                 'price': row['price'],
                 
                 # Display different cols for Magic Formula
                 'magic_ey': ey_str,
                 'magic_roa': roa_str,
                 'ev_ebitda': ev_ebitda,
                 
                 'score_text': f"Score: {int(row['composite_score'])}"
            })
            
        return results[:30]
