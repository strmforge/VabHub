"""
数据库迁移脚本：添加全局规则设置表
SETTINGS-RULES-1: 创建 global_rule_settings 表并填充默认值
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).parent))

from sqlalchemy import text
from app.core.database import get_db_session
from app.models.global_rules import GlobalRuleSettings
from app.models.enums.global_rules import (
    HRPolicy, HRMode, ResolutionTier, ResolutionPolicy,
    SourceQualityPolicy, HdrPolicy, CodecPolicy,
    SubtitlePolicy, AudioLangPolicy, ExtraFeaturePolicy
)
from loguru import logger


async def create_global_rules_table():
    """创建全局规则设置表"""
    
    async with get_db_session() as db:
        try:
            # 检查表是否已存在
            result = await db.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'global_rule_settings'
            """))
            table_exists = result.scalar() > 0
            
            if table_exists:
                logger.info("全局规则设置表已存在，跳过创建")
                return
            
            # 创建表
            create_table_sql = """
            CREATE TABLE global_rule_settings (
                id INTEGER PRIMARY KEY,
                hr_policy VARCHAR(20) NOT NULL DEFAULT 'SAFE_SKIP',
                hr_mode VARCHAR(20) NOT NULL DEFAULT 'B_BALANCED',
                resolution_policy VARCHAR(20) NOT NULL DEFAULT 'AUTO',
                resolution_tier VARCHAR(20) NOT NULL DEFAULT 'MID_1080P',
                source_quality_policy VARCHAR(20) NOT NULL DEFAULT 'NO_TRASH',
                hdr_policy VARCHAR(20) NOT NULL DEFAULT 'ANY',
                codec_policy VARCHAR(20) NOT NULL DEFAULT 'ANY',
                subtitle_policy VARCHAR(20) NOT NULL DEFAULT 'ANY',
                audio_lang_policy VARCHAR(20) NOT NULL DEFAULT 'ANY',
                extra_feature_policy VARCHAR(20) NOT NULL DEFAULT 'FORBID_3D',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_by VARCHAR(100)
            )
            """
            
            await db.execute(text(create_table_sql))
            logger.info("全局规则设置表创建成功")
            
            # 插入默认设置
            default_settings = GlobalRuleSettings.get_default_settings()
            insert_sql = """
            INSERT INTO global_rule_settings (
                id, hr_policy, hr_mode, resolution_policy, resolution_tier,
                source_quality_policy, hdr_policy, codec_policy,
                subtitle_policy, audio_lang_policy, extra_feature_policy,
                created_at, updated_at
            ) VALUES (
                1, :hr_policy, :hr_mode, :resolution_policy, :resolution_tier,
                :source_quality_policy, :hdr_policy, :codec_policy,
                :subtitle_policy, :audio_lang_policy, :extra_feature_policy,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            """
            
            await db.execute(text(insert_sql), default_settings)
            await db.commit()
            
            logger.info("默认全局规则设置插入成功")
            logger.info(f"默认设置: {default_settings}")
            
        except Exception as e:
            logger.error(f"创建全局规则设置表失败: {e}")
            await db.rollback()
            raise


async def verify_migration():
    """验证迁移结果"""
    
    async with get_db_session() as db:
        try:
            # 查询表结构
            result = await db.execute(text("""
                SELECT column_name, data_type, column_default, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'global_rule_settings'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            
            logger.info("全局规则设置表结构:")
            for column in columns:
                logger.info(f"  {column[0]}: {column[1]} (默认值: {column[2]}, 可空: {column[3]})")
            
            # 查询默认数据
            result = await db.execute(text("""
                SELECT * FROM global_rule_settings WHERE id = 1
            """))
            settings = result.fetchone()
            
            if settings:
                logger.info("默认全局规则设置:")
                logger.info(f"  HR策略: {settings.hr_policy}")
                logger.info(f"  HR模式: {settings.hr_mode}")
                logger.info(f"  分辨率策略: {settings.resolution_policy}")
                logger.info(f"  分辨率档位: {settings.resolution_tier}")
                logger.info(f"  源质量策略: {settings.source_quality_policy}")
                logger.info(f"  HDR策略: {settings.hdr_policy}")
                logger.info(f"  编码策略: {settings.codec_policy}")
                logger.info(f"  字幕策略: {settings.subtitle_policy}")
                logger.info(f"  音轨策略: {settings.audio_lang_policy}")
                logger.info(f"  额外功能策略: {settings.extra_feature_policy}")
                logger.info(f"  创建时间: {settings.created_at}")
                logger.info(f"  更新时间: {settings.updated_at}")
            else:
                logger.warning("未找到默认全局规则设置")
            
        except Exception as e:
            logger.error(f"验证迁移失败: {e}")
            raise


async def main():
    """主函数"""
    logger.info("开始全局规则设置表迁移...")
    
    try:
        await create_global_rules_table()
        await verify_migration()
        logger.info("全局规则设置表迁移完成")
        
    except Exception as e:
        logger.error(f"迁移失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
