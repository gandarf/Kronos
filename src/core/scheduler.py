from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import time
import logging

from src.api.kis import KisApi
from src.core.collector import MarketDataCollector
from src.execution.order_manager import OrderManager
from src.database.db_manager import DatabaseManager

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KronosScheduler")

class KronosScheduler:
    def __init__(self, kis: KisApi, collector: MarketDataCollector, order_manager: OrderManager, db: DatabaseManager):
        self.kis = kis
        self.collector = collector
        self.order_manager = order_manager
        self.db = db
        
        self.scheduler = BackgroundScheduler()
        self.target_symbols = ["005930", "000660"] # Default Watchlist: Samsung, Hynix
        self.target_prices = {} # {symbol: target_price}
        self.today_bought = set() # Symbols bought today

    def start(self):
        # 1. Pre-Market (08:50) - Login Check & Token Refresh
        self.scheduler.add_job(self._job_pre_market, CronTrigger(hour=8, minute=50, day_of_week='mon-fri'))
        
        # 2. Market Open (09:00) - Calculate Targets
        self.scheduler.add_job(self._job_market_open, CronTrigger(hour=9, minute=0, day_of_week='mon-fri'))
        
        # 3. Intraday Watcher (09:01 ~ 15:20) - Every 1 minute
        self.scheduler.add_job(self._job_intraday_monitoring, CronTrigger(hour='9-15', minute='*', day_of_week='mon-fri'))
        
        # 4. After Market (15:40) - Data Collection
        self.scheduler.add_job(self._job_after_market, CronTrigger(hour=15, minute=40, day_of_week='mon-fri'))
        
        self.scheduler.start()
        logger.info("Kronos Scheduler Started.")

    def _job_pre_market(self):
        logger.info("[Scheduler] Pre-Market Check...")
        try:
            # Refresh Token (Access Token usually lasts 24h, but good to refresh)
            # kis.py automatically handles token, but we can force a balance check to warm up.
            balance = self.kis.get_balance()
            logger.info(f"Current Balance Checked: {balance.get('output2', [{}])[0].get('dnca_tot_amt', 'N/A')}")
        except Exception as e:
            logger.error(f"Pre-Market Check Failed: {e}")

    def _job_market_open(self):
        logger.info("[Scheduler] Market Open! Calculating Target Prices...")
        self.target_prices = {}
        self.today_bought = set()
        
        for symbol in self.target_symbols:
            try:
                # Get Yesterday's OHLC
                # We need "Daily Candle" which is available after market close.
                # So we query DB or API for "Yesterday's daily candle".
                # API 'get_daily_price' returns recent history.
                
                # Option 1: Use DB (Might be outdated if we didn't collect yesterday?)
                # Option 2: Use API direct fetch for latest standard.
                
                # Let's fetch last 5 days just to be sure
                daily_data = self.kis.get_daily_price(symbol, period="D")
                if daily_data and 'output' in daily_data:
                    # output[0] is most recent (which is Today usually if market started? Or yesterday?)
                    # At 09:00:00, Daily data might show Yesterday as [0] or Today as [0] (with dummy data)?
                    # Usually [0] is today (active), [1] is yesterday.
                    
                    # Verify Date
                    today_str = datetime.now().strftime("%Y%m%d")
                    record0 = daily_data['output'][0]
                    record1 = daily_data['output'][1]
                    
                    prev_day = record1 # Default assumption
                    
                    # Log logic checking
                    # logger.info(f"Record 0 Date: {record0['stck_bsop_date']}") 
                    
                    high = float(prev_day['stck_hgpr'])
                    low = float(prev_day['stck_lwpr'])
                    close = float(prev_day['stck_clpr'])
                    
                    # Volatility Breakout Logic (k=0.5)
                    rng = high - low
                    
                    # We need TODAY's Open. At 09:00 it might be fluctuating. 
                    # We can get "Current Price" which is Open at start.
                    current_price_data = self.kis.get_current_price(symbol)
                    current_open = float(current_price_data['output']['stck_oprc'])
                    
                    target = current_open + (rng * 0.5)
                    self.target_prices[symbol] = target
                    
                    logger.info(f"[{symbol}] Target Calculated. Open: {current_open}, Range: {rng}, Target: {target}")
                    
            except Exception as e:
                logger.error(f"Failed to calc target for {symbol}: {e}")

    def _job_intraday_monitoring(self):
        # Skip if outside market hours (Double check)
        now = datetime.now()
        if now.hour == 15 and now.minute > 20:
            return
            
        logger.info(f"[Scheduler] Intraday Monitor Running... Watching: {list(self.target_prices.keys())}")
        
        for symbol, target in self.target_prices.items():
            if symbol in self.today_bought:
                continue
                
            try:
                price_data = self.kis.get_current_price(symbol)
                current_price = float(price_data['output']['stck_prpr'])
                
                if current_price >= target:
                    logger.info(f"[{symbol}] BREAKOUT! Price {current_price} >= Target {target}")
                    # Place Order
                    # We simply buy 1 share for testing or calculate qty.
                    # For safety, let's Buy 1 share first.
                    self.order_manager.buy_stock(symbol, qty=1, price=0, order_type="01") # Market Order
                    self.today_bought.add(symbol)
                    
            except Exception as e:
                logger.error(f"Error watching {symbol}: {e}")

    def _job_after_market(self):
        logger.info("[Scheduler] After Market Data Collection...")
        for symbol in self.target_symbols:
            self.collector.collect_daily_price(symbol)
