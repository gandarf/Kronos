CREATE TABLE IF NOT EXISTS daily_price (
    symbol TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    PRIMARY KEY (symbol, date)
);

CREATE TABLE IF NOT EXISTS stock_master (
    code TEXT PRIMARY KEY,
    name TEXT
);
