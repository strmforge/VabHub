<template>
  <div v-if="error" class="error-handler">
    <v-alert
      :type="errorType"
      :title="errorTitle"
      :text="errorMessage"
      closable
      @click:close="dismiss"
      class="mb-4"
    >
      <template v-if="errorCode">
        <div class="error-code">错误代码: {{ errorCode }}</div>
      </template>
      <template v-if="errorDetails">
        <div class="error-details mt-2">
          <details>
            <summary>详细信息</summary>
            <pre>{{ errorDetails }}</pre>
          </details>
        </div>
      </template>
      <template v-slot:append>
        <v-btn
          v-if="showRetry"
          color="primary"
          variant="text"
          size="small"
          @click="retry"
        >
          重试
        </v-btn>
      </template>
    </v-alert>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  error: Error | null
  showRetry?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showRetry: true
})

const emit = defineEmits<{
  retry: []
  dismiss: []
}>()

const errorType = computed(() => {
  if (!props.error) return 'error'
  
  // 根据错误类型确定提示类型
  if (props.error.message?.includes('网络') || props.error.message?.includes('连接')) {
    return 'warning'
  }
  if (props.error.message?.includes('权限') || props.error.message?.includes('认证')) {
    return 'warning'
  }
  return 'error'
})

const errorTitle = computed(() => {
  if (!props.error) return '错误'
  
  if (props.error.message?.includes('网络') || props.error.message?.includes('连接')) {
    return '网络错误'
  }
  if (props.error.message?.includes('权限') || props.error.message?.includes('认证')) {
    return '权限错误'
  }
  if (props.error.message?.includes('超时')) {
    return '请求超时'
  }
  return '发生错误'
})

const errorMessage = computed(() => {
  if (!props.error) return '发生未知错误'
  
  // 提取用户友好的错误消息
  const message = props.error.message || '发生未知错误'
  
  // 处理常见的错误消息
  if (message.includes('网络连接失败')) {
    return '网络连接失败，请检查网络设置'
  }
  if (message.includes('请求超时')) {
    return '请求超时，请稍后重试'
  }
  if (message.includes('权限') || message.includes('认证')) {
    return '您没有权限执行此操作，请重新登录'
  }
  if (message.includes('服务器错误')) {
    return '服务器错误，请稍后重试'
  }
  
  return message
})

const errorCode = computed(() => {
  if (!props.error) return null
  
  // 从错误对象中提取错误代码
  const errorAny = props.error as any
  return errorAny.code || errorAny.errorCode || null
})

const errorDetails = computed(() => {
  if (!props.error) return null
  
  // 只在开发环境显示详细信息
  if (import.meta.env.DEV) {
    return JSON.stringify(props.error, null, 2)
  }
  return null
})

const retry = () => {
  emit('retry')
}

const dismiss = () => {
  emit('dismiss')
}
</script>

<style scoped>
.error-handler {
  width: 100%;
}

.error-code {
  font-size: 0.875rem;
  color: rgba(0, 0, 0, 0.6);
  margin-top: 0.5rem;
}

.error-details {
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.6);
}

.error-details pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
}
</style>

