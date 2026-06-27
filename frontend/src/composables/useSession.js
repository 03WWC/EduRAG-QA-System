import { ref, computed } from 'vue'

function getStorageKey() {
  const username = localStorage.getItem('eduraag_username') || 'default'
  return `eduraag_sessions_${username}`
}

/**
 * Helper: make an authenticated API call.
 */
function authFetch(path, options = {}) {
  const base = localStorage.getItem('api_base') || ''
  const token = localStorage.getItem('eduraag_token') || ''
  return fetch(`${base}${path}`, {
    ...options,
    headers: {
      ...(options.headers || {}),
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
  })
}

/**
 * Session management: CRUD + localStorage persistence.
 */
export function useSession() {
  const currentSessionId = ref(null)
  const sessions = ref(loadSessions())
  const sources = ref([])

  function loadSessions() {
    try {
      const raw = localStorage.getItem(getStorageKey())
      return raw ? JSON.parse(raw) : []
    } catch {
      return []
    }
  }

  function reloadSessions() {
    sessions.value = loadSessions()
  }

  function saveSessions() {
    localStorage.setItem(getStorageKey(), JSON.stringify(sessions.value))
  }

  /**
   * Create a new session via API, store and switch to it.
   */
  async function createSession() {
    const resp = await authFetch('/api/create_session', { method: 'POST' })
    if (!resp.ok) throw new Error('创建会话失败')
    const data = await resp.json()

    const session = {
      id: data.session_id,
      title: '新对话',
      createdAt: Date.now(),
      messageCount: 0,
    }
    sessions.value.unshift(session)
    saveSessions()
    currentSessionId.value = session.id
    return session
  }

  /**
   * Switch to an existing session.
   */
  async function switchSession(sessionId) {
    currentSessionId.value = sessionId
  }

  /**
   * Rename a session.
   */
  function renameSession(sessionId, newTitle) {
    const s = sessions.value.find((s) => s.id === sessionId)
    if (s) {
      s.title = newTitle
      saveSessions()
    }
  }

  /**
   * Delete a session.
   */
  function deleteSession(sessionId) {
    sessions.value = sessions.value.filter((s) => s.id !== sessionId)
    if (currentSessionId.value === sessionId) {
      currentSessionId.value = null
    }
    saveSessions()
    // Also clear from server
    try {
      authFetch(`/api/history/${sessionId}`, { method: 'DELETE' })
    } catch {
      // Silently ignore server clear failures
    }
  }

  /**
   * Fetch conversation history from API (authenticated).
   */
  async function fetchHistory(sessionId) {
    try {
      const resp = await authFetch(`/api/history/${sessionId}`)
      if (!resp.ok) return []
      const data = await resp.json()
      return data.history || []
    } catch (e) {
      console.error('获取历史失败:', e)
      return []
    }
  }

  /**
   * Clear history for current session on the server.
   */
  async function clearHistory(sessionId) {
    const resp = await authFetch(`/api/history/${sessionId}`, { method: 'DELETE' })
    return resp.ok
  }

  /**
   * Fetch available source filters from API.
   */
  async function fetchSources() {
    try {
      const resp = await authFetch('/api/sources')
      if (!resp.ok) return
      const data = await resp.json()
      sources.value = data.sources || []
    } catch {
      sources.value = []
    }
  }

  const currentSession = computed(() =>
    sessions.value.find((s) => s.id === currentSessionId.value) || null
  )

  return {
    currentSessionId,
    currentSession,
    sessions,
    sources,
    reloadSessions,
    createSession,
    switchSession,
    renameSession,
    deleteSession,
    saveSessions,
    fetchHistory,
    clearHistory,
    fetchSources,
  }
}
