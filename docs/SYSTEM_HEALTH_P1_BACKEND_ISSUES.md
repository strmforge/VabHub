# System Health – P1 Backend Issues

## 执行的基础命令

| 命令 | 状态 | 备注 |
| --- | --- | --- |
| `python -m compileall backend/app -q` | ✅ 通过 | 无语法错误 |
| `python -m mypy backend/app` | ❌ 失败 | 检测到 3000+ 条历史类型错误（部分模块未纳入 mypy 配置、部分旧代码类型缺失） |
| `ruff backend/app` | ⏳ 待执行 | 等待先清理 mypy/导入类错误后再运行 |

> 目前阻塞在 mypy，其余命令计划在修复/抑制关键错误后继续执行。

## mypy 错误分类

### 1. 模块导入缺失 / 名称未定义
- `backend/app/api/__init__.py` 多处 `Name "notification" is not defined`、`notifications_user`, `video_progress`, `player_wall`, `music_chart_admin`, `music_subscription` 等：
  - 原因：这些路由模块在 `app/api/__init__.py` 中被引用，但文件顶部 `from app.api import ...` 列表已经注释掉相应模块，导致 mypy 解析时报错。
  - 影响：400+ 条同类错误（每个引用一次报错），阻挡 mypy。
  - 计划：若模块确实存在，补充导入；若模块已废弃，在 include_router 时也应注释/删除。

### 2. Chain 初始化赋值非法
- `backend/app/chain/__init__.py`：`SearchChain = None` 之类的语句触发 `Cannot assign to a type`、`Incompatible types in assignment`；
  - 这是老代码用来延迟绑定类对象，但 mypy 检测到类型与实例不匹配。
  - 影响：约 40 条错误。
  - 计划：改为 `SearchChainType = Type[SearchChain]` 风格，或使用 `typing.cast`/`Optional[Type[...]]` 存放引用。

### 3. 可为 None 的模块/对象直接访问属性
- 例：`backend/app/core/ext_indexer/runtime.py:183: Item "None" of Module | None has no attribute "get_download_link"`。
- 说明：`ext_indexer_module` 之类的全局值可能为 None，需要先做 None 判断。

### 4. 函数返回类型不匹配
- 例：`backend/app/modules/hnr/utils/text.py:83: Incompatible return value type (got "None", expected "str")`。
- 常见原因：函数在某些分支没有返回值。

### 5. 类型别名/Callable 注解错误
- 例：`backend/app/core/cloud_storage/providers/base.py:84: Perhaps you meant "typing.Callable" instead of "callable"?`
- 说明：注解写成内置 `callable` 而非 `typing.Callable`。

> 以上只是采样，完整列表约 3000+ 项，集中在 API 注册、Chain 模块、通知/索引等历史代码。

## 下一步修复策略

1. **整理 mypy 范围**：确认是否需要把所有模块纳入检查，或为旧模块添加 `pyproject/mypy.ini` 排除。
2. **优先修链路**：先补齐 `app/api/__init__.py` 的导入/注释，以消除大量 `Name not defined` 错误。
3. **Chain 类型修复**：为 `backend/app/chain/__init__.py` 添加 `typing.Optional[Type[...]` 结构或使用 `TYPE_CHECKING`。
4. **修复关键函数**：对 `hnr/utils/text.py`、`core/ext_indexer/runtime.py` 等明显 bug 做短修。
5. **再跑 mypy**：逐步减少错误数量，直到 mypy 通过或仅剩记录的例外。

完成以上步骤后，将继续执行 `ruff backend/app` 并在文档末尾追加“已修复问题汇总”。
