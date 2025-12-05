# Git 历史敏感信息清理指南

> ⚠️ **警告**: 本文档仅供参考。历史清理操作会重写 Git 历史，影响所有已有 clone。
> 请在完全理解后果后再执行，且务必先备份仓库。

---

## 1. 何时需要历史清理

以下情况建议执行历史清理：

- ✅ 泄露了真实的云服务 API Key（AWS、Azure、GCP 等）
- ✅ 泄露了外网可达的数据库密码
- ✅ 泄露了第三方服务的真实 Token
- ❌ 仅泄露了本地开发用的占位符密码（如本次 `vabhub_password`）

**本次事故评估**: 低风险，`vabhub_password` 为占位符密码，非真实生产凭据，历史清理为**可选**操作。

---

## 2. 准备工作

### 2.1 备份仓库

```bash
# 完整备份当前仓库
cp -r VabHub VabHub-backup-$(date +%Y%m%d)

# 或使用 git bundle
git bundle create ../VabHub-backup.bundle --all
```

### 2.2 安装工具

推荐使用 `git-filter-repo`（比 BFG 更现代）：

```bash
# macOS
brew install git-filter-repo

# Linux (pip)
pip install git-filter-repo

# Windows (pip)
pip install git-filter-repo
```

---

## 3. 定位敏感 commit

### 3.1 搜索包含敏感字符串的 commit

```bash
# 搜索包含特定字符串的 commit
git log -p --all -S 'vabhub_password' --oneline

# 搜索特定文件的历史
git log --all --full-history -- docker-compose.yml
```

### 3.2 列出涉及的文件

```bash
# 列出所有曾包含敏感字符串的文件
git grep -l 'vabhub_password' $(git rev-list --all)
```

---

## 4. 清理方法

### 4.1 方法一：替换文本（推荐）

创建替换规则文件 `replacements.txt`：

```
vabhub_password==>REDACTED-PASSWORD
```

执行替换：

```bash
# ⚠️ 警告：此操作会重写历史！
git filter-repo --replace-text replacements.txt --force
```

### 4.2 方法二：删除特定文件的所有历史

```bash
# ⚠️ 警告：此操作会从所有历史中删除该文件！
git filter-repo --path docker-compose.yml --invert-paths --force
```

### 4.3 方法三：使用 BFG（备选）

```bash
# 安装 BFG
# https://rtyley.github.io/bfg-repo-cleaner/

# 替换文本
bfg --replace-text replacements.txt

# 清理
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

---

## 5. 推送清理后的历史

```bash
# ⚠️ 强制推送 - 所有协作者需要重新 clone
git push origin --force-with-lease --all
git push origin --force-with-lease --tags
```

---

## 6. 清理后的影响

### 6.1 对协作者的影响

- 所有已有 clone 将与远程不兼容
- 协作者需要执行：
  ```bash
  # 删除旧仓库，重新 clone
  rm -rf VabHub
  git clone https://github.com/strmforge/VabHub.git
  ```

### 6.2 对 CI/CD 的影响

- 缓存可能失效
- 可能需要重新配置 Actions secrets

### 6.3 对 GitHub 的影响

- GitHub 可能仍缓存旧 commit，需要联系 GitHub Support 彻底清除
- Fork 仓库不受影响，需要通知 fork 所有者

---

## 7. 验证清理结果

```bash
# 验证敏感字符串已被移除
git log -p --all -S 'vabhub_password' --oneline
# 应返回空结果

# 验证文件内容
git show HEAD:docker-compose.yml | grep -i password
# 应只显示变量引用，无明文密码
```

---

## 8. 本次事故的建议

由于本次泄露的 `vabhub_password` 是：
- 占位符/示例密码
- 非真实生产凭据
- 数据库未暴露公网

**建议**：
1. ✅ 完成代码脱敏（P2）即可
2. ❌ 无需执行历史清理
3. ✅ 如果真实环境使用了此密码，请旋转密码（P1）

如果您仍希望清理历史，请按上述步骤操作，并通知所有协作者重新 clone。
