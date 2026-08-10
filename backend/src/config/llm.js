const path = require('path');
const dotenv = require('dotenv');

dotenv.config({ path: path.resolve(__dirname, '../../../.env') });
dotenv.config({ path: path.resolve(__dirname, '../../.env'), override: false });

const DEFAULT_BASE_URL = 'https://api.deepseek.com';
const DEFAULT_MODEL = 'deepseek-chat';

function getLlmConfig() {
  return {
    baseURL: process.env.LLM_BASE_URL || DEFAULT_BASE_URL,
    model: process.env.LLM_MODEL || DEFAULT_MODEL,
    apiKey: process.env.DEEPSEEK_API_KEY || ''
  };
}

function getPublicLlmConfig() {
  const config = getLlmConfig();
  return {
    baseURL: config.baseURL,
    model: config.model,
    configured: Boolean(config.apiKey)
  };
}

function updatePublicLlmConfig({ baseURL, model }) {
  if (typeof baseURL === 'string' && baseURL.trim()) {
    process.env.LLM_BASE_URL = baseURL.trim();
  }
  if (typeof model === 'string' && model.trim()) {
    process.env.LLM_MODEL = model.trim();
  }
  return getPublicLlmConfig();
}

module.exports = { getLlmConfig, getPublicLlmConfig, updatePublicLlmConfig };
