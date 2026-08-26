<div align="center">

# DataBili

**A Bilibili public-data collection, analysis, and visualization platform for learning and research.**

![Vue 3](https://img.shields.io/badge/Vue-3-42b883?logo=vuedotjs&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-18%2B-339933?logo=nodedotjs&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8%2B-4479a1?logo=mysql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-black.svg)

[Overview](#overview) · [Screenshots](#screenshots) · [Quick start](#quick-start) · [Crawler risk levels](#crawler-modules-and-risk-levels) · [Compliance](#compliance-boundaries)

[简体中文](README.md)

</div>

DataBili brings together Python asynchronous collection, MySQL storage, an Express API, Vue 3 visualizations, and UP creator clustering in one local learning project. It supports public trending-video observation, hourly change snapshots, UP profile presentation, and clustering. It does not provide mechanisms to bypass platform access controls.

> This project is for learning, research, and local experiments only. Follow Bilibili terms, robots rules, third-party service terms, data-subject rights, and applicable laws before use.

## Overview

| Module | Capability |
| --- | --- |
| Trending videos | Collects public trending-video metadata, categories, creators, tags, and engagement metrics. |
| Change analysis | Stores hourly trending-video snapshots and shows engagement and online-audience trends. |
| UP analysis | Queries stored UP profiles and presents clustering results from available data. |
| Observed-video fallback | Returns videos already observed by this project's trending dataset when a creator's submission list is restricted; it is never presented as a complete submission list. |
| User activity analysis | Provides backend user-tracking and comment-analysis endpoints with a frontend entry point. |
| LLM integration | Configures OpenAI-compatible services at runtime from **System Settings -> Integration Settings**. |

## Architecture

```text
┌─────────────────────────────────────────────────────────────────────┐
│ Vue 3 + Vite frontend                                                │
│ Dashboard · Trending videos · UP lookup · Clustering · User tracking │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ HTTP / JSON
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Express API                                                          │
│ Trending data · UP profiles · Observed videos · User tracking · LLM  │
└───────────────┬───────────────────────────────────────┬─────────────┘
                │                                       │
                ▼                                       ▼
┌─────────────────────────────┐           ┌───────────────────────────┐
│ MySQL 8                     │           │ OpenAI-compatible service │
│ Video snapshots · UP data   │           │ Configured by the user    │
└──────────────┬──────────────┘           └───────────────────────────┘
               ▲
               │ Low-frequency, controlled requests; stop on errors
┌──────────────┴──────────────────────────────────────────────────────┐
│ Python collection                                                    │
│ Trending videos · Hourly snapshots · UP profiles and safe fallback   │
└─────────────────────────────────────────────────────────────────────┘
```

## Repository layout

| Directory | Description |
| --- | --- |
| [`frontend/`](frontend) | Vue 3 + Vite pages and charts. |
| [`backend/`](backend) | Express APIs, MySQL access, proxy route, and runtime LLM configuration. |
| [`dataCrawler/`](dataCrawler) | Python asynchronous collectors for trending data, change tracking, and UP profiles. |
| [`upModel/`](upModel) | UP data preparation, clustering, and prediction scripts. |
| [`docs/`](docs) | Research report, screenshots, verification evidence, and disclaimer. |

## Screenshots

The following screenshots are historical run records extracted from the project research report. They illustrate the UI and functionality only; they do not represent current data.

| Dashboard | UP lookup |
| --- | --- |
| ![Dashboard](docs/screenshots/dashboard.png) | ![UP lookup](docs/screenshots/up-select.png) |

| UP clustering | Trending videos |
| --- | --- |
| ![UP clustering](docs/screenshots/up-analysis.png) | ![Trending videos](docs/screenshots/hot-videos.png) |

| Online audience trend | Tag cloud |
| --- | --- |
| ![Online audience trend](docs/screenshots/online-trend.png) | ![Tag cloud](docs/screenshots/tag-cloud.png) |

## Quick start

### Prerequisites

- Node.js 18+
- Python 3.10+
- MySQL 8+

### 1. Configure environment variables

Copy the root `.env.example` to `.env`, then provide local MySQL settings:

```dotenv
PORT=3000

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-password
DB_NAME=databili

BILI_USE_CREDENTIAL=false
BILI_SESSDATA=
BILI_BILI_JCT=
BILI_PROXY_URL=
```

`.env` is ignored by Git. Never commit database passwords, cookies, API keys, or personal data.

### 2. Import the database

Import the root initialization SQL with MySQL:

```powershell
mysql -u root -p databili < databili_max.sql
```

### 3. Start the backend

```powershell
Set-Location backend
npm install
npm start
```

The backend listens on `http://localhost:3000` by default.

### 4. Start the frontend

In another terminal:

```powershell
Set-Location frontend
npm install
npm run dev
```

Open `http://localhost:8080`. Vite proxies `/api` and `/proxy` to `http://localhost:3000`.

### 5. Install collector dependencies and run a health check

```powershell
Set-Location dataCrawler
python -m pip install -r requirements.txt
python healthcheck.py --timeout 10
```

The health check uses only the public trending endpoint. HTTP 403, 412, 429, or a non-zero risk-control API code stops the current request; no bypass is attempted.

## Crawler modules and risk levels

Levels describe access-control sensitivity and operating constraints in the current implementation. They are not guarantees of long-term platform availability. Run every task at a low frequency, record state, and follow platform rules.

| Module | Entry point | Level | Verified behavior and limits |
| --- | --- | --- | --- |
| Trending videos | `dataCrawler/fetch_hot.py` | Low | Uses public trending data. Controlled low-frequency tests passed; the current request stops on error states. |
| Trending-video change tracking | `dataCrawler/real_time_people_nums/fetch_hot_server.py` | Medium | Saves hourly snapshots, tags, and online counts. Tag requests can receive HTTP 412 and the affected request stops. |
| UP basic profile | `dataCrawler/fetch_up.py` | Medium | An unauthenticated environment can retrieve partial profile information and follower count; rate control remains required. |
| UP submission list and video statistics | `dataCrawler/fetch_up.py` | High | The current environment has observed HTTP 412 from the submission-list endpoint. Confirmed basic profile data is retained, `risk_blocked` and a cooldown are recorded, and zero-valued statistics are not fabricated. |
| Observed-video fallback | `GET /api/up-profile/known-videos?uid=<UID>` | Low | Reads only existing records in `bilibili_hot_videos_server`; it does not request the submission list and is not a complete creator-video dataset. |

### Trending videos and hourly snapshots

Run a single collection pass:

```powershell
Set-Location dataCrawler/real_time_people_nums
python fetch_hot_server.py --items 5
```

Run hourly collection:

```powershell
python fetch_hot_server.py --loop --items 500 --interval 3600
```

Generate JSON without writing to MySQL:

```powershell
Set-Location dataCrawler
$env:CRAWLER_SKIP_DB='true'
python fetch_hot.py
```

### UP data

`fetch_up.py` reads a UID file and writes to `up_profile`. When the submission list triggers HTTP 412, the system neither retries indefinitely nor evades risk controls. It preserves accessible basic profile data, records state, and skips another request during the cooldown.

Read the full research and state design in [`docs/up主数据爬取接口调研文档.md`](docs/up主数据爬取接口调研文档.md).

## LLM configuration

Open **System Settings -> Integration Settings** in the frontend and provide a service name, Base URL, model name, and API key for any OpenAI-compatible service.

- Configuration is stored in the local browser and submitted to the local backend as runtime configuration.
- `GET /api/llm-config` does not return the API key.
- Do not place LLM API keys in `.env` or commit them to this repository.

## Verification

See [`docs/VERIFICATION.md`](docs/VERIFICATION.md) for release verification evidence covering Python syntax, public-endpoint health checks, crawler tests, frontend build, Node.js syntax, MySQL connectivity, and LLM configuration APIs.

The controlled stability check ran trending-list, tag, and online-audience requests for three consecutive rounds in one shared HTTP session. It demonstrates the complete path under low-frequency, small-sample conditions only; it is not a guarantee for long-running or large-scale collection.

## Compliance boundaries

DataBili does not provide or encourage:

- Sharing, purchasing, or using unknown-origin cookies or accounts.
- Proxy rotation to evade rate limits or risk controls.
- Device-fingerprint spoofing, CAPTCHA bypass, login-restriction bypass, ban evasion, or any other access-control bypass technique.
- Committing unauthorized collected data, personal data, database passwords, or API keys.

See [`docs/DISCLAIMER.md`](docs/DISCLAIMER.md) for the detailed responsibility and usage boundaries.

## Contributing

1. Create a focused feature branch from `main`.
2. Add relevant tests and documentation when behavior changes.
3. Run `git diff --check` and affected Python, Node.js, or frontend checks before committing.
4. Do not commit `.env`, cookies, API keys, logs, `node_modules/`, caches, or unauthorized data.

## License

DataBili is released under the [MIT License](LICENSE). The MIT License does not remove a user's responsibility to follow platform rules, service terms, and applicable laws.
