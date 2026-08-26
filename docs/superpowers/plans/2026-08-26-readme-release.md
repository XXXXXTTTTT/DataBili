# DataBili README Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish bilingual, screenshot-backed GitHub READMEs that accurately document DataBili's setup, crawler risk boundaries, and compliance requirements.

**Architecture:** Extract six existing report images into `docs/screenshots/`, then reference those stable local assets from Chinese and English README files. Documentation derives crawler claims only from the checked-in modules and existing verification records.

**Tech Stack:** Markdown, Word `.docx` ZIP media extraction, Git.

---

### Task 1: Publish verified page screenshots

**Files:**
- Create: `docs/screenshots/dashboard.png`
- Create: `docs/screenshots/up-select.png`
- Create: `docs/screenshots/up-analysis.png`
- Create: `docs/screenshots/hot-videos.png`
- Create: `docs/screenshots/online-trend.png`
- Create: `docs/screenshots/tag-cloud.png`

- [x] Extract `word/media/image11.png`, `image12.png`, `image13.png`, `image17.png`, `image24.png`, and `image15.png` from `docs/社交网络大数据研究报告---B站数据挖掘与分析.docx`.
- [x] Rename the extracted files according to the screenshot mapping in `docs/superpowers/specs/2026-08-26-readme-release-design.md`.
- [x] Verify all six files exist and preserve their original PNG format.
- [x] Commit the screenshot assets with the README release documents.

### Task 2: Write the Chinese release README

**Files:**
- Modify: `README.md`

- [x] Replace the existing short README with a GitHub-oriented Chinese document that contains language links, a capabilities table, an ASCII architecture diagram, six local screenshots, prerequisites, `.env` configuration, MySQL import, backend/frontend launch commands, crawler risk classification, LLM settings, verification, compliance, contribution, and MIT license sections.
- [x] State that high-risk UP video-list collection may return HTTP 412 and supports only authorized access or the existing observed-hot-video fallback.
- [x] Link `docs/DISCLAIMER.md`, `docs/VERIFICATION.md`, `docs/up主数据爬取接口调研文档.md`, and `LICENSE`.

### Task 3: Write the English release README

**Files:**
- Create: `README_EN.md`

- [x] Create an English document with the same functional sections and the same local screenshot paths as `README.md`.
- [x] Preserve the exact risk boundary: no credential sharing, proxy evasion, fingerprint spoofing, CAPTCHA bypass, or other access-control bypass techniques.

### Task 4: Validate and commit to main

**Files:**
- Modify: `README.md`
- Create: `README_EN.md`
- Create: `docs/screenshots/*.png`

- [x] Run `git diff --check` limited to README and screenshot files.
- [x] Confirm every referenced local image path exists.
- [x] Commit only README, screenshot, specification, and plan files.
- [x] Merge the documentation commits into local `main` without staging or modifying unrelated working-tree changes.
