"""
添加音乐订阅关键字字段迁移脚本

为 user_music_subscriptions 表添加关键字订阅支持：
- subscription_type: 订阅类型（chart/keyword）
- music_query: 搜索关键字
- music_site: 指定站点
- music_quality: 质量偏好
- 更新索引结构
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

    print("检查并升级用户音乐订阅表...")

    if not table_exists(cursor, "user_music_subscriptions"):
        print("  [ERROR] user_music_subscriptions 表不存在，请先运行基础迁移")
        exit(1)

    # 检查并添加 subscription_type 字段
    if not column_exists(cursor, "user_music_subscriptions", "subscription_type"):
        cursor.execute("""
            ALTER TABLE user_music_subscriptions 
            ADD COLUMN subscription_type VARCHAR(20) DEFAULT 'chart' NOT NULL
        """)
        print("  [OK] 添加 subscription_type 字段")
    else:
        print("  [-] subscription_type 字段已存在")

    # 检查并修改 chart_id 字段为可空
    # SQLite 不支持直接修改列，需要重建表
    cursor.execute("PRAGMA table_info(user_music_subscriptions)")
    columns_info = cursor.fetchall()
    chart_id_nullable = None
    for col in columns_info:
        if col[1] == "chart_id":
            chart_id_nullable = col[3] == 0  # 3是nullable索引，0表示NOT NULL
            break
    
    if chart_id_nullable:
        print("  [INFO] 需要重建表以使 chart_id 可空...")
        
        # 创建临时表
        cursor.execute("""
            CREATE TABLE user_music_subscriptions_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subscription_type VARCHAR(20) DEFAULT 'chart' NOT NULL,
                chart_id INTEGER,
                music_query VARCHAR(500),
                music_site VARCHAR(100),
                music_quality VARCHAR(50),
                status VARCHAR(20) DEFAULT 'active',
                auto_search BOOLEAN DEFAULT 1,
                auto_download BOOLEAN DEFAULT 0,
                max_new_tracks_per_run INTEGER DEFAULT 10,
                quality_preference VARCHAR(20) DEFAULT 'flac',
                preferred_sites VARCHAR(500),
                allow_hr BOOLEAN DEFAULT 0,
                allow_h3h5 BOOLEAN DEFAULT 0,
                strict_free_only BOOLEAN DEFAULT 0,
                last_run_at DATETIME,
                last_run_new_count INTEGER,
                last_run_search_count INTEGER,
                last_run_download_count INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (chart_id) REFERENCES music_charts(id) ON DELETE CASCADE
            )
        """)
        
        # 复制数据
        cursor.execute("""
            INSERT INTO user_music_subscriptions_temp (
                id, user_id, subscription_type, chart_id, status, auto_search, 
                auto_download, max_new_tracks_per_run, quality_preference, 
                preferred_sites, allow_hr, allow_h3h5, strict_free_only,
                last_run_at, last_run_new_count, 
                last_run_search_count, last_run_download_count, created_at, updated_at
            )
            SELECT 
                id, user_id, 'chart', chart_id, status, auto_search, 
                auto_download, max_new_tracks_per_run, quality_preference, 
                preferred_sites, 0, 0, 0,
                last_run_at, last_run_new_count, 
                last_run_search_count, last_run_download_count, created_at, updated_at
            FROM user_music_subscriptions
        """)
        
        # 删除旧表
        cursor.execute("DROP TABLE user_music_subscriptions")
        
        # 重命名临时表
        cursor.execute("ALTER TABLE user_music_subscriptions_temp RENAME TO user_music_subscriptions")
        
        print("  [OK] 重建表完成，chart_id 现在可空")
    else:
        print("  [-] chart_id 已是可空字段")

    # 添加关键字订阅字段
    if not column_exists(cursor, "user_music_subscriptions", "music_query"):
        cursor.execute("ALTER TABLE user_music_subscriptions ADD COLUMN music_query VARCHAR(500)")
        print("  [OK] 添加 music_query 字段")
    else:
        print("  [-] music_query 字段已存在")

    if not column_exists(cursor, "user_music_subscriptions", "music_site"):
        cursor.execute("ALTER TABLE user_music_subscriptions ADD COLUMN music_site VARCHAR(100)")
        print("  [OK] 添加 music_site 字段")
    else:
        print("  [-] music_site 字段已存在")

    if not column_exists(cursor, "user_music_subscriptions", "music_quality"):
        cursor.execute("ALTER TABLE user_music_subscriptions ADD COLUMN music_quality VARCHAR(50)")
        print("  [OK] 添加 music_quality 字段")
    else:
        print("  [-] music_quality 字段已存在")

    # 添加安全策略字段
    if not column_exists(cursor, "user_music_subscriptions", "allow_hr"):
        cursor.execute("ALTER TABLE user_music_subscriptions ADD COLUMN allow_hr BOOLEAN DEFAULT 0")
        print("  [OK] 添加 allow_hr 字段")
    else:
        print("  [-] allow_hr 字段已存在")

    if not column_exists(cursor, "user_music_subscriptions", "allow_h3h5"):
        cursor.execute("ALTER TABLE user_music_subscriptions ADD COLUMN allow_h3h5 BOOLEAN DEFAULT 0")
        print("  [OK] 添加 allow_h3h5 字段")
    else:
        print("  [-] allow_h3h5 字段已存在")

    if not column_exists(cursor, "user_music_subscriptions", "strict_free_only"):
        cursor.execute("ALTER TABLE user_music_subscriptions ADD COLUMN strict_free_only BOOLEAN DEFAULT 0")
        print("  [OK] 添加 strict_free_only 字段")
    else:
        print("  [-] strict_free_only 字段已存在")

    # 重建索引
    print("  [INFO] 重建索引...")
    
    # 删除旧索引
    cursor.execute("DROP INDEX IF EXISTS ix_user_music_subs_user_chart")
    cursor.execute("DROP INDEX IF EXISTS ix_user_music_subs_status_last_run")
    
    # 创建新索引
    cursor.execute("CREATE INDEX ix_user_music_subs_user_chart_type ON user_music_subscriptions(user_id, subscription_type, chart_id)")
    cursor.execute("CREATE INDEX ix_user_music_subs_user_query_type ON user_music_subscriptions(user_id, subscription_type, music_query)")
    cursor.execute("CREATE INDEX ix_user_music_subs_status_last_run ON user_music_subscriptions(status, last_run_at)")
    cursor.execute("CREATE INDEX ix_user_music_subs_type_status ON user_music_subscriptions(subscription_type, status)")
    cursor.execute("CREATE INDEX ix_user_music_subs_music_query ON user_music_subscriptions(music_query)")
    
    print("  [OK] 索引重建完成")

    conn.commit()
    print("\n[SUCCESS] 音乐订阅关键字字段迁移完成！")

except Exception as e:
    print(f"[ERROR] 迁移失败: {e}")
    conn.rollback()
finally:
    conn.close()
