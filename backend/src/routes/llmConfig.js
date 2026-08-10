const express = require('express');
const { getPublicLlmConfig, updatePublicLlmConfig } = require('../config/llm');

const router = express.Router();

router.get('/', (req, res) => {
  res.json({ code: 0, data: getPublicLlmConfig() });
});

router.put('/', (req, res) => {
  const { baseURL, model } = req.body || {};
  if ((baseURL !== undefined && typeof baseURL !== 'string') ||
      (model !== undefined && typeof model !== 'string')) {
    return res.status(400).json({ code: 1, message: 'baseURL 和 model 必须是字符串' });
  }
  res.json({ code: 0, data: updatePublicLlmConfig({ baseURL, model }) });
});

module.exports = router;
