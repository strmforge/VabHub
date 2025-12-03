"""添加用户漫画追更表迁移脚本

创建 user_manga_follow 表，用于记录用户对本地漫画系列的追更状态。
"""
import os
import sqlite3

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vabhub.db")
DB_PATH = DATABASE_URL.replace("sqlite:///./", "")


def table_exists(cursor: sqlite3.Cursor, table_name: str) -> bool:
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cursor.fetchone() is not None


try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("检查并创建 user_manga_follow 表...")

    if not table_exists(cursor, "user_manga_follow"):
        cursor.execute(
            """
            CREATE TABLE user_manga_follow (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                series_id INTEGER NOT NULL,
                last_synced_chapter_id INTEGER,
                last_seen_chapter_id INTEGER,
                unread_chapter_count INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (series_id) REFERENCES manga_series_local(id) ON DELETE CASCADE,
                FOREIGN KEY (last_synced_chapter_id) REFERENCES manga_chapter_local(id),
                FOREIGN KEY (last_seen_chapter_id) REFERENCES manga_chapter_local(id),
                UNIQUE(user_id, series_id)
            )
            """
        )
        cursor.execute(
            "CREATE INDEX idx_user_manga_follow_user_id ON user_manga_follow(user_id)"
        )
        cursor.execute(
            "CREATE INDEX idx_user_manga_follow_series_id ON user_manga_follow(series_id)"
        )
        print("  [OK] user_manga_follow 表创建成功")
    else:
        print("  [-] user_manga_follow 表已存在，跳过创建")

    conn.commit()
    print("\n[SUCCESS] 迁移完成！")
except Exception as e:  # noqa: BLE001
    print(f"[ERROR] 迁移失败: {e}")
    conn.rollback()
finally:
    conn.close()
