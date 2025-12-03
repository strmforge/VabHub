<template>
  <div class="markdown-content" v-html="renderedContent"></div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  payload: { content: string }
  config?: Record<string, any>
}>()

// 简单的 Markdown 渲染（只支持基本语法）
const renderedContent = computed(() => {
  const content = props.payload?.content || ''
  
  return content
    // 标题
    .replace(/^### (.*$)/gm, '<h4>$1</h4>')
    .replace(/^## (.*$)/gm, '<h3>$1</h3>')
    .replace(/^# (.*$)/gm, '<h2>$1</h2>')
    // 粗体和斜体
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // 行内代码
    .replace(/`(.+?)`/g, '<code>$1</code>')
    // 链接
    .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank">$1</a>')
    // 换行
    .replace(/\n/g, '<br>')
})
</script>

<style scoped>
.markdown-content {
  line-height: 1.6;
}

.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4) {
  margin-top: 1em;
  margin-bottom: 0.5em;
}

.markdown-content :deep(code) {
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', 'Consolas', monospace;
  font-size: 0.9em;
}

.markdown-content :deep(a) {
  color: rgb(var(--v-theme-primary));
}
</style>
