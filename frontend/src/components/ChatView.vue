<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import MessageBubble from './MessageBubble.vue'
import WelcomeScreen from './WelcomeScreen.vue'
import TypingIndicator from './TypingIndicator.vue'

const props = defineProps({
  messages: { type: Array, required: true },
  isStreaming: { type: Boolean, default: false },
  wsConnected: { type: Boolean, default: false },
  sources: { type: Array, default: () => [] },
})

const emit = defineEmits([
  'send',
  'feedback',
  'copy',
  'clear-history',
])

const chatRef = ref(null)
const selectedSource = ref('')
const inputText = ref('')
const userHasScrolled = ref(false)

// Auto-scroll to bottom on new messages, unless user scrolled up
watch(
  () => props.messages.length,
  () => {
    if (!userHasScrolled.value) {
      scrollToBottom()
    }
  }
)

watch(
  () => props.isStreaming,
  (val) => {
    if (val) {
      userHasScrolled.value = false
      scrollToBottom()
    }
  }
)

function scrollToBottom() {
  nextTick(() => {
    if (chatRef.value) {
      chatRef.value.scrollTop = chatRef.value.scrollHeight
    }
  })
}

function onScroll() {
  if (!chatRef.value) return
  const { scrollTop, scrollHeight, clientHeight } = chatRef.value
  userHasScrolled.value = scrollHeight - scrollTop - clientHeight > 80
}

function handleSend() {
  const text = inputText.value.trim()
  if (!text || props.isStreaming) return
  emit('send', text, selectedSource.value)
  inputText.value = ''
  userHasScrolled.value = false
}

function handleSuggestion(q) {
  inputText.value = q
  handleSend()
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

const statusText = computed(() => {
  if (props.wsConnected) return null
  return 'disconnected'
})

const showWelcome = computed(() => props.messages.length === 0)
</script>

<template>
  <div class="chat-view">
    <!-- Top Bar -->
    <header class="chat-header">
      <div class="header-left">
        <h2 class="header-title">对话</h2>
        <span v-if="statusText === 'disconnected'" class="status-badge disconnected">
          ⚠️ 连接断开
        </span>
        <span v-else-if="statusText === 'reconnecting'" class="status-badge reconnecting">
          🔄 重连中...
        </span>
      </div>
      <div class="header-right">
        <!-- Source Filter -->
        <select v-model="selectedSource" class="source-select">
          <option value="">全部学科</option>
          <option v-for="src in sources" :key="src" :value="src">{{ src }}</option>
        </select>
        <!-- Clear History -->
        <button class="header-btn" @click="$emit('clear-history')" title="清除历史">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M3 4h10l-.8 9.6a1.5 1.5 0 01-1.5 1.4H5.3a1.5 1.5 0 01-1.5-1.4L3 4z" stroke="currentColor" stroke-width="1.2" />
            <path d="M6 4V2.5A1.5 1.5 0 017.5 1h1A1.5 1.5 0 0110 2.5V4" stroke="currentColor" stroke-width="1.2" />
          </svg>
        </button>
      </div>
    </header>

    <!-- Messages Area -->
    <div class="messages-area" ref="chatRef" @scroll="onScroll">
      <WelcomeScreen v-if="showWelcome" @send="handleSuggestion" />

      <template v-else>
        <MessageBubble
          v-for="msg in messages"
          :key="msg.id"
          :message="msg"
          @feedback="(id, type) => $emit('feedback', id, type)"
          @copy="(id) => $emit('copy', id)"
        />
        <TypingIndicator v-if="isStreaming" />
      </template>
    </div>

    <!-- Input Area -->
    <div class="input-area">
      <div class="input-wrapper">
        <textarea
          v-model="inputText"
          class="chat-input"
          placeholder="输入你的问题... (Enter 发送, Shift+Enter 换行)"
          rows="1"
          @keydown="onKeydown"
          :disabled="isStreaming"
        ></textarea>
        <button
          class="send-btn"
          @click="handleSend"
          :disabled="isStreaming || !inputText.trim()"
          :class="{ streaming: isStreaming }"
        >
          <svg v-if="!isStreaming" width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M3 17L19 10L3 3L5 10L3 17Z" fill="currentColor" />
          </svg>
          <span v-else class="stop-icon">■</span>
        </button>
      </div>
      <p class="input-hint">
        {{ wsConnected ? '已连接 · Enter 发送' : '未连接 · 请检查后端服务' }}
      </p>
    </div>
  </div>
</template>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-chat);
  transition: background var(--transition);
}

/* Header */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
}

.status-badge {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 10px;
  font-weight: 500;
}

.status-badge.disconnected {
  background: #fef2f2;
  color: #dc2626;
}

.status-badge.reconnecting {
  background: #fffbeb;
  color: #d97706;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.source-select {
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-input);
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
  cursor: pointer;
}

.source-select:focus {
  border-color: var(--primary);
}

.header-btn {
  background: none;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 6px 8px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all var(--transition);
}

.header-btn:hover {
  background: var(--bg-system);
  color: #ef4444;
}

/* Messages */
.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
  scroll-behavior: smooth;
}

/* Input */
.input-area {
  padding: 12px 20px 16px;
  border-top: 1px solid var(--border);
  background: var(--bg-input);
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: var(--bg-chat);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 10px 14px;
  box-shadow: var(--shadow-sm);
  transition: border var(--transition);
}

.input-wrapper:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.chat-input {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  font-size: 14px;
  line-height: 1.5;
  background: transparent;
  color: var(--text-primary);
  font-family: inherit;
  max-height: 120px;
}

.chat-input::placeholder {
  color: var(--text-secondary);
}

.send-btn {
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: none;
  background: var(--primary);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition);
}

.send-btn:hover:not(:disabled) {
  background: var(--primary-dark);
  transform: scale(1.05);
}

.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.send-btn.streaming {
  background: #ef4444;
}

.stop-icon {
  font-size: 10px;
}

.input-hint {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 6px;
  text-align: center;
}

@media (max-width: 640px) {
  .chat-header {
    padding: 10px 14px;
  }
  .messages-area {
    padding: 12px 14px;
  }
  .input-area {
    padding: 10px 14px 14px;
  }
}
</style>
