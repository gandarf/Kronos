# Kronos 개발 사양서 (Development Specification)

## 1. 개요 (Overview)
**Kronos**는 한국투자증권 Open API를 활용한 퀀트 투자 시스템입니다. 라즈베리 파이(Debian) 환경에서 구동되며, 단계적 접근(백테스팅 -> 모의투자 -> 실전투자)을 통해 안정적인 수익 모델을 찾는 것을 목표로 합니다.

## 2. 목표 (Goals)
- **1단계**: 데이터 수집 및 기본 전략(단순 이동평균 등) 백테스팅 구현.
- **2단계**: 모의투자를 통한 자동 매매 시스템 검증 (Paper Trading).
- **3단계**: 실전 투자 적용 및 전략 고도화.
- **상시**: 웹 대시보드를 통한 시스템 상태 및 투자 현황 모니터링.

## 3. 기술 스택 (Tech Stack)
- **Language**: Python 3.9+
- **OS**: Debian (Raspberry Pi)
- **Broker API**: 한국투자증권(KIS) Open API
- **Web Framework**: FastAPI (또는 Flask) - 대시보드 및 컨트롤러용
- **Database**: SQLite (초기 단계), 필요 시 PostgreSQL로 확장
- **Scheduler**: APScheduler (정기 데이터 수집 및 매매 타이밍 제어)
- **Visualization**: Jinja2 Templates + Simple CSS (Dashboard)
- **Containerization** (Optional): Docker (추후 배포 용이성 확보)

## 4. 시스템 아키텍처 (System Architecture)

시스템은 크게 4가지 핵심 모듈로 구성됩니다.

### 4.1. Core Module (엔진)
- **Trader**: 전체 트레이딩 루프를 관장하는 메인 프로세스.
- **Scheduler**: 장 시작/마감, 데이터 수집 주기 등을 관리.

### 4.2. Data Module (데이터)
- **MarketDataCollector**: KIS API를 통해 실시간/과거 주가 데이터를 수집 및 자동 보정(Auto-Fetch).
- **Repository (DatabaseManager)**: 
    - **Hybrid Storage**: SQLite(신뢰성) + Parquet(성능) 하이브리드 구조.
    - **Optimization**: 백테스팅 데이터 로딩 속도 향상을 위한 Parquet 캐싱 레이어 적용.

### 4.3. Strategy Module (전략)
*다양한 전략을 플러그인 형태로 교체 가능한 구조.*
- **StrategyInterface**: 모든 전략의 공통 인터페이스.
- **Implemented Strategies**:
    1. **Moving Average Crossover**: 이동평균선 기반 추세 추종 (Trend Following).
    2. **Volatility Breakout**: 래리 윌리엄스 변동성 돌파 + 이평선 스코어링 (Volatility + Market Regime).
- **Strategy Selector**: 웹 대시보드에서 실행할 전략을 동적으로 선택 가능.

### 4.4. Execution Module (실행)
- **OrderManager**: 매매 주문의 중앙 제어 타워.
    - **Safety Checks**: 보유 잔고, 현금 여력 확인.
    - **Logging**: `data/trade.log`에 모든 주문 내역 기록.
- **KisApi**: `place_order` 메서드를 통해 지정가/시장가 주문 실행 (모의/실전 자동 전환).

### 4.5. Dashboard (웹)
- **Status Monitor**: 실시간 계좌 잔고 및 수익률 표시.
- **Backtest UI**:
    - 종목 코드 및 **전략 선택(Dropdown)**.
    - 시뮬레이션 결과(수익률, MDD, 승률) 및 **로그(Debug Log)** 출력.

### 4.6. 백테스팅 엔진 (Backtesting Engine)
- **Enhanced Logic**:
    - **Intraday Simulation**: 시가, 고가, 저가, 종가를 모두 활용하여 장중 돌파 매매 시뮬레이션 지원.
    - **Execution Timing**: 
        - 당일 종가(Close-on-Close)
        - 익일 시가(Next Open)
        - 장중 지정가(Intraday Limit/Stop) 지원.

## 5. 데이터 흐름 (Data Flow)
1. **Collector**가 API를 통해 데이터 수집 -> **SQLite & Parquet** 저장.
2. **Strategy**가 캐싱된 과거 데이터를 로드하여 **Signal(Entry/Exit Price, Weight)** 생성.
3. **Execution**이 Signal을 수신 -> 리스크 체크 -> **OrderManager**를 통해 주문.
4. **Dashboard**는 이 모든 과정을 제어하고 결과를 시각화.

## 6. 개발 로드맵 (Roadmap)
1. **환경 설정**: Python Venv, Git, KIS API Key 발급 및 설정.
2. **KIS Wrapper 구현**: 접속, 시세 조회, 잔고 조회, 주문 기능 캡슐화.
3. **데이터 수집기 구현**: 종목별 일봉/분봉 데이터 수집 및 DB 저장.
4. **기본 전략 구현 및 백테스팅**: 골든크로스 등 단순 전략으로 백테스트 엔진 검증.
5. **매매 봇 연동**: 모의투자 계좌 연동하여 자동 매매 테스트.
6. **대시보드 구축**: 웹 브라우저에서 상태 확인 기능 추가.

## 7. 디렉토리 구조 (Directory Structure)
```
Kronos/
├── config/             # 설정 파일 (API Key 등 - 보안 주의)
├── data/               # SQLite DB 및 데이터 파일
├── src/
│   ├── api/            # KIS Open API Wrapper
│   ├── strategies/     # 투자 전략 클래스 (Strategy Pattern 적용)
│   ├── core/           # 메인 루프, 스케줄러
│   ├── database/       # DB 모델 및 쿼리
│   └── web/            # 대시보드 웹 서버 (FastAPI/Flask)
├── tests/              # 단위 테스트
├── main.py             # 실행 진입점
├── requirements.txt    # 의존성 목록
└── spec.md             # 본 사양서
```
