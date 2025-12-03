# 音乐订阅功能概述 (MUSIC-AUTOLOOP-2)

## 功能简介

音乐订阅功能是 VabHub 的核心自动化功能，支持榜单订阅和关键字订阅两种模式，能够自动搜索、过滤和下载音乐资源。该功能集成了安全策略过滤、去重逻辑和详细的运行统计。

## 核心特性

### 🎵 订阅类型
- **榜单订阅**: 基于音乐榜单（如Billboard、Oricon等）自动跟踪新发布内容
- **关键字订阅**: 基于自定义关键字进行音乐搜索

### 🔒 安全策略过滤
- **HR过滤**: 可选择是否允许HR（Hit and Run）种子
- **H3/H5过滤**: 可选择是否允许H3/H5标记的种子
- **Free过滤**: 可选择仅允许免费或半免费种子

### 📊 详细统计
- 搜索候选数量统计
- 过滤详情（HR/H3H5/非免费/重复）
- 创建任务数量
- 错误信息记录

### 🚀 批量操作
- 单个订阅立即运行/试运行
- 批量运行所有激活订阅
- 支持试运行模式（仅统计，不创建任务）

## API 接口

### 单个订阅运行
```http
POST /api/music/subscriptions/{id}/run_once?dry_run=false
```

**参数:**
- `dry_run`: 是否为试运行模式（默认false）

**响应:**
```json
{
  "data": {
    "subscription_id": 1,
    "found_total": 15,
    "filtered_out": {
      "hr": 3,
      "h3h5": 2,
      "non_free": 5,
      "duplicate": 1
    },
    "skipped_existing": 2,
    "created_tasks": 2,
    "errors": []
  },
  "message": "运行完成：找到 15 条候选，过滤 10 条，跳过重复 2 条，创建任务 2 个"
}
```

### 批量运行订阅
```http
POST /api/music/subscriptions/run_all?only_active=true&limit=20&dry_run=false
```

**参数:**
- `only_active`: 仅运行激活订阅（默认true）
- `limit`: 单次最多运行数量（默认20，最大100）
- `dry_run`: 是否为试运行模式（默认false）

**响应:**
```json
{
  "data": {
    "total_subscriptions": 5,
    "runs": [...],
    "summary": {
      "found_total": 45,
      "filtered_total": {
        "hr": 8,
        "h3h5": 5,
        "non_free": 12
      },
      "created_tasks_total": 10,
      "succeeded_checks": 5,
      "failed_checks": 0
    }
  },
  "message": "批量运行完成：共检查 5 个订阅，找到 45 条候选，过滤 25 条，创建任务 10 个，成功 5 个，失败 0 个"
}
```

## 前端操作指南

### 订阅卡片操作
1. **立即运行**: 点击播放按钮，选择"立即运行"执行订阅
2. **试运行**: 点击播放按钮，选择"试运行（仅统计）"进行预览
3. **暂停/恢复**: 点击暂停/播放按钮切换订阅状态
4. **删除**: 点击删除按钮移除订阅

### 批量操作
1. **批量检查**: 点击"批量检查"按钮，选择运行模式
2. **批量试运行**: 选择"试运行（仅统计）"预览所有订阅效果
3. **批量运行**: 选择"运行全部激活订阅"执行实际下载任务

## Runner 使用

### 命令行运行
```bash
# 运行一次检查
python -m app.runners.music_subscription_checker --mode once --max-subscriptions 50

# 持续运行（每30分钟检查一次）
python -m app.runners.music_subscription_checker --mode loop --interval-seconds 1800

# 试运行模式
python -m app.runners.music_subscription_checker --mode once --dry-run
```

### 参数说明
- `--mode`: 运行模式（once/loop）
- `--max-subscriptions`: 每次最多处理的订阅数量（默认50）
- `--cooldown-minutes`: 冷却时间（分钟，默认30）
- `--interval-seconds`: 检查间隔（秒，仅loop模式，默认1800）
- `--dry-run`: 试运行模式

## 安全策略配置

### 推荐配置组合

**保守策略**（适合新手）:
- `allow_hr`: false
- `allow_h3h5`: false  
- `strict_free_only`: true

**平衡策略**（适合一般用户）:
- `allow_hr`: false
- `allow_h3h5`: true
- `strict_free_only`: false

**激进策略**（适合高级用户）:
- `allow_hr`: true
- `allow_h3h5`: true
- `strict_free_only`: false

## 过滤逻辑详解

### HR 过滤
基于种子站点的HR策略，自动检测并过滤需要保种的种子

### H3/H5 过滤
通过种子标题检测H3/H5标记，过滤高风险种子

### Free 过滤
根据种子的免费状态：
- `free_percent = 100%`: 完全免费
- `free_percent = 50%`: 半免费
- 其他: 非免费

## 去重机制

系统基于以下组合进行去重：
- `matched_site`: 种子来源站点
- `matched_torrent_id`: 种子ID
- 排除状态为 `failed` 或 `cancelled` 的任务

## 运行统计说明

### 统计字段
- `found_total`: 搜索到的候选总数
- `filtered_out`: 被过滤的候选分类统计
- `skipped_existing`: 因重复而跳过的候选数
- `created_tasks`: 实际创建的下载任务数
- `errors`: 运行过程中的错误信息

### 兼容性字段
为保持向后兼容，系统同时提供：
- `last_run_new_count`: 新创建任务数
- `last_run_search_count`: 搜索候选数
- `last_run_download_count`: 下载任务数

## 故障排除

### 常见问题

**Q: 为什么搜索到的候选很多，但创建的任务很少？**
A: 检查安全策略设置，可能大部分候选被过滤了。可以尝试试运行模式查看过滤详情。

**Q: 批量运行时某些订阅失败怎么办？**
A: 查看错误信息，常见原因包括网络问题、站点维护、搜索关键字无效等。

**Q: 如何避免重复下载？**
A: 系统已内置去重机制，基于站点和种子ID进行去重。重复运行时相同种子不会重复创建任务。

### 日志查看
```bash
# 查看订阅运行日志
tail -f logs/app.log | grep "音乐订阅"

# 查看 Runner 日志
tail -f logs/app.log | grep "music_subscription_checker"
```

## 最佳实践

1. **合理设置安全策略**: 根据网络环境和站点规则配置安全策略
2. **定期试运行**: 使用试运行模式预览效果，避免不必要的下载
3. **监控运行统计**: 关注过滤统计，优化订阅配置
4. **使用批量操作**: 定期批量运行所有订阅，保持内容更新
5. **合理设置限制**: 避免单次运行过多订阅，防止站点限流

## 版本历史

- **MUSIC-AUTOLOOP-2**: 当前版本，支持安全策略过滤、去重逻辑、详细统计
- **MUSIC-SUBS-1**: 初始版本，基础榜单订阅功能

## 相关文件

- 后端服务: `app/services/music_subscription_service.py`
- API路由: `app/api/music_subscription.py`
- Runner脚本: `app/runners/music_subscription_checker.py`

## 在 Telegram 中管理音乐订阅

VabHub Telegram Bot 提供了完整的音乐订阅管理功能，让你可以在聊天中便捷地管理订阅。

### 可用命令

| 命令 | 功能 | 说明 |
|------|------|------|
| `/music_subs` | 列出订阅 | 查看所有音乐订阅和状态 |
| `/music_sub <ID>` | 查看详情 | 显示单个订阅的详细信息 |
| `/music_sub_check <ID>` | 试运行 | 预览搜索效果，不创建下载任务 |
| `/music_sub_run <ID>` | 真实执行 | 创建下载任务（需订阅激活） |
| `/music_sub_toggle <ID>` | 切换状态 | 激活/暂停订阅 |

### 使用场景

**快速查看所有订阅状态：**
```bash
/music_subs
```

**预览新订阅效果：**
```bash
/music_sub_check 12  # 先试运行
/music_sub_run 12    # 效果满意后真实执行
```

**管理订阅状态：**
```bash
/music_sub_toggle 12  # 暂停某个订阅
/music_sub_toggle 12  # 再次激活
```

### 注意事项

- 所有音乐订阅命令只对已绑定用户有效
- 安全策略配置沿用 Web 端设置
- 推荐先用试运行模式观察效果，再用真实执行
- 详细的命令说明请参考：[Telegram Bot 命令参考手册](BOT_TELEGRAM_COMMANDS_REFERENCE.md#音乐订阅管理)
- 前端服务: `frontend/src/services/music.ts`
- 前端组件: `frontend/src/components/music/MusicSubscriptionCard.vue`, `frontend/src/components/music/MusicSubscriptions.vue`
