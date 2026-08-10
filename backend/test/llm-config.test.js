const test = require('node:test');
const assert = require('node:assert/strict');

const {
  getLlmConfig,
  getPublicLlmConfig,
  updateLlmConfig
} = require('../src/config/llm');

test('运行时可配置任意 OpenAI-compatible 服务并隐藏 API key', () => {
  const result = updateLlmConfig({
    baseURL: 'https://example.test/v1',
    model: 'custom-model',
    apiKey: 'runtime-secret'
  });

  assert.equal(result.baseURL, 'https://example.test/v1');
  assert.equal(result.model, 'custom-model');
  assert.equal(result.configured, true);
  assert.equal(result.apiKey, undefined);
  assert.equal(getLlmConfig().apiKey, 'runtime-secret');
  assert.equal(getPublicLlmConfig().apiKey, undefined);
});
