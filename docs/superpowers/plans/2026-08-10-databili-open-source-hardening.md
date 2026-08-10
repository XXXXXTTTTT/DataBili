# DataBili Open Source Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task with review checkpoints.

**Goal:** 让 DataBili 在不绕过平台安全控制的前提下可配置、可诊断、可公开发布。

**Architecture:** 后端 Node.js 和 Python 爬虫从环境变量读取凭据与大模型参数；前端设置页通过受保护的后端配置接口管理非敏感模型参数。爬虫保留公开接口访问，增加配置校验、可控重试和 dry-run 健康检查。根 README 汇总安装、运行、截图、许可证和学习用途免责声明。

**Tech Stack:** Express 4, OpenAI Node SDK, Vue 3/Vite, Python 3, aiohttp, bilibili-api-python, MySQL.

---

### Task 1: 安全配置基线

**Files:**
- Modify: `.gitignore`
- Create: `.env.example`
- Create: `backend/.env.example`
- Create: `dataCrawler/.env.example`
- Modify: `backend/src/routes/userTrack.js`
- Modify: `dataCrawler/fetch_up.py`
- Modify: `dataCrawler/fetch_hot.py`
- Modify: `dataCrawler/writetosql.py`

- [ ] 检查现有环境变量名称并建立明确示例。
- [ ] 移除源码中的 API key、Cookie 和远程数据库密码，改用 `process.env`/`os.getenv`。
- [ ] 为缺少必需配置提供明确错误，不在日志打印密钥。
- [ ] 提交里程碑 `security: externalize runtime credentials`。

### Task 2: 大模型运行时配置

**Files:**
- Create: `backend/src/config/llm.js`
- Create: `backend/src/routes/llmConfig.js`
- Modify: `backend/src/app.js`
- Modify: `backend/src/routes/userTrack.js`
- Modify: `frontend/src/views/Settings.vue`

- [ ] 用统一配置读取 DeepSeek/OpenAI-compatible `baseURL`、`model` 和后端密钥。
- [ ] 提供 GET/PUT `/api/llm-config`，只返回脱敏配置，禁止通过 API 写入密钥。
- [ ] 设置页增加供应商、Base URL、模型名和保存/重置交互。
- [ ] 提交里程碑 `feat: configurable llm runtime settings`。

### Task 3: 爬虫诊断与合规修复

**Files:**
- Modify: `dataCrawler/fetch_up.py`
- Modify: `dataCrawler/fetch_hot.py`
- Create: `dataCrawler/healthcheck.py`

- [ ] 修复入口相对路径和同步 sleep 阻塞问题。
- [ ] 增加 `--dry-run` 健康检查，只请求公开接口并输出 HTTP/API 状态。
- [ ] 对 403、412、风控 API code、超时提供有限重试和退避后退出；不实现绕过措施。
- [ ] 在无数据库时允许只验证抓取和 JSON 输出。
- [ ] 提交里程碑 `fix: make crawler health checks bounded and observable`。

### Task 4: 开源发布材料

**Files:**
- Modify: `README.md`
- Create: `LICENSE`
- Create: `docs/DISCLAIMER.md`
- Create: `docs/screenshots/README.md`

- [ ] 写正式 GitHub README：功能、架构、环境、数据库、运行、配置、接口、合规边界、截图引用和贡献方式。
- [ ] 使用 MIT License，并明确第三方服务和数据使用责任。
- [ ] 提供截图目录说明；优先引用现有 docs 资源，缺少可直接渲染图片时明确标注截图生成命令。
- [ ] 提交里程碑 `docs: prepare open source release materials`。

### Task 5: 验证与收尾

**Files:**
- Create: `dataCrawler/test_healthcheck.py`
- Modify: `backend/package.json` (仅在需要时)

- [ ] 运行 Python 语法/健康检查、Node 依赖安装与后端启动、前端生产构建。
- [ ] 用 `rg` 确认源码不再含真实密钥、Cookie 或远程密码。
- [ ] 检查 git diff、提交历史和工作树，完成最终版本提交。
- [ ] 只有在所有证据齐全后标记目标完成。
