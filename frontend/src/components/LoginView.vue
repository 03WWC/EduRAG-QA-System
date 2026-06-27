<script setup>
import { ref } from 'vue'

const emit = defineEmits(['login-success'])

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  if (!username.value.trim() || !password.value.trim()) {
    error.value = '请输入用户名和密码'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const apiBase = localStorage.getItem('api_base') || ''
    const resp = await fetch(`${apiBase}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username.value.trim(),
        password: password.value,
      }),
    })

    if (!resp.ok) {
      const data = await resp.json()
      throw new Error(data.detail || '登录失败')
    }

    const data = await resp.json()
    localStorage.setItem('eduraag_token', data.token)
    localStorage.setItem('eduraag_username', data.username)
    localStorage.setItem('eduraag_role', data.role)
    emit('login-success', data)
  } catch (e) {
    error.value = e.message || '登录失败，请检查网络连接'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <div class="login-icon">
          <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
            <rect width="48" height="48" rx="14" fill="url(#lg)" />
            <path d="M14 30V18l10 6-10 6z" fill="#fff" />
            <path d="M24 30V18l10 6-10 6z" fill="rgba(255,255,255,0.7)" />
            <defs>
              <linearGradient id="lg" x1="0" y1="0" x2="48" y2="48">
                <stop stop-color="#6366f1" />
                <stop offset="1" stop-color="#a78bfa" />
              </linearGradient>
            </defs>
          </svg>
        </div>
        <h1>EduRAG</h1>
        <p>智能问答系统</p>
      </div>

      <form class="login-form" @submit.prevent="handleLogin">
        <div class="field">
          <label>用户名</label>
          <input
            v-model="username"
            type="text"
            placeholder="请输入用户名"
            :disabled="loading"
            autocomplete="username"
          />
        </div>

        <div class="field">
          <label>密码</label>
          <input
            v-model="password"
            type="password"
            placeholder="请输入密码"
            :disabled="loading"
            autocomplete="current-password"
          />
        </div>

        <p v-if="error" class="error-msg">{{ error }}</p>

        <button type="submit" class="btn-login" :disabled="loading">
          {{ loading ? '登录中...' : '登 录' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  background: var(--bg-chat, #fff);
  border-radius: var(--radius-lg, 24px);
  padding: 40px;
  width: 380px;
  max-width: 90vw;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-icon {
  margin-bottom: 12px;
}

.login-header h1 {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary, #1e293b);
  margin-bottom: 4px;
}

.login-header p {
  font-size: 13px;
  color: var(--text-secondary, #64748b);
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary, #1e293b);
}

.field input {
  padding: 10px 14px;
  border: 1px solid var(--border, #e2e8f0);
  border-radius: var(--radius-sm, 8px);
  font-size: 14px;
  background: var(--bg-input, #fff);
  color: var(--text-primary, #1e293b);
  outline: none;
  transition: border 0.2s;
}

.field input:focus {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.error-msg {
  font-size: 13px;
  color: #ef4444;
  text-align: center;
  margin: 0;
}

.btn-login {
  padding: 12px;
  border: none;
  border-radius: var(--radius-sm, 8px);
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-login:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-login:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
