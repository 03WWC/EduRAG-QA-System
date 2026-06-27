<script setup>
import { ref, onMounted } from 'vue'

const emit = defineEmits(['close'])

const sources = ref([])
const documents = ref([])
const selectedSource = ref('')
const fileInput = ref(null)
const uploading = ref(false)
const uploadMsg = ref('')

onMounted(async () => {
  await loadSources()
  await loadDocuments()
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

async function loadSources() {
  try {
    const resp = await api('/api/sources')
    const data = await resp.json()
    sources.value = data.sources || []
  } catch {}
}

async function loadDocuments() {
  try {
    const resp = await api('/api/admin/documents')
    const data = await resp.json()
    documents.value = data.documents || []
  } catch {}
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

    const resp = await api('/api/admin/upload', {
      method: 'POST',
      body: form,
    })

    if (!resp.ok) {
      const data = await resp.json()
      throw new Error(data.detail || '上传失败')
    }

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
  if (!confirm(`确定删除学科 "${source}" 的所有文档？这将同时清除 Milvus 中的数据。`)) return

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
      <h2>管理面板</h2>
      <button class="close-btn" @click="$emit('close')">✕</button>
    </div>

    <!-- Upload Section -->
    <section class="section">
      <h3>📤 上传文件</h3>
      <div class="upload-row">
        <select v-model="selectedSource" class="source-select">
          <option value="">选择学科</option>
          <option v-for="s in sources" :key="s" :value="s">{{ s }}</option>
        </select>
        <input
          ref="fileInput"
          type="file"
          accept=".pdf,.ppt,.pptx,.docx,.txt,.md,.jpg,.png"
          class="file-input"
        />
        <button class="btn-upload" :disabled="uploading" @click="handleUpload">
          {{ uploading ? '上传中...' : '上传' }}
        </button>
      </div>
      <p v-if="uploadMsg" class="upload-msg">{{ uploadMsg }}</p>
      <p class="hint">支持: PDF / PPT / DOCX / TXT / MD / JPG / PNG</p>
    </section>

    <!-- Documents List -->
    <section class="section">
      <h3>📄 已上传文档</h3>
      <table class="doc-table" v-if="documents.length > 0">
        <thead>
          <tr>
            <th>学科</th>
            <th>文件数</th>
            <th>分块总数</th>
            <th>最近上传</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="doc in documents" :key="doc.source">
            <td><span class="source-tag">{{ doc.source }}</span></td>
            <td>{{ doc.file_count }}</td>
            <td>{{ doc.total_chunks }}</td>
            <td class="time-col">{{ doc.latest_upload ? doc.latest_upload.slice(0, 16) : '-' }}</td>
            <td>
              <button class="btn-delete" @click="handleDelete(doc.source)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty">暂无已上传文档</p>
    </section>
  </div>
</template>

<style scoped>
.admin-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border, #e2e8f0);
}

.panel-header h2 {
  font-size: 18px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: var(--text-secondary, #64748b);
  padding: 4px 8px;
  border-radius: 4px;
}

.close-btn:hover {
  background: var(--bg-system, #e2e8f0);
}

.section {
  padding: 20px;
  border-bottom: 1px solid var(--border, #e2e8f0);
}

.section h3 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text-primary, #1e293b);
}

.upload-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.source-select {
  padding: 8px 10px;
  border: 1px solid var(--border, #e2e8f0);
  border-radius: var(--radius-sm, 8px);
  background: var(--bg-input, #fff);
  color: var(--text-primary, #1e293b);
  font-size: 13px;
  outline: none;
}

.file-input {
  flex: 1;
  font-size: 13px;
}

.btn-upload {
  padding: 8px 18px;
  border: none;
  border-radius: var(--radius-sm, 8px);
  background: #6366f1;
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
}

.btn-upload:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.upload-msg {
  margin-top: 8px;
  font-size: 13px;
}

.hint {
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-secondary, #64748b);
}

.doc-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.doc-table th, .doc-table td {
  text-align: left;
  padding: 8px 10px;
  border-bottom: 1px solid var(--border, #e2e8f0);
}

.doc-table th {
  font-weight: 600;
  color: var(--text-secondary, #64748b);
  font-size: 11px;
}

.source-tag {
  display: inline-block;
  background: #e0e7ff;
  color: #4338ca;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.time-col {
  font-size: 12px;
  color: var(--text-secondary, #64748b);
}

.btn-delete {
  padding: 4px 10px;
  border: 1px solid #fca5a5;
  border-radius: 4px;
  background: #fef2f2;
  color: #dc2626;
  font-size: 12px;
  cursor: pointer;
}

.btn-delete:hover {
  background: #fee2e2;
}

.empty {
  font-size: 13px;
  color: var(--text-secondary, #64748b);
  padding: 20px 0;
  text-align: center;
}
</style>
