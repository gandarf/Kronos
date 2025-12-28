import logging
from src.api.kis import KisApi

# Setup Logger
logger = logging.getLogger("OrderManager")
logger.setLevel(logging.INFO)
# Basic file handler
fh = logging.FileHandler("data/trade.log")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

class OrderManager:
    def __init__(self, kis: KisApi):
        self.kis = kis

    def buy_stock(self, symbol, qty, price=0, order_type="01"):
        """
        Safely execute a Buy Order.
        Default is Market Order (01), price=0.
        """
        # 1. Check Cash Balance (Simple check, can be improved)
        balance = self.kis.get_balance()
        if not balance:
            logger.error("Failed to fetch balance before buying.")
            return None
        
        deposit = float(balance['output2'][0]['dnca_tot_amt'])
        est_cost = price * qty if price > 0 else 0 # Can't check market order cost exactly upfront without current price
        
        if est_cost > deposit:
            logger.warning(f"Insufficient funds. Cash: {deposit}, Cost: {est_cost}")
            # return None # Strict check disabled for now as market order price is unknown here

        # 2. Place Order
        res = self.kis.place_order(symbol, qty, price, order_type, buy_sell="BUY")
        
        if res and res['rt_cd'] == '0':
            logger.info(f"[BUY SUCCESS] {symbol}, Qty: {qty}, Price: {price}, Msg: {res['msg1']}")
            return res
        else:
            logger.error(f"[BUY FAIL] {symbol}, Qty: {qty}, Msg: {res['msg1'] if res else 'Unknown'}")
            return res

    def sell_stock(self, symbol, qty, price=0, order_type="01"):
        """
        Safely execute a Sell Order.
        """
        # 1. Check Holdings
        balance = self.kis.get_balance()
        if not balance:
            logger.error("Failed to fetch holdings before selling.")
            return None
            
        holdings = balance['output1']
        current_qty = 0
        for h in holdings:
            if h['pdno'] == symbol:
                current_qty = int(h['hldg_qty'])
                break
        
        if current_qty < qty:
            logger.warning(f"Insufficient holdings. Owned: {current_qty}, Selling: {qty}")
            return None

        # 2. Place Order
        res = self.kis.place_order(symbol, qty, price, order_type, buy_sell="SELL")
        
        if res and res['rt_cd'] == '0':
            logger.info(f"[SELL SUCCESS] {symbol}, Qty: {qty}, Price: {price}, Msg: {res['msg1']}")
            return res
        else:
            logger.error(f"[SELL FAIL] {symbol}, Qty: {qty}, Msg: {res['msg1'] if res else 'Unknown'}")
            return res
