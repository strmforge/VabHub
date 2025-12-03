"""
添加用户视频播放进度表迁移脚本

创建 user_video_progress 表
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

    print("检查并创建用户视频播放进度表...")

    # 创建 user_video_progress 表
    if not table_exists(cursor, "user_video_progress"):
        cursor.execute("""
            CREATE TABLE user_video_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                work_id INTEGER NOT NULL,
                position_seconds INTEGER NOT NULL DEFAULT 0,
                duration_seconds INTEGER NOT NULL DEFAULT 0,
                progress_percent REAL NOT NULL DEFAULT 0.0,
                is_finished BOOLEAN NOT NULL DEFAULT 0,
                source_type VARCHAR(50) NOT NULL DEFAULT 'local',
                last_play_url VARCHAR(500),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (work_id) REFERENCES media(id),
                UNIQUE(user_id, work_id)
            )
        """)
        
        # 创建索引优化查询性能
        cursor.execute("CREATE INDEX idx_user_video_progress_user_id ON user_video_progress(user_id)")
        cursor.execute("CREATE INDEX idx_user_video_progress_work_id ON user_video_progress(work_id)")
        cursor.execute("CREATE INDEX idx_user_video_progress_user_updated ON user_video_progress(user_id, updated_at)")
        cursor.execute("CREATE INDEX idx_user_video_progress_is_finished ON user_video_progress(is_finished)")
        
        print("  [OK] user_video_progress 表创建成功")
    else:
        print("  [-] user_video_progress 表已存在，跳过创建")

    conn.commit()
    print("\n[SUCCESS] 迁移完成！")

except Exception as e:
    print(f"[ERROR] 迁移失败: {e}")
    conn.rollback()
finally:
    conn.close()
