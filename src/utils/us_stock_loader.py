
import pandas as pd
import ssl
import logging

logger = logging.getLogger("UsStockLoader")

class UsStockLoader:
    def __init__(self):
        pass

    def download_and_parse(self):
        """
        Downloads S&P 500 list from Wikipedia.
        Returns DataFrame with columns ['code', 'name', 'market']
        """
        logger.info("Fetching S&P 500 list from Wikipedia...")
        
        # SSL Context for pandas read_html
        ssl._create_default_https_context = ssl._create_unverified_context
        
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        
        try:
            import requests
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            dfs = pd.read_html(response.text)
            df = dfs[0] # First table is usually the S&P 500 list
            
            # Columns usually: Symbol, Security, GICS Sector, ...
            # We want: Symbol -> code, Security -> name
            
            df = df[['Symbol', 'Security']].copy()
            df.columns = ['code', 'name']
            df['market'] = 'US' # Marker for US stocks
            
            print(f"Fetched {len(df)} US stocks.")
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch S&P 500 list: {e}")
            print(f"Error fetching US stocks: {e}")
            return pd.DataFrame()

if __name__ == "__main__":
    loader = UsStockLoader()
    df = loader.download_and_parse()
    print(df.head())
