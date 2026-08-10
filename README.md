# DataBili

DataBili 是一个用于学习 B 站公开数据采集、统计分析与可视化的全栈示例项目，包含 Python 爬虫、Node.js API、Vue 3 前端和 UP 主聚类模型。

> 本项目仅用于学习、研究和本地实验。请遵守 B 站用户协议、robots 规则、相关法律法规与数据主体权益，不要绕过登录、验证码、频率限制、风控或其他访问控制。

## 项目结构

```text
backend/      Express API、MySQL 访问和大模型代理
frontend/     Vue 3 + Vite 前端
dataCrawler/  Python 异步爬虫和公开接口健康检查
upModel/      聚类模型与预测脚本
docs/         研究材料、免责声明和截图说明
```

## 环境要求

- Node.js 18+
- Python 3.10+
- MySQL 8+

复制 `.env.example` 为 `.env` 并填写配置。真实 `.env` 已被忽略；大模型密钥只在后端环境变量中配置。

```dotenv
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-password
DB_NAME=databili
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
DEEPSEEK_API_KEY=your-key
```

可先导入 `databili_max.sql` 创建表结构。

## 启动

```bash
cd backend
npm install
npm start
```

另开终端：

```bash
cd frontend
npm install
npm run dev
```

打开 <http://localhost:8080>。前端开发服务器会把 `/api` 和 `/proxy` 转发到 `http://localhost:3000`。

## 爬虫诊断

```bash
cd dataCrawler
python healthcheck.py
```

热门视频采集可设置 `CRAWLER_SKIP_DB=true` 只生成 JSON。接口返回 403、412、429 或风控 API code 时，程序会记录状态并停止当前请求，不尝试绕过平台控制。

```powershell
$env:CRAWLER_SKIP_DB='true'
python fetch_hot.py
```

UP 主批量采集前请确认已获授权并谨慎设置频率；凭据通过 `BILI_*` 环境变量提供，默认不登录。

稳定性验证采用低频、小样本方式：同一会话内连续执行热门列表、标签和实时人数三阶段 3 轮，并跳过数据库写入。详见 [`docs/VERIFICATION.md`](docs/VERIFICATION.md)。

## 大模型配置

后端提供 `GET/PUT /api/llm-config` 管理 Base URL 和模型名，响应只包含脱敏状态，不接受 API key 写入。前端“系统设置 -> 集成设置”可修改非敏感字段；密钥必须由部署者在 `.env` 中设置。

## 截图

截图约定见 [`docs/screenshots/README.md`](docs/screenshots/README.md)，截图中不得显示密钥或个人数据。

## 许可证与免责声明

本项目采用 [MIT License](LICENSE)。使用者需自行确认数据来源、访问频率、模型服务条款和输出内容的合法性；详见 [`docs/DISCLAIMER.md`](docs/DISCLAIMER.md)。

发布前验证记录见 [`docs/VERIFICATION.md`](docs/VERIFICATION.md)。

## 贡献

欢迎提交 Issue 和 Pull Request。请不要提交 `.env`、Cookie、API 密钥、个人数据或未经授权的抓取结果。
