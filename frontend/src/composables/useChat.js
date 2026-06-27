import { reactive, ref } from 'vue'
import { useWebSocket } from './useWebSocket.js'

/**
 * Core chat logic: messages, sending, streaming.
 */
export function useChat() {
  const messages = ref([])
  const isStreaming = ref(false)
  const currentStreamContent = ref('')
  const wsConnected = ref(false)
  const wsStatus = ref('connecting') // 'connecting' | 'connected' | 'disconnected' | 'reconnecting'
  let messageIdCounter = 0
  let sessionId = null

  const ws = useWebSocket({
    onStart(data) {
      sessionId = data.session_id || sessionId
      isStreaming.value = true
      currentStreamContent.value = ''
      // Add empty assistant message to fill with tokens
      const msg = {
        id: ++messageIdCounter,
        role: 'assistant',
        content: '',
        time: new Date(),
        isStreaming: true,
        feedback: null,
      }
      messages.value.push(msg)
    },
    onToken(token) {
      currentStreamContent.value += token
      // Update the last message in place
      const last = messages.value[messages.value.length - 1]
      if (last && last.isStreaming) {
        last.content = currentStreamContent.value
      }
    },
    onEnd(data) {
      const last = messages.value[messages.value.length - 1]
      if (last && last.isStreaming) {
        last.isStreaming = false
        last.processingTime = data.processing_time
        last.sessionId = data.session_id
      }
      isStreaming.value = false
      currentStreamContent.value = ''
    },
    onError(error) {
      const last = messages.value[messages.value.length - 1]
      if (last && last.isStreaming) {
        last.isStreaming = false
        last.content += `\n\n❌ 错误: ${error}`
      }
      isStreaming.value = false
      currentStreamContent.value = ''
    },
    onStatusChange(status) {
      wsStatus.value = status
      wsConnected.value = status === 'connected'
    },
  })

  /**
   * Send a user message and initiate streaming response.
   * @param {string} query
   * @param {string} sourceFilter
   * @param {string} sid - session ID
   */
  function sendMessage(query, sourceFilter = '', sid) {
    if (isStreaming.value || !query.trim()) return

    sessionId = sid || sessionId

    // Add user message
    messages.value.push({
      id: ++messageIdCounter,
      role: 'user',
      content: query.trim(),
      time: new Date(),
    })

    // Send via WebSocket
    ws.send({
      query: query.trim(),
      source_filter: sourceFilter || null,
      session_id: sessionId,
    })
  }

  /**
   * Load historical messages into the chat view.
   * @param {Array} history - Array of {question, answer} objects
   */
  function loadHistory(history) {
    messages.value = []
    messageIdCounter = 0
    if (!history || !Array.isArray(history)) return
    for (const entry of history) {
      messages.value.push({
        id: ++messageIdCounter,
        role: 'user',
        content: entry.question,
        time: new Date(),
      })
      messages.value.push({
        id: ++messageIdCounter,
        role: 'assistant',
        content: entry.answer,
        time: new Date(),
        feedback: null,
      })
    }
  }

  function clearMessages() {
    messages.value = []
    messageIdCounter = 0
  }

  /**
   * Toggle feedback (like/dislike) on an assistant message.
   * @param {number} msgId
   * @param {'up'|'down'} type
   */
  function setFeedback(msgId, type) {
    const msg = messages.value.find((m) => m.id === msgId)
    if (msg) {
      msg.feedback = msg.feedback === type ? null : type
    }
  }

  /**
   * Copy a message's content to clipboard.
   * @param {string} content
   * @returns {Promise<boolean>}
   */
  async function copyContent(content) {
    try {
      await navigator.clipboard.writeText(content)
      return true
    } catch {
      return false
    }
  }

  function reconnectWs() {
    ws.reconnect()
  }

  return {
    messages,
    isStreaming,
    currentStreamContent,
    wsConnected,
    wsStatus,
    sendMessage,
    loadHistory,
    clearMessages,
    setFeedback,
    copyContent,
    reconnectWs,
  }
}
