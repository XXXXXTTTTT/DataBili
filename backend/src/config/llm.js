const DEFAULT_BASE_URL = 'https://api.deepseek.com';
const DEFAULT_MODEL = 'deepseek-chat';

const runtimeConfig = {
  provider: 'OpenAI-compatible',
  baseURL: DEFAULT_BASE_URL,
  model: DEFAULT_MODEL,
  apiKey: ''
};

function getLlmConfig() {
  return { ...runtimeConfig };
}

function getPublicLlmConfig() {
  const { apiKey, ...publicConfig } = getLlmConfig();
  return {
    ...publicConfig,
    configured: Boolean(apiKey)
  };
}

function updateLlmConfig({ provider, baseURL, model, apiKey }) {
  if (typeof provider === 'string' && provider.trim()) {
    runtimeConfig.provider = provider.trim();
  }
  if (typeof baseURL === 'string' && baseURL.trim()) {
    runtimeConfig.baseURL = baseURL.trim().replace(/\/+$/, '');
  }
  if (typeof model === 'string' && model.trim()) {
    runtimeConfig.model = model.trim();
  }
  if (typeof apiKey === 'string') {
    runtimeConfig.apiKey = apiKey.trim();
  }
  return getPublicLlmConfig();
}

module.exports = { getLlmConfig, getPublicLlmConfig, updateLlmConfig };
