# 贡献指南 / 文档规范

感谢愿意参与 VabHub 的同学！为保持文档和代码质量，请在提交前完成以下检查：

## 1. Markdown 风格

- 标题前后请留出一个空行，尽量使用 `##`/`###` 等规范层级。
- 列表项之间保持一致的缩进，避免混用 Tab 与空格。
- 如需在段落中强制换行，使用两个空格结尾即可（仓库的 markdownlint 配置已允许此写法）。

## 2. Markdown Lint

仓库根目录引入了 `markdownlint-cli`。首次使用请安装依赖：

```bash
cd VabHub
npm install
```

执行文档检查：

```bash
npm run md:lint
```

该命令会校验 `README*.md`、`docs/**/*.md` 以及 `services/**/*.md`，并使用 `.markdownlint.json` 中的统一规则。

## 3. 其他建议

- 代码变更请保持与现有格式一致，若包含前端/后端修改，记得运行对应 lint 或格式化命令。
- 如需新增文档，请在文档顶部补充简要说明，便于搜索与理解。
- 对大型功能或流程变更，建议同步更新 `docs/DEV_PROGRESS_VABHUB.md`，记录完成的子任务与使用方式。

欢迎在 Issue 或 PR 中继续交流，感谢你的贡献！ 🎉


