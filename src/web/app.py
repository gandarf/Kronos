from fastapi import APIRouter, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime

from src.api.kis import KisApi
from src.database.db_manager import DatabaseManager
from src.core.backtester import Backtester
from src.core.collector import MarketDataCollector
from src.strategies.ma_crossover import MovingAverageCrossoverStrategy
from src.strategies.volatility_breakout import VolatilityBreakoutStrategy
from src.strategies.buy_and_hold import BuyAndHoldStrategy
from src.strategies.dca import BasicDCAStrategy, DynamicDCAStrategy
from src.strategies.dca import BasicDCAStrategy, DynamicDCAStrategy
from src.utils.market_loader import MarketLoader



router = APIRouter(prefix="/web")
templates = Jinja2Templates(directory="src/web/templates")

# Initialize shared resources (Quick & dirty singleton)
kis = KisApi()
db = DatabaseManager()
collector = MarketDataCollector(kis, db)

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    # Fetch real balance
    balance_data = kis.get_balance()
    
    context = {
        "request": request,
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "balance": {},
        "holdings": []
    }
    
    if balance_data and 'output2' in balance_data:
        # Summary
        summary = balance_data['output2'][0]
        context['balance'] = {
            "total_assets": summary.get('tot_evlu_amt', '0'), # Total Evaluation Amount
            "cash": summary.get('dnca_tot_amt', '0'), # Deposit
            "profit_rate": summary.get('evlu_pfls_smt_tl1', '0') # Profit/Loss
        }
    
    if balance_data and 'output1' in balance_data:
        # Holdings
        context['holdings'] = balance_data['output1']

    return templates.TemplateResponse("index.html", context)

@router.get("/backtest", response_class=HTMLResponse)
async def backtest_page(request: Request):
    return templates.TemplateResponse("backtest.html", {"request": request})

@router.post("/backtest/run", response_class=HTMLResponse)
async def run_backtest(
    request: Request, 
    symbol: str = Form(...), 
    mode: str = Form(...), 
    strategy_name: str = Form(None),
    initial_capital: float = Form(10000), 
    monthly_deposit: float = Form(0)
):
    # 1. Check Data Availability
    # If not enough data, try to collect
    df = db.get_daily_price_optimized(symbol)
    
    if len(df) < 60: # Threshold for at least 3 months for decent backtest
        print(f"Data missing/insufficient for {symbol}. Triggering Auto-Fetch...", flush=True)
        try:
            count = collector.collect_historical_data(symbol, years=1)
            # Fetch again to ensure df is populated
            df = db.get_daily_price_optimized(symbol)
            
            if df.empty:
                return templates.TemplateResponse("backtest.html", {
                    "request": request, 
                    "error": f"데이터 수집 실패: '{symbol}'에 대한 데이터가 없습니다. (종목코드 확인 필요)", 
                    "symbol": symbol
                })

            if len(df) < 20:
                return templates.TemplateResponse("backtest.html", {
                    "request": request, 
                    "error": f"데이터 부족: '{symbol}'의 과거 데이터가 너무 적습니다 ({len(df)}일). 최근 상장된 종목일 수 있습니다. (최소 20일 필요)", 
                    "symbol": symbol
                })
                
        except Exception as e:
            return templates.TemplateResponse("backtest.html", {
                "request": request, 
                "error": f"데이터 수집 중 오류: {str(e)}", 
                "symbol": symbol
            })

    # 2. Select Strategy based on Mode
    strategy = None
    
    if mode == "lump":
        strategy = BuyAndHoldStrategy()
        monthly_deposit = 0 # Force 0 for lump sum
    elif mode == "dca":
        # Default to Basic DCA for now, or could allow sub-selection
        strategy = BasicDCAStrategy()
    elif mode == "algo":
        if strategy_name == "volatility_breakout":
            strategy = VolatilityBreakoutStrategy(k=0.5)
        elif strategy_name == "ma_crossover":
            strategy = MovingAverageCrossoverStrategy(short_window=5, long_window=20, regime_window=60)
        else:
            strategy = VolatilityBreakoutStrategy(k=0.5)
        monthly_deposit = 0 # Force 0 for pure algo
            
    if strategy is None:
         strategy = BuyAndHoldStrategy() # Fallback

    # 3. Run Backtest
    # Korea: Comm ~0.014%, Tax 0.2%
    # US: Comm ~0.25% (vary), Tax 0% (Transaction tax is 0, Capital gains is separate)
    if symbol.isdigit(): # Korean Stock
        commission_rate = 0.000140527
        tax_rate = 0.002
    else: # US Stock
        commission_rate = 0.0025
        tax_rate = 0.0
        
    backtester = Backtester(db, strategy, commission_rate=commission_rate, tax_rate=tax_rate)
    
    summary = backtester.run(symbol, initial_capital=initial_capital, monthly_deposit=monthly_deposit)
    
    if not summary:
         return templates.TemplateResponse("backtest.html", {
            "request": request, 
            "error": "Backtest finished with no results (Insufficient history for strategy?)", 
            "symbol": symbol,
            "mode": mode,
            "selected_strategy": strategy_name
        })
    
    return templates.TemplateResponse("backtest.html", {
        "request": request, 
        "summary": summary, 
        "symbol": symbol,
        "mode": mode,
        "selected_strategy": strategy_name
    })



@router.on_event("startup")
async def check_master_data():
    """Check if stock master data exists, if not, download it."""
    try:
        # Check if table has data (Quick count)
        conn = db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM stock_master")
        count = cursor.fetchone()[0]
        conn.close()
        
        if count < 5000:
            print(f"Stock Master DB has {count} records. Downloading Full Master Data (KRX+US)...")
            loader = KrxLoader()
            df = loader.download_and_parse()
            if not df.empty:
                db.save_stock_master(df)
            else:
                print("Warning: Failed to download/parse Stock Master.")
        else:
            print(f"Stock Master DB ready ({count} records).")
            
    except Exception as e:
        print(f"Startup Data Check Failed: {e}")

@router.get("/search", response_class=HTMLResponse)
async def search_page(request: Request, q: str = ""):
    results = []
    if q:
        results = db.search_stock(q)
        
    return templates.TemplateResponse("search.html", {"request": request, "results": results, "query": q})

