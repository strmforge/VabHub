"""
添加站点表新字段的迁移脚本
"""
import sqlite3
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vabhub.db")
DB_PATH = DATABASE_URL.replace("sqlite:///./", "")

def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return any(col[1] == column_name for col in columns)

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("检查并添加站点表（sites）的新字段...")

    # 获取现有列
    cursor.execute("PRAGMA table_info(sites)")
    columns = [col[1] for col in cursor.fetchall()]

    fields_to_add = [
        ('cookiecloud_server', 'VARCHAR(500)'),
        ('last_checkin', 'DATETIME'),
    ]

    for field_name, field_type in fields_to_add:
        if field_name not in columns:
            print(f"添加字段 {field_name}...")
            cursor.execute(f"ALTER TABLE sites ADD COLUMN {field_name} {field_type}")
            print(f"  [OK] {field_name} 字段添加成功")
        else:
            print(f"  [-] {field_name} 字段已存在，跳过")

    # 提交更改
    conn.commit()
    print("\n[SUCCESS] 迁移完成！")

except Exception as e:
    print(f"[ERROR] 迁移失败: {e}")
    conn.rollback()
finally:
    conn.close()

