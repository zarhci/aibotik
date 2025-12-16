import sqlite3
from config import DB_NAME
from contextlib import contextmanager
from datetime import date

DB_PATH = DB_NAME + ".db"
DEFAULT_DAILY_LIMIT = 150


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Database error: {e}")
        raise
    finally:
        conn.close()


class DatabaseManager:
    def __init__(self):
        self.create_tables()

    # ==================== ТАБЛИЦЫ ====================

    def create_tables(self):
        with get_db() as conn:
            cursor = conn.cursor()

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER UNIQUE NOT NULL,

                daily_limit INTEGER NOT NULL DEFAULT 150,
                requests_left INTEGER NOT NULL DEFAULT 150,
                last_reset DATE NOT NULL,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER NOT NULL,
                prompt TEXT NOT NULL,
                result TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_tg_id ON users(tg_id);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_results_tg_id ON results(tg_id);"
            )

    # ==================== ПОЛЬЗОВАТЕЛИ ====================

    def add_user(self, tg_id, daily_limit=DEFAULT_DAILY_LIMIT):
        today = date.today().isoformat()

        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO users
                    (tg_id, daily_limit, requests_left, last_reset)
                    VALUES (?, ?, ?, ?)
                    """,
                    (tg_id, daily_limit, daily_limit, today)
                )
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Ошибка при добавлении пользователя: {e}")
            return False

    def get_user_requests(self, tg_id):
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT requests_left FROM users WHERE tg_id = ?",
                    (tg_id,)
                )
                row = cursor.fetchone()
                return row[0] if row else 0
        except Exception as e:
            print(f"Ошибка при получении баланса: {e}")
            return 0

    def use_request(self, tg_id):
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE users
                    SET requests_left = requests_left - 1
                    WHERE tg_id = ? AND requests_left > 0
                    """,
                    (tg_id,)
                )
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Ошибка при списании запроса: {e}")
            return False

    # ==================== ДНЕВНОЙ СБРОС ====================

    def reset_daily_requests_if_needed(self, tg_id):
        today = date.today().isoformat()

        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT daily_limit, last_reset
                    FROM users
                    WHERE tg_id = ?
                    """,
                    (tg_id,)
                )
                row = cursor.fetchone()

                if not row:
                    return

                daily_limit, last_reset = row

                if last_reset == today:
                    return

                cursor.execute(
                    """
                    UPDATE users
                    SET requests_left = ?, last_reset = ?
                    WHERE tg_id = ?
                    """,
                    (daily_limit, today, tg_id)
                )
        except Exception as e:
            print(f"Ошибка при дневном сбросе: {e}")

    # ==================== РЕЗУЛЬТАТЫ ====================

    def add_result(self, tg_id, prompt, result):
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO results (tg_id, prompt, result)
                    VALUES (?, ?, ?)
                    """,
                    (tg_id, prompt, result)
                )
        except Exception as e:
            print(f"Ошибка при сохранении результата: {e}")

    # ==================== СТАТИСТИКА ====================

    def get_total_users(self):
        with get_db() as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM users"
            ).fetchone()[0]

    def get_total_requests(self):
        with get_db() as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM results"
            ).fetchone()[0]


db_manager = DatabaseManager()
