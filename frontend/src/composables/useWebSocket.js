import { ref, onMounted, onUnmounted } from 'vue'

let instance = null

/**
 * Singleton WebSocket manager for streaming chat.
 * @param {object} options
 * @param {function} options.onToken - Called with each token string
 * @param {function} options.onStart - Called when streaming starts {session_id}
 * @param {function} options.onEnd - Called when streaming ends {session_id, processing_time}
 * @param {function} options.onError - Called on error {error}
 * @param {function} options.onStatusChange - Called when connection status changes (connected|disconnected|reconnecting)
 */
export function useWebSocket(options = {}) {
  if (instance) return instance

  const ws = ref(null)
  const connected = ref(false)
  const reconnecting = ref(false)
  let retryCount = 0
  const maxRetries = 5
  let retryTimer = null
  let heartbeatTimer = null
  const pendingMessages = []

  function getWsUrl() {
    const apiBase = localStorage.getItem('api_base') || ''
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = apiBase ? apiBase.replace(/^https?:\/\//, '') : location.host
    return `${protocol}//${host}/api/stream`
  }

  function connect() {
    if (ws.value && (ws.value.readyState === WebSocket.OPEN || ws.value.readyState === WebSocket.CONNECTING)) {
      return
    }

    try {
      ws.value = new WebSocket(getWsUrl())
    } catch (e) {
      scheduleReconnect()
      return
    }

    ws.value.onopen = () => {
      connected.value = true
      reconnecting.value = false
      retryCount = 0

      if (options.onStatusChange) options.onStatusChange('connected')

      // Start heartbeat
      heartbeatTimer = setInterval(() => {
        if (ws.value?.readyState === WebSocket.OPEN) {
          ws.value.send(JSON.stringify({ type: 'ping' }))
        }
      }, 30000)

      // Flush pending messages
      while (pendingMessages.length > 0) {
        const msg = pendingMessages.shift()
        ws.value.send(JSON.stringify(msg))
      }
    }

    ws.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        switch (data.type) {
          case 'start':
            if (options.onStart) options.onStart(data)
            break
          case 'token':
            if (options.onToken) options.onToken(data.token, data)
            break
          case 'end':
            if (options.onEnd) options.onEnd(data)
            break
          case 'error':
            if (options.onError) options.onError(data.error)
            break
        }
      } catch {
        // Non-JSON message (e.g. pong), ignore
      }
    }

    ws.value.onclose = (event) => {
      connected.value = false
      if (heartbeatTimer) clearInterval(heartbeatTimer)

      if (!event.wasClean && retryCount < maxRetries) {
        scheduleReconnect()
      } else if (!event.wasClean) {
        if (options.onStatusChange) options.onStatusChange('disconnected')
      }
    }

    ws.value.onerror = () => {
      // onclose will fire after this
    }
  }

  function scheduleReconnect() {
    if (reconnecting.value) return
    reconnecting.value = true
    if (options.onStatusChange) options.onStatusChange('reconnecting')

    const delay = Math.min(1000 * Math.pow(2, retryCount), 16000)
    retryCount++

    retryTimer = setTimeout(() => {
      connect()
    }, delay)
  }

  function send(data) {
    if (ws.value?.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify(data))
    } else {
      pendingMessages.push(data)
      if (!ws.value || ws.value.readyState === WebSocket.CLOSED) {
        connect()
      }
    }
  }

  function disconnect() {
    if (retryTimer) clearTimeout(retryTimer)
    if (heartbeatTimer) clearInterval(heartbeatTimer)
    retryCount = maxRetries // prevent reconnect
    if (ws.value) {
      ws.value.close(1000, 'User disconnect')
      ws.value = null
    }
    connected.value = false
    reconnecting.value = false
  }

  // Auto-connect
  connect()

  // Cleanup on unmount only if this was the creator
  onUnmounted(() => {
    disconnect()
    instance = null
  })

  instance = { send, disconnect, connected, reconnecting }
  return instance
}
