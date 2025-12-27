# Backtesting Logic Flow

## 1. Data Preparation (데이터 준비)
- **Source**: KIS Open API (or Yahoo Finance for testing).
- **Storage**: SQLite Database (`data/market_data.db`).
- **Structure**: Table `ohlcv` (date, open, high, low, close, volume).
- **Action**: Fetch 1~3 years of historical daily data (일봉) for target stocks.

## 2. Simulation Engine (시뮬레이션 엔진)
We will build a lightweight `Backtester` class instead of using heavy libraries like `backtrader` to keep it simple and transparent ("Vibe Coding").

### Core Loop
```python
class Backtester:
    def run(self, strategy, data):
        balance = 10_000_000 # 10 million KRW start
        holdings = 0
        
        for day_data in data:
            # 1. Feed data to Strategy
            signal = strategy.calculate_signals(day_data)
            
            # 2. Execute Virtual Trade
            if signal == "BUY" and balance > 0:
                # Buy logic
            elif signal == "SELL" and holdings > 0:
                # Sell logic
                
            # 3. Record Equity
            self.equity_curve.append(...)
```

## 3. Performance Metrics (성과 분석)
- **CAGR**: Compound Annual Growth Rate
- **MDD**: Maximum Drawdown (최대 낙폭)
- **Win Rate**: 승률
- **Profit Factor**: 총 이익 / 총 손실

## 4. Visualization (시각화)
- Use `matplotlib` or render a simple HTML chart in the Dashboard to show the equity curve vs. Benchmark (e.g., KOSPI).
