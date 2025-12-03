# 快速开始：HelloWorld 插件

本指南将带你完成一个完整的插件开发和部署流程。

## 前提条件

- VabHub 已正常运行
- 具有管理员权限的账号

## Step 1：复制示例插件

将示例插件复制到 VabHub 的插件目录：

```bash
# 方法 1：直接复制
cp -r plugins-example/hello-world backend/plugins/

# 方法 2：创建软链接（开发时推荐）
ln -s $(pwd)/plugins-example/hello-world backend/plugins/hello-world
```

如果插件目录不存在，需要先创建：

```bash
mkdir -p backend/plugins
```

## Step 2：扫描插件

1. 登录 VabHub 管理员账号
2. 访问 `/dev/plugins`（插件开发中心）
3. 点击「扫描插件目录」按钮
4. 应该看到 "Hello World 示例插件" 出现在列表中

或者通过 API：

```bash
curl -X POST http://localhost:8092/api/dev/plugins/scan \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

## Step 3：启用插件

1. 在插件列表中找到 "Hello World 示例插件"
2. 点击「启用」按钮
3. 状态变为「已启用」

## Step 4：验证全局搜索

1. 在 VabHub 顶部搜索框中输入 "hello"
2. 应该看到一条来自插件的搜索结果：
   - 标题：来自 HelloWorld 插件的搜索结果
   - 副标题：你搜索了：hello

## Step 5：验证 Bot 命令

前提：已配置 Telegram Bot 并完成绑定。

1. 在 Telegram 中向你的 Bot 发送 `/hello`
2. 应该收到类似以下的回复：
   ```
   👋 你好，xxx！

   这是来自 **HelloWorld 插件** 的问候。
   插件系统工作正常！
   ```

## Step 6：验证 Workflow

1. 在插件开发中心切换到「Workflows」标签
2. 找到 "HelloWorld 演示任务"
3. 点击「执行」按钮
4. 在弹出的对话框中输入 JSON payload（可选）：
   ```json
   {"test": "value"}
   ```
5. 点击「执行」
6. 应该看到类似以下的返回结果：
   ```json
   {
     "message": "Hello from HelloWorld workflow!",
     "echo": {"test": "value"},
     "status": "completed"
   }
   ```

## Step 7：禁用插件测试

1. 在插件列表中点击「禁用」
2. 再次搜索 "hello"，应该不再出现插件结果
3. 在 Telegram 中发送 `/hello`，应该提示"未知命令"

## 下一步

恭喜！你已经成功运行了示例插件。接下来可以：

1. 阅读 [PDK 概述文档](./DEV_SDK_OVERVIEW.md) 了解完整 API
2. 复制 `plugins-example/hello-world` 作为模板开发自己的插件
3. 修改 `plugin.json` 中的 `id` 和 `display_name`
4. 在 `main.py` 中实现你的扩展逻辑

## 常见问题

### Q: 插件显示 BROKEN 状态

A: 查看插件详情中的 `last_error` 字段，常见原因：
- `entry_module` 路径配置错误
- Python 代码语法错误
- 缺少 `register_plugin` 函数

### Q: 搜索结果没有出现

A: 确认：
1. 插件状态为「已启用」
2. 搜索关键词包含 "hello"
3. 查看后端日志是否有错误

### Q: Bot 命令没有响应

A: 确认：
1. Telegram Bot 已正确配置
2. 用户已绑定 VabHub 账号
3. 插件状态为「已启用」

### Q: 如何在 Docker 中使用

A: 在 `docker-compose.yml` 中添加卷映射：

```yaml
services:
  vabhub:
    volumes:
      - ./plugins:/app/plugins
```

然后将插件放入 `./plugins` 目录。
