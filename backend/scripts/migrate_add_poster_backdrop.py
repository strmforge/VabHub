"""
迁移脚本：为subscriptions表添加poster和backdrop列
"""

import sqlite3
import sys
from pathlib import Path

# 添加backend目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def migrate():
    """添加poster和backdrop列到subscriptions表"""
    # 数据库路径
    db_path = backend_dir / "vabhub.db"
    
    if not db_path.exists():
        print(f"[INFO] 数据库文件不存在: {db_path}")
        print("[INFO] 数据库将在首次启动时自动创建")
        return
    
    print(f"[INFO] 连接到数据库: {db_path}")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # 检查poster列是否存在
        cursor.execute("PRAGMA table_info(subscriptions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        changes_made = False
        
        # 添加poster列
        if "poster" not in columns:
            print("[INFO] 添加poster列...")
            cursor.execute("ALTER TABLE subscriptions ADD COLUMN poster VARCHAR(500)")
            changes_made = True
        else:
            print("[INFO] poster列已存在")
        
        # 添加backdrop列
        if "backdrop" not in columns:
            print("[INFO] 添加backdrop列...")
            cursor.execute("ALTER TABLE subscriptions ADD COLUMN backdrop VARCHAR(500)")
            changes_made = True
        else:
            print("[INFO] backdrop列已存在")
        
        if changes_made:
            conn.commit()
            print("[OK] 迁移完成")
        else:
            print("[OK] 无需迁移，所有列已存在")
            
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] 迁移失败: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()

