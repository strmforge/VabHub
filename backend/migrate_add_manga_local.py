"""
添加本地漫画库表迁移脚本

创建 manga_series_local 与 manga_chapter_local 表
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

    print("检查并创建本地漫画库表...")

    # 创建 manga_series_local 表
    if not table_exists(cursor, "manga_series_local"):
        cursor.execute("""
            CREATE TABLE manga_series_local (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL,
                remote_series_id VARCHAR(256) NOT NULL,
                title VARCHAR(512) NOT NULL,
                alt_titles TEXT,
                cover_path VARCHAR(1024),
                summary TEXT,
                authors TEXT,
                tags TEXT,
                status VARCHAR(64),
                language VARCHAR(32),
                is_favorite BOOLEAN NOT NULL DEFAULT 0,
                is_hidden BOOLEAN NOT NULL DEFAULT 0,
                total_chapters INTEGER,
                downloaded_chapters INTEGER,
                last_sync_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES manga_sources(id)
            )
        """)
        cursor.execute("CREATE INDEX idx_manga_series_local_source_id ON manga_series_local(source_id)")
        cursor.execute("CREATE INDEX idx_manga_series_local_remote_series_id ON manga_series_local(remote_series_id)")
        print("  [OK] manga_series_local 表创建成功")
    else:
        print("  [-] manga_series_local 表已存在，跳过创建")

    # 创建 manga_chapter_local 表
    if not table_exists(cursor, "manga_chapter_local"):
        cursor.execute("""
            CREATE TABLE manga_chapter_local (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                series_id INTEGER NOT NULL,
                remote_chapter_id VARCHAR(256) NOT NULL,
                title VARCHAR(512) NOT NULL,
                number REAL,
                volume INTEGER,
                published_at DATETIME,
                file_path VARCHAR(1024),
                page_count INTEGER,
                status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
                last_error TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (series_id) REFERENCES manga_series_local(id)
            )
        """)
        cursor.execute("CREATE INDEX idx_manga_chapter_local_series_id ON manga_chapter_local(series_id)")
        cursor.execute("CREATE INDEX idx_manga_chapter_local_remote_chapter_id ON manga_chapter_local(remote_chapter_id)")
        cursor.execute("CREATE INDEX idx_manga_chapter_local_status ON manga_chapter_local(status)")
        print("  [OK] manga_chapter_local 表创建成功")
    else:
        print("  [-] manga_chapter_local 表已存在，跳过创建")

    conn.commit()
    print("\n[SUCCESS] 迁移完成！")

except Exception as e:
    print(f"[ERROR] 迁移失败: {e}")
    conn.rollback()
finally:
    conn.close()

