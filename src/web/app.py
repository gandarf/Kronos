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

# Initialize shared resources (Quick & dirty singleton)
kis = KisApi()
db = DatabaseManager()

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
    # Run synchronous backtest
    strategy = MovingAverageCrossoverStrategy(short_window=5, long_window=20, regime_window=60)
    backtester = Backtester(db, strategy, commission_rate=0.000140527)
    
    summary = backtester.run(symbol, initial_capital=10_000_000)
    
    return templates.TemplateResponse("backtest.html", {
        "request": request, 
        "summary": summary, 
        "symbol": symbol
    })
