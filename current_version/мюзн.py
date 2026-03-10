import sqlite3
import json
from datetime import datetime
import shutil

def backup_database():
    shutil.copyfile('my_database.db', 'my_database_backup_before_migration.db')
    print("✅ Создана резервная копия: my_database_backup_before_migration.db")

def migrate():
    conn = sqlite3.connect('my_database.db')
    cursor = conn.cursor()

    # Проверяем текущую структуру таблицы projects
    cursor.execute("PRAGMA table_info(projects)")
    columns = {col[1]: col for col in cursor.fetchall()}
    has_authors_ids = 'authors_ids' in columns
    has_participants = 'participants' in columns
    has_suggestions = 'suggestions' in columns

    # 1. Добавляем недостающие столбцы
    if not has_participants:
        print("➕ Добавление столбца participants...")
        cursor.execute("ALTER TABLE projects ADD COLUMN participants JSON DEFAULT '[]'")
    if not has_suggestions:
        print("➕ Добавление столбца suggestions...")
        cursor.execute("ALTER TABLE projects ADD COLUMN suggestions JSON DEFAULT '[]'")

    # 2. Перенос данных из authors_ids в participants, если participants пусты
    cursor.execute("SELECT id, authors_ids, participants FROM projects")
    projects = cursor.fetchall()
    updated_count = 0
    for proj_id, authors_json, participants_json in projects:
        # Если participants уже заполнены — пропускаем
        if participants_json and json.loads(participants_json):
            continue

        authors_ids = json.loads(authors_json) if authors_json else []
        if not authors_ids:
            continue

        participants = []
        for uid in authors_ids:
            cursor.execute("SELECT is_teacher, teacher_info FROM users WHERE id = ?", (uid,))
            user = cursor.fetchone()
            if not user:
                print(f"⚠️ Пользователь {uid} не найден, пропускаем в проекте {proj_id}")
                continue

            is_teacher, teacher_info_json = user
            teacher_info = json.loads(teacher_info_json) if teacher_info_json else {}

            # Определяем роль по умолчанию
            role = "executor"
            if is_teacher:
                roles = teacher_info.get("roles", [])
                if "customer" in roles:
                    role = "customer"
                elif "supervisor" in roles:
                    role = "supervisor"
                elif "expert" in roles:
                    role = "expert"
                if teacher_info.get("curator"):
                    role = "curator"  # куратор — отдельная роль

            participants.append({
                "user_id": uid,
                "role": role,
                "joined_at": datetime.utcnow().isoformat(),
                "invited_by": None
            })

        cursor.execute(
            "UPDATE projects SET participants = ? WHERE id = ?",
            (json.dumps(participants), proj_id)
        )
        updated_count += 1

    if updated_count > 0:
        conn.commit()
        print(f"🔄 Обновлено {updated_count} проектов: данные перенесены в participants.")
    else:
        print("ℹ️ Все проекты уже имеют заполненное поле participants.")

    # 3. Удаляем столбец authors_ids, если он существует
    if has_authors_ids:
        print("🗑️ Удаление столбца authors_ids...")
        backup_database()

        # Создаём новую таблицу без authors_ids
        cursor.execute("""
            CREATE TABLE projects_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                underbody TEXT DEFAULT '',
                participants JSON DEFAULT '[]',
                tasks JSON DEFAULT '[]',
                links JSON DEFAULT '{}',
                comments JSON DEFAULT '[]',
                suggestions JSON DEFAULT '[]'
            )
        """)

        # Копируем данные из старой таблицы
        cursor.execute("""
            INSERT INTO projects_new (id, title, body, underbody, participants, tasks, links, comments, suggestions)
            SELECT id, title, body, underbody, participants, tasks, links, comments, suggestions
            FROM projects
        """)

        # Удаляем старую таблицу и переименовываем новую
        cursor.execute("DROP TABLE projects")
        cursor.execute("ALTER TABLE projects_new RENAME TO projects")

        # Восстанавливаем индексы (например, для поиска по названию)
        cursor.execute("CREATE INDEX idx_projects_title ON projects(title)")

        conn.commit()
        print("✅ Столбец authors_ids успешно удалён.")
    else:
        print("ℹ️ Столбец authors_ids уже отсутствует.")

    conn.close()
    print("🎉 Миграция завершена.")

if __name__ == "__main__":
    migrate()