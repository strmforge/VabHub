from __future__ import annotations

import strawberry
from fastapi import APIRouter

from app.core.plugins.graphql_builder import GraphQLSchemaBuilder
from app.core.plugins.spec import PluginContext, PluginHooks, PluginMetadata
from app.core.schemas import success_response


PLUGIN_METADATA = PluginMetadata(
    id="example_extension_plugin",
    name="插件扩展演示",
    version="0.1.0",
    description="演示 register_rest / register_graphql 扩展点的官方示例。",
    author="VabHub",
    tags=["demo", "extension"],
)


def register(context: PluginContext) -> PluginHooks:
    def register_rest(router: APIRouter) -> None:
        @router.get("/ping")
        async def ping():
            return success_response(
                data={"plugin": context.name, "message": "pong"},
                message="插件扩展接口工作正常",
            )

    def register_graphql(builder: GraphQLSchemaBuilder) -> None:
        @strawberry.type
        class ExtensionQuery:
            @strawberry.field(description="插件自带的 echo 字段")
            def plugin_echo(self, text: str = "hello") -> str:
                return f"{context.name}:{text}"

        builder.add_query(ExtensionQuery)

    return PluginHooks(register_rest=register_rest, register_graphql=register_graphql)


