"""
添加HNR检测表的迁移脚本
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

    print("检查并创建HNR检测表...")

    # 创建HNR检测记录表
    if not table_exists(cursor, "hnr_detections"):
        cursor.execute("""
            CREATE TABLE hnr_detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                download_task_id INTEGER,
                title VARCHAR(500) NOT NULL,
                site_id INTEGER,
                site_name VARCHAR(100),
                verdict VARCHAR(20) NOT NULL,
                confidence FLOAT DEFAULT 0.0,
                matched_rules TEXT,
                category VARCHAR(50),
                penalties TEXT,
                message TEXT,
                detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  [OK] hnr_detections 表创建成功")
    else:
        print("  [-] hnr_detections 表已存在，跳过创建")

    # 创建HNR监控任务表
    if not table_exists(cursor, "hnr_tasks"):
        cursor.execute("""
            CREATE TABLE hnr_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                download_task_id INTEGER NOT NULL,
                title VARCHAR(500) NOT NULL,
                site_id INTEGER,
                site_name VARCHAR(100),
                status VARCHAR(20) DEFAULT 'monitoring',
                risk_score FLOAT DEFAULT 0.0,
                current_ratio FLOAT DEFAULT 0.0,
                required_ratio FLOAT DEFAULT 1.0,
                seed_time_hours FLOAT DEFAULT 0.0,
                required_seed_time_hours FLOAT DEFAULT 0.0,
                downloaded_gb FLOAT DEFAULT 0.0,
                uploaded_gb FLOAT DEFAULT 0.0,
                last_check DATETIME,
                next_check DATETIME,
                completed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX idx_hnr_tasks_download_task_id ON hnr_tasks(download_task_id)")
        cursor.execute("CREATE INDEX idx_hnr_tasks_status ON hnr_tasks(status)")
        cursor.execute("CREATE INDEX idx_hnr_tasks_risk_score ON hnr_tasks(risk_score)")
        print("  [OK] hnr_tasks 表创建成功")
    else:
        print("  [-] hnr_tasks 表已存在，跳过创建")

    # 创建HNR签名规则表
    if not table_exists(cursor, "hnr_signatures"):
        cursor.execute("""
            CREATE TABLE hnr_signatures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                patterns TEXT NOT NULL,
                confidence FLOAT DEFAULT 0.8,
                category VARCHAR(50),
                penalties TEXT,
                is_active BOOLEAN DEFAULT 1,
                site_ids TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  [OK] hnr_signatures 表创建成功")
    else:
        print("  [-] hnr_signatures 表已存在，跳过创建")

    conn.commit()
    print("\n[SUCCESS] 迁移完成！")

except Exception as e:
    print(f"[ERROR] 迁移失败: {e}")
    conn.rollback()
finally:
    conn.close()

