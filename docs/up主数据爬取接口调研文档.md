# UP 主数据爬取接口调研文档

更新日期：2026-08-10（Asia/Shanghai）

## 1. 目标与边界

目标是为 DataBili 获取 UP 主基础资料、粉丝数、投稿视频列表和视频统计，并持续更新 `up_profile`。

本调研只验证合规数据路径。不会尝试绕过 HTTP 412、验证码、登录限制、设备指纹、封禁、代理规避或其他平台访问控制；这些做法既不可持续，也不应写入项目。

## 2. 现有实现

| 项目 | 位置 | 用途 |
| --- | --- | --- |
| UID 批量爬虫 | `dataCrawler/fetch_up.py` | 读取 UID、获取资料和视频统计、写入 `up_profile` |
| 基础资料 | `bilibili_api.user.User.get_user_info()` | 昵称、头像等 |
| 关系统计 | `bilibili_api.user.User.get_relation_info()` | 粉丝数等 |
| 投稿列表 | `bilibili_api.user.User.get_videos()` | 获取 BVID 列表 |
| 视频详情 | `bilibili_api.video.Video.get_info()` | 播放、点赞、投币、收藏等汇总字段 |

已从本地 `bilibili-api-python==17.2.1` 源码确认，投稿列表调用的是：

```text
GET https://api.bilibili.com/x/space/wbi/arc/search
```

该库对该调用启用了 WBI/WBI2 参数处理。

## 3. 实测记录

### 3.1 测试 UID 来源

从 `databili.bilibili_hot_videos` 的本次热门视频结果选择：

```text
owner_mid = 373388923
owner_name = 脱缰凯Kk
```

该 UID 来自项目已采集的公开热门视频数据，不是随机生成。

### 3.2 未登录基础资料：成功

环境配置：

```dotenv
BILI_USE_CREDENTIAL=false
BILI_SESSDATA=
BILI_BILI_JCT=
```

对同一 UID 实测：

| 调用 | 结果 |
| --- | --- |
| `get_user_info()` | 成功返回昵称和头像 |
| `get_relation_info()` | 成功返回粉丝数 `6491953` |

结论：基础资料和粉丝数可以作为无授权状态下的降级数据源。

### 3.3 未登录投稿列表：被拒绝

对同一 UID 调用 `get_videos(pn=1, ps=5)`，返回：

```text
HTTP 412
The request was rejected because of the bilibili security control policy.
```

结论：当前网络环境中，无授权状态不能稳定获取投稿列表。此结果不表示所有网络、账号或时间段都相同，也不能作为规避访问控制的理由。

### 3.4 现有异常处理缺陷：已修复

原代码把 `NetworkException` 当作只含 `.code` 的异常处理。实测表明 HTTP 412 对应 `NetworkException.status`，访问 `.code` 会导致二次 `AttributeError`。

已在 `fetch_up.py` 增加 `get_api_error_code()`，统一读取 `.status` 或 `.code`；HTTP 403、412、429 会停止该 UID 并报告风控，不再无限重试或写入半截数据。

回归测试：

```text
dataCrawler/test_fetch_up_errors.py: passed
```

### 3.5 依赖缺陷：已修复

`fetch_up.py` 导入了 `tqdm`，但 `dataCrawler/requirements.txt` 原先没有该依赖。已补充 `tqdm==4.70.0`。

## 4. 可持续的合规方案

### 4.1 已授权的官方访问

部署者在获得平台允许的前提下，在本地 `.env` 填写其自己的有效凭据：

```dotenv
BILI_USE_CREDENTIAL=true
BILI_SESSDATA=...
BILI_BILI_JCT=...
```

然后只按平台允许的频率请求、缓存结果并记录失败状态。当前仓库没有可验证的授权凭据，因此此路径尚未在本环境执行。不能把他人的 Cookie、共享账号或来源不明凭据写入项目。

### 4.2 有合同/授权的商业数据 API

市面上的付费产品可能来自平台授权、内容创作者授权、公开数据加工或第三方数据服务。接入前必须获得以下精确信息：

1. 服务商名称和合同/授权范围。
2. API 文档中的精确 Base URL、认证方式、字段和限额。
3. 数据刷新周期、价格、删除机制和隐私条款。
4. 服务端密钥管理方式。

这些信息目前不在仓库中，不能凭名称或接口格式猜测。获得文档和测试密钥后，可新增一个供应商适配器，并写入独立的集成测试。

### 4.3 UP 主本人授权导出

对于与项目合作的 UP 主，可以让其自行导出或通过正式授权接口提供投稿和统计数据。项目只保存授权范围内字段，并记录授权时间、数据来源和到期时间。

### 4.4 无授权降级模式

当投稿列表返回 412 时：

1. 保存可获得的 UID、昵称、头像、粉丝数和采集时间。
2. 把视频列表状态标记为 `risk_blocked`，不伪造为“无视频”。
3. 使用已经由热门视频爬虫获得的 `owner_mid`、视频标题和视频统计作为有限补充。
4. 在明确的冷却期后，只有在授权配置变更或运营者人工确认后才再次尝试。

## 5. 推荐的系统设计

```text
前端输入 UID
    -> 后端创建采集任务
    -> 来源路由：授权官方访问 / 已签约数据 API / 无授权降级
    -> 结果缓存和来源记录
    -> up_profile、任务状态、最近采集时间
```

建议将任务状态区分为：

| 状态 | 含义 | 后续动作 |
| --- | --- | --- |
| `success` | 数据完整写入 | 按允许的刷新周期缓存 |
| `partial` | 仅有基础资料 | 在前端显示数据来源和缺失字段 |
| `risk_blocked` | 平台返回 403、412、429 | 停止自动重试，等待授权或人工处理 |
| `provider_error` | 已签约供应商失败 | 按合同重试策略处理 |

缓存键应使用 UID；缓存内容应包含 `source`、`fetched_at`、`expires_at` 和字段完整度。视频统计应按视频和采集时间保存快照，避免覆盖历史变化量。

## 6. 明确不采用的方向

下列行为不纳入 DataBili：伪造/轮换设备指纹、规避验证码、绕过登录限制、使用来源不明 Cookie、代理规避、规避频率限制、攻击或规避平台风控。这些方案无法提供合法、可靠的持续数据源。

## 7. 下一步需要的输入

要继续验证完整的 UP 主投稿与视频统计，必须提供以下两者之一：

1. 经平台允许、由部署者本人提供的授权凭据，并确认允许本项目使用该凭据进行测试；或
2. 已签约商业数据服务的精确 API 文档和测试密钥。

在此之前，项目可以持续采集热门视频及其变化量，并对 UP 主提供基础资料降级结果。
