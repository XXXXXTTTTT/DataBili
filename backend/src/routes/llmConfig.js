const express = require('express');
const { getPublicLlmConfig, updateLlmConfig } = require('../config/llm');

const router = express.Router();

router.get('/', (req, res) => {
  res.json({ code: 0, data: getPublicLlmConfig() });
});

router.put('/', (req, res) => {
  const { provider, baseURL, model, apiKey } = req.body || {};
  const values = { provider, baseURL, model, apiKey };
  if (Object.values(values).some((value) => value !== undefined && typeof value !== 'string')) {
    return res.status(400).json({ code: 1, message: '大模型配置字段必须是字符串' });
  }
  res.json({ code: 0, data: updateLlmConfig(values) });
});

module.exports = router;
