"""
添加搜索历史表的迁移脚本
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

    print("检查并创建搜索历史表（search_history）...")

    if not table_exists(cursor, "search_history"):
        print("创建 search_history 表...")
        cursor.execute("""
            CREATE TABLE search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query VARCHAR(255) NOT NULL,
                user_id INTEGER,
                media_type VARCHAR(20),
                filters TEXT,
                result_count INTEGER DEFAULT 0,
                searched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX idx_search_history_query ON search_history(query)")
        cursor.execute("CREATE INDEX idx_search_history_user_id ON search_history(user_id)")
        cursor.execute("CREATE INDEX idx_search_history_searched_at ON search_history(searched_at)")
        
        print("  [OK] search_history 表创建成功")
    else:
        print("  [-] search_history 表已存在，跳过")

    # 提交更改
    conn.commit()
    print("\n[SUCCESS] 迁移完成！")

except Exception as e:
    print(f"[ERROR] 迁移失败: {e}")
    conn.rollback()
finally:
    conn.close()

