# add_comments_column.py
from database import engine
from sqlalchemy import text

def add_comments_column():
    """Добавляет колонку comments в таблицу projects"""
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE projects ADD COLUMN comments JSON DEFAULT '[]'"))
            conn.commit()
            print("Колонка comments успешно добавлена")
        except Exception as e:
            print(f"Ошибка при добавлении колонки: {e}")

if __name__ == "__main__":
    add_comments_column()