# 本地智能大脑 · Phase 3B 说明

本阶段聚焦于「HTTP 客户端注册」与「HTML 解析骨架」：

1. `app/core/intel_local/http_clients.py`
   - 定义 `SiteHttpClient` 协议
   - 提供全局 `SiteHttpClientRegistry`
   - 通过 `set_http_client_registry` / `get_http_client_registry` 注入实际实现

2. `app/core/intel_local/parsers/`
   - `hr_html_parser.py`：输出 `ParsedHRRow`
   - `inbox_html_parser.py`：输出 `ParsedInboxMessage`
   - 预留指定站点解析器（如 hdsky / ttg），具体实现由主工程填充

3. `HRWatcher.fetch_hr_rows` / `InboxWatcher.fetch_new_messages`
   - 改为调用 HTTP 客户端 + 解析器
   - 当前依旧返回空列表，作为安全默认值；待接入真实 HTML 解析后即可生效

后续接线建议：
- 在基础设施层构造 `SiteHttpClientAdapter`，复用现有 PT 站点 Session；
- 在启动时注册到 `SiteHttpClientRegistry`；
- 按站点类型实现解析函数，逐步替换默认占位逻辑。 

