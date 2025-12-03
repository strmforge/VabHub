"""
添加漫画阅读进度表迁移脚本

创建 manga_reading_progress 表
"""
import sqlite3
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vabhub.db")
DB_PATH = DATABASE_URL.replace("sqlite:///./", "")

def table_exists(cursor, table_name):
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    return cursor.fetchone() is not None

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("检查并创建漫画阅读进度表...")

    # 创建 manga_reading_progress 表
    if not table_exists(cursor, "manga_reading_progress"):
        cursor.execute("""
            CREATE TABLE manga_reading_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                series_id INTEGER NOT NULL,
                chapter_id INTEGER,
                last_page_index INTEGER NOT NULL DEFAULT 1,
                total_pages INTEGER,
                is_finished BOOLEAN NOT NULL DEFAULT 0,
                last_read_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (series_id) REFERENCES manga_series_local(id),
                FOREIGN KEY (chapter_id) REFERENCES manga_chapter_local(id),
                UNIQUE(user_id, series_id)
            )
        """)
        cursor.execute("CREATE INDEX idx_manga_reading_progress_user_id ON manga_reading_progress(user_id)")
        cursor.execute("CREATE INDEX idx_manga_reading_progress_series_id ON manga_reading_progress(series_id)")
        cursor.execute("CREATE INDEX idx_manga_reading_progress_chapter_id ON manga_reading_progress(chapter_id)")
        cursor.execute("CREATE INDEX idx_manga_reading_progress_last_read_at ON manga_reading_progress(last_read_at)")
        print("  [OK] manga_reading_progress 表创建成功")
    else:
        print("  [-] manga_reading_progress 表已存在，跳过创建")

    conn.commit()
    print("\n[SUCCESS] 迁移完成！")

except Exception as e:
    print(f"[ERROR] 迁移失败: {e}")
    conn.rollback()
finally:
    conn.close()

