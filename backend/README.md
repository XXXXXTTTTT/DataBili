# Bilibili 热门视频后端API

## 模块简介
本模块基于 Express.js，提供 Bilibili 数据的API接口。

## 启动方式

1. 安装依赖：
   ```bash
   npm install
   ```
2. 启动开发环境：
   ```bash
   npm run dev
   ```
3. 启动生产环境：
   ```bash
   npm start
   ```

## 接口总览
- `GET /api/hot-videos` 获取最新一批Bilibili热门视频数据。
- `GET /api/up-profile`获取全部UP主的信息
- `GET /api/up-profile/known-videos?uid=123456` 获取项目已观测到的该 UP 主热门视频，不表示完整投稿列表。
- `GET /api/up-profile/analysis`获取UP主用于聚类分析时的特征值以及聚类标签
- `GET /api/up-profile/summary`获取爬取的全部Up主数据统计
