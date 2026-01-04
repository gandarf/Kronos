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

    def get_daily_price_optimized(self, symbol):
        """
        Hybrid Fetch: Check Parquet Cache -> If valid, load it. Else, load from SQL and cache it.
        """
        cache_dir = "data/cache"
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, f"{symbol}.parquet")
        
        # Check Cache Validity
        is_cache_valid = False
        if os.path.exists(cache_path) and os.path.exists(self.db_path):
            db_mtime = os.path.getmtime(self.db_path)
            cache_mtime = os.path.getmtime(cache_path)
            if cache_mtime > db_mtime:
                is_cache_valid = True
                
        if is_cache_valid:
            try:
                # print(f"[{symbol}] Loading from Parquet Cache...")
                return pd.read_parquet(cache_path)
            except Exception as e:
                print(f"[{symbol}] Failed to read cache: {e}. Fallback to SQL.")
        
        # Cache Miss or Invalid
        # print(f"[{symbol}] Loading from SQL (and caching)...")
        df = self.get_daily_price_as_df(symbol)
        
        if not df.empty:
            try:
                df.to_parquet(cache_path)
            except Exception as e:
                print(f"[{symbol}] Failed to write cache: {e}")
                
        return df

    def save_stock_master(self, df):
        """
        Save dataframe (code_short, name_kr) to stock_master table.
        replaces existing data.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # We can clear table or replace. Since master is definitive, clear and insert is safer for consistency?
        # Or upsert. Let's use upsert.
        
        data_list = list(zip(df['code_short'], df['name_kr']))
        
        sql = "INSERT OR REPLACE INTO stock_master (code, name) VALUES (?, ?)"
        
        try:
            cursor.executemany(sql, data_list)
            conn.commit()
            print(f"Stock Master Updated: {len(data_list)} records.")
        except Exception as e:
            print(f"Error saving stock master: {e}")
        finally:
            conn.close()

    def save_us_stock_master(self, df):
        """
        Save US stock dataframe (code, name) to stock_master.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Assuming df has 'code' and 'name'
        data_list = list(zip(df['code'], df['name']))
        
        sql = "INSERT OR REPLACE INTO stock_master (code, name) VALUES (?, ?)"
        
        try:
            cursor.executemany(sql, data_list)
            conn.commit()
            print(f"US Stock Master Updated: {len(data_list)} records.")
        except Exception as e:
            print(f"Error saving US stock master: {e}")
        finally:
            conn.close()


    def search_stock(self, keyword):
        """
        Search stock by name or code.
        Returns list of dict: [{'code': '...', 'name': '...'}]
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row # Access columns by name
        cursor = conn.cursor()
        
        query = "SELECT code, name FROM stock_master WHERE name LIKE ? OR code LIKE ? LIMIT 50"
        param = f"%{keyword}%"
        
        cursor.execute(query, (param, param))
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def insert_dividends(self, dividend_list):
        """
        dividend_list: list of (symbol, date, dividend)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        sql = "INSERT OR REPLACE INTO dividends (symbol, date, dividend) VALUES (?, ?, ?)"
        
        try:
            cursor.executemany(sql, dividend_list)
            conn.commit()
            print(f"Dividends Updated: {len(dividend_list)} records.")
        except Exception as e:
            print(f"Error saving dividends: {e}")
        finally:
            conn.close()

    def get_dividends(self, symbol, start_date=None, end_date=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT date, dividend FROM dividends WHERE symbol = ?"
        params = [symbol]
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
            
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        # Return as dict {date_str: amount}
        return {row[0]: row[1] for row in rows}

