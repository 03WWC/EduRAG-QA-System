<script setup>
const emit = defineEmits(['send'])

const suggestions = [
  'AI学科有哪些课程？',
  'Java 基本数据类型有哪些？',
  '机器学习的基本流程是什么？',
  '什么是深度学习的反向传播？',
]
</script>

<template>
  <div class="welcome">
    <div class="welcome-icon">
      <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
        <rect width="56" height="56" rx="16" fill="url(#w-grad)" />
        <path d="M16 36V20l12 8-12 8z" fill="#fff" />
        <path d="M28 36V20l12 8-12 8z" fill="rgba(255,255,255,0.7)" />
        <defs>
          <linearGradient id="w-grad" x1="0" y1="0" x2="56" y2="56">
            <stop stop-color="#6366f1" />
            <stop offset="1" stop-color="#a78bfa" />
          </linearGradient>
        </defs>
      </svg>
    </div>
    <h1 class="welcome-title">你好，我是黑马程序员</h1>
    <p class="welcome-desc">
      你的智能学习助手，基于 RAG + 知识库检索，<br />
      为你解答 IT 教育相关问题
    </p>
    <div class="suggestions">
      <button
        v-for="(q, i) in suggestions"
        :key="i"
        class="suggestion-card"
        @click="$emit('send', q)"
      >
        <span class="s-icon">💡</span>
        <span>{{ q }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 40px 20px;
  text-align: center;
}

.welcome-icon {
  margin-bottom: 20px;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

.welcome-title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 8px;
  background: linear-gradient(135deg, #6366f1, #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-desc {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 28px;
}

.suggestions {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  max-width: 500px;
  width: 100%;
}

.suggestion-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--bg-chat);
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition);
  text-align: left;
  box-shadow: var(--shadow-sm);
}

.suggestion-card:hover {
  border-color: var(--primary-light);
  box-shadow: var(--shadow);
  transform: translateY(-1px);
}

.s-icon {
  flex-shrink: 0;
  font-size: 16px;
}

@media (max-width: 640px) {
  .suggestions {
    grid-template-columns: 1fr;
  }
}
</style>
