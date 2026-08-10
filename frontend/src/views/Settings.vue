<template>
  <div>
    <div class="page-header">
      <h2>系统设置</h2>
    </div>

    <!-- 设置面板 -->
    <div class="settings-container">
      <!-- 左侧导航 -->
      <div class="settings-nav">
        <div class="nav-section">
          <h3>基本设置</h3>
          <ul>
            <li :class="{ active: activeTab === 'general' }" @click="activeTab = 'general'">
              <SettingsIcon />
              常规设置
            </li>
            <li :class="{ active: activeTab === 'appearance' }" @click="activeTab = 'appearance'">
              <PaletteIcon />
              外观设置
            </li>
            <li :class="{ active: activeTab === 'notifications' }" @click="activeTab = 'notifications'">
              <BellIcon />
              通知设置
            </li>
          </ul>
        </div>
        <div class="nav-section">
          <h3>高级设置</h3>
          <ul>
            <li :class="{ active: activeTab === 'security' }" @click="activeTab = 'security'">
              <ShieldIcon />
              安全设置
            </li>
            <li :class="{ active: activeTab === 'integrations' }" @click="activeTab = 'integrations'">
              <PlugIcon />
              集成设置
            </li>
            <li :class="{ active: activeTab === 'backup' }" @click="activeTab = 'backup'">
              <DatabaseIcon />
              备份设置
            </li>
          </ul>
        </div>
      </div>

      <!-- 右侧内容 -->
      <div class="settings-content">
        <!-- 常规设置 -->
        <div v-if="activeTab === 'general'" class="settings-panel">
          <h3>常规设置</h3>
          <div class="form-group">
            <label>系统名称</label>
            <input type="text" v-model="settings.systemName" />
          </div>
          <div class="form-group">
            <label>时区</label>
            <select v-model="settings.timezone">
              <option value="Asia/Shanghai">亚洲/上海</option>
              <option value="UTC">UTC</option>
              <option value="America/New_York">美洲/纽约</option>
            </select>
          </div>
          <div class="form-group">
            <label>语言</label>
            <select v-model="settings.language">
              <option value="zh-CN">简体中文</option>
              <option value="en-US">English</option>
            </select>
          </div>
        </div>

        <!-- 外观设置 -->
        <div v-if="activeTab === 'appearance'" class="settings-panel">
          <h3>外观设置</h3>
          <div class="form-group">
            <label>主题模式</label>
            <div class="radio-group">
              <label class="radio-label">
                <input type="radio" v-model="settings.theme" value="light" />
                浅色模式
              </label>
              <label class="radio-label">
                <input type="radio" v-model="settings.theme" value="dark" />
                深色模式
              </label>
              <label class="radio-label">
                <input type="radio" v-model="settings.theme" value="auto" />
                跟随系统
              </label>
            </div>
          </div>
          <div class="form-group">
            <label>主色调</label>
            <div class="color-picker">
              <div 
                v-for="color in colorOptions" 
                :key="color.value"
                class="color-option"
                :class="{ active: settings.primaryColor === color.value }"
                :style="{ backgroundColor: color.color }"
                @click="settings.primaryColor = color.value"
              ></div>
            </div>
          </div>
        </div>

        <!-- 其他设置面板... -->
        <div v-if="activeTab === 'integrations'" class="settings-panel">
          <h3>大模型设置</h3>
          <p class="settings-hint">此处配置立即作用于本地后端运行时，不会写入 .env。</p>
          <div class="form-group">
            <label>服务名称</label>
            <input type="text" v-model="llmConfig.provider" placeholder="OpenAI-compatible" />
          </div>
          <div class="form-group">
            <label>API Base URL</label>
            <input type="url" v-model="llmConfig.baseURL" placeholder="https://api.deepseek.com" />
          </div>
          <div class="form-group">
            <label>模型名称</label>
            <input type="text" v-model="llmConfig.model" placeholder="deepseek-chat" />
          </div>
          <div class="form-group">
            <label>API Key</label>
            <input type="password" v-model="llmConfig.apiKey" autocomplete="new-password" placeholder="输入所选服务的 API Key" />
          </div>
          <p class="settings-hint">支持任意 OpenAI-compatible 服务。配置仅保存在当前浏览器并在运行时发送给本地后端，不写入 .env。</p>
          <div class="llm-status" :class="{ configured: llmConfig.configured }">
            {{ llmConfig.configured ? '当前模型已配置' : '请填写 API Key 后保存' }}
          </div>
        </div>

        <div v-if="activeTab === 'notifications'" class="settings-panel">
          <h3>通知设置</h3>
          <div class="form-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="settings.emailNotifications" />
              启用邮件通知
            </label>
          </div>
          <div class="form-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="settings.pushNotifications" />
              启用推送通知
            </label>
          </div>
        </div>

        <!-- 保存按钮 -->
        <div class="settings-actions">
          <button class="save-button" @click="saveSettings">
            保存设置
          </button>
          <button class="reset-button" @click="resetSettings">
            重置为默认
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { 
  Settings as SettingsIcon,
  Palette as PaletteIcon,
  Bell as BellIcon,
  Shield as ShieldIcon,
  Plug as PlugIcon,
  Database as DatabaseIcon
} from 'lucide-vue-next';

const activeTab = ref('general');
const llmConfig = ref({ provider: '', baseURL: '', model: '', apiKey: '', configured: false });
const llmStorageKey = 'databili.llmConfig';

const settings = ref({
  systemName: 'DataBili',
  timezone: 'Asia/Shanghai',
  language: 'zh-CN',
  theme: 'light',
  primaryColor: 'pink',
  emailNotifications: true,
  pushNotifications: false
});

const colorOptions = [
  { value: 'pink', color: '#FB7299' },
  { value: 'blue', color: '#23ADE5' },
  { value: 'green', color: '#10B981' },
  { value: 'purple', color: '#8B5CF6' },
  { value: 'orange', color: '#F59E0B' }
];

const loadLlmConfig = async () => {
  try {
    const savedConfig = localStorage.getItem(llmStorageKey);
    if (savedConfig) {
      const response = await fetch('/api/llm-config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: savedConfig
      });
      const result = await response.json();
      if (result.code === 0) {
        llmConfig.value = { ...result.data, ...JSON.parse(savedConfig) };
        return;
      }
    }
    const response = await fetch('/api/llm-config');
    const result = await response.json();
    if (result.code === 0) llmConfig.value = { ...llmConfig.value, ...result.data };
  } catch (error) {
    console.error('读取大模型配置失败:', error);
  }
};

const saveSettings = async () => {
  if (activeTab.value === 'integrations') {
    const response = await fetch('/api/llm-config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        provider: llmConfig.value.provider,
        baseURL: llmConfig.value.baseURL,
        model: llmConfig.value.model,
        apiKey: llmConfig.value.apiKey
      })
    });
    const result = await response.json();
    if (result.code === 0) {
      const savedConfig = {
        provider: llmConfig.value.provider,
        baseURL: llmConfig.value.baseURL,
        model: llmConfig.value.model,
        apiKey: llmConfig.value.apiKey
      };
      localStorage.setItem(llmStorageKey, JSON.stringify(savedConfig));
      llmConfig.value = { ...result.data, ...savedConfig };
    }
    return;
  }
  console.log('保存设置:', settings.value);
};

const resetSettings = () => {
  if (activeTab.value === 'integrations') {
    loadLlmConfig();
    return;
  }
  console.log('重置设置');
};

loadLlmConfig();
</script>

<style scoped>
.page-header {
  margin-bottom: 1.5rem;
}

.page-header h2 {
  font-size: 1.5rem;
  font-weight: 600;
}

.settings-container {
  display: grid;
  grid-template-columns: 250px 1fr;
  gap: 2rem;
}

.settings-nav {
  background-color: var(--card);
  border-radius: var(--radius);
  padding: 1.5rem;
  height: fit-content;
}

.nav-section {
  margin-bottom: 2rem;
}

.nav-section:last-child {
  margin-bottom: 0;
}

.nav-section h3 {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--muted-foreground);
  margin-bottom: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.nav-section ul {
  list-style: none;
}

.nav-section li {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  margin-bottom: 0.25rem;
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.2s;
  color: var(--muted-foreground);
}

.nav-section li:hover {
  background-color: var(--muted);
}

.nav-section li.active {
  background-color: var(--primary-light);
  color: var(--primary);
  font-weight: 500;
}

.settings-content {
  background-color: var(--card);
  border-radius: var(--radius);
  padding: 2rem;
}

.settings-panel h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--foreground);
  margin-bottom: 0.5rem;
}

.form-group input,
.form-group select {
  width: 100%;
  max-width: 300px;
  padding: 0.75rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background-color: var(--background);
  color: var(--foreground);
}

.settings-hint {
  color: var(--muted-foreground);
  font-size: 0.875rem;
  margin-bottom: 1.5rem;
}

.llm-status {
  color: #b45309;
  font-size: 0.875rem;
}

.llm-status.configured {
  color: #047857;
}

.radio-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.radio-label,
.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--foreground);
  cursor: pointer;
}

.radio-label input,
.checkbox-label input {
  width: auto;
}

.color-picker {
  display: flex;
  gap: 0.75rem;
}

.color-option {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.color-option.active {
  border-color: var(--foreground);
  transform: scale(1.1);
}

.settings-actions {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid var(--border);
}

.save-button,
.reset-button {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.save-button {
  background-color: var(--primary);
  color: white;
}

.save-button:hover {
  background-color: #e91e63;
}

.reset-button {
  background-color: var(--muted);
  color: var(--foreground);
  border: 1px solid var(--border);
}

.reset-button:hover {
  background-color: var(--border);
}

@media (max-width: 768px) {
  .settings-container {
    grid-template-columns: 1fr;
  }
  
  .settings-nav {
    order: 2;
  }
  
  .settings-content {
    order: 1;
  }
}
</style>
