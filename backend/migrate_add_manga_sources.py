"""
添加漫画源表迁移脚本

创建 manga_sources 表
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

    print("检查并创建漫画源表（manga_sources）...")

    if not table_exists(cursor, "manga_sources"):
        cursor.execute("""
            CREATE TABLE manga_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(128) NOT NULL,
                type VARCHAR(50) NOT NULL,
                base_url VARCHAR(512) NOT NULL,
                api_key VARCHAR(512),
                username VARCHAR(128),
                password VARCHAR(256),
                is_enabled BOOLEAN NOT NULL DEFAULT 1,
                extra_config TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX idx_manga_sources_type ON manga_sources(type)")
        cursor.execute("CREATE INDEX idx_manga_sources_enabled ON manga_sources(is_enabled)")
        print("  [OK] manga_sources 表创建成功")
    else:
        print("  [-] manga_sources 表已存在，跳过创建")

    conn.commit()
    print("\n[SUCCESS] 迁移完成！")

except Exception as e:
    print(f"[ERROR] 迁移失败: {e}")
    conn.rollback()
finally:
    conn.close()

