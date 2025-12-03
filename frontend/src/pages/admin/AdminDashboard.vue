<template>
  <div class="admin-dashboard">
    <!-- 顶部 PageHeader -->
    <PageHeader title="系统控制台" subtitle="查看后台服务、外部源和存储状态">
      <template v-slot:actions>
        <v-btn
          variant="outlined"
          size="small"
          prepend-icon="mdi-refresh"
          @click="loadData"
          :loading="loading"
        >
          刷新
        </v-btn>
      </template>
    </PageHeader>

    <v-container fluid>
      <!-- 加载状态 -->
      <div v-if="loading && !data" class="text-center py-12">
        <v-progress-circular indeterminate color="primary" size="64" />
        <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
      </div>

      <!-- 错误状态 -->
      <v-alert v-else-if="error" type="error" variant="tonal" class="mb-4">
        {{ error }}
        <template v-slot:append>
          <v-btn variant="text" size="small" @click="loadData">重试</v-btn>
        </template>
      </v-alert>

      <template v-else-if="data">
        <!-- Tabs -->
        <v-tabs v-model="activeTab" class="mb-4">
          <v-tab value="runners">
            <v-icon start>mdi-cog-sync</v-icon>
            Runner & 定时任务
          </v-tab>
          <v-tab value="sources">
            <v-icon start>mdi-cloud</v-icon>
            外部源状态
          </v-tab>
          <v-tab value="storage">
            <v-icon start>mdi-database</v-icon>
            存储概览
          </v-tab>
        </v-tabs>

        <!-- Runner Tab -->
        <v-window v-model="activeTab">
          <v-window-item value="runners">
            <v-card>
              <v-card-title>后台服务状态</v-card-title>
              <v-card-subtitle>
                以下服务需要通过 systemd timer 或 cron 定时运行
              </v-card-subtitle>
              <v-card-text>
                <v-table density="comfortable">
                  <thead>
                    <tr>
                      <th>服务名称</th>
                      <th>标识</th>
                      <th>状态</th>
                      <th>最近运行</th>
                      <th>配置命令</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="runner in data.runners" :key="runner.key">
                      <td class="font-weight-medium">{{ runner.name }}</td>
                      <td>
                        <code class="text-caption">{{ runner.key }}</code>
                      </td>
                      <td>
                        <v-chip
                          :color="getStatusColor(runner.last_status)"
                          size="small"
                          variant="flat"
                        >
                          {{ getStatusLabel(runner.last_status) }}
                        </v-chip>
                      </td>
                      <td>
                        {{ runner.last_run_at ? formatDate(runner.last_run_at) : '-' }}
                      </td>
                      <td>
                        <code class="text-caption text-medium-emphasis">
                          {{ runner.last_message || '-' }}
                        </code>
                      </td>
                    </tr>
                  </tbody>
                </v-table>
              </v-card-text>
            </v-card>

            <!-- 配置说明 -->
            <v-card class="mt-4">
              <v-card-title>配置说明</v-card-title>
              <v-card-text>
                <v-alert type="info" variant="tonal" class="mb-4">
                  后台服务需要通过 systemd timer 或 cron 定时运行。
                  以下是推荐的配置方式：
                </v-alert>
                <pre class="text-caption bg-grey-lighten-4 pa-3 rounded">
# 示例：TTS Worker systemd timer
[Unit]
Description=VabHub TTS Worker

[Timer]
OnCalendar=*:0/5
Persistent=true

[Install]
WantedBy=timers.target
                </pre>
              </v-card-text>
            </v-card>
          </v-window-item>

          <!-- External Sources Tab -->
          <v-window-item value="sources">
            <v-card>
              <v-card-title>外部源状态</v-card-title>
              <v-card-subtitle>
                漫画源、音乐榜单源等外部数据源
              </v-card-subtitle>
              <v-card-text>
                <v-list v-if="data.external_sources.length > 0">
                  <v-list-item
                    v-for="source in data.external_sources"
                    :key="`${source.type}-${source.name}`"
                  >
                    <template v-slot:prepend>
                      <v-avatar :color="getSourceTypeColor(source.type)" size="40">
                        <v-icon color="white">{{ getSourceTypeIcon(source.type) }}</v-icon>
                      </v-avatar>
                    </template>
                    <v-list-item-title>{{ source.name }}</v-list-item-title>
                    <v-list-item-subtitle>
                      {{ source.message || source.type }}
                      <span v-if="source.url" class="ml-2">
                        · {{ source.url }}
                      </span>
                    </v-list-item-subtitle>
                    <template v-slot:append>
                      <div class="d-flex flex-column align-end">
                        <v-chip
                          :color="getSourceStatusColor(source.last_status)"
                          size="small"
                          variant="flat"
                        >
                          {{ getSourceStatusLabel(source.last_status) }}
                        </v-chip>
                        <span v-if="source.last_check_at" class="text-caption text-medium-emphasis mt-1">
                          {{ formatDate(source.last_check_at) }}
                        </span>
                      </div>
                    </template>
                  </v-list-item>
                </v-list>
                <div v-else class="text-center py-8 text-medium-emphasis">
                  <v-icon size="48" class="mb-2">mdi-cloud-off-outline</v-icon>
                  <div>暂无外部源配置</div>
                </div>
              </v-card-text>
            </v-card>
          </v-window-item>

          <!-- Storage Tab -->
          <v-window-item value="storage">
            <v-row>
              <v-col
                v-for="storage in data.storage"
                :key="storage.name"
                cols="12"
                sm="6"
                md="4"
              >
                <v-card>
                  <v-card-text class="text-center">
                    <v-icon
                      :color="getStorageStatusColor(storage.status)"
                      size="48"
                      class="mb-2"
                    >
                      {{ getStorageIcon(storage.name) }}
                    </v-icon>
                    <div class="text-h6 mb-1">{{ storage.name }}</div>
                    <div class="text-h4 font-weight-bold mb-2">
                      {{ storage.total_items }}
                    </div>
                    <div v-if="storage.size_description" class="text-caption text-medium-emphasis mb-2">
                      {{ storage.size_description }}
                    </div>
                    <v-chip
                      :color="getStorageStatusColor(storage.status)"
                      size="small"
                      variant="flat"
                    >
                      {{ getStorageStatusLabel(storage.status) }}
                    </v-chip>
                    <div v-if="storage.path" class="text-caption text-disabled mt-2">
                      {{ storage.path }}
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-window-item>
        </v-window>
      </template>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from '@/composables/useToast'
import { adminApi } from '@/services/api'
import type { AdminDashboardResponse } from '@/types/admin'
import PageHeader from '@/components/common/PageHeader.vue'

const toast = useToast()

// 状态
const loading = ref(false)
const error = ref<string | null>(null)
const data = ref<AdminDashboardResponse | null>(null)
const activeTab = ref('runners')

// 加载数据
const loadData = async () => {
  try {
    loading.value = true
    error.value = null
    data.value = await adminApi.getDashboard()
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } }; message?: string }
    console.error('加载管理控制台数据失败:', err)
    error.value = e.response?.data?.detail || e.message || '加载失败'
    toast.error(error.value || '加载失败')
  } finally {
    loading.value = false
  }
}

// 辅助函数
const getStatusColor = (status: string | null | undefined): string => {
  if (!status) return 'grey'
  const colors: Record<string, string> = {
    success: 'success',
    failed: 'error',
    unknown: 'grey',
  }
  return colors[status] || 'grey'
}

const getStatusLabel = (status: string | null | undefined): string => {
  if (!status) return '未知'
  const labels: Record<string, string> = {
    success: '正常',
    failed: '失败',
    unknown: '未配置',
  }
  return labels[status] || status
}

const getSourceTypeColor = (type: string): string => {
  const colors: Record<string, string> = {
    manga: 'orange',
    music: 'green',
    indexer: 'blue',
  }
  return colors[type] || 'grey'
}

const getSourceTypeIcon = (type: string): string => {
  const icons: Record<string, string> = {
    manga: 'mdi-book-open-variant',
    music: 'mdi-music',
    indexer: 'mdi-magnify',
  }
  return icons[type] || 'mdi-cloud'
}

const getSourceStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    ok: 'success',
    error: 'error',
    disabled: 'grey',
    unknown: 'warning',
  }
  return colors[status] || 'grey'
}

const getSourceStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    ok: '正常',
    error: '错误',
    disabled: '已禁用',
    unknown: '未知',
  }
  return labels[status] || status
}

const getStorageStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    ok: 'success',
    warning: 'warning',
    error: 'error',
    empty: 'grey',
    unknown: 'grey',
  }
  return colors[status] || 'grey'
}

const getStorageStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    ok: '正常',
    warning: '警告',
    error: '错误',
    empty: '空',
    unknown: '未知',
  }
  return labels[status] || status
}

const getStorageIcon = (name: string): string => {
  if (name.includes('小说') || name.includes('电子书')) return 'mdi-book-open-page-variant'
  if (name.includes('漫画')) return 'mdi-book-open-variant'
  if (name.includes('音乐')) return 'mdi-music'
  if (name.includes('TTS')) return 'mdi-text-to-speech'
  return 'mdi-database'
}

const formatDate = (dateStr: string): string => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) {
    const hours = Math.floor(diff / (1000 * 60 * 60))
    if (hours === 0) {
      const mins = Math.floor(diff / (1000 * 60))
      return mins <= 1 ? '刚刚' : `${mins}分钟前`
    }
    return `${hours}小时前`
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}

// 初始化
onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.admin-dashboard {
  min-height: 100vh;
  background-color: rgb(var(--v-theme-surface));
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
