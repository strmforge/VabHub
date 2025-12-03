"""
添加系统设置表的迁移脚本
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

    print("检查并创建系统设置表（system_settings）...")

    if not table_exists(cursor, "system_settings"):
        cursor.execute("""
            CREATE TABLE system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key VARCHAR(100) UNIQUE NOT NULL,
                value TEXT,
                category VARCHAR(50) NOT NULL,
                description TEXT,
                is_encrypted BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX idx_system_settings_key ON system_settings(key)")
        cursor.execute("CREATE INDEX idx_system_settings_category ON system_settings(category)")
        print("  [OK] system_settings 表创建成功")
    else:
        print("  [-] system_settings 表已存在，跳过创建")

    conn.commit()
    print("\n[SUCCESS] 迁移完成！")

except Exception as e:
    print(f"[ERROR] 迁移失败: {e}")
    conn.rollback()
finally:
    conn.close()

