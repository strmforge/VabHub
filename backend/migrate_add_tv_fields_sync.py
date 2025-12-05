"""
数据库迁移脚本：添加电视剧相关字段（同步版本）
"""
import sqlite3
from pathlib import Path

# 获取数据库路径
db_path = Path(__file__).parent / "vabhub.db"

if not db_path.exists():
    print(f"数据库文件不存在: {db_path}")
    print("请先运行主程序创建数据库表")
    exit(1)

# 连接数据库
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

try:
    # 检查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subscriptions'")
    if not cursor.fetchone():
        print("subscriptions表不存在，请先创建表")
        conn.close()
        exit(1)
    
    # 获取现有字段
    cursor.execute("PRAGMA table_info(subscriptions)")
    columns = {row[1] for row in cursor.fetchall()}
    
    # 需要添加的字段
    fields_to_add = [
        ('season', 'INTEGER'),
        ('total_episode', 'INTEGER'),
        ('start_episode', 'INTEGER'),
        ('episode_group', 'VARCHAR(100)'),
    ]
    
    for field_name, field_type in fields_to_add:
        if field_name not in columns:
            print(f"添加字段 {field_name}...")
            cursor.execute(f"ALTER TABLE subscriptions ADD COLUMN {field_name} {field_type}")
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

