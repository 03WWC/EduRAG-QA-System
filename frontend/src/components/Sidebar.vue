<script setup>
import { ref, computed } from 'vue'
import { stripMarkdown } from '../utils/markdown.js'

const props = defineProps({
  sessions: { type: Array, required: true },
  currentSessionId: { type: String, default: null },
})

const emit = defineEmits([
  'new-session',
  'switch-session',
  'rename-session',
  'delete-session',
  'toggle-settings',
])

const showContextMenu = ref({ visible: false, x: 0, y: 0, sessionId: null })
const editingId = ref(null)
const editingTitle = ref('')

function startRename(session) {
  editingId.value = session.id
  editingTitle.value = session.title
}

function confirmRename(sessionId) {
  const title = editingTitle.value.trim()
  if (title) {
    emit('rename-session', sessionId, title)
  }
  editingId.value = null
}

function cancelRename() {
  editingId.value = null
}

function onContextMenu(e, sessionId) {
  e.preventDefault()
  showContextMenu.value = {
    visible: true,
    x: e.clientX,
    y: e.clientY,
    sessionId,
  }
}

function hideContextMenu() {
  showContextMenu.value.visible = false
}

function handleRenameFromMenu() {
  const session = props.sessions.find((s) => s.id === showContextMenu.value.sessionId)
  if (session) startRename(session)
  hideContextMenu()
}

function handleDeleteFromMenu() {
  emit('delete-session', showContextMenu.value.sessionId)
  hideContextMenu()
}

const sortedSessions = computed(() =>
  [...props.sessions].sort((a, b) => b.createdAt - a.createdAt)
)

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  const now = new Date()
  const diff = now - d
  if (diff < 86400000) {
    return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  if (diff < 604800000) {
    const days = ['日', '一', '二', '三', '四', '五', '六']
    return `周${days[d.getDay()]}`
  }
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}
</script>

<template>
  <aside class="sidebar">
    <!-- Brand -->
    <div class="sidebar-brand">
      <div class="brand-icon">
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
          <rect width="28" height="28" rx="8" fill="url(#brand-grad)" />
          <path d="M8 18V10l6 4-6 4z" fill="#fff" />
          <path d="M14 18V10l6 4-6 4z" fill="rgba(255,255,255,0.7)" />
          <defs>
            <linearGradient id="brand-grad" x1="0" y1="0" x2="28" y2="28">
              <stop stop-color="#6366f1" />
              <stop offset="1" stop-color="#a78bfa" />
            </linearGradient>
          </defs>
        </svg>
      </div>
      <div class="brand-text">
        <span class="brand-name">EduRAG</span>
        <span class="brand-subtitle">智能问答系统</span>
      </div>
    </div>

    <!-- New Session Button -->
    <button class="btn-new-session" @click="$emit('new-session')">
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
        <path d="M9 3v12M3 9h12" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
      </svg>
      新对话
    </button>

    <!-- Session List -->
    <div class="session-list">
      <div
        v-for="session in sortedSessions"
        :key="session.id"
        class="session-item"
        :class="{ active: session.id === currentSessionId }"
        @click="$emit('switch-session', session.id)"
        @contextmenu="onContextMenu($event, session.id)"
      >
        <div class="session-icon">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path
              d="M2 3.5A1.5 1.5 0 013.5 2h9A1.5 1.5 0 0114 3.5v6a1.5 1.5 0 01-1.5 1.5h-5L4 14V11h-.5A1.5 1.5 0 012 9.5v-6z"
              stroke="currentColor"
              stroke-width="1.2"
              fill="none"
            />
          </svg>
        </div>
        <div class="session-info">
          <div class="session-title" v-if="editingId === session.id">
            <input
              v-model="editingTitle"
              class="rename-input"
              @keyup.enter="confirmRename(session.id)"
              @keyup.escape="cancelRename"
              @blur="confirmRename(session.id)"
              @click.stop
              autofocus
            />
          </div>
          <div class="session-title" v-else>{{ session.title }}</div>
          <div class="session-meta">{{ formatTime(session.createdAt) }} · {{ session.messageCount || 0 }} 条消息</div>
        </div>
      </div>

      <div v-if="sessions.length === 0" class="empty-sessions">
        暂无历史对话
      </div>
    </div>

    <!-- Bottom Actions -->
    <div class="sidebar-footer">
      <button class="footer-btn" @click="$emit('toggle-settings')" title="设置">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path
            d="M9 11.5a2.5 2.5 0 100-5 2.5 2.5 0 000 5z"
            stroke="currentColor"
            stroke-width="1.3"
          />
          <path
            d="M14.3 9c0-.25.04-.5.07-.74l1.32-.4c.18-.06.3-.2.34-.37a7.6 7.6 0 00-.68-2.52c-.1-.18-.27-.3-.47-.3l-1.36.2a4.3 4.3 0 00-1.28-.74l-.06-1.38a.43.43 0 00-.24-.42 7.5 7.5 0 00-2.58-.42c-.19 0-.34.14-.39.32l-.3 1.32a4.5 4.5 0 00-.74 0l-.72-1.14a.42.42 0 00-.47-.17c-.88.3-1.7.74-2.42 1.3-.13.1-.17.28-.13.44l.62 1.2a4.3 4.3 0 00-.54.48l-1.28-.4a.43.43 0 00-.5.18 7.6 7.6 0 00-1.04 2.38c-.04.17.02.35.18.44l1.07.8a4.7 4.7 0 000 .92l-1.07.8a.43.43 0 00-.18.44 7.6 7.6 0 001.04 2.38c.1.17.3.26.5.18l1.28-.4c.17.17.35.33.54.48l-.62 1.2c-.04.16 0 .34.13.44a7.5 7.5 0 002.42 1.3c.18.06.38.02.47-.17l.72-1.14c.25.03.5.03.74 0l.3 1.32a.43.43 0 00.39.32 7.5 7.5 0 002.58-.42.43.43 0 00.24-.42l.06-1.38c.46-.2.9-.46 1.28-.74l1.36.2c.2.02.38-.12.47-.3a7.6 7.6 0 00.68-2.52c.04-.18-.06-.35-.22-.42l-1.42-.34A4.5 4.5 0 0014.3 9z"
            stroke="currentColor"
            stroke-width="1.3"
          />
        </svg>
      </button>
      <span class="version">v1.0</span>
    </div>

    <!-- Context Menu -->
    <Teleport to="body">
      <div v-if="showContextMenu.visible" class="context-overlay" @click="hideContextMenu" @contextmenu.prevent="hideContextMenu">
        <div
          class="context-menu"
          :style="{ left: showContextMenu.x + 'px', top: showContextMenu.y + 'px' }"
        >
          <button @click="handleRenameFromMenu">重命名</button>
          <button class="danger" @click="handleDeleteFromMenu">删除</button>
        </div>
      </div>
    </Teleport>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 280px;
  height: 100%;
  background: var(--bg-sidebar);
  color: var(--text-sidebar);
  display: flex;
  flex-direction: column;
  transition: background var(--transition);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 16px 12px;
}

.brand-icon {
  flex-shrink: 0;
}

.brand-text {
  display: flex;
  flex-direction: column;
}

.brand-name {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.3px;
}

.brand-subtitle {
  font-size: 11px;
  color: var(--text-sidebar-dim);
}

.btn-new-session {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin: 8px 12px 16px;
  padding: 10px;
  border-radius: var(--radius-sm);
  border: 1px dashed rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-sidebar);
  font-size: 14px;
  cursor: pointer;
  transition: all var(--transition);
}

.btn-new-session:hover {
  background: var(--bg-sidebar-hover);
  border-color: var(--primary-light);
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px;
}

.session-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 8px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background var(--transition);
}

.session-item:hover {
  background: var(--bg-sidebar-hover);
}

.session-item.active {
  background: var(--bg-sidebar-active);
}

.session-icon {
  margin-top: 1px;
  flex-shrink: 0;
  opacity: 0.7;
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-title {
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-meta {
  font-size: 11px;
  color: var(--text-sidebar-dim);
  margin-top: 2px;
}

.rename-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid var(--primary-light);
  border-radius: 4px;
  color: #fff;
  padding: 2px 6px;
  font-size: 13px;
  outline: none;
}

.empty-sessions {
  text-align: center;
  padding: 30px 16px;
  font-size: 13px;
  color: var(--text-sidebar-dim);
}

.sidebar-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.footer-btn {
  background: none;
  border: none;
  color: var(--text-sidebar-dim);
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  transition: all var(--transition);
}

.footer-btn:hover {
  color: var(--text-sidebar);
  background: var(--bg-sidebar-hover);
}

.version {
  font-size: 11px;
  color: var(--text-sidebar-dim);
}

/* Context Menu */
.context-overlay {
  position: fixed;
  inset: 0;
  z-index: 999;
}

.context-menu {
  position: fixed;
  z-index: 1000;
  background: var(--bg-chat);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-lg);
  padding: 4px;
  min-width: 120px;
}

.context-menu button {
  display: block;
  width: 100%;
  text-align: left;
  padding: 8px 12px;
  border: none;
  background: none;
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
  border-radius: 4px;
}

.context-menu button:hover {
  background: var(--bg-system);
}

.context-menu button.danger {
  color: #ef4444;
}
</style>
