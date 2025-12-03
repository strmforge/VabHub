"""
GraphQL Router
集成strawberry-graphql到FastAPI
"""

from fastapi import APIRouter, Request
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL

from app.api.graphql.schema import schema
from app.core.database import AsyncSessionLocal


def create_graphql_router() -> APIRouter:
    """创建GraphQL路由器"""
    
    # 创建GraphQL路由器
    graphql_app = GraphQLRouter(
        schema,
        # GraphiQL开发界面（开发环境）
        graphiql=True,
        # 支持订阅协议
        subscription_protocols=[
            GRAPHQL_TRANSPORT_WS_PROTOCOL,
            GRAPHQL_WS_PROTOCOL,
        ],
        # 上下文处理器
        context_getter=get_context,
    )
    
    # 创建FastAPI路由器
    router = APIRouter()
    
    # 挂载GraphQL端点
    router.include_router(graphql_app, prefix="/graphql", tags=["GraphQL"])
    
    return router


async def get_context(request: Request) -> dict:
    """获取GraphQL上下文"""
    # 可以在这里添加认证、数据库会话等
    return {
        "request": request,
        "session_factory": AsyncSessionLocal,
        # "user": await get_current_user(request),  # 如果需要认证
        # "db": get_db(),  # 如果需要数据库会话
    }


# 创建路由器实例
router = create_graphql_router()

