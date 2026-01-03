import FinanceDataReader as fdr
import pandas as pd

class MarketLoader:
    def download_and_parse(self):
        """
        Download stock master data using FinanceDataReader.
        Returns a DataFrame with columns ['code_short', 'name_kr'].
        Target: KRX (KOSPI + KOSDAQ + KONEX) + S&P500 + NASDAQ
        """
        print("Downloading stock master data from KRX, S&P500, NASDAQ via FinanceDataReader...")
        try:
            # 1. KRX
            df_krx = fdr.StockListing('KRX')
            df_krx['Code'] = df_krx['Code'].astype(str)
            df_krx = df_krx[['Code', 'Name']].copy()
            df_krx.columns = ['code_short', 'name_kr']
            print(f"KRX downloaded: {len(df_krx)}")

            # 2. S&P500
            df_sp500 = fdr.StockListing('S&P500')
            df_sp500 = df_sp500[['Symbol', 'Name']].copy()
            df_sp500.columns = ['code_short', 'name_kr']
            print(f"S&P500 downloaded: {len(df_sp500)}")

            # 3. NASDAQ
            df_nasdaq = fdr.StockListing('NASDAQ')
            df_nasdaq = df_nasdaq[['Symbol', 'Name']].copy()
            df_nasdaq.columns = ['code_short', 'name_kr']
            print(f"NASDAQ downloaded: {len(df_nasdaq)}")

            # 4. NYSE (New York Stock Exchange)
            df_nyse = fdr.StockListing('NYSE')
            df_nyse = df_nyse[['Symbol', 'Name']].copy()
            df_nyse.columns = ['code_short', 'name_kr']
            print(f"NYSE downloaded: {len(df_nyse)}")

            # 5. US ETFs
            df_etf_us = fdr.StockListing('ETF/US')
            df_etf_us = df_etf_us[['Symbol', 'Name']].copy()
            df_etf_us.columns = ['code_short', 'name_kr']
            print(f"US ETFs downloaded: {len(df_etf_us)}")

            # Merge and drop duplicates
            result_df = pd.concat([df_krx, df_sp500, df_nasdaq, df_nyse, df_etf_us], ignore_index=True)
            result_df.drop_duplicates(subset=['code_short'], inplace=True)
            
            print(f"Total Master Data: {len(result_df)} records.")
            return result_df
            
        except Exception as e:
            print(f"Error downloading stock master data: {e}")
            return pd.DataFrame()

