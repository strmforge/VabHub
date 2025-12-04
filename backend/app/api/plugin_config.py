"""
插件配置 API
PLUGIN-UX-3 实现

提供插件配置的读取和更新接口
"""

from typing import Any
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from loguru import logger

from app.core.deps import DbSessionDep, CurrentAdminUserDep
from app.schemas.response import BaseResponse
from app.models.plugin import Plugin
from app.models.plugin_config import PluginConfig
from app.schemas.plugin import PluginConfigSchema, PluginConfigUpdate


router = APIRouter(prefix="/dev/plugins", tags=["plugin-config"])


def _validate_config(config: dict[str, Any], schema: dict[str, Any] | None) -> list[str]:
    """
    简单的配置校验
    
    Args:
        config: 配置数据
        schema: JSON Schema（简化版）
        
    Returns:
        错误列表
    """
    if not schema:
        return []
    
    errors = []
    schema_type = schema.get("type")
    
    if schema_type != "object":
        return []
    
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    # 检查 required 字段
    for field in required:
        if field not in config:
            errors.append(f"缺少必填字段: {field}")
    
    # 检查类型
    for key, value in config.items():
        if key not in properties:
            continue
        
        prop_schema = properties[key]
        prop_type = prop_schema.get("type")
        
        if prop_type == "string" and not isinstance(value, str):
            errors.append(f"字段 {key} 应为字符串")
        elif prop_type == "boolean" and not isinstance(value, bool):
            errors.append(f"字段 {key} 应为布尔值")
        elif prop_type in ("integer", "number"):
            if not isinstance(value, (int, float)):
                errors.append(f"字段 {key} 应为数字")
            else:
                # 检查范围
                minimum = prop_schema.get("minimum")
                maximum = prop_schema.get("maximum")
                if minimum is not None and value < minimum:
                    errors.append(f"字段 {key} 不能小于 {minimum}")
                if maximum is not None and value > maximum:
                    errors.append(f"字段 {key} 不能大于 {maximum}")
        elif prop_type == "array" and not isinstance(value, list):
            errors.append(f"字段 {key} 应为数组")
    
    return errors


def _get_default_config(schema: dict[str, Any] | None) -> dict[str, Any]:
    """
    根据 schema 生成默认配置
    """
    if not schema or schema.get("type") != "object":
        return {}
    
    defaults = {}
    properties = schema.get("properties", {})
    
    for key, prop_schema in properties.items():
        if "default" in prop_schema:
            defaults[key] = prop_schema["default"]
        else:
            # 根据类型设置默认值
            prop_type = prop_schema.get("type")
            if prop_type == "boolean":
                defaults[key] = False
            elif prop_type == "string":
                defaults[key] = ""
            elif prop_type in ("integer", "number"):
                defaults[key] = 0
            elif prop_type == "array":
                defaults[key] = []
            elif prop_type == "object":
                defaults[key] = {}
    
    return defaults


@router.get(
    "/{plugin_id}/config",
    response_model=BaseResponse[PluginConfigSchema],
    summary="获取插件配置",
)
async def get_plugin_config(
    plugin_id: str,
    db: DbSessionDep,
    current_admin: CurrentAdminUserDep,
):
    """
    获取插件当前配置
    
    - 若不存在配置记录，返回空配置或根据 schema 生成默认值
    - plugin_id 为插件的 name 字段（如 vabhub.example.hello）
    """
    # 验证插件存在
    stmt = select(Plugin).where(Plugin.name == plugin_id)
    result = await db.execute(stmt)
    plugin = result.scalar_one_or_none()
    
    if not plugin:
        raise HTTPException(status_code=404, detail=f"插件不存在: {plugin_id}")
    
    # 获取配置
    stmt = select(PluginConfig).where(PluginConfig.plugin_id == plugin_id)
    result = await db.execute(stmt)
    config_record = result.scalar_one_or_none()
    
    if config_record:
        return BaseResponse(
            success=True,
            data=PluginConfigSchema(
                plugin_id=plugin_id,
                config=config_record.config,
                updated_at=config_record.updated_at,
            )
        )
    
    # 返回默认配置
    default_config = _get_default_config(plugin.config_schema)
    
    return BaseResponse(
        success=True,
        data=PluginConfigSchema(
            plugin_id=plugin_id,
            config=default_config,
            updated_at=None,
        )
    )


@router.put(
    "/{plugin_id}/config",
    response_model=BaseResponse[PluginConfigSchema],
    summary="更新插件配置",
)
async def update_plugin_config(
    plugin_id: str,
    body: PluginConfigUpdate,
    db: DbSessionDep,
    current_admin: CurrentAdminUserDep,
):
    """
    更新插件配置
    
    - 会进行基础的类型校验（如果插件声明了 config_schema）
    - 保存到 PluginConfig 表
    """
    # 验证插件存在
    stmt = select(Plugin).where(Plugin.name == plugin_id)
    result = await db.execute(stmt)
    plugin = result.scalar_one_or_none()
    
    if not plugin:
        raise HTTPException(status_code=404, detail=f"插件不存在: {plugin_id}")
    
    # 校验配置
    errors = _validate_config(body.config, plugin.config_schema)
    if errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))
    
    # 查找或创建配置记录
    stmt = select(PluginConfig).where(PluginConfig.plugin_id == plugin_id)
    result = await db.execute(stmt)
    config_record = result.scalar_one_or_none()
    
    if config_record:
        config_record.config = body.config
    else:
        config_record = PluginConfig(
            plugin_id=plugin_id,
            config=body.config,
        )
        db.add(config_record)
    
    await db.commit()
    await db.refresh(config_record)
    
    logger.info(f"[plugin-config] Updated config for {plugin_id}")
    
    return BaseResponse(
        success=True,
        data=PluginConfigSchema(
            plugin_id=plugin_id,
            config=config_record.config,
            updated_at=config_record.updated_at,
        )
    )
