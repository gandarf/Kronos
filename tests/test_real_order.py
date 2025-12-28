from src.api.kis import KisApi
from src.execution.order_manager import OrderManager

def test_real_buy():
    kis = KisApi()
    om = OrderManager(kis)
    
    print(">>> Attempting to BUY 1 share of Samsung Elec (005930) at Market Price (Simulation)...")
    
    # 005930: Samsung Electronics
    # Qty: 1
    # Price: 0 (Market Order)
    # Type: 01 (Market Price)
    res = om.buy_stock("005930", 1, 0, "01")
    
    print("Result:", res)

if __name__ == "__main__":
    test_real_buy()
