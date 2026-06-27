import { ref, computed } from 'vue'

const STORAGE_KEY = 'eduraag_sessions'

/**
 * Session management: CRUD + localStorage persistence.
 */
export function useSession() {
  const currentSessionId = ref(null)
  const sessions = ref(loadSessions())
  const sources = ref([])

  function loadSessions() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      return raw ? JSON.parse(raw) : []
    } catch {
      return []
    }
  }

  function saveSessions() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions.value))
  }

  /**
   * Create a new session via API, store and switch to it.
   */
  async function createSession() {
    const apiBase = localStorage.getItem('api_base') || ''
    const resp = await fetch(`${apiBase}/api/create_session`, { method: 'POST' })
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
   * @param {string} sessionId
   */
  async function switchSession(sessionId) {
    currentSessionId.value = sessionId
  }

  /**
   * Rename a session.
   * @param {string} sessionId
   * @param {string} newTitle
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
   * @param {string} sessionId
   */
  function deleteSession(sessionId) {
    sessions.value = sessions.value.filter((s) => s.id !== sessionId)
    if (currentSessionId.value === sessionId) {
      currentSessionId.value = null
    }
    saveSessions()
    // Also clear from server
    try {
      const apiBase = localStorage.getItem('api_base') || ''
      fetch(`${apiBase}/api/history/${sessionId}`, { method: 'DELETE' })
    } catch {
      // Silently ignore server clear failures
    }
  }

  /**
   * Fetch conversation history from API.
   * @param {string} sessionId
   * @returns {Promise<Array>}
   */
  async function fetchHistory(sessionId) {
    const apiBase = localStorage.getItem('api_base') || ''
    const resp = await fetch(`${apiBase}/api/history/${sessionId}`)
    if (!resp.ok) return []
    const data = await resp.json()
    return data.history || []
  }

  /**
   * Clear history for current session on the server.
   * @param {string} sessionId
   */
  async function clearHistory(sessionId) {
    const apiBase = localStorage.getItem('api_base') || ''
    const resp = await fetch(`${apiBase}/api/history/${sessionId}`, { method: 'DELETE' })
    return resp.ok
  }

  /**
   * Fetch available source filters from API.
   */
  async function fetchSources() {
    try {
      const apiBase = localStorage.getItem('api_base') || ''
      const resp = await fetch(`${apiBase}/api/sources`)
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
    createSession,
    switchSession,
    renameSession,
    deleteSession,
    fetchHistory,
    clearHistory,
    fetchSources,
  }
}
