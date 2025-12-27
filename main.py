import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.kis import KisApi

kis = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global kis
    print("Kronos System Starting...")
    
    # Initialize API Wrapper
    # This might fail if keys are invalid, but we'll print errors
    try:
        kis = KisApi()
        print("KIS API Initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize KIS API: {e}")

    print("Initializing Database...")
    print("Scheduling Background Tasks...")
    yield
    print("Kronos System Shutting Down...")

app = FastAPI(title="Kronos Trading System", lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "ok", "message": "Kronos System is running"}

@app.get("/api/test/price/{symbol}")
async def test_price(symbol: str):
    if not kis:
        return {"error": "KIS API not initialized"}
    return kis.get_current_price(symbol)

@app.get("/api/test/balance")
async def test_balance():
    if not kis:
        return {"error": "KIS API not initialized"}
    return kis.get_balance()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
