<template>
  <div class="home-dashboard">
    <!-- Demo 模式横幅 -->
    <v-banner
      v-if="appStore.isDemoMode"
      color="warning"
      icon="mdi-flask"
      lines="one"
      class="mb-0"
    >
      <template v-slot:text>
        <span class="font-weight-medium">当前为 Demo 模式</span>：所有下载/外部操作均为模拟，数据仅供体验
      </template>
      <template v-slot:actions>
        <v-chip size="small" color="warning" variant="flat">
          v{{ appStore.appVersion?.version || '0.0.0' }}
        </v-chip>
      </template>
    </v-banner>
    
    <!-- 顶部 PageHeader -->
    <PageHeader title="VabHub 总览" subtitle="一眼看到你最近的观看 / 阅读 / 收听和系统状态">
      <template v-slot:actions>
        <v-btn
          variant="outlined"
          size="small"
          prepend-icon="mdi-book-open-page-variant"
          @click="$router.push({ name: 'ReadingHub' })"
          class="mr-2"
        >
          阅读中心
        </v-btn>
        <v-btn
          variant="outlined"
          size="small"
          prepend-icon="mdi-music"
          @click="$router.push({ name: 'MusicCenter' })"
        >
          音乐中心
        </v-btn>
      </template>
    </PageHeader>

    <v-container fluid>
      <!-- 加载状态 -->
      <div v-if="loading" class="text-center py-12">
        <v-progress-circular indeterminate color="primary" size="64" />
        <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
      </div>

      <!-- 错误状态 -->
      <v-alert v-else-if="error" type="error" variant="tonal" class="mb-4">
        {{ error }}
        <template v-slot:append>
          <v-btn variant="text" size="small" @click="loadDashboard">重试</v-btn>
        </template>
      </v-alert>

      <template v-else-if="dashboard">
        <!-- 第一行：核心状态统计 -->
        <v-row class="mb-4">
          <v-col
            v-for="stat in dashboard.stats"
            :key="stat.label"
            cols="6"
            sm="3"
          >
            <v-card rounded="xl" elevation="1" class="pa-4">
              <div class="text-center">
                <v-icon :color="stat.color || 'primary'" size="32" class="mb-2">
                  {{ stat.icon || 'mdi-chart-box' }}
                </v-icon>
                <div class="text-h4 font-weight-bold" :class="`text-${stat.color || 'primary'}`">
                  {{ stat.value }}
                </div>
                <div class="text-caption text-medium-emphasis">{{ stat.label }}</div>
              </div>
            </v-card>
          </v-col>
        </v-row>

        <!-- 第二行：TTS/插件/阅读统计卡片 -->
        <v-row class="mb-4" v-if="dashboardData">
          <!-- TTS 统计 -->
          <v-col cols="12" sm="4">
            <v-card rounded="xl" elevation="1" class="pa-4">
              <div class="d-flex align-center mb-3">
                <v-icon class="mr-2" color="info">mdi-voice</v-icon>
                <h3 class="text-h6 m-0">TTS 任务</h3>
              </div>
              <v-row dense>
                <v-col cols="4" class="text-center">
                  <div class="text-h5 text-warning font-weight-bold">
                    {{ dashboardData.tts_stats?.pending_jobs || 0 }}
                  </div>
                  <div class="text-caption text-medium-emphasis">待处理</div>
                </v-col>
                <v-col cols="4" class="text-center">
                  <div class="text-h5 text-info font-weight-bold">
                    {{ dashboardData.tts_stats?.running_jobs || 0 }}
                  </div>
                  <div class="text-caption text-medium-emphasis">进行中</div>
                </v-col>
                <v-col cols="4" class="text-center">
                  <div class="text-h5 text-success font-weight-bold">
                    {{ dashboardData.tts_stats?.completed_last_24h || 0 }}
                  </div>
                  <div class="text-caption text-medium-emphasis">24h完成</div>
                </v-col>
              </v-row>
            </v-card>
          </v-col>

          <!-- 插件统计 -->
          <v-col cols="12" sm="4">
            <v-card rounded="xl" elevation="1" class="pa-4">
              <div class="d-flex align-center mb-3">
                <v-icon class="mr-2" color="purple">mdi-puzzle</v-icon>
                <h3 class="text-h6 m-0">插件状态</h3>
              </div>
              <v-row dense>
                <v-col cols="4" class="text-center">
                  <div class="text-h5 text-primary font-weight-bold">
                    {{ dashboardData.plugin_stats?.total_plugins || 0 }}
                  </div>
                  <div class="text-caption text-medium-emphasis">总数</div>
                </v-col>
                <v-col cols="4" class="text-center">
                  <div class="text-h5 text-success font-weight-bold">
                    {{ dashboardData.plugin_stats?.active_plugins || 0 }}
                  </div>
                  <div class="text-caption text-medium-emphasis">活跃</div>
                </v-col>
                <v-col cols="4" class="text-center">
                  <div class="text-h5 text-error font-weight-bold">
                    {{ dashboardData.plugin_stats?.quarantined_plugins || 0 }}
                  </div>
                  <div class="text-caption text-medium-emphasis">隔离</div>
                </v-col>
              </v-row>
            </v-card>
          </v-col>

          <!-- 阅读统计 -->
          <v-col cols="12" sm="4">
            <v-card rounded="xl" elevation="1" class="pa-4">
              <div class="d-flex align-center mb-3">
                <v-icon class="mr-2" color="teal">mdi-book-open-page-variant</v-icon>
                <h3 class="text-h6 m-0">阅读活跃</h3>
              </div>
              <v-row dense>
                <v-col cols="4" class="text-center">
                  <div class="text-h5 text-info font-weight-bold">
                    {{ dashboardData.reading_stats?.active_novels || 0 }}
                  </div>
                  <div class="text-caption text-medium-emphasis">小说</div>
                </v-col>
                <v-col cols="4" class="text-center">
                  <div class="text-h5 text-purple font-weight-bold">
                    {{ dashboardData.reading_stats?.active_audiobooks || 0 }}
                  </div>
                  <div class="text-caption text-medium-emphasis">有声书</div>
                </v-col>
                <v-col cols="4" class="text-center">
                  <div class="text-h5 text-pink font-weight-bold">
                    {{ dashboardData.reading_stats?.active_manga || 0 }}
                  </div>
                  <div class="text-caption text-medium-emphasis">漫画</div>
                </v-col>
              </v-row>
            </v-card>
          </v-col>
        </v-row>

        <!-- 最近活动时间线 -->
        <v-row class="mb-4" v-if="dashboardData?.recent_events?.length > 0">
          <v-col cols="12">
            <v-card rounded="xl" elevation="1" class="pa-4">
              <div class="d-flex align-center mb-3">
                <v-icon class="mr-2">mdi-clock-time-eight-outline</v-icon>
                <h3 class="text-h6 m-0">最近活动</h3>
              </div>
              <v-timeline density="compact" align="start" class="timeline-container">
                <v-timeline-item
                  v-for="event in dashboardData.recent_events.slice(0, 10)"
                  :key="`${event.type}-${event.time}`"
                  :dot-color="getEventColor(event.type)"
                  :icon="getEventIcon(event.type)"
                  size="small"
                  class="timeline-item"
                >
                  <template v-slot:opposite>
                    <div class="text-caption text-medium-emphasis min-w-[80px]">
                      {{ formatEventTime(event.time) }}
                    </div>
                  </template>
                  <div class="timeline-content">
                    <div class="text-body-2 font-weight-medium break-words">{{ event.title }}</div>
                    <div class="text-caption text-medium-emphasis break-words mt-1">{{ event.message }}</div>
                  </div>
                </v-timeline-item>
              </v-timeline>
            </v-card>
          </v-col>
        </v-row>

        <!-- 系统健康卡片（管理员可见） -->
        <v-row class="mb-4">
          <v-col cols="12" md="4">
            <SystemHealthCard
              show-actions
              @view-details="$router.push({ name: 'AdminDashboard', query: { tab: 'health' } })"
            />
          </v-col>
        </v-row>

        <!-- 第二行：继续阅读 + 最近新增 -->
        <v-row class="mb-4">
          <!-- 继续阅读/收听 -->
          <v-col cols="12" md="6">
            <v-card rounded="xl" elevation="1" class="pa-4">
              <div class="d-flex align-center mb-3">
                <v-icon class="mr-2">mdi-play-circle</v-icon>
                <h3 class="text-h6 m-0">继续阅读 / 收听</h3>
              </div>
              <v-list v-if="dashboard.up_next.length > 0" density="compact">
                <v-list-item
                  v-for="item in dashboard.up_next"
                  :key="`${item.media_type}-${item.title}`"
                  @click="goToItem(item)"
                  class="cursor-pointer mb-2 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <template v-slot:prepend>
                    <v-avatar size="48" rounded class="mr-3">
                      <v-img v-if="item.cover_url" :src="item.cover_url" cover />
                      <v-icon v-else :color="getMediaColor(item.media_type)">
                        {{ getMediaIcon(item.media_type) }}
                      </v-icon>
                    </v-avatar>
                  </template>
                  <v-list-item-title>{{ item.title }}</v-list-item-title>
                  <v-list-item-subtitle>
                    {{ item.sub_title || getMediaLabel(item.media_type) }}
                  </v-list-item-subtitle>
                  <template v-slot:append>
                    <div class="d-flex flex-column align-end">
                      <v-chip
                        :color="getMediaColor(item.media_type)"
                        size="x-small"
                        variant="flat"
                        class="mb-1"
                      >
                        {{ getMediaLabel(item.media_type) }}
                      </v-chip>
                      <span v-if="item.progress_percent != null" class="text-caption">
                        {{ item.progress_percent }}%
                      </span>
                    </div>
                  </template>
                </v-list-item>
              </v-list>
              <div v-else class="text-center py-8 text-medium-emphasis">
                <v-icon size="48" class="mb-2">mdi-book-open-blank-variant</v-icon>
                <div>暂无进行中的阅读</div>
                <v-btn
                  variant="text"
                  color="primary"
                  size="small"
                  class="mt-2"
                  @click="$router.push({ name: 'NovelCenter' })"
                >
                  去小说中心看看
                </v-btn>
              </div>
            </v-card>
          </v-col>

          <!-- 最近新增 -->
          <v-col cols="12" md="6">
            <v-card rounded="xl" elevation="1" class="pa-4">
              <div class="d-flex align-center mb-3">
                <v-icon class="mr-2">mdi-new-box</v-icon>
                <h3 class="text-h6 m-0">最近新增</h3>
              </div>
              <v-list v-if="dashboard.recent_items.length > 0" density="compact">
                <v-list-item
                  v-for="item in dashboard.recent_items"
                  :key="`${item.media_type}-${item.title}`"
                  @click="goToRecentItem(item)"
                  class="cursor-pointer mb-2 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <template v-slot:prepend>
                    <v-avatar size="48" rounded class="mr-3">
                      <v-img v-if="item.cover_url" :src="item.cover_url" cover />
                      <v-icon v-else :color="getMediaColor(item.media_type)">
                        {{ getMediaIcon(item.media_type) }}
                      </v-icon>
                    </v-avatar>
                  </template>
                  <v-list-item-title>{{ item.title }}</v-list-item-title>
                  <v-list-item-subtitle>
                    {{ item.sub_title || getMediaLabel(item.media_type) }}
                  </v-list-item-subtitle>
                  <template v-slot:append>
                    <div class="d-flex flex-column align-end">
                      <v-chip
                        :color="getMediaColor(item.media_type)"
                        size="x-small"
                        variant="flat"
                        class="mb-1"
                      >
                        {{ getMediaLabel(item.media_type) }}
                      </v-chip>
                      <span v-if="item.created_at" class="text-caption">
                        {{ formatDate(item.created_at) }}
                      </span>
                    </div>
                  </template>
                </v-list-item>
              </v-list>
              <div v-else class="text-center py-8 text-medium-emphasis">
                <v-icon size="48" class="mb-2">mdi-folder-open</v-icon>
                <div>暂无新增内容</div>
              </div>
            </v-card>
          </v-col>
        </v-row>

        <!-- 第三行：系统运行状态 -->
        <v-row class="mb-4">
          <!-- 后台服务状态 -->
          <v-col cols="12" md="8">
            <v-card rounded="xl" elevation="1" class="pa-4">
              <div class="d-flex align-center mb-3">
                <v-icon class="mr-2">mdi-cog-sync</v-icon>
                <h3 class="text-h6 m-0">后台服务状态</h3>
              </div>
              <v-table density="compact" rounded="md" class="bg-transparent">
                <thead class="bg-gray-50">
                  <tr class="border-b">
                    <th class="text-start py-2 px-4">服务名称</th>
                    <th class="text-center py-2 px-4">状态</th>
                    <th class="text-center py-2 px-4">最近运行</th>
                    <th class="text-start py-2 px-4">说明</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="runner in dashboard.runners" :key="runner.key" class="hover:bg-gray-50 border-b" style="height: 40px;">
                    <td class="py-1 px-4 align-middle">{{ runner.name }}</td>
                    <td class="text-center py-1 px-4 align-middle">
                      <v-chip
                        :color="getRunnerStatusColor(runner.last_status)"
                        size="x-small"
                        variant="flat"
                      >
                        {{ getRunnerStatusLabel(runner.last_status) }}
                      </v-chip>
                    </td>
                    <td class="text-center py-1 px-4 align-middle">
                      {{ runner.last_run_at ? formatDate(runner.last_run_at) : '-' }}
                    </td>
                    <td class="text-caption text-medium-emphasis py-1 px-4 align-middle">
                      {{ runner.last_message || '-' }}
                    </td>
                  </tr>
                </tbody>
              </v-table>
            </v-card>
          </v-col>

          <!-- 任务汇总 -->
          <v-col cols="12" md="4">
            <v-card rounded="xl" elevation="1" class="pa-4">
              <div class="d-flex align-center mb-3">
                <v-icon class="mr-2">mdi-clipboard-list</v-icon>
                <h3 class="text-h6 m-0">任务汇总</h3>
              </div>
              <div class="d-flex justify-space-between align-center mb-4">
                <span class="text-body-2">运行中</span>
                <div class="text-h4 font-weight-bold text-primary">
                  {{ dashboard.tasks.total_running }}
                </div>
              </div>
              <div class="d-flex justify-space-between align-center mb-4">
                <span class="text-body-2">等待中</span>
                <div class="text-h4 font-weight-bold text-info">
                  {{ dashboard.tasks.total_waiting }}
                </div>
              </div>
              <div class="d-flex justify-space-between align-center mb-4">
                <span class="text-body-2">最近失败</span>
                <div class="text-h4 font-weight-bold" :class="dashboard.tasks.total_failed_recent > 0 ? 'text-error' : 'text-success'">
                  {{ dashboard.tasks.total_failed_recent }}
                </div>
              </div>
              <v-divider class="my-3" />
              <v-btn
                variant="outlined"
                color="primary"
                block
                size="small"
                @click="$router.push({ name: 'TaskCenter' })"
                rounded="md"
              >
                查看任务中心
              </v-btn>
            </v-card>
          </v-col>
        </v-row>

        <!-- 第四行：插件扩展面板 -->
        <v-row class="mb-4">
          <v-col cols="12">
            <v-card rounded="xl" elevation="1" class="pa-4">
              <div class="d-flex align-center mb-3">
                <v-icon class="mr-2" color="primary">mdi-puzzle</v-icon>
                <h3 class="text-h6 m-0">插件扩展</h3>
              </div>
              <PluginPanelHost placement="home_dashboard" hide-empty />
            </v-card>
          </v-col>
        </v-row>
      </template>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { useAppStore } from '@/stores/app'
import { homeApi, dashboardApi } from '@/services/api'
import type {
  HomeDashboardResponse,
  HomeUpNextItem,
  HomeRecentItem
} from '@/types/home'
import type { DashboardData, RecentEvent } from '@/types/dashboard'
import PageHeader from '@/components/common/PageHeader.vue'
import SystemHealthCard from '@/components/admin/SystemHealthCard.vue'
import PluginPanelHost from '@/components/plugin/PluginPanelHost.vue'

const router = useRouter()
const toast = useToast()
const appStore = useAppStore()

// 状态
const loading = ref(false)
const error = ref<string | null>(null)
const dashboard = ref<HomeDashboardResponse | null>(null)
const dashboardData = ref<DashboardData | null>(null)

// 加载数据
const loadDashboard = async () => {
  try {
    loading.value = true
    error.value = null
    
    // 并行获取个性化首页数据和系统统计数据
    const [homeData, systemData] = await Promise.all([
      homeApi.getDashboard(),
      dashboardApi.getDashboard()
    ])
    
    dashboard.value = homeData
    dashboardData.value = systemData.data
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } }; message?: string }
    console.error('加载首页数据失败:', err)
    error.value = e.response?.data?.detail || e.message || '加载失败'
    toast.error(error.value || '加载失败')
  } finally {
    loading.value = false
  }
}

// 事件处理函数
const getEventColor = (eventType: string): string => {
  switch (eventType) {
    case 'download_completed':
      return 'success'
    case 'tts_completed':
      return 'info'
    case 'plugin_error':
      return 'error'
    default:
      return 'grey'
  }
}

const getEventIcon = (eventType: string): string => {
  switch (eventType) {
    case 'download_completed':
      return 'mdi-download-check'
    case 'tts_completed':
      return 'mdi-voice'
    case 'plugin_error':
      return 'mdi-alert-circle'
    default:
      return 'mdi-information'
  }
}

const formatEventTime = (timeStr: string | null): string => {
  if (!timeStr) return '未知时间'
  
  try {
    const date = new Date(timeStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
    
    if (diffMins < 1) {
      return '刚刚'
    } else if (diffMins < 60) {
      return `${diffMins}分钟前`
    } else if (diffHours < 24) {
      return `${diffHours}小时前`
    } else if (diffDays < 7) {
      return `${diffDays}天前`
    } else {
      return date.toLocaleDateString('zh-CN')
    }
  } catch (error) {
    console.error('时间格式化错误:', error)
    return '时间格式错误'
  }
}

// 跳转到继续阅读项
const goToItem = (item: HomeUpNextItem) => {
  if (item.route_name && item.route_params) {
    router.push({ name: item.route_name, params: item.route_params })
  } else {
    // 根据媒体类型跳转到对应中心
    const routeMap: Record<string, string> = {
      novel: 'NovelCenter',
      audiobook: 'AudiobookCenter',
      manga: 'MangaLibraryPage',
      music: 'MusicCenter',
      movie: 'Dashboard',
      series: 'Dashboard'
    }
    router.push({ name: routeMap[item.media_type] || 'Dashboard' })
  }
}

// 跳转到最近新增项
const goToRecentItem = (item: HomeRecentItem) => {
  if (item.route_name && item.route_params) {
    router.push({ name: item.route_name, params: item.route_params })
  } else {
    const routeMap: Record<string, string> = {
      novel: 'NovelCenter',
      audiobook: 'AudiobookCenter',
      manga: 'MangaLibraryPage',
      music: 'MusicCenter',
      movie: 'Dashboard',
      series: 'Dashboard'
    }
    router.push({ name: routeMap[item.media_type] || 'Dashboard' })
  }
}

// 辅助函数
const getMediaIcon = (type: string): string => {
  const icons: Record<string, string> = {
    novel: 'mdi-book-open-page-variant',
    audiobook: 'mdi-headphones',
    manga: 'mdi-book-open-variant',
    music: 'mdi-music',
    movie: 'mdi-movie',
    series: 'mdi-television'
  }
  return icons[type] || 'mdi-file'
}

const getMediaColor = (type: string): string => {
  const colors: Record<string, string> = {
    novel: 'blue',
    audiobook: 'purple',
    manga: 'orange',
    music: 'green',
    movie: 'red',
    series: 'teal'
  }
  return colors[type] || 'grey'
}

const getMediaLabel = (type: string): string => {
  const labels: Record<string, string> = {
    novel: '小说',
    audiobook: '有声书',
    manga: '漫画',
    music: '音乐',
    movie: '电影',
    series: '剧集'
  }
  return labels[type] || type
}

const getRunnerStatusColor = (status: string | null | undefined): string => {
  if (!status) return 'grey'
  const colors: Record<string, string> = {
    success: 'success',
    failed: 'error',
    unknown: 'grey'
  }
  return colors[status] || 'grey'
}

const getRunnerStatusLabel = (status: string | null | undefined): string => {
  if (!status) return '未知'
  const labels: Record<string, string> = {
    success: '正常',
    failed: '失败',
    unknown: '未配置'
  }
  return labels[status] || status
}

const formatDate = (dateStr: string): string => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) {
    const hours = Math.floor(diff / (1000 * 60 * 60))
    if (hours === 0) {
      const mins = Math.floor(diff / (1000 * 60))
      return mins <= 1 ? '刚刚' : `${mins} 分钟前`
    }
    return `${hours} 小时前`
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days} 天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}

// 初始化
onMounted(() => {
  loadDashboard()
  // 获取版本信息（如果尚未加载）
  if (!appStore.appVersion) {
    appStore.fetchVersion()
  }
})
</script>

<style scoped lang="scss">
.home-dashboard {
  min-height: 100vh;
  background-color: rgb(var(--v-theme-surface));
}

.cursor-pointer {
  cursor: pointer;
}

.timeline-container {
  overflow-x: auto;
  white-space: nowrap;
}

.timeline-item {
  min-width: 100%;
}

.timeline-content {
  word-break: break-word;
  white-space: normal;
  overflow-wrap: break-word;
}

.break-words {
  word-break: break-word;
  overflow-wrap: break-word;
}

.min-w-\[80px\] {
  min-width: 80px;
}
</style>
