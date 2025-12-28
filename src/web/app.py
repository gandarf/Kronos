from fastapi import APIRouter, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime

from src.api.kis import KisApi
from src.database.db_manager import DatabaseManager
from src.core.backtester import Backtester
from src.strategies.ma_crossover import MovingAverageCrossoverStrategy

router = APIRouter(prefix="/web")
templates = Jinja2Templates(directory="src/web/templates")

from src.core.collector import MarketDataCollector

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
async def run_backtest(request: Request, symbol: str = Form(...)):
    # 1. Check Data Availability
    # If not enough data, try to collect
    df = db.get_daily_price_as_df(symbol)
    
    if len(df) < 60: # Threshold for at least 3 months for decent backtest
        print(f"Data missing/insufficient for {symbol}. Triggering Auto-Fetch...")
        try:
            count = collector.collect_historical_data(symbol, years=1)
            if count == 0:
                return templates.TemplateResponse("backtest.html", {
                    "request": request, 
                    "error": f"Invalid Symbol '{symbol}' or data collection failed (0 records found).", 
                    "symbol": symbol
                })
        except Exception as e:
            return templates.TemplateResponse("backtest.html", {
                "request": request, 
                "error": f"Error collecting data: {str(e)}", 
                "symbol": symbol
            })

    # 2. Run Backtest
    strategy = MovingAverageCrossoverStrategy(short_window=5, long_window=20, regime_window=60)
    backtester = Backtester(db, strategy, commission_rate=0.000140527)
    
    summary = backtester.run(symbol, initial_capital=10_000_000)
    
    if not summary:
         return templates.TemplateResponse("backtest.html", {
            "request": request, 
            "error": "Backtest finished with no results (Insufficient history for strategy?)", 
            "symbol": symbol
        })
    
    return templates.TemplateResponse("backtest.html", {
        "request": request, 
        "summary": summary, 
        "symbol": symbol
    })
