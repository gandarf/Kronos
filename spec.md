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
- **MarketDataCollector**: KIS API를 통해 실시간/과거 주가 데이터를 수집.
- **Repository**: DB에 데이터를 저장하고 로드하는 추상화 계층.

### 4.3. Strategy Module (전략)
*종목 선정 및 매매 신호 생성 로직을 Execution과 완전히 분리.*
- **StrategyInterface**: 모든 전략이 따라야 할 기본 클래스 (e.g., `calculate_signals()`).
- **Signal**: 매수(BUY), 매도(SELL), 관망(HOLD) 신호를 생성하여 Execution 모듈로 전달.
- **Backtester**: 과거 데이터를 기반으로 전략의 성과를 시뮬레이션.

### 4.4. Execution Module (실행)
- **OrderManager**: 생성된 Signal을 실제 주문(Order)으로 변환.
- **KIS_API_Wrapper**: 한국투자증권 API 인증(Token 관리), 주문 전송, 잔고 조회를 담당.

### 4.5. Dashboard (웹)
- **Status Monitor**: 봇 작동 상태(Running/Stopped), 최근 로그 표시.
- **Portfolio View**: 현재 보유 종목 및 수익률 표시.

### 4.6. 백테스팅 엔진 (Backtesting Engine) - Custom Implementation
*복잡한 프레임워크 대신 직관적인 커스텀 시뮬레이터를 구현하여 로직의 투명성 확보.*
- **Simulation Loop (가상 매매)**:
  1. **Historical Data**: DB에 저장된 과거 일봉(OHLCV) 데이터를 로드.
  2. **Step-by-Step**: 과거 데이터를 날짜별로 순회하며 전략(Strategy)에 입력.
  3. **Virtual Execution**: 전략이 생성한 Signal(BUY/SELL)에 따라 가상 잔고와 주식 수를 갱신.
  4. **Logging**: 일별 총 자산 가치(Equity)를 기록하여 그래프화.
- **Performance Metrics**: CAGR(연평균 성장률), MDD(최대 낙폭), Win Rate(승률) 계산.

## 5. 데이터 흐름 (Data Flow)
1. **Collector**가 장중/장마감 데이터를 수집 -> **DB** 저장.
2. **Strategy**가 DB 데이터를 분석하여 **Signal** 생성.
3. **Execution**이 Signal을 확인하고, 리스크 관리(자금 상황 등) 체크 후 **API** 주문 전송.
4. **Dashboard**는 DB 및 메모리 상태를 주기적으로 조회하여 사용자에게 표시.

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
