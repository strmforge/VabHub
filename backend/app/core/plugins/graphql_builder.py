from __future__ import annotations

from typing import List, Type


class GraphQLSchemaBuilder:
    """
    提供给插件的 GraphQL 拓展构建器。

    插件可以调用 `add_query(mixin_cls)` / `add_mutation(mixin_cls)` 注册
    自定义的 Strawberry Query / Mutation mixin，框架会在最终构建 Schema 时
    把这些 mixin 混入主 Query / Mutation。
    """

    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name
        self._query_mixins: List[Type] = []
        self._mutation_mixins: List[Type] = []

    def add_query(self, mixin: Type) -> None:
        if not isinstance(mixin, type):
            raise TypeError("Query mixin 必须是 class 类型")
        self._query_mixins.append(mixin)

    def add_mutation(self, mixin: Type) -> None:
        if not isinstance(mixin, type):
            raise TypeError("Mutation mixin 必须是 class 类型")
        self._mutation_mixins.append(mixin)

    def dump(self) -> dict[str, List[Type]]:
        return {
            "query": list(self._query_mixins),
            "mutation": list(self._mutation_mixins),
        }


