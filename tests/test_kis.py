from src.api.kis import KisApi
import sys

def test_kis():
    print(">>> Testing KIS API Initialization...")
    try:
        kis = KisApi()
        print("[OK] KIS API Initialized & Token Received")
        print(f"     Token: {kis.access_token[:20]}...")
    except Exception as e:
        print(f"[FAIL] Initialization failed: {e}")
        return

    print("\n>>> Testing Price Fetch (Samsung Electronics: 005930)...")
    price_info = kis.get_current_price("005930")
    if price_info:
        print(f"[OK] Price fetched: {price_info.get('stck_prpr')} KRW")
    else:
        print("[FAIL] Failed to fetch price")

    print("\n>>> Testing Balance Fetch...")
    balance_info = kis.get_balance()
    if balance_info:
        output1 = balance_info.get('output1', [])
        output2 = balance_info.get('output2', [])
        print(f"[OK] Balance fetched. Holdings count: {len(output1)}")
        if output2:
            print(f"     Total Eval Amount: {output2[0].get('tot_evlu_mamt')} KRW")
    else:
        print("[FAIL] Failed to fetch balance")

if __name__ == "__main__":
    test_kis()
