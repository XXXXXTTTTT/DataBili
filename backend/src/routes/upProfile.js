const express = require('express');
const router = express.Router();
const pool = require('../db');
const { spawnSync } = require('child_process');
const path = require('path');

// GET /api/up-profile?uid=123456
// GET /api/up-profile?name=某某
router.get('/', async (req, res) => {
  const { uid, name } = req.query;
  try {
    let rows = [];

    if (uid) {
      //优先使用uid查询
      [rows] = await pool.query(`
        SELECT p.*, a.cluster_label
        FROM up_profile p
        LEFT JOIN up_analysis a ON p.uid = a.uid
        WHERE p.uid = ?
      `, [uid]);
    } else if (name) {
      //其次依据名称模糊查询
      [rows] = await pool.query(`
        SELECT p.*, a.cluster_label
        FROM up_profile p
        LEFT JOIN up_analysis a ON p.uid = a.uid
        WHERE p.name LIKE ?
      `, [`%${name}%`]);
    } 
    else {
      //如果空则显示全部
      [rows] = await pool.query(`
        SELECT p.*, a.cluster_label
        FROM up_profile p
        LEFT JOIN up_analysis a ON p.uid = a.uid
      `);
      // return res.json({ code: 0, data: rows });
    }

    if (rows.length === 0 && uid) {
      // 数据库查不到
      // await runSpider(uid);
      [rows] = await pool.query('SELECT * FROM up_profile WHERE uid = ?', [uid]);
      if (rows.length === 0) {
        return res.status(404).json({ code: 1, message: '未找到该UP主' });
      }
    }

    // // 对每个up主单独预测
    // const results = [];
    // for (const up of rows) {
    //   const pyArgs = [path.resolve(__dirname, '../../../upModel/test.py'), '--uid', up.uid];
    //   const pyResult = spawnSync('python', pyArgs, { encoding: 'utf-8' });

    //   if (pyResult.error) {
    //     return res.status(500).json({ code: 1, message: 'Python 脚本出错', error: pyResult.error.toString() });
    //   }
    //   if (pyResult.status !== 0) {
    //     return res.status(500).json({ code: 1, message: 'Python 脚本出错', error: pyResult.stderr });
    //   }

    //   let clusterLabel = null;
    //   try {
    //     const pyData = JSON.parse(pyResult.stdout);
    //     clusterLabel = pyData.cluster_label ?? null;
    //   } catch (e) {
    //     return res.status(500).json({ code: 1, message: 'Python 输出解析失败', error: e.toString(), raw: pyResult.stdout });
    //   }

    //   results.push({ ...up, cluster_label: clusterLabel });
    // }

    res.json({ code: 0, data: rows });
  } catch (error) {
    res.status(500).json({ code: 1, message: '服务器内部错误', error: error.toString() });
  }
});

// GET /api/up-profile/known-videos?uid=123456
router.get('/known-videos', async (req, res) => {
  const { uid } = req.query;
  if (!uid) {
    return res.status(400).json({ code: 1, message: '缺少参数uid' });
  }

  try {
    const [rows] = await pool.query(`
      SELECT
        video.aid,
        video.title,
        video.pic,
        video.pubdate,
        video.tname,
        video.duration,
        video.stat_view,
        video.stat_like,
        video.stat_coin,
        video.stat_favorite,
        video.stat_reply,
        video.stat_danmaku,
        video.timestamp AS observed_at
      FROM bilibili_hot_videos_server AS video
      INNER JOIN (
        SELECT aid, MAX(timestamp) AS latest_timestamp
        FROM bilibili_hot_videos_server
        WHERE owner_mid = ?
        GROUP BY aid
      ) AS latest
        ON video.aid = latest.aid
        AND video.timestamp = latest.latest_timestamp
      WHERE video.owner_mid = ?
      ORDER BY video.timestamp DESC
      LIMIT 100
    `, [uid, uid]);

    res.json({
      code: 0,
      source: 'bilibili_hot_videos_server',
      completeness: 'observed_hot_videos_only',
      data: rows
    });
  } catch (error) {
    console.error('已观测 UP 主视频查询失败:', error);
    res.status(500).json({ code: 1, message: '服务器内部错误' });
  }
});

//GetUP主聚类分析API
router.get('/analysis', async (req, res) => {
  try {
    // 联表查询up_profile和up_analysis，返回uid, name, avatar_url, 以及up_analysis表中的所有特征和cluster_label
    const [rows] = await pool.query(`
      SELECT 
        p.uid, p.name, p.avatar_url, p.followers, p.total_view, p.total_like, 
        a.log_followers, a.log_view, a.like_rate, a.engagement_rate, a.duration_engagement, a.cluster_label
      FROM up_profile p
      LEFT JOIN up_analysis a ON p.uid = a.uid
    `);
    res.json({ code: 0, data: rows });
  } catch (error) {
    res.status(500).json({ code: 1, message: '服务器内部错误', error: error.toString() });
  }
});

// 汇总统计API
router.get('/summary', async (req, res) => {
  try {
    // up_profile表汇总
    const [[profileStats]] = await pool.query(`
      SELECT 
        COUNT(*) as up_count,
        SUM(total_videos) as total_videos,
        SUM(total_view) as total_view,
        SUM(followers) as total_followers,
        SUM(total_like) as total_like,
        SUM(total_coin) as total_coin,
        SUM(total_favorite) as total_favorite,
        SUM(total_share) as total_share,
        SUM(total_comment) as total_comment,
        SUM(total_danmaku) as total_danmaku,
        SUM(total_duration) as total_duration,
        SUM(total_chargers) as total_chargers
      FROM up_profile
    `);
    // up_analysis表汇总
    const [[analysisStats]] = await pool.query(`SELECT COUNT(*) as analysis_count FROM up_analysis`);
    const [clusterCounts] = await pool.query(`SELECT cluster_label, COUNT(*) as count FROM up_analysis GROUP BY cluster_label`);
    res.json({
      code: 0,
      data: {
        ...profileStats,
        analysis_count: analysisStats.analysis_count,
        cluster_counts: clusterCounts
      }
    });
  } catch (error) {
    res.status(500).json({ code: 1, message: '服务器内部错误', error: error.toString() });
  }
});

module.exports = router;
