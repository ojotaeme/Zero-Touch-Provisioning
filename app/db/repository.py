import psycopg2
from psycopg2 import OperationalError
from app.config import Config

class DatabaseRepository:
    def __init__(self):
        self.db_config = Config.DB_CONFIG
        self.connection = None

    def connect(self):
        try:
            self.connection = psycopg2.connect(**self.db_config)
            return self.connection
        except OperationalError as e:
            print(f"[DB-ERROR] Database connection failed: {e}")
            raise e
    
    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def test_connection(self):
        try:
            conn = self.connect()
            cur = conn.cursor()

            cur.execute("SELECT version();")
            db_version = cur.fetchone()
            print(f"[DB-SUCCESS] Database connection successful. PostgreSQL version: {db_version[0]}")
            cur.close()
            return True
        except Exception as e:
            print(f"[DB-FAIL] Database connection test failed: {e}")
            return False
        finally:
            self.close()
