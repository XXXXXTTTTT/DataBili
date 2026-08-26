# DataBili README 发布文档设计

## 目标

将根目录 README 重构为适合 GitHub 开源仓库的中文主文档，并提供结构对应的英文版 `README_EN.md`。文档需准确介绍项目能力、复现路径、截图、爬虫风险边界和开源协作规范。

## 范围

- 提取课程报告 `docs/社交网络大数据研究报告---B站数据挖掘与分析.docx` 中已存在的页面截图，写入 `docs/screenshots/`。
- 重写 `README.md` 与新增 `README_EN.md`。
- 保留现有 MIT `LICENSE` 和 `docs/DISCLAIMER.md`，README 只链接并概述其边界。
- 不修改爬虫、后端、前端或数据库实现。

## 文档结构

两份 README 均采用以下章节：

1. 居中项目名称、简介、技术栈和许可证徽章，以及语言切换链接。
2. 项目概览与能力矩阵。
3. 系统架构与仓库模块说明。
4. 页面截图。
5. 环境要求、配置、数据库导入与启动步骤。
6. 爬虫模块和风险分级。
7. 大模型运行时配置。
8. 验证、合规边界、贡献和许可证。

## 截图映射

从报告提取以下已确认的页面图，并使用与页面功能一致的文件名：

| 报告图片 | 目标文件 | README 用途 |
| --- | --- | --- |
| `image11.png` | `docs/screenshots/dashboard.png` | 平台概览 |
| `image12.png` | `docs/screenshots/up-select.png` | UP 主查询 |
| `image13.png` | `docs/screenshots/up-analysis.png` | UP 主聚类分析 |
| `image17.png` | `docs/screenshots/hot-videos.png` | 热门视频列表 |
| `image24.png` | `docs/screenshots/online-trend.png` | 在线人数趋势 |
| `image15.png` | `docs/screenshots/tag-cloud.png` | 标签词云 |

图片均来自用户指定的报告，README 仅将其作为历史运行界面示例，不把其中的数值表述为当前线上数据。

## 爬虫分级与边界

风险表按现有代码和验证记录陈述：

| 模块 | 实现位置 | 分级 | 已验证行为 |
| --- | --- | --- | --- |
| 热门视频 | `dataCrawler/fetch_hot.py` | 低 | 公开接口、低频受控请求；错误状态停止当前请求。 |
| 热门视频变化量 | `dataCrawler/real_time_people_nums/fetch_hot_server.py` | 中 | 每小时快照，包含热门列表、标签和实时人数；标签请求可遭 412。 |
| UP 主基础资料 | `dataCrawler/fetch_up.py` | 中 | 无授权时可获取部分基础资料；需按规则控制频率。 |
| UP 主投稿与视频统计 | `dataCrawler/fetch_up.py` | 高 | 当前环境实测投稿列表收到 HTTP 412；保留基础资料，写入风控状态和冷却时间。 |
| 项目已观测视频降级数据 | `backend/src/routes/upProfile.js` | 低 | 只读取项目已有的 `bilibili_hot_videos_server`，不等同完整投稿列表。 |

README 必须明确：不会提供 Cookie 共享、代理规避、指纹伪造、验证码规避或任何绕过平台访问控制的方法。

## 验证标准

- 图片文件存在且 README 使用相对路径引用。
- `README.md` 和 `README_EN.md` 均包含启动、风险分级、免责声明和许可证链接。
- 文档中不含数据库密码、Cookie、API Key 或个人信息。
- `git diff --check` 通过。
- 仅暂存 README 与本次新增截图、规格文档；不包含已有无关工作区改动。

