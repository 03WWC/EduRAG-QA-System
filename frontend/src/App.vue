<script setup>
import { ref, onMounted, computed } from 'vue'
import Sidebar from './components/Sidebar.vue'
import ChatView from './components/ChatView.vue'
import LoginView from './components/LoginView.vue'
import AdminPanel from './components/AdminPanel.vue'
import SettingsModal from './components/SettingsModal.vue'
import { useChat } from './composables/useChat.js'
import { useSession } from './composables/useSession.js'

// Auth state
const isLoggedIn = ref(false)
const username = ref('')
const userRole = ref('')
const showAdmin = ref(false)

// Check existing token on mount
function checkLogin() {
  const token = localStorage.getItem('eduraag_token')
  if (token) {
    isLoggedIn.value = true
    username.value = localStorage.getItem('eduraag_username') || ''
    userRole.value = localStorage.getItem('eduraag_role') || 'user'
  }
}
checkLogin()

function handleLoginSuccess(data) {
  isLoggedIn.value = true
  username.value = data.username
  userRole.value = data.role
  initApp()
}

function handleLogout() {
  localStorage.removeItem('eduraag_token')
  localStorage.removeItem('eduraag_username')
  localStorage.removeItem('eduraag_role')
  isLoggedIn.value = false
  username.value = ''
  userRole.value = ''
  showAdmin.value = false
  location.reload()
}

const isAdmin = computed(() => userRole.value === 'admin')

const {
  messages,
  isStreaming,
  wsConnected,
  wsStatus,
  sendMessage,
  loadHistory,
  clearMessages,
  setFeedback,
} = useChat()

const {
  currentSessionId,
  currentSession,
  sessions,
  sources,
  createSession,
  switchSession,
  renameSession,
  deleteSession,
  fetchHistory,
  clearHistory,
  fetchSources,
} = useSession()

const showSettings = ref(false)
const sidebarOpen = ref(window.innerWidth > 768)
const isMobile = ref(window.innerWidth <= 768)
const appReady = ref(false)

async function initApp() {
  const theme = localStorage.getItem('eduraag_theme')
  if (theme === 'dark') {
    document.documentElement.classList.add('dark')
  }

  await fetchSources()

  if (sessions.value.length === 0) {
    await handleNewSession()
  } else {
    const lastId = sessions.value[0].id
    await handleSwitchSession(lastId)
  }

  appReady.value = true
  window.addEventListener('keydown', onGlobalKeydown)
  window.addEventListener('resize', onResize)
}

onMounted(() => {
  if (isLoggedIn.value) {
    initApp()
  }
})

function onResize() {
  isMobile.value = window.innerWidth <= 768
  if (!isMobile.value) sidebarOpen.value = true
}

function onGlobalKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
    e.preventDefault()
    handleNewSession()
  }
}

async function handleNewSession() {
  await createSession()
  clearMessages()
}

async function handleSwitchSession(sessionId) {
  await switchSession(sessionId)
  const history = await fetchHistory(sessionId)
  loadHistory(history)
  if (isMobile.value) sidebarOpen.value = false
}

async function handleDeleteSession(sessionId) {
  deleteSession(sessionId)
  if (sessions.value.length > 0) {
    await handleSwitchSession(sessions.value[0].id)
  } else {
    await handleNewSession()
  }
}

async function handleClearHistory() {
  if (!currentSessionId.value) return
  await clearHistory(currentSessionId.value)
  clearMessages()
  const s = sessions.value.find((s) => s.id === currentSessionId.value)
  if (s) s.messageCount = 0
}

function handleSend(query, sourceFilter) {
  sendMessage(query, sourceFilter, currentSessionId.value)
  const s = sessions.value.find((s) => s.id === currentSessionId.value)
  if (s) {
    s.messageCount = (s.messageCount || 0) + 1
    if (s.title === '新对话') {
      s.title = query.slice(0, 20) + (query.length > 20 ? '...' : '')
    }
    s.createdAt = Date.now()
    sessions.value.sort((a, b) => b.createdAt - a.createdAt)
  }
}

function handleRenameSession(sessionId, newTitle) {
  renameSession(sessionId, newTitle)
}
</script>

<template>
  <!-- Login Page -->
  <LoginView v-if="!isLoggedIn" @login-success="handleLoginSuccess" />

  <!-- Main App -->
  <div v-else-if="appReady" style="height:100vh">
    <!-- Admin Panel (full screen overlay) -->
    <div v-if="showAdmin" class="admin-overlay">
      <AdminPanel @close="showAdmin = false" />
    </div>

    <div v-else class="app-layout">
      <!-- Sidebar -->
      <div class="sidebar-container" :class="{ open: sidebarOpen }">
        <Sidebar
          :sessions="sessions"
          :current-session-id="currentSessionId"
          @new-session="handleNewSession"
          @switch-session="handleSwitchSession"
          @rename-session="handleRenameSession"
          @delete-session="handleDeleteSession"
          @toggle-settings="showSettings = true"
        />
      </div>

      <button v-if="!sidebarOpen" class="sidebar-toggle" @click="sidebarOpen = true">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M3 5h14M3 10h14M3 15h14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
        </svg>
      </button>

      <!-- Chat Area -->
      <div class="chat-wrapper">
        <!-- Top bar with user info + admin entry -->
        <div class="user-bar">
          <span class="user-tag" :class="{ admin: isAdmin }">{{ username }}{{ isAdmin ? ' [管理员]' : '' }}</span>
          <div>
            <button v-if="isAdmin" class="bar-btn admin-btn" @click="showAdmin = true">⚙️ 管理</button>
            <button class="bar-btn logout-btn" @click="handleLogout">退出</button>
          </div>
        </div>
        <ChatView
          :messages="messages"
          :is-streaming="isStreaming"
          :ws-connected="wsConnected"
          :sources="sources"
          @send="handleSend"
          @feedback="setFeedback"
          @clear-history="handleClearHistory"
        />
      </div>

      <SettingsModal v-if="showSettings" @close="showSettings = false" />
      <div v-if="sidebarOpen && isMobile" class="sidebar-overlay" @click="sidebarOpen = false"></div>
    </div>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  position: relative;
}

.admin-overlay {
  height: 100vh;
  overflow-y: auto;
  background: var(--bg-chat, #fff);
}

.chat-wrapper {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.user-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  border-bottom: 1px solid var(--border, #e2e8f0);
  background: var(--bg-main, #f8fafc);
}

.user-tag {
  font-size: 13px;
  color: var(--text-primary, #1e293b);
}

.user-tag.admin {
  color: #4338ca;
  font-weight: 600;
}

.bar-btn {
  font-size: 12px;
  padding: 4px 10px;
  border: 1px solid var(--border, #e2e8f0);
  border-radius: 6px;
  background: var(--bg-chat, #fff);
  color: var(--text-primary, #1e293b);
  cursor: pointer;
  margin-left: 8px;
  transition: all 0.2s;
}

.bar-btn:hover {
  background: var(--bg-system, #e2e8f0);
}

.admin-btn {
  background: #e0e7ff;
  border-color: #c7d2fe;
  color: #4338ca;
}

.logout-btn {
  color: var(--text-secondary, #64748b);
}

.sidebar-container {
  position: relative;
  z-index: 100;
  flex-shrink: 0;
}

.sidebar-toggle {
  position: fixed;
  top: 12px;
  left: 12px;
  z-index: 100;
  width: 38px;
  height: 38px;
  border-radius: 8px;
  border: 1px solid var(--border, #e2e8f0);
  background: var(--bg-chat, #fff);
  color: var(--text-primary, #1e293b);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow, 0 4px 24px rgba(0,0,0,0.08));
}

.sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 90;
}

@media (max-width: 768px) {
  .sidebar-container {
    position: fixed;
    left: -280px;
    top: 0;
    bottom: 0;
    transition: left 0.3s ease;
  }
  .sidebar-container.open {
    left: 0;
  }
}
</style>
