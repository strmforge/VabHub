<template>
  <div class="graphql-explorer">
    <PageHeader
      title="GraphQL 实验室"
      subtitle="用预设示例快速调试 /graphql 查询"
    />

    <v-row class="mt-4" dense>
      <v-col cols="12" md="3">
        <v-card>
          <v-card-title class="text-subtitle-1">预设查询</v-card-title>
          <v-divider />
          <v-list density="compact" nav>
            <v-list-item
              v-for="preset in presets"
              :key="preset.id"
              :title="preset.title"
              :subtitle="preset.description"
              @click="applyPreset(preset)"
              :active="activePreset === preset.id"
            >
              <template #prepend>
                <v-icon :color="preset.color || 'primary'">{{ preset.icon }}</v-icon>
              </template>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>

      <v-col cols="12" md="4">
        <v-card class="fill-height">
<v-card-title class="text-subtitle-1 d-flex align-center justify-space-between">
  <span>GraphQL Query</span>
  <div class="d-flex ga-2">
    <v-btn
      size="small"
      variant="text"
      icon="mdi-content-copy"
      @click="copyText(currentQuery, 'Query')"
      :disabled="!currentQuery"
    />
    <v-btn
      size="small"
      variant="text"
      icon="mdi-code-json"
      @click="copyText(currentVariables, 'Variables')"
      :disabled="!currentVariables"
    />
  </div>
</v-card-title>
          <v-divider />
          <v-card-text class="pa-0">
            <v-textarea
              v-model="currentQuery"
              class="query-editor"
              auto-grow
              variant="outlined"
              rows="12"
              hide-details
            />
            <v-textarea
              v-model="currentVariables"
              label="Variables (JSON)"
              auto-grow
              variant="outlined"
              rows="4"
              hide-details
              class="variables-editor"
            />
          </v-card-text>
          <v-card-actions>
            <v-btn
              color="primary"
              prepend-icon="mdi-play"
              :loading="loading"
              @click="executeQuery"
            >
              执行查询
            </v-btn>
            <v-spacer />
            <v-btn variant="text" prepend-icon="mdi-delete" @click="resetResult">
              清空结果
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <v-col cols="12" md="5">
        <v-card class="fill-height">
          <v-card-title class="text-subtitle-1">
            响应结果
            <v-chip size="small" class="ms-2" variant="outlined">
              {{ lastStatus }}
            </v-chip>
          </v-card-title>
          <v-divider />
<v-card-text class="result-viewer">
  <v-alert
    v-if="errorMessages.length"
    type="error"
    variant="tonal"
    density="compact"
    class="mb-3"
  >
    <div v-for="(msg, idx) in errorMessages" :key="idx">
      {{ msg }}
    </div>
  </v-alert>
  <pre>{{ formattedResult }}</pre>
</v-card-text>
<v-card-actions>
  <v-spacer />
  <v-btn
    variant="text"
    prepend-icon="mdi-content-copy"
    :disabled="!result"
    @click="copyText(formattedResult, 'Result')"
  >
    复制结果
  </v-btn>
</v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useToast } from 'vue-toastification'
import PageHeader from '@/components/common/PageHeader.vue'
import api from '@/services/api'

interface PresetQuery {
  id: string
  title: string
  description: string
  query: string
  variables?: Record<string, any>
  icon: string
  color?: string
}

const toast = useToast()
const loading = ref(false)
const activePreset = ref<string | null>(null)
const currentQuery = ref('')
const currentVariables = ref('{}')
const result = ref<Record<string, any> | null>(null)
const lastStatus = ref('待执行')
const lastErrors = ref<string[]>([])

const presets: PresetQuery[] = [
  {
    id: 'musicSubscriptions',
    title: '音乐订阅列表',
    description: '最近创建的音乐订阅',
    icon: 'mdi-music',
    color: 'purple',
    query: `
query MusicSubscriptions($limit: Int!) {
  musicSubscriptions(limit: $limit) {
    id
    name
    platform
    status
    subscriptionId
    createdAt
  }
}
    `.trim(),
    variables: {
      limit: 5
    }
  },
  {
    id: 'musicCharts',
    title: '音乐榜单历史',
    description: 'GraphQL 方式获取音乐榜单',
    icon: 'mdi-chart-line',
    color: 'primary',
    query: `
query MusicCharts($platform: String, $chartType: String) {
  musicCharts(platform: $platform, chartType: $chartType, batches: 1) {
    batchId
    capturedAt
    platform
    chartType
    entries {
      rank
      title
      artist
    }
  }
}
    `.trim(),
    variables: {
      platform: 'qq_music',
      chartType: 'hot'
    }
  },
  {
    id: 'dashboard',
    title: '订阅 / 下载概览',
    description: '综合查询订阅 + 下载任务',
    icon: 'mdi-view-dashboard',
    query: `
query CombinedData($page: Int!, $pageSize: Int!, $mediaType: String) {
  dashboardStats {
    totalSubscriptions
    activeDownloads
    musicSubscriptions
    hnrRisks
  }
  subscriptions(page: $page, pageSize: $pageSize, mediaType: $mediaType) {
    total
    items {
      id
      title
      mediaType
      status
    }
  }
  downloadTasks(limit: 5) {
    id
    title
    status
    progress
  }
}
    `.trim(),
    variables: {
      page: 1,
      pageSize: 5,
      mediaType: 'music'
    }
  }
  ,
  {
    id: 'rsshubHealth',
    title: 'RSSHub 健康',
    description: '查看需要人工处理的 RSSHub 订阅',
    icon: 'mdi-rss',
    color: 'orange',
    query: `
query RSSHubHealth($limit: Int!) {
  rsshubSubscriptionHealth(limit: $limit) {
    userId
    username
    targetType
    targetName
    healthStatus
    lastErrorCode
    lastErrorMessage
    lastErrorAt
  }
}
    `.trim(),
    variables: {
      limit: 10
    }
  },
  {
    id: 'schedulerTasks',
    title: '调度任务',
    description: '最近更新的调度任务状态',
    icon: 'mdi-timer-cog',
    color: 'teal',
    query: `
query SchedulerTasks($limit: Int!) {
  schedulerTasks(limit: $limit) {
    jobId
    name
    taskType
    status
    triggerType
    nextRunTime
    lastRunTime
    enabled
  }
}
    `.trim(),
    variables: {
      limit: 10
    }
  }
]

const formattedResult = computed(() => {
  if (!result.value) {
    return '等待执行...'
  }
  return JSON.stringify(result.value, null, 2)
})

const errorMessages = computed(() => lastErrors.value)

const applyPreset = (preset: PresetQuery) => {
  activePreset.value = preset.id
  currentQuery.value = preset.query
  currentVariables.value = JSON.stringify(preset.variables ?? {}, null, 2)
  result.value = null
  lastStatus.value = '待执行'
  lastErrors.value = []
}

const resetResult = () => {
  result.value = null
  lastStatus.value = '待执行'
  lastErrors.value = []
}

const executeQuery = async () => {
  loading.value = true
  try {
    let variables: Record<string, any> | undefined
    if (currentVariables.value.trim()) {
      try {
        variables = JSON.parse(currentVariables.value)
      } catch (error) {
        toast.error('Variables 需要是合法的 JSON 格式')
        loading.value = false
        return
      }
    }

    const response = await api.post('/graphql', {
      query: currentQuery.value,
      variables
    })
    const payload = response.data || {}
    if (payload.errors && payload.errors.length) {
      lastErrors.value = payload.errors.map((err: any) => err.message || '未知错误')
      result.value = payload.data || null
      lastStatus.value = '失败'
      toast.error('GraphQL 查询返回错误')
      return
    }
    lastErrors.value = []
    result.value = payload.data || {}
    lastStatus.value = '完成'
  } catch (error: any) {
    lastStatus.value = '失败'
    lastErrors.value = [error.message || 'GraphQL 查询失败']
    toast.error(error.message || 'GraphQL 查询失败')
  } finally {
    loading.value = false
  }
}

const copyText = async (value: string | Record<string, any> | null, label: string) => {
  const text = typeof value === 'string' ? value : JSON.stringify(value, null, 2)
  try {
    await navigator.clipboard.writeText(text || '')
    toast.success(`${label} 已复制`)
  } catch (error) {
    toast.error(`复制 ${label} 失败`)
  }
}

applyPreset(presets[0])
</script>

<style scoped lang="scss">
.graphql-explorer {
  padding: 24px;
}

.query-editor,
.variables-editor {
  font-family: 'Fira Code', 'JetBrains Mono', Consolas, monospace;
}

.result-viewer {
  background: rgba(var(--v-theme-surface-variant), 0.4);
  border-radius: 8px;
  min-height: 320px;
  max-height: 600px;
  overflow: auto;
  font-family: 'Fira Code', 'JetBrains Mono', Consolas, monospace;
  font-size: 0.85rem;
}
</style>

