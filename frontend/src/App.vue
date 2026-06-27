<script setup>
import { ref, onMounted } from 'vue'
import Sidebar from './components/Sidebar.vue'
import ChatView from './components/ChatView.vue'
import SettingsModal from './components/SettingsModal.vue'
import { useChat } from './composables/useChat.js'
import { useSession } from './composables/useSession.js'

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

// Init
onMounted(async () => {
  // Load theme
  const theme = localStorage.getItem('eduraag_theme')
  if (theme === 'dark') {
    document.documentElement.classList.add('dark')
  }

  // Fetch sources
  await fetchSources()

  // Create initial session
  if (sessions.value.length === 0) {
    await handleNewSession()
  } else {
    // Restore last session
    const lastId = sessions.value[0].id
    await handleSwitchSession(lastId)
  }

  // Keyboard shortcuts
  window.addEventListener('keydown', onGlobalKeydown)
  window.addEventListener('resize', onResize)
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

// Session handlers
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
  // Update session message count
  const s = sessions.value.find((s) => s.id === currentSessionId.value)
  if (s) s.messageCount = 0
}

// Chat handlers
function handleSend(query, sourceFilter) {
  sendMessage(query, sourceFilter, currentSessionId.value)
  // Update session
  const s = sessions.value.find((s) => s.id === currentSessionId.value)
  if (s) {
    s.messageCount = (s.messageCount || 0) + 1
    // Use first ~20 chars as title if still default
    if (s.title === '新对话') {
      s.title = query.slice(0, 20) + (query.length > 20 ? '...' : '')
    }
    s.createdAt = Date.now()
    // Re-sort
    sessions.value.sort((a, b) => b.createdAt - a.createdAt)
  }
}

function handleRenameSession(sessionId, newTitle) {
  renameSession(sessionId, newTitle)
}
</script>

<template>
  <div class="app-layout">
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

    <!-- Mobile sidebar toggle -->
    <button v-if="!sidebarOpen" class="sidebar-toggle" @click="sidebarOpen = true">
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M3 5h14M3 10h14M3 15h14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
      </svg>
    </button>

    <!-- Chat Area -->
    <div class="chat-wrapper">
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

    <!-- Settings Modal -->
    <SettingsModal v-if="showSettings" @close="showSettings = false" />

    <!-- Mobile sidebar overlay -->
    <div v-if="sidebarOpen && isMobile" class="sidebar-overlay" @click="sidebarOpen = false"></div>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  position: relative;
}

.chat-wrapper {
  flex: 1;
  min-width: 0;
  overflow: hidden;
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
  border: 1px solid var(--border);
  background: var(--bg-chat);
  color: var(--text-primary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow);
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
