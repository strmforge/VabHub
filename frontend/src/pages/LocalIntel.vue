<template>
  <div class="local-intel-page">
    <PageHeader
      title="Local Intel 智能监控"
      subtitle="HR 任务监控、智能事件时间线和站点健康状态"
    >
      <template #actions>
        <v-btn
          color="primary"
          prepend-icon="mdi-refresh"
          @click="refreshAll"
          :loading="refreshing"
        >
          刷新全部
        </v-btn>
      </template>
    </PageHeader>

    <!-- 开发者模式提示 -->
    <v-alert
      v-if="isDevMode()"
      type="info"
      variant="tonal"
      density="compact"
      class="mb-4"
    >
      <template #prepend>
        <v-icon>mdi-information</v-icon>
      </template>
      <div class="text-caption">
        开发者模式页面 · 普通用户部署时请不要开启 VITE_DEV_MODE。
      </div>
    </v-alert>

    <!-- HR 任务表格区域 -->
    <v-card variant="outlined" class="mb-4">
      <v-card-title class="d-flex align-center justify-space-between">
        <span>HR 任务列表</span>
        <div class="d-flex align-center ga-2">
          <v-select
            v-model="hrTaskFilter.site"
            :items="siteOptions"
            label="站点"
            variant="outlined"
            density="compact"
            style="width: 150px"
            clearable
            @update:model-value="loadHRTasks"
          />
          <v-select
            v-model="hrTaskFilter.status"
            :items="statusOptions"
            label="状态"
            variant="outlined"
            density="compact"
            style="width: 150px"
            clearable
            @update:model-value="loadHRTasks"
          />
          <v-btn
            icon="mdi-refresh"
            variant="text"
            size="small"
            @click="loadHRTasks"
            :loading="hrTasksLoading"
          />
        </div>
      </v-card-title>
      <v-card-text>
        <div v-if="hrTasksLoading" class="text-center py-12">
          <v-progress-circular indeterminate color="primary" size="64" />
          <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
        </div>
        <v-data-table
          v-else
          :headers="hrTaskHeaders"
          :items="hrTasks"
          :items-per-page="20"
          class="elevation-0"
        >
          <template v-slot:item.hr_status="{ item }">
            <v-chip
              :color="getHRStatusColor(item.hr_status)"
              size="small"
              variant="flat"
            >
              {{ item.hr_status }}
            </v-chip>
          </template>
          <template v-slot:item.risk_level="{ item }">
            <v-chip
              :color="getRiskLevelColor(item.risk_level)"
              size="small"
              variant="flat"
            >
              {{ getRiskLevelText(item.risk_level) }}
            </v-chip>
          </template>
          <template v-slot:item.deadline="{ item }">
            {{ item.deadline ? formatDateTime(item.deadline) : '-' }}
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <!-- 智能事件时间线区域 -->
    <v-card variant="outlined" class="mb-4">
      <v-card-title class="d-flex align-center justify-space-between">
        <span>智能事件时间线</span>
        <div class="d-flex align-center ga-2">
          <v-select
            v-model="eventFilter.site"
            :items="siteOptions"
            label="站点"
            variant="outlined"
            density="compact"
            style="width: 150px"
            clearable
            @update:model-value="loadEvents"
          />
          <v-btn
            icon="mdi-refresh"
            variant="text"
            size="small"
            @click="loadEvents"
            :loading="eventsLoading"
          />
        </div>
      </v-card-title>
      <v-card-text>
        <div v-if="eventsLoading" class="text-center py-12">
          <v-progress-circular indeterminate color="primary" size="64" />
          <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
        </div>
        <div v-else-if="events.length === 0" class="text-center py-12">
          <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-information-outline</v-icon>
          <div class="text-h6 text-medium-emphasis mb-2">暂无事件</div>
          <div class="text-body-2 text-medium-emphasis">当前没有智能事件记录</div>
        </div>
        <v-timeline v-else density="compact" side="end">
          <v-timeline-item
            v-for="event in events"
            :key="event.id"
            :dot-color="getEventTypeColor(event.type)"
            size="small"
          >
            <template v-slot:icon>
              <v-icon :color="getEventTypeColor(event.type)">
                {{ getEventTypeIcon(event.type) }}
              </v-icon>
            </template>
            <v-card variant="outlined" class="mb-2">
              <v-card-title class="text-subtitle-1 d-flex align-center justify-space-between">
                <span>{{ event.title }}</span>
                <v-chip
                  :color="getEventTypeColor(event.type)"
                  size="x-small"
                  variant="flat"
                >
                  {{ event.type }}
                </v-chip>
              </v-card-title>
              <v-card-text>
                <div class="text-body-2 mb-2">{{ event.message }}</div>
                <div class="text-caption text-medium-emphasis">
                  {{ formatDateTime(event.created_at) }}
                  <span v-if="event.site" class="ml-2">站点: {{ event.site }}</span>
                  <span v-if="event.torrent_id" class="ml-2">种子ID: {{ event.torrent_id }}</span>
                </div>
              </v-card-text>
            </v-card>
          </v-timeline-item>
        </v-timeline>
      </v-card-text>
    </v-card>

    <!-- 站点健康状态区域 -->
    <v-card variant="outlined">
      <v-card-title class="d-flex align-center justify-space-between">
        <span>站点健康状态</span>
        <v-btn
          icon="mdi-refresh"
          variant="text"
          size="small"
          @click="loadSites"
          :loading="sitesLoading"
        />
      </v-card-title>
      <v-card-text>
        <div v-if="sitesLoading" class="text-center py-12">
          <v-progress-circular indeterminate color="primary" size="64" />
          <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
        </div>
        <v-row v-else>
          <v-col
            v-for="site in sites"
            :key="site.id"
            cols="12"
            sm="6"
            md="4"
            lg="3"
          >
            <v-card
              :variant="site.is_throttled ? 'outlined' : 'flat'"
              :color="site.is_throttled ? 'warning' : undefined"
            >
              <v-card-title class="d-flex align-center justify-space-between">
                <span>{{ site.name }}</span>
                <v-chip
                  v-if="site.is_throttled"
                  color="warning"
                  size="small"
                  variant="flat"
                >
                  限流中
                </v-chip>
              </v-card-title>
              <v-card-text>
                <div class="text-body-2 mb-2">
                  <div class="d-flex justify-space-between mb-1">
                    <span class="text-medium-emphasis">上次成功:</span>
                    <span>{{ site.last_ok ? formatDateTime(site.last_ok) : '未知' }}</span>
                  </div>
                  <div class="d-flex justify-space-between mb-1">
                    <span class="text-medium-emphasis">上次错误:</span>
                    <span>{{ site.last_error ? formatDateTime(site.last_error) : '无' }}</span>
                  </div>
                  <div class="d-flex justify-space-between mb-1">
                    <span class="text-medium-emphasis">错误次数:</span>
                    <v-chip
                      :color="site.error_count > 0 ? 'error' : 'success'"
                      size="x-small"
                      variant="flat"
                    >
                      {{ site.error_count }}
                    </v-chip>
                  </div>
                </div>
              </v-card-text>
              <v-card-actions>
                <v-btn
                  variant="text"
                  size="small"
                  prepend-icon="mdi-refresh"
                  @click="refreshSite(site.id)"
                  :loading="refreshingSites.includes(site.id)"
                >
                  手动刷新
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useToast } from 'vue-toastification'
import PageHeader from '@/components/common/PageHeader.vue'
import api from '@/services/api'
import { isDevMode } from '@/utils/devMode'

const toast = useToast()

// 数据状态
const hrTasks = ref<any[]>([])
const events = ref<any[]>([])
const sites = ref<any[]>([])
const hrTasksLoading = ref(false)
const eventsLoading = ref(false)
const sitesLoading = ref(false)
const refreshing = ref(false)
const refreshingSites = ref<string[]>([])

// 过滤条件
const hrTaskFilter = ref({
  site: null as string | null,
  status: null as string | null,
})
const eventFilter = ref({
  site: null as string | null,
})

// 站点选项（从 HR 任务和站点列表中提取）
const siteOptions = computed(() => {
  const sitesSet = new Set<string>()
  hrTasks.value.forEach(task => {
    if (task.site) sitesSet.add(task.site)
  })
  sites.value.forEach(site => {
    if (site.id) sitesSet.add(site.id)
  })
  return Array.from(sitesSet).map(s => ({ title: s, value: s }))
})

const statusOptions = [
  { title: 'ACTIVE', value: 'ACTIVE' },
  { title: 'FINISHED', value: 'FINISHED' },
  { title: 'FAILED', value: 'FAILED' },
  { title: 'NONE', value: 'NONE' },
  { title: 'UNKNOWN', value: 'UNKNOWN' },
]

// HR 任务表格列
const hrTaskHeaders = [
  { title: '站点', key: 'site', sortable: true },
  { title: '标题', key: 'title', sortable: true },
  { title: 'HR 状态', key: 'hr_status', sortable: true },
  { title: '截止时间', key: 'deadline', sortable: true },
  { title: '已保种', key: 'seeding_time', sortable: false },
  { title: '风险等级', key: 'risk_level', sortable: true },
]

// 加载 HR 任务
const loadHRTasks = async () => {
  hrTasksLoading.value = true
  try {
    const params: any = {}
    if (hrTaskFilter.value.site) params.site = hrTaskFilter.value.site
    if (hrTaskFilter.value.status) params.status = hrTaskFilter.value.status
    
    const resp = await api.get('/intel/hr-tasks', { params })
    hrTasks.value = resp.data?.items || resp.data || []
  } catch (error: any) {
    toast.error(error.message || '加载 HR 任务失败')
  } finally {
    hrTasksLoading.value = false
  }
}

// 加载智能事件
const loadEvents = async () => {
  eventsLoading.value = true
  try {
    const params: any = { limit: 100 }
    if (eventFilter.value.site) params.site = eventFilter.value.site
    
    const resp = await api.get('/intel/events', { params })
    events.value = resp.data?.items || resp.data || []
  } catch (error: any) {
    toast.error(error.message || '加载智能事件失败')
  } finally {
    eventsLoading.value = false
  }
}

// 加载站点健康状态
const loadSites = async () => {
  sitesLoading.value = true
  try {
    const resp = await api.get('/intel/sites')
    sites.value = resp.data?.items || resp.data || []
  } catch (error: any) {
    toast.error(error.message || '加载站点健康状态失败')
  } finally {
    sitesLoading.value = false
  }
}

// 刷新单个站点
const refreshSite = async (siteId: string) => {
  if (refreshingSites.value.includes(siteId)) return
  
  refreshingSites.value.push(siteId)
  try {
    await api.post(`/admin/local-intel/refresh/${siteId}`)
    toast.success(`站点 ${siteId} 刷新成功`)
    // 刷新相关数据
    await Promise.all([loadHRTasks(), loadEvents(), loadSites()])
  } catch (error: any) {
    toast.error(error.message || `刷新站点 ${siteId} 失败`)
  } finally {
    const index = refreshingSites.value.indexOf(siteId)
    if (index > -1) {
      refreshingSites.value.splice(index, 1)
    }
  }
}

// 刷新全部
const refreshAll = async () => {
  refreshing.value = true
  try {
    await Promise.all([loadHRTasks(), loadEvents(), loadSites()])
    toast.success('数据刷新成功')
  } catch (error: any) {
    toast.error(error.message || '刷新失败')
  } finally {
    refreshing.value = false
  }
}

// 工具函数
const formatDateTime = (dateStr: string | null) => {
  if (!dateStr) return '-'
  try {
    return new Date(dateStr).toLocaleString('zh-CN')
  } catch {
    return dateStr
  }
}

const getHRStatusColor = (status: string) => {
  const map: Record<string, string> = {
    ACTIVE: 'warning',
    FINISHED: 'success',
    FAILED: 'error',
    NONE: 'grey',
    UNKNOWN: 'info',
  }
  return map[status] || 'grey'
}

const getRiskLevelColor = (level: string) => {
  const map: Record<string, string> = {
    high: 'error',
    medium: 'warning',
    low: 'success',
  }
  return map[level] || 'grey'
}

const getRiskLevelText = (level: string) => {
  const map: Record<string, string> = {
    high: '高风险',
    medium: '中风险',
    low: '低风险',
  }
  return map[level] || level
}

const getEventTypeColor = (type: string) => {
  const map: Record<string, string> = {
    HR_PENALTY: 'error',
    TORRENT_DELETED: 'warning',
    SITE_THROTTLED: 'warning',
    OTHER: 'info',
  }
  return map[type] || 'grey'
}

const getEventTypeIcon = (type: string) => {
  const map: Record<string, string> = {
    HR_PENALTY: 'mdi-alert-circle',
    TORRENT_DELETED: 'mdi-delete',
    SITE_THROTTLED: 'mdi-speedometer',
    OTHER: 'mdi-information',
  }
  return map[type] || 'mdi-circle'
}

// 初始化
onMounted(() => {
  loadHRTasks()
  loadEvents()
  loadSites()
})
</script>

<style scoped>
.local-intel-page {
  padding: 24px;
}
</style>

