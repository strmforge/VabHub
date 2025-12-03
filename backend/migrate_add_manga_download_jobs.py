#!/usr/bin/env python3
"""
添加漫画下载任务表

迁移脚本：创建 manga_download_jobs 表
"""
import sqlite3
import sys
from pathlib import Path

def migrate():
    """执行数据库迁移"""
    db_path = Path(__file__).parent / "vabhub.db"
    
    if not db_path.exists():
        print(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 检查表是否已存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='manga_download_jobs'
        """)
        
        if cursor.fetchone():
            print("manga_download_jobs 表已存在，跳过迁移")
            return True
        
        # 创建 manga_download_jobs 表
        cursor.execute("""
            CREATE TABLE manga_download_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                source_id INTEGER NOT NULL,
                source_type VARCHAR(50) NOT NULL,
                source_series_id VARCHAR(100) NOT NULL,
                source_chapter_id VARCHAR(100) NULL,
                target_local_series_id INTEGER NULL,
                mode VARCHAR(20) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                priority INTEGER NOT NULL DEFAULT 0,
                error_msg TEXT NULL,
                total_chapters INTEGER NULL,
                downloaded_chapters INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                started_at DATETIME NULL,
                completed_at DATETIME NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (source_id) REFERENCES manga_sources (id),
                FOREIGN KEY (target_local_series_id) REFERENCES manga_series_local (id)
            )
        """)
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX idx_manga_download_jobs_user_id ON manga_download_jobs(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_manga_download_jobs_source_id ON manga_download_jobs(source_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_manga_download_jobs_source_series_id ON manga_download_jobs(source_series_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_manga_download_jobs_source_chapter_id ON manga_download_jobs(source_chapter_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_manga_download_jobs_target_local_series_id ON manga_download_jobs(target_local_series_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_manga_download_jobs_status ON manga_download_jobs(status)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_manga_download_jobs_created_at ON manga_download_jobs(created_at)
        """)
        
        # 创建触发器：自动更新 updated_at
        cursor.execute("""
            CREATE TRIGGER update_manga_download_jobs_updated_at 
            AFTER UPDATE ON manga_download_jobs
            FOR EACH ROW
            BEGIN
                UPDATE manga_download_jobs 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END
        """)
        
        conn.commit()
        print("manga_download_jobs 表创建成功")
        
        # 验证表结构
        cursor.execute("PRAGMA table_info(manga_download_jobs)")
        columns = cursor.fetchall()
        print(f"表结构验证成功，共 {len(columns)} 个字段")
        
        return True
        
    except Exception as e:
        print(f"迁移失败: {e}")
        return False
    finally:
        if conn:
            conn.close()

def rollback():
    """回滚迁移"""
    db_path = Path(__file__).parent / "vabhub.db"
    
    if not db_path.exists():
        print(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 删除触发器
        cursor.execute("""
            DROP TRIGGER IF EXISTS update_manga_download_jobs_updated_at
        """)
        
        # 删除表
        cursor.execute("""
            DROP TABLE IF EXISTS manga_download_jobs
        """)
        
        conn.commit()
        print("manga_download_jobs 表删除成功")
        return True
        
    except Exception as e:
        print(f"回滚失败: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        success = rollback()
    else:
        success = migrate()
    
    sys.exit(0 if success else 1)
