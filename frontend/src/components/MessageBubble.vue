<script setup>
import { ref, computed } from 'vue'
import { renderMarkdown } from '../utils/markdown.js'

const props = defineProps({
  message: { type: Object, required: true },
})

const emit = defineEmits(['feedback', 'copy'])

const copied = ref(false)
const showActions = ref(false)

const renderedContent = computed(() => renderMarkdown(props.message.content))

const bubbleClass = computed(() => ({
  'message-bubble': true,
  'role-user': props.message.role === 'user',
  'role-assistant': props.message.role === 'assistant',
  'role-system': props.message.role === 'system',
}))

function formatTime(date) {
  if (!date) return ''
  const d = date instanceof Date ? date : new Date(date)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

async function handleCopy() {
  const ok = await navigator.clipboard.writeText(props.message.content)
  if (ok !== false) {
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
  }
  emit('copy', props.message.id)
}

function handleFeedback(type) {
  emit('feedback', props.message.id, type)
}
</script>

<template>
  <!-- System Message -->
  <div v-if="message.role === 'system'" class="message-system">
    <span>{{ message.content }}</span>
  </div>

  <!-- User or Assistant Message -->
  <div
    v-else
    :class="bubbleClass"
    @mouseenter="showActions = true"
    @mouseleave="showActions = false"
  >
    <!-- Avatar for assistant -->
    <div v-if="message.role === 'assistant'" class="avatar">
      <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
        <rect width="28" height="28" rx="8" fill="url(#avatar-grad)" />
        <circle cx="11" cy="12" r="1.5" fill="#fff" />
        <circle cx="17" cy="12" r="1.5" fill="#fff" />
        <path d="M9 18c2-3 8-3 10 0" stroke="#fff" stroke-width="1.5" stroke-linecap="round" fill="none" />
        <defs>
          <linearGradient id="avatar-grad" x1="0" y1="0" x2="28" y2="28">
            <stop stop-color="#6366f1" />
            <stop offset="1" stop-color="#a78bfa" />
          </linearGradient>
        </defs>
      </svg>
    </div>

    <!-- Bubble Content -->
    <div class="bubble-content">
      <div class="bubble-body">
        <div
          class="markdown-body"
          :class="{ 'cursor-blink': message.isStreaming }"
          v-html="renderedContent"
        ></div>
        <div v-if="message.isStreaming && !message.content" class="typing-dots">
          <span class="dot"></span><span class="dot"></span><span class="dot"></span>
        </div>
      </div>

      <!-- Actions: time, copy, feedback -->
      <div v-if="message.role === 'assistant'" class="bubble-actions" :class="{ visible: showActions }">
        <span class="action-time">{{ formatTime(message.time) }}</span>
        <span v-if="message.processingTime" class="action-time">
          · {{ (message.processingTime).toFixed(1) }}s
        </span>
        <button class="action-btn" @click="handleCopy" :title="copied ? '已复制' : '复制'">
          <svg v-if="!copied" width="14" height="14" viewBox="0 0 14 14" fill="none">
            <rect x="4" y="4" width="9" height="9" rx="1.5" stroke="currentColor" stroke-width="1.2" />
            <path d="M10 4V2.5A1.5 1.5 0 008.5 1h-5A1.5 1.5 0 002 2.5v5A1.5 1.5 0 003.5 9H4" stroke="currentColor" stroke-width="1.2" />
          </svg>
          <span v-else>✓</span>
        </button>
        <button
          class="action-btn"
          :class="{ active: message.feedback === 'up' }"
          @click="handleFeedback('up')"
          title="点赞"
        >👍
        </button>
        <button
          class="action-btn"
          :class="{ active: message.feedback === 'down' }"
          @click="handleFeedback('down')"
          title="点踩"
        >👎
        </button>
      </div>
    </div>

    <!-- Avatar placeholder for user (right side) -->
    <div v-if="message.role === 'user'" class="avatar user-avatar">
      <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
        <circle cx="14" cy="14" r="14" fill="var(--primary)" />
        <circle cx="14" cy="10" r="4" fill="#fff" />
        <path d="M6 24c0-4.4 3.6-8 8-8s8 3.6 8 8" fill="#fff" />
      </svg>
    </div>
  </div>
</template>

<style scoped>
.message-system {
  text-align: center;
  padding: 8px 0;
}

.message-system span {
  font-size: 12px;
  color: var(--text-secondary);
  background: var(--bg-system);
  padding: 4px 14px;
  border-radius: 20px;
}

.message-bubble {
  display: flex;
  gap: 10px;
  padding: 6px 0;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.role-user {
  flex-direction: row-reverse;
}

.role-user .bubble-body {
  background: var(--bg-user-bubble);
  color: var(--text-user-bubble);
  border-radius: var(--radius) var(--radius) 4px var(--radius);
}

.role-assistant .bubble-body {
  background: var(--bg-ai-bubble);
  color: var(--text-primary);
  border-radius: var(--radius) var(--radius) var(--radius) 4px;
  border-left: 3px solid var(--primary);
}

.avatar {
  flex-shrink: 0;
  margin-top: 2px;
}

.bubble-content {
  max-width: 75%;
  min-width: 60px;
}

.bubble-body {
  padding: 12px 16px;
  box-shadow: var(--shadow-sm);
}

.typing-dots {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.typing-dots .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-secondary);
  animation: pulse 1.4s infinite;
}

.typing-dots .dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dots .dot:nth-child(3) { animation-delay: 0.4s; }

.bubble-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  opacity: 0;
  transition: opacity var(--transition);
  padding-left: 4px;
}

.bubble-actions.visible {
  opacity: 1;
}

.action-time {
  font-size: 11px;
  color: var(--text-secondary);
}

.action-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 13px;
  padding: 2px 4px;
  border-radius: 4px;
  color: var(--text-secondary);
  transition: all var(--transition);
}

.action-btn:hover {
  background: var(--bg-system);
  color: var(--text-primary);
}

.action-btn.active {
  color: var(--primary);
}

@media (max-width: 640px) {
  .bubble-content {
    max-width: 85%;
  }
  .bubble-actions {
    opacity: 1;
  }
}
</style>
