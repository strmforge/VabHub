"""
AI 工具抽象基类

FUTURE-AI-ORCHESTRATOR-1 P2 实现
定义所有 AI 工具的统一接口
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from app.models.user import User


class OrchestratorContext(BaseModel):
    """
    Orchestrator 执行上下文
    
    通过 FastAPI DI 注入，提供工具执行所需的依赖
    """
    
    # 数据库会话
    db: Any = Field(..., description="数据库会话 (AsyncSession)")
    
    # 当前用户信息
    user_id: Optional[int] = Field(None, description="当前用户 ID")
    user_name: Optional[str] = Field(None, description="当前用户名")
    is_admin: bool = Field(False, description="是否为管理员")
    
    # 配置信息
    debug_mode: bool = Field(False, description="是否为调试模式")
    
    class Config:
        arbitrary_types_allowed = True
    
    @classmethod
    def from_request(
        cls,
        db: AsyncSession,
        user: Optional["User"] = None,
        debug: bool = False,
    ) -> "OrchestratorContext":
        """
        从请求创建上下文
        
        Args:
            db: 数据库会话
            user: 当前用户
            debug: 是否为调试模式
        """
        return cls(
            db=db,
            user_id=user.id if user else None,
            user_name=user.username if user else None,
            is_admin=getattr(user, "is_admin", False) if user else False,
            debug_mode=debug,
        )


class AITool(ABC):
    """
    AI 工具抽象基类
    
    所有 AI 工具必须继承此类并实现 run 方法
    """
    
    # 工具名称（用于 LLM 调用）
    name: str
    
    # 工具描述（用于 LLM 理解工具用途）
    description: str
    
    # 输入参数模型（Pydantic BaseModel 子类）
    input_model: type[BaseModel]
    
    # 输出结果模型（Pydantic BaseModel 子类）
    output_model: type[BaseModel]
    
    @abstractmethod
    async def run(
        self,
        params: BaseModel,
        context: OrchestratorContext,
    ) -> BaseModel:
        """
        执行工具
        
        Args:
            params: 输入参数（符合 input_model 的实例）
            context: 执行上下文
            
        Returns:
            输出结果（符合 output_model 的实例）
        """
        ...
    
    def get_json_schema(self) -> dict:
        """
        获取工具的 JSON Schema 定义
        
        用于生成 LLM 的工具描述
        """
        return {
            "type": "object",
            "properties": self.input_model.model_json_schema().get("properties", {}),
            "required": self.input_model.model_json_schema().get("required", []),
        }
    
    def to_llm_spec(self) -> dict:
        """
        转换为 LLM 工具规范格式
        """
        from ..llm_client import LLMToolSpec
        return LLMToolSpec(
            name=self.name,
            description=self.description,
            parameters=self.get_json_schema(),
        )


# ==================== 通用输入/输出模型 ====================

class EmptyInput(BaseModel):
    """空输入参数"""
    pass


class MediaTypeInput(BaseModel):
    """媒体类型输入参数"""
    media_type: Optional[str] = Field(
        None,
        description="媒体类型: movie/tv/music/novel/comic/audiobook"
    )


class KeywordSearchInput(BaseModel):
    """关键词搜索输入参数"""
    keyword: str = Field(..., description="搜索关键词")
    media_type: Optional[str] = Field(
        None,
        description="媒体类型过滤: movie/tv/music/novel/comic"
    )
    site_ids: Optional[list[int]] = Field(
        None,
        description="限定站点 ID 列表"
    )


class LogFilterInput(BaseModel):
    """日志过滤输入参数"""
    level: Optional[str] = Field(
        None,
        description="日志级别过滤: debug/info/warning/error/critical"
    )
    source: Optional[str] = Field(
        None,
        description="日志来源过滤"
    )
    component: Optional[str] = Field(
        None,
        description="组件过滤"
    )
    limit: int = Field(
        20,
        description="返回条数限制",
        ge=1,
        le=100
    )


class HealthFilterInput(BaseModel):
    """健康检查过滤输入参数"""
    module: Optional[str] = Field(
        None,
        description="模块名过滤: database/redis/downloader/indexer/disk"
    )


class ErrorInfo(BaseModel):
    """错误信息"""
    code: Optional[str] = None
    message: str
    details: Optional[dict] = None


class ToolResult(BaseModel):
    """通用工具执行结果"""
    success: bool = Field(True, description="是否成功")
    error: Optional[ErrorInfo] = Field(None, description="错误信息")
    data: Optional[dict] = Field(None, description="结果数据")
