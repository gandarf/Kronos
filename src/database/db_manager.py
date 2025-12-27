import sqlite3
import os
import pandas as pd

class DatabaseManager:
    def __init__(self, db_path="data/market_data.db"):
        self.db_path = db_path
        self._initialize_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _initialize_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        # Load schema
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                schema = f.read()
            conn = self._get_connection()
            conn.executescript(schema)
            conn.close()
        else:
            print(f"Schema file not found at {schema_path}")

    def insert_daily_price(self, data_list):
        """
        data_list: list of dicts or tuples matching schema
        (symbol, date, open, high, low, close, volume)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Upsert (Replace) strategy
        sql = """
        INSERT OR REPLACE INTO daily_price (symbol, date, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.executemany(sql, data_list)
        conn.commit()
        conn.close()
        print(f"Inserted/Updated {len(data_list)} rows into daily_price.")

    def get_daily_price(self, symbol, start_date=None, end_date=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM daily_price WHERE symbol = ?"
        params = [symbol]
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
            
        query += " ORDER BY date ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_daily_price_as_df(self, symbol, start_date=None, end_date=None):
        """Fetch daily price and return as Pandas DataFrame."""
        rows = self.get_daily_price(symbol, start_date, end_date)
        if not rows:
            return pd.DataFrame()
            
        df = pd.DataFrame(rows, columns=['symbol', 'date', 'open', 'high', 'low', 'close', 'volume'])
        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
        df.set_index('date', inplace=True)
        return df
