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

## 爬虫稳定性复验

在 2026-08-10 完成 3 轮受控真实请求：每轮以一个共享 HTTP 会话依次请求热门列表 1 条、标签和实时人数，轮次间等待 1 秒，不写数据库。三轮均返回 HTTP 成功结果，热门数据、10 个标签和实时在线字段完整。

该验证证明当前公开接口在低频、小样本请求下可稳定完成完整链路；它不构成对平台长期可用性或大规模采集的保证。生产运行应继续遵守平台规则，并在返回 403、412、429 或非零 API code 时停止当前请求。

说明：健康检查只访问公开热门接口；出现 403、412、429 或风控 API code 时会停止当前请求，不执行绕过行为。当前环境未配置大模型密钥，因此 LLM 接口的 `configured` 为 `false`，配置密钥后即可启用评论分析。
