# migrate_add_join_requests.py
"""
Скрипт для добавления поля join_requests в таблицу projects
Запуск: python migrate_add_join_requests.py
"""

import sqlite3
import os
from pathlib import Path

# Путь к базе данных (относительно корня проекта)
DB_PATH = "my_database.db"

def add_join_requests_column():
    """
    Добавляет колонку join_requests типа TEXT (JSON) в таблицу projects,
    если она ещё не существует.
    """
    if not os.path.exists(DB_PATH):
        print(f"Ошибка: файл базы данных {DB_PATH} не найден.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Проверяем существование колонки
        cursor.execute("PRAGMA table_info(projects)")
        columns = [col[1] for col in cursor.fetchall()]

        if "join_requests" not in columns:
            print("Добавление колонки join_requests в таблицу projects...")
            cursor.execute("ALTER TABLE projects ADD COLUMN join_requests TEXT DEFAULT '[]'")
            conn.commit()
            print("✅ Колонка успешно добавлена.")
        else:
            print("ℹ️ Колонка join_requests уже существует.")
    except sqlite3.Error as e:
        print(f"❌ Ошибка SQLite: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_join_requests_column()