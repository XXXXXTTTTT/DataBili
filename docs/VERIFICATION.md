# 发布前验证记录

验证日期：2026-08-10（Asia/Shanghai）

| 检查项 | 命令 | 结果 |
| --- | --- | --- |
| Python 语法 | `python -m py_compile dataCrawler/*.py upModel/*.py` | 通过 |
| 爬虫健康检查 | `python dataCrawler/healthcheck.py --timeout 10` | HTTP 200，API code 0 |
| 健康检查测试 | `python -m pytest dataCrawler/test_healthcheck.py -q` | 1 passed |
| 前端构建 | `npm run build`（frontend） | 通过，Vite 生成 dist |
| Node 语法 | `node --check`（后端入口、LLM 配置和用户追踪路由） | 通过 |
| MySQL 连接 | `SELECT DATABASE()` | 返回 `databili` |
| LLM 配置接口 | `GET/PUT /api/llm-config` | HTTP 200，响应不返回密钥 |

说明：健康检查只访问公开热门接口；出现 403、412、429 或风控 API code 时会停止当前请求，不执行绕过行为。当前环境未配置大模型密钥，因此 LLM 接口的 `configured` 为 `false`，配置密钥后即可启用评论分析。
