import requests
import yaml
import json
import time
from datetime import datetime

class KisApi:
    def __init__(self, config_path="config/settings.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.app_key = self.config['kis']['app_key']
        self.app_secret = self.config['kis']['app_secret']
        self.account_no = self.config['kis']['account_no']
        self.url_base = self.config['kis']['url_base']
        
        # Token Management
        self.token_file = "data/token.json"
        self.access_token = None
        self.token_expired_at = None
        
        # Initial Auth
        self._load_token_from_file()
        self._ensure_token()

    def _load_token_from_file(self):
        import os
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'r') as f:
                    data = json.load(f)
                    self.access_token = data.get('access_token')
                    try:
                        self.token_expired_at = datetime.fromisoformat(data.get('expired_at'))
                    except:
                         self.token_expired_at = None
            except Exception as e:
                print(f"Failed to load token cache: {e}")

    def _ensure_token(self):
        """Check if token is valid, otherwise refresh it layout."""
        if self.access_token and self.token_expired_at and datetime.now() < self.token_expired_at:
            return

        # print("Fetching new KIS Access Token...")
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        url = f"{self.url_base}/oauth2/tokenP"
        res = requests.post(url, headers=headers, data=json.dumps(body))
        
        if res.status_code == 200:
            data = res.json()
            self.access_token = data['access_token']
            # Token usually lasts 24h, set safe expiry (e.g., 23h)
            # Example response: "expires_in": 86400
            self.token_expired_at = datetime.fromtimestamp(time.time() + data['expires_in'] - 600)
            # print(f"Token refreshed. Expires at {self.token_expired_at}")
            
            # Save to file
            try:
                with open(self.token_file, 'w') as f:
                    json.dump({
                        'access_token': self.access_token,
                        'expired_at': self.token_expired_at.isoformat()
                    }, f)
            except Exception as e:
                print(f"Failed to save token to cache: {e}")
                
        else:
            raise Exception(f"Failed to get token: {res.text}")

    def _get_headers(self, tr_id=None):
        self._ensure_token()
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        if tr_id:
            headers["tr_id"] = tr_id
        return headers

    def get_current_price(self, symbol):
        """
        주식 현재가 시세 조회
        Note: 모의투자/실전투자에 따라 tr_id가 다를 수 있음.
        FHKST01010100 : 주식 현재가 시세 (실전/모의 동일)
        """
        url = f"{self.url_base}/uapi/domestic-stock/v1/quotations/inquire-price"
        headers = self._get_headers(tr_id="FHKST01010100")
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": symbol
        }
        
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 200:
            return res.json().get('output', {})
        else:
            print(f"Error fetching price for {symbol}: {res.text}")
            return None

    def get_daily_price(self, symbol, start_date, end_date, period_code="D"):
        """
        주식 기간별 시세 (일/주/월/년) - 일봉 데이터 수집용
        TR_ID: FHKST01010400
        """
        url = f"{self.url_base}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        headers = self._get_headers(tr_id="FHKST01010400")
        
        # 'D': Day, 'W': Week, 'M': Month, 'Y': Year
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": symbol,
            "FID_INPUT_DATE_1": start_date, # YYYYMMDD
            "FID_INPUT_DATE_2": end_date,   # YYYYMMDD
            "FID_PERIOD_DIV_CODE": period_code,
            "FID_ORG_ADJ_PRC": "0" # 0: 수정주가 아님, 1: 수정주가
        }
        
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 200:
            data = res.json()
            data = res.json()
            # print(f"DEBUG_API: rt_cd={data.get('rt_cd')}, msg1={data.get('msg1')}")
            
            # In some environments (e.g. VTS), data might be in 'output' instead of 'output2'
            if 'output2' in data and data['output2']:
                return data['output2']
            elif 'output' in data:
                return data['output']
            else:
                print(f"Warning: neither 'output2' nor 'output' found in response: {data}")
                return []
        else:
            print(f"Error fetching daily price for {symbol}: {res.text}")
            return []

    def get_balance(self):
        """
        주식 잔고 조회
        VTTC8434R : (모의투자) 주식 잔고 조회
        TTTC8434R : (실전투자) 주식 잔고 조회
        """
        # Determine TR_ID based on URL (Simple check)
        if "openapivts" in self.url_base:
            tr_id = "VTTC8434R" # Simulation
        else:
            tr_id = "TTTC8434R" # Real

        url = f"{self.url_base}/uapi/domestic-stock/v1/trading/inquire-balance"
        headers = self._get_headers(tr_id=tr_id)
        
        # Account format: 12345678-01 -> Split to 12345678 and 01
        acc_no_prefix = self.account_no.split('-')[0]
        acc_no_suffix = self.account_no.split('-')[1]

        params = {
            "CANO": acc_no_prefix,
            "ACNT_PRDT_CD": acc_no_suffix,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "N",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "00",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }
        
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 200:
            return res.json()
        else:
            print(f"Error fetching balance: {res.text}")
            return None
