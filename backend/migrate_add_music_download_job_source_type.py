"""
添加音乐下载任务来源类型字段迁移脚本

为 music_download_jobs 表添加 source_type 字段，支持区分榜单订阅和关键字订阅的任务来源。
"""
import sqlite3
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vabhub.db")
DB_PATH = DATABASE_URL.replace("sqlite:///./", "")

def table_exists(cursor, table_name):
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    return cursor.fetchone() is not None

def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("检查并升级音乐下载任务表...")

    if not table_exists(cursor, "music_download_jobs"):
        print("  [ERROR] music_download_jobs 表不存在，请先运行基础迁移")
        exit(1)

    # 检查并添加 source_type 字段
    if not column_exists(cursor, "music_download_jobs", "source_type"):
        cursor.execute("""
            ALTER TABLE music_download_jobs 
            ADD COLUMN source_type VARCHAR(20) DEFAULT 'chart' NOT NULL
        """)
        print("  [OK] 添加 source_type 字段")
        
        # 更新现有记录为chart类型
        cursor.execute("""
            UPDATE music_download_jobs 
            SET source_type = 'chart' 
            WHERE source_type IS NULL OR source_type = ''
        """)
        print("  [OK] 更新现有记录为chart类型")
    else:
        print("  [-] source_type 字段已存在")

    # 重建索引
    print("  [INFO] 重建索引...")
    
    # 删除旧索引（如果存在）
    cursor.execute("DROP INDEX IF EXISTS ix_music_download_jobs_status_created")
    cursor.execute("DROP INDEX IF EXISTS ix_music_download_jobs_user_status")
    cursor.execute("DROP INDEX IF EXISTS ix_music_download_jobs_downloader_hash")
    
    # 创建新索引（包含source_type）
    cursor.execute("CREATE INDEX ix_music_download_jobs_status_created ON music_download_jobs(status, created_at)")
    cursor.execute("CREATE INDEX ix_music_download_jobs_user_status ON music_download_jobs(user_id, status)")
    cursor.execute("CREATE INDEX ix_music_download_jobs_source_type ON music_download_jobs(source_type)")
    cursor.execute("CREATE INDEX ix_music_download_jobs_subscription_source ON music_download_jobs(subscription_id, source_type)")
    cursor.execute("CREATE INDEX ix_music_download_jobs_downloader_hash ON music_download_jobs(downloader_hash)")
    
    print("  [OK] 索引重建完成")

    conn.commit()
    print("\n[SUCCESS] 音乐下载任务来源类型字段迁移完成！")

except Exception as e:
    print(f"[ERROR] 迁移失败: {e}")
    conn.rollback()
finally:
    conn.close()
