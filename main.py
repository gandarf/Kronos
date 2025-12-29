import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.web.app import router as web_router
from src.web.app import kis, db, collector # Import shared resources
from src.execution.order_manager import OrderManager
from src.core.scheduler import KronosScheduler
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import os

scheduler_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("Kronos System Starting up...")
    
    # Initialize Scheduler specific components
    order_manager = OrderManager(kis)
    scheduler = KronosScheduler(kis, collector, order_manager, db)
    scheduler.start()
    
    global scheduler_instance
    scheduler_instance = scheduler # Keep reference
    
    yield
    # Shutdown logic
    print("Kronos System Shutting Down...")
    if scheduler_instance:
        scheduler_instance.scheduler.shutdown()

app = FastAPI(title="Kronos Trading System", lifespan=lifespan)

# Mount Web Router
app.include_router(web_router)

# Mount Static if exists (optional for now, but good practice)
static_path = "src/web/static"
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/")
async def root():
    return RedirectResponse(url="/web")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
