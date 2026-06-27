<script setup>
import { ref } from 'vue'

const emit = defineEmits(['close'])

const apiBase = ref(localStorage.getItem('api_base') || '')
const darkMode = ref(document.documentElement.classList.contains('dark'))
const saved = ref(false)

function toggleDark() {
  darkMode.value = !darkMode.value
  if (darkMode.value) {
    document.documentElement.classList.add('dark')
    localStorage.setItem('eduraag_theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark')
    localStorage.setItem('eduraag_theme', 'light')
  }
}

function saveSettings() {
  localStorage.setItem('api_base', apiBase.value.trim())
  saved.value = true
  setTimeout(() => (saved.value = false), 2000)
}

function clearAllData() {
  if (confirm('确定要清除所有本地数据吗？（会话记录和设置）')) {
    localStorage.clear()
    location.reload()
  }
}
</script>

<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal-header">
        <h3>设置</h3>
        <button class="close-btn" @click="$emit('close')">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <path d="M4 4l10 10M14 4L4 14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
          </svg>
        </button>
      </div>

      <div class="modal-body">
        <!-- API Base URL -->
        <div class="setting-group">
          <label>API 地址</label>
          <input
            v-model="apiBase"
            type="text"
            placeholder="http://localhost:8000"
            class="setting-input"
          />
          <p class="hint">开发模式下留空使用 Vite 代理，生产模式填写后端地址</p>
        </div>

        <!-- Theme Toggle -->
        <div class="setting-group">
          <label>外观模式</label>
          <div class="toggle-row">
            <span>{{ darkMode ? '🌙 暗色模式' : '☀️ 亮色模式' }}</span>
            <button class="toggle" :class="{ on: darkMode }" @click="toggleDark">
              <span class="toggle-knob"></span>
            </button>
          </div>
        </div>

        <!-- Clear Data -->
        <div class="setting-group">
          <label>数据管理</label>
          <button class="btn-danger" @click="clearAllData">清除所有本地数据</button>
        </div>

        <!-- Save -->
        <button class="btn-save" @click="saveSettings">
          {{ saved ? '✓ 已保存' : '保存设置' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 500;
}

.modal {
  background: var(--bg-chat);
  border-radius: var(--radius);
  box-shadow: var(--shadow-lg);
  width: 400px;
  max-width: 90vw;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.modal-header h3 {
  font-size: 16px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
}

.close-btn:hover {
  background: var(--bg-system);
  color: var(--text-primary);
}

.modal-body {
  padding: 20px;
}

.setting-group {
  margin-bottom: 20px;
}

.setting-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 6px;
  color: var(--text-primary);
}

.hint {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.setting-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 14px;
  background: var(--bg-input);
  color: var(--text-primary);
  outline: none;
  transition: border var(--transition);
}

.setting-input:focus {
  border-color: var(--primary);
}

.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.toggle {
  width: 48px;
  height: 26px;
  border-radius: 13px;
  border: none;
  background: var(--border);
  cursor: pointer;
  position: relative;
  transition: background var(--transition);
}

.toggle.on {
  background: var(--primary);
}

.toggle-knob {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #fff;
  transition: transform var(--transition);
}

.toggle.on .toggle-knob {
  transform: translateX(22px);
}

.btn-danger {
  width: 100%;
  padding: 8px;
  border: 1px solid #fca5a5;
  border-radius: var(--radius-sm);
  background: #fef2f2;
  color: #dc2626;
  cursor: pointer;
  font-size: 13px;
  transition: all var(--transition);
}

.btn-danger:hover {
  background: #fee2e2;
}

.btn-save {
  width: 100%;
  padding: 10px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--primary);
  color: #fff;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all var(--transition);
}

.btn-save:hover {
  background: var(--primary-dark);
}
</style>
