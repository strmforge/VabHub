<template>
  <div class="plugin-dashboard">
    <!-- 加载中 -->
    <div v-if="loading" class="text-center py-8">
      <v-progress-circular indeterminate color="primary" />
      <div class="text-medium-emphasis mt-2">加载 Dashboard...</div>
    </div>

    <!-- 无 Dashboard -->
    <v-alert v-else-if="!schema" type="info" variant="tonal">
      <v-icon class="mr-2">mdi-view-dashboard-outline</v-icon>
      此插件未提供 Dashboard
    </v-alert>

    <!-- Dashboard 内容 -->
    <div v-else class="dashboard-widgets">
      <v-row>
        <v-col
          v-for="widget in schema.widgets"
          :key="widget.id"
          :cols="getWidgetCols(widget)"
        >
          <!-- Stat Card -->
          <v-card v-if="widget.type === 'stat_card'" variant="outlined" class="pa-4">
            <div class="d-flex align-center">
              <v-icon
                v-if="widget.icon"
                :color="widget.color || 'primary'"
                size="36"
                class="mr-3"
              >
                {{ widget.icon }}
              </v-icon>
              <div>
                <div class="text-h4 font-weight-bold" :class="widget.color ? `text-${widget.color}` : ''">
                  {{ widget.value }}
                  <span v-if="widget.unit" class="text-body-2 text-medium-emphasis">{{ widget.unit }}</span>
                </div>
                <div class="text-body-2 text-medium-emphasis">{{ widget.title }}</div>
              </div>
            </div>
          </v-card>

          <!-- Table -->
          <v-card v-else-if="widget.type === 'table'" variant="outlined">
            <v-card-title v-if="widget.title" class="text-subtitle-1">
              {{ widget.title }}
            </v-card-title>
            <v-data-table
              :headers="getTableHeaders(widget)"
              :items="widget.rows || []"
              density="compact"
              class="elevation-0"
            />
          </v-card>

          <!-- Text / Markdown -->
          <v-card v-else-if="widget.type === 'text'" variant="outlined">
            <v-card-title v-if="widget.title" class="text-subtitle-1">
              {{ widget.title }}
            </v-card-title>
            <v-card-text>
              <div v-html="renderMarkdown(widget.markdown || '')"></div>
            </v-card-text>
          </v-card>

          <!-- Action Button -->
          <v-card v-else-if="widget.type === 'action_button'" variant="outlined" class="pa-4">
            <div class="d-flex flex-column align-center">
              <div v-if="widget.title" class="text-subtitle-2 mb-2">{{ widget.title }}</div>
              <div v-if="widget.description" class="text-caption text-medium-emphasis mb-3">
                {{ widget.description }}
              </div>
              <v-btn
                :color="widget.color || 'primary'"
                :loading="actionLoading[widget.id]"
                @click="handleAction(widget)"
              >
                <v-icon v-if="widget.icon" class="mr-2">{{ widget.icon }}</v-icon>
                {{ widget.action_label || '执行' }}
              </v-btn>
            </div>
          </v-card>
        </v-col>
      </v-row>
    </div>

    <!-- Action 结果对话框 -->
    <v-dialog v-model="actionResultDialog" max-width="500">
      <v-card>
        <v-card-title>操作结果</v-card-title>
        <v-card-text>
          <pre class="text-body-2">{{ JSON.stringify(actionResult, null, 2) }}</pre>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="actionResultDialog = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useToast } from 'vue-toastification'
import { pluginDashboardApi } from '@/services/api'
import type { PluginDashboardSchema, PluginDashboardWidget } from '@/types/plugin'
import api from '@/services/api'

const props = defineProps<{
  pluginId: string
}>()

const toast = useToast()

const loading = ref(false)
const schema = ref<PluginDashboardSchema | null>(null)
const actionLoading = ref<Record<string, boolean>>({})
const actionResultDialog = ref(false)
const actionResult = ref<any>(null)

// 加载 Dashboard
async function loadDashboard() {
  if (!props.pluginId) return
  
  loading.value = true
  try {
    schema.value = await pluginDashboardApi.get(props.pluginId)
  } catch (error: any) {
    console.error('Failed to load dashboard:', error)
    toast.error('加载 Dashboard 失败')
  } finally {
    loading.value = false
  }
}

// 获取 Widget 列宽
function getWidgetCols(widget: PluginDashboardWidget): number {
  switch (widget.type) {
    case 'stat_card':
      return 6
    case 'table':
      return 12
    case 'text':
      return 12
    case 'action_button':
      return 6
    default:
      return 12
  }
}

// 获取表格 headers
function getTableHeaders(widget: PluginDashboardWidget) {
  if (!widget.columns) return []
  return widget.columns.map(col => ({
    title: col,
    key: col,
    sortable: false,
  }))
}

// 渲染 Markdown（简化版本，仅处理换行）
function renderMarkdown(content: string): string {
  // 简单处理：将换行转为 <br>，保留基本格式
  return content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>')
}

// 执行 Action
async function handleAction(widget: PluginDashboardWidget) {
  if (!widget.action_api) {
    toast.warning('未配置操作 API')
    return
  }
  
  actionLoading.value[widget.id] = true
  
  try {
    const method = (widget.action_method || 'POST').toLowerCase()
    let response: any
    
    if (method === 'get') {
      response = await api.get(widget.action_api)
    } else if (method === 'post') {
      response = await api.post(widget.action_api, {})
    } else if (method === 'put') {
      response = await api.put(widget.action_api, {})
    } else if (method === 'delete') {
      response = await api.delete(widget.action_api)
    }
    
    actionResult.value = response?.data
    actionResultDialog.value = true
    toast.success('操作执行成功')
  } catch (error: any) {
    toast.error(error.response?.data?.detail || '操作执行失败')
  } finally {
    actionLoading.value[widget.id] = false
  }
}

// 监听 pluginId 变化
watch(() => props.pluginId, () => {
  loadDashboard()
})

onMounted(() => {
  loadDashboard()
})
</script>

<style scoped>
.plugin-dashboard {
  width: 100%;
}
</style>
