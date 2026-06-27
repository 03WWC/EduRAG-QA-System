<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  username: String,
  role: String,
})

const emit = defineEmits(['close', 'logout'])

const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const msg = ref('')
const msgType = ref('') // 'success' | 'error'

const isAdmin = computed(() => props.role === 'admin')

async function handleChangePassword() {
  if (!oldPassword.value || !newPassword.value || !confirmPassword.value) {
    msg.value = '请填写所有密码字段'
    msgType.value = 'error'
    return
  }
  if (newPassword.value.length < 3) {
    msg.value = '新密码至少3位'
    msgType.value = 'error'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    msg.value = '两次新密码不一致'
    msgType.value = 'error'
    return
  }

  loading.value = true
  msg.value = ''
  try {
    const base = localStorage.getItem('api_base') || ''
    const token = localStorage.getItem('eduraag_token')
    const resp = await fetch(`${base}/api/auth/change-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        old_password: oldPassword.value,
        new_password: newPassword.value,
      }),
    })
    if (!resp.ok) {
      const data = await resp.json()
      throw new Error(data.detail || '修改失败')
    }
    msg.value = '密码修改成功'
    msgType.value = 'success'
    oldPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
  } catch (e) {
    msg.value = e.message
    msgType.value = 'error'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="profile-modal">
      <div class="modal-header">
        <h3>用户信息</h3>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <!-- User Info Card -->
      <div class="user-info-card">
        <div class="avatar-large">
          <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
            <circle cx="24" cy="24" r="24" :fill="isAdmin ? '#6366f1' : '#10b981'" />
            <circle cx="24" cy="18" r="7" fill="#fff" />
            <path d="M10 42c0-7.7 6.3-14 14-14s14 6.3 14 14" fill="#fff" />
          </svg>
        </div>
        <div class="user-details">
          <span class="uname">{{ username }}</span>
          <span class="role-badge" :class="{ admin: isAdmin }">{{ isAdmin ? '管理员' : '普通用户' }}</span>
        </div>
      </div>

      <!-- Change Password -->
      <div class="pwd-section">
        <h4>修改密码</h4>
        <div class="field">
          <label>原密码</label>
          <input v-model="oldPassword" type="password" placeholder="输入原密码" :disabled="loading" />
        </div>
        <div class="field">
          <label>新密码</label>
          <input v-model="newPassword" type="password" placeholder="至少3位" :disabled="loading" />
        </div>
        <div class="field">
          <label>确认新密码</label>
          <input v-model="confirmPassword" type="password" placeholder="再次输入新密码" :disabled="loading" />
        </div>
        <p v-if="msg" class="msg" :class="msgType">{{ msg }}</p>
        <button class="btn-save" @click="handleChangePassword" :disabled="loading">
          {{ loading ? '保存中...' : '修改密码' }}
        </button>
      </div>

      <div class="modal-footer">
        <button class="btn-logout" @click="$emit('logout')">退出登录</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 500;
}

.profile-modal {
  background: var(--bg-chat, #fff);
  border-radius: var(--radius, 16px);
  box-shadow: var(--shadow-lg, 0 10px 40px rgba(0,0,0,0.12));
  width: 400px;
  max-width: 90vw;
  max-height: 85vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border, #e2e8f0);
}

.modal-header h3 { font-size: 16px; font-weight: 600; }

.close-btn {
  background: none; border: none; font-size: 18px;
  cursor: pointer; color: var(--text-secondary, #64748b);
  padding: 4px 8px; border-radius: 4px;
}
.close-btn:hover { background: var(--bg-system, #e2e8f0); }

.user-info-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px 20px;
  border-bottom: 1px solid var(--border, #e2e8f0);
}

.avatar-large { flex-shrink: 0; }

.user-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.uname {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary, #1e293b);
}

.role-badge {
  display: inline-block;
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 10px;
  background: #d1fae5;
  color: #065f46;
  width: fit-content;
}

.role-badge.admin {
  background: #e0e7ff;
  color: #3730a3;
}

.pwd-section {
  padding: 20px;
  border-bottom: 1px solid var(--border, #e2e8f0);
}

.pwd-section h4 {
  font-size: 14px; font-weight: 600;
  margin-bottom: 14px;
  color: var(--text-primary, #1e293b);
}

.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
}

.field label {
  font-size: 12px; font-weight: 600;
  color: var(--text-secondary, #64748b);
}

.field input {
  padding: 8px 12px;
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
  box-shadow: 0 0 0 3px rgba(99,102,241,0.1);
}

.msg {
  font-size: 13px;
  margin-bottom: 10px;
  text-align: center;
}

.msg.success { color: #22c55e; }
.msg.error { color: #ef4444; }

.btn-save {
  width: 100%;
  padding: 10px;
  border: none;
  border-radius: var(--radius-sm, 8px);
  background: #6366f1;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-save:disabled { opacity: 0.6; cursor: not-allowed; }

.modal-footer {
  padding: 16px 20px;
  text-align: center;
}

.btn-logout {
  padding: 8px 20px;
  border: 1px solid #fca5a5;
  border-radius: var(--radius-sm, 8px);
  background: #fef2f2;
  color: #dc2626;
  font-size: 13px;
  cursor: pointer;
}

.btn-logout:hover { background: #fee2e2; }
</style>
