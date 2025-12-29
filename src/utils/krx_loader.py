import urllib.request
import ssl
import zipfile
import os
import pandas as pd
import logging

logger = logging.getLogger("KrxLoader")

class KrxLoader:
    def __init__(self, download_dir="data"):
        self.download_dir = download_dir
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

    def download_and_parse(self):
        """
        Downloads KOSPI master file, parses it, and returns a DataFrame.
        """
        logger.info("Starting KOSPI Master download...")
        
        # SSL Context
        ssl._create_default_https_context = ssl._create_unverified_context
        
        zip_path = os.path.join(self.download_dir, "kospi_code.zip")
        url = "https://new.real.download.dws.co.kr/common/master/kospi_code.mst.zip"
        
        try:
            urllib.request.urlretrieve(url, zip_path)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.download_dir)
                
            # Parse
            mst_file = os.path.join(self.download_dir, "kospi_code.mst")
            df = self._parse_kospi_mst(mst_file)
            
            # Cleanup
            if os.path.exists(zip_path):
                os.remove(zip_path)
            if os.path.exists(mst_file):
                os.remove(mst_file)
                
            return df
            
        except Exception as e:
            logger.error(f"Failed to download/parse KRX master: {e}")
            return pd.DataFrame()

    def _parse_kospi_mst(self, file_path):
        tmp_fil1 = os.path.join(self.download_dir, "kospi_code_part1.tmp")
        tmp_fil2 = os.path.join(self.download_dir, "kospi_code_part2.tmp")

        try:
            # Write temp files in UTF-8
            wf1 = open(tmp_fil1, mode="w", encoding="utf-8")
            wf2 = open(tmp_fil2, mode="w", encoding="utf-8")

            with open(file_path, mode="r", encoding="cp949", errors="replace") as f:
                for row in f:
                    try:
                        # Parsing logic
                        rf1 = row[0:len(row) - 228]
                        rf1_1 = rf1[0:9].rstrip()
                        rf1_2 = rf1[9:21].rstrip()
                        rf1_3 = rf1[21:].strip()
                        wf1.write(rf1_1 + ',' + rf1_2 + ',' + rf1_3 + '\n')
                        rf2 = row[-228:]
                        wf2.write(rf2)
                    except Exception as parse_e:
                        logger.warning(f"Skipping malformed row: {parse_e}")

            wf1.close()
            wf2.close()

            part1_columns = ['code_short', 'code_standard', 'name_kr']
            # Read temp files as UTF-8
            df1 = pd.read_csv(tmp_fil1, header=None, names=part1_columns, encoding='utf-8')

            field_specs = [2, 1, 4, 4, 4,
                           1, 1, 1, 1, 1,
                           1, 1, 1, 1, 1,
                           1, 1, 1, 1, 1,
                           1, 1, 1, 1, 1,
                           1, 1, 1, 1, 1,
                           1, 9, 5, 5, 1,
                           1, 1, 2, 1, 1,
                           1, 2, 2, 2, 3,
                           1, 3, 12, 12, 8,
                           15, 21, 2, 7, 1,
                           1, 1, 1, 1, 9,
                           9, 9, 5, 9, 8,
                           9, 3, 1, 1, 1]

            part2_columns = ['group_code', 'market_cap_scale', 'idx_ind_l', 'idx_ind_m', 'idx_ind_s',
                             'manuf', 'low_liq', 'gov_idx', 'k200_sec', 'k100',
                             'k50', 'krx', 'etp', 'elw', 'krx100',
                             'krx_auto', 'krx_semi', 'krx_bio', 'krx_bank', 'spac',
                             'krx_energy', 'krx_steel', 'short_heat', 'krx_media', 'krx_const',
                             'non1', 'krx_sec', 'krx_ship', 'krx_ins', 'krx_trans',
                             'sri', 'base_price', 'trade_unit', 'ot_unit', 'halt',
                             'clean_up', 'managed', 'warning', 'warn_notice', 'insincere',
                             'backdoor', 'lock', 'split', 'cap_inc', 'margin_rate',
                             'credit_avail', 'credit_period', 'vol_prev', 'par_value', 'list_date',
                             'shares_listed', 'capital', 'fisc_month', 'public_price', 'pref_stock',
                             'short_heat_2', 'abnormal_soar', 'krx300', 'kospi', 'sales',
                             'op_profit', 'net_profit_ord', 'net_profit', 'roe', 'base_ym',
                             'mkt_cap', 'group_code_2', 'credit_limit_over', 'loan_avail', 'lending_avail']

            df2 = pd.read_fwf(tmp_fil2, widths=field_specs, names=part2_columns, encoding='utf-8')


            df = pd.merge(df1, df2, how='outer', left_index=True, right_index=True)
            
            # Filter relevant columns for our use case (Code, Name)
            # Short code (단축코드) usually starts with 'A' in parsing but here user code slices [0:9].
            # Actually standard short code is 6 digits.
            # In 'code_short', it seems to be what we want.
            
            # Let's inspect the first row in debugging if needed.
            # For now, return essential columns.
            
            return df[['code_short', 'name_kr']]

        except Exception as e:
            logger.error(f"Error parsing MST file: {e}")
            return pd.DataFrame()
        finally:
            if os.path.exists(tmp_fil1):
                os.remove(tmp_fil1)
            if os.path.exists(tmp_fil2):
                os.remove(tmp_fil2)
