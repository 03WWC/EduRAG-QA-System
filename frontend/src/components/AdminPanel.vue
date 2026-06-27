<script setup>
import { ref, onMounted } from 'vue'

const emit = defineEmits(['close'])

// Tab
const tab = ref('docs') // 'docs' | 'users'

// Document state
const sources = ref([])
const documents = ref([])
const selectedSource = ref('')
const fileInput = ref(null)
const uploading = ref(false)
const uploadMsg = ref('')

// User state
const users = ref([])
const newUsername = ref('')
const newPassword = ref('')
const newRole = ref('user')
const userMsg = ref('')

onMounted(async () => {
  await loadSources()
  await loadDocuments()
  await loadUsers()
})

async function api(path, options = {}) {
  const base = localStorage.getItem('api_base') || ''
  const token = localStorage.getItem('eduraag_token')
  return fetch(`${base}${path}`, {
    ...options,
    headers: {
      ...(options.headers || {}),
      'Authorization': `Bearer ${token}`,
    },
  })
}

// ========== Documents ==========
async function loadSources() {
  try {
    const resp = await api('/api/sources')
    sources.value = (await resp.json()).sources || []
  } catch {}
}

async function loadDocuments() {
  try {
    documents.value = (await api('/api/admin/documents')).json().then(d => d.documents || [])
    // fallback if above fails
  } catch {
    const resp = await api('/api/admin/documents')
    const data = await resp.json()
    documents.value = data.documents || []
  }
}

async function handleUpload() {
  const file = fileInput.value?.files?.[0]
  if (!file || !selectedSource.value) {
    uploadMsg.value = '请选择文件和学科'
    return
  }
  uploading.value = true
  uploadMsg.value = ''
  try {
    const form = new FormData()
    form.append('file', file)
    form.append('source', selectedSource.value)
    const resp = await api('/api/admin/upload', { method: 'POST', body: form })
    if (!resp.ok) throw new Error((await resp.json()).detail || '上传失败')
    const data = await resp.json()
    uploadMsg.value = `✅ 上传成功: ${data.chunks_count} 个分块`
    fileInput.value.value = ''
    await loadDocuments()
  } catch (e) {
    uploadMsg.value = `❌ ${e.message}`
  } finally {
    uploading.value = false
  }
}

async function handleDelete(source) {
  if (!confirm(`确定删除学科 "${source}" 的所有文档？Milvus + 磁盘 同步清除。`)) return
  try {
    const resp = await api(`/api/admin/documents/${source}`, { method: 'DELETE' })
    if (resp.ok) {
      uploadMsg.value = `已删除 ${source} 的文档`
      await loadDocuments()
    }
  } catch (e) {
    uploadMsg.value = `删除失败: ${e.message}`
  }
}

// ========== Users ==========
async function loadUsers() {
  try {
    const resp = await api('/api/auth/users')
    users.value = (await resp.json()).users || []
  } catch {}
}

async function handleCreateUser() {
  if (!newUsername.value.trim() || !newPassword.value.trim()) {
    userMsg.value = '请填写用户名和密码'
    return
  }
  try {
    const resp = await api('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: newUsername.value.trim(),
        password: newPassword.value,
        role: newRole.value,
      }),
    })
    if (!resp.ok) throw new Error((await resp.json()).detail || '创建失败')
    userMsg.value = `✅ 用户 ${newUsername.value} 创建成功`
    newUsername.value = ''
    newPassword.value = ''
    newRole.value = 'user'
    await loadUsers()
  } catch (e) {
    userMsg.value = `❌ ${e.message}`
  }
}

async function handleDeleteUser(userId, username) {
  if (!confirm(`确定删除用户 "${username}"？`)) return
  try {
    const resp = await api(`/api/auth/users/${userId}`, { method: 'DELETE' })
    if (!resp.ok) throw new Error((await resp.json()).detail || '删除失败')
    userMsg.value = `已删除用户 ${username}`
    await loadUsers()
  } catch (e) {
    userMsg.value = `❌ ${e.message}`
  }
}

function formatSize(bytes) {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}
</script>

<template>
  <div class="admin-panel">
    <div class="panel-header">
      <div class="panel-tabs">
        <button :class="{ active: tab === 'docs' }" @click="tab = 'docs'">📄 文档管理</button>
        <button :class="{ active: tab === 'users' }" @click="tab = 'users'">👥 用户管理</button>
      </div>
      <button class="close-btn" @click="$emit('close')">✕</button>
    </div>

    <!-- ==================== 文档管理 ==================== -->
    <template v-if="tab === 'docs'">
      <section class="section">
        <h3>📤 上传文件</h3>
        <div class="upload-row">
          <select v-model="selectedSource" class="source-select">
            <option value="">选择学科</option>
            <option v-for="s in sources" :key="s" :value="s">{{ s }}</option>
          </select>
          <input ref="fileInput" type="file" accept=".pdf,.ppt,.pptx,.docx,.txt,.md,.jpg,.png" class="file-input" />
          <button class="btn-primary" :disabled="uploading" @click="handleUpload">{{ uploading ? '上传中...' : '上传' }}</button>
        </div>
        <p v-if="uploadMsg" class="msg">{{ uploadMsg }}</p>
        <p class="hint">支持: PDF / PPT / DOCX / TXT / MD / JPG / PNG</p>
      </section>

      <section class="section">
        <h3>📄 已上传文档</h3>
        <table class="table" v-if="documents.length">
          <thead><tr><th>文件名</th><th>学科</th><th>大小</th><th>分块</th><th>时间</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="doc in documents" :key="doc.id">
              <td class="ellipsis" :title="doc.file_name">{{ doc.file_name }}</td>
              <td><span class="tag">{{ doc.source }}</span></td>
              <td>{{ formatSize(doc.file_size) }}</td>
              <td>{{ doc.chunks_count }}</td>
              <td class="time-col">{{ doc.uploaded_at ? doc.uploaded_at.slice(0, 16) : '-' }}</td>
              <td><button class="btn-danger-sm" @click="handleDelete(doc.source)">删除</button></td>
            </tr>
          </tbody>
        </table>
        <p v-else class="empty">暂无已上传文档</p>
      </section>
    </template>

    <!-- ==================== 用户管理 ==================== -->
    <template v-if="tab === 'users'">
      <section class="section">
        <h3>➕ 创建用户</h3>
        <div class="user-form">
          <input v-model="newUsername" placeholder="用户名" class="form-input" />
          <input v-model="newPassword" type="password" placeholder="密码" class="form-input" />
          <select v-model="newRole" class="form-select">
            <option value="user">普通用户</option>
            <option value="admin">管理员</option>
          </select>
          <button class="btn-primary" @click="handleCreateUser">创建</button>
        </div>
        <p v-if="userMsg" class="msg">{{ userMsg }}</p>
      </section>

      <section class="section">
        <h3>👥 用户列表 ({{ users.length }})</h3>
        <table class="table" v-if="users.length">
          <thead><tr><th>ID</th><th>用户名</th><th>角色</th><th>创建时间</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td>{{ u.id }}</td>
              <td>{{ u.username }}</td>
              <td><span class="tag" :class="{ admin: u.role === 'admin' }">{{ u.role === 'admin' ? '管理员' : '用户' }}</span></td>
              <td class="time-col">{{ u.created_at ? u.created_at.slice(0, 16) : '-' }}</td>
              <td><button class="btn-danger-sm" @click="handleDeleteUser(u.id, u.username)">删除</button></td>
            </tr>
          </tbody>
        </table>
        <p v-else class="empty">暂无用户</p>
      </section>
    </template>
  </div>
</template>

<style scoped>
.admin-panel { height: 100%; display: flex; flex-direction: column; overflow-y: auto; }

.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 20px; border-bottom: 1px solid var(--border, #e2e8f0);
}

.panel-tabs { display: flex; gap: 4px; }
.panel-tabs button {
  padding: 6px 14px; border: none; background: none; font-size: 14px;
  cursor: pointer; border-radius: 6px; color: var(--text-secondary, #64748b);
  transition: all 0.15s;
}
.panel-tabs button.active { background: #e0e7ff; color: #4338ca; font-weight: 600; }
.panel-tabs button:hover:not(.active) { background: var(--bg-system, #e2e8f0); }

.close-btn { background: none; border: none; font-size: 18px; cursor: pointer; color: var(--text-secondary, #64748b); padding: 4px 8px; border-radius: 4px; }
.close-btn:hover { background: var(--bg-system, #e2e8f0); }

.section { padding: 20px; border-bottom: 1px solid var(--border, #e2e8f0); }
.section h3 { font-size: 14px; font-weight: 600; margin-bottom: 12px; }

.upload-row { display: flex; gap: 8px; align-items: center; }
.source-select, .form-select {
  padding: 8px 10px; border: 1px solid var(--border, #e2e8f0); border-radius: 8px;
  background: var(--bg-input, #fff); color: var(--text-primary, #1e293b); font-size: 13px; outline: none;
}
.file-input { flex: 1; font-size: 13px; }

.btn-primary {
  padding: 8px 18px; border: none; border-radius: 8px; background: #6366f1;
  color: #fff; font-size: 13px; font-weight: 500; cursor: pointer; white-space: nowrap;
}
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-danger-sm {
  padding: 4px 10px; border: 1px solid #fca5a5; border-radius: 4px;
  background: #fef2f2; color: #dc2626; font-size: 12px; cursor: pointer;
}
.btn-danger-sm:hover { background: #fee2e2; }

.msg { margin-top: 8px; font-size: 13px; }
.hint { margin-top: 6px; font-size: 12px; color: var(--text-secondary, #64748b); }

.table { width: 100%; border-collapse: collapse; font-size: 13px; }
.table th, .table td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--border, #e2e8f0); }
.table th { font-weight: 600; color: var(--text-secondary, #64748b); font-size: 11px; }
.ellipsis { max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.time-col { font-size: 12px; color: var(--text-secondary, #64748b); white-space: nowrap; }

.tag { display: inline-block; background: #e0e7ff; color: #4338ca; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 500; }
.tag.admin { background: #fef3c7; color: #92400e; }

.user-form { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.form-input {
  padding: 8px 12px; border: 1px solid var(--border, #e2e8f0); border-radius: 8px;
  font-size: 13px; background: var(--bg-input, #fff); color: var(--text-primary, #1e293b);
  outline: none; width: 140px;
}
.form-input:focus { border-color: #6366f1; }

.empty { font-size: 13px; color: var(--text-secondary, #64748b); padding: 20px 0; text-align: center; }
</style>
