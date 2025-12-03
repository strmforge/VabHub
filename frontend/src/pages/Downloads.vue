<template>
  <div class="downloads-page">
    <PageHeader
      title="下载管理"
      subtitle="管理您的下载任务"
    />
    
    <!-- 统计卡片 - DOWNLOAD-CENTER-UI-1 重构 -->
    <v-row class="mb-4">
      <v-col cols="12" sm="6" md="3">
        <v-card variant="elevated" color="success" class="stat-card">
          <v-card-text class="pa-4 text-center">
            <v-icon size="32" class="mb-2">mdi-download</v-icon>
            <div class="stat-number">{{ stats.downloading }}</div>
            <div class="stat-label">正在下载</div>
            <div class="stat-speed text-caption" v-if="totalSpeed > 0">
              {{ formatSpeed(totalSpeed) }}
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card variant="elevated" color="info" class="stat-card">
          <v-card-text class="pa-4 text-center">
            <v-icon size="32" class="mb-2">mdi-clock-outline</v-icon>
            <div class="stat-number">{{ stats.queued }}</div>
            <div class="stat-label">排队中</div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card variant="elevated" color="error" class="stat-card">
          <v-card-text class="pa-4 text-center">
            <v-icon size="32" class="mb-2">mdi-alert-circle</v-icon>
            <div class="stat-number">{{ stats.error }}</div>
            <div class="stat-label">异常/失败</div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card variant="elevated" color="primary" class="stat-card">
          <v-card-text class="pa-4 text-center">
            <v-icon size="32" class="mb-2">mdi-speedometer</v-icon>
            <div class="stat-number">{{ formatSpeed(totalSpeed) }}</div>
            <div class="stat-label">总下载速度</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    
    <!-- 下载标签页 - DOWNLOAD-CENTER-UI-1 重构 -->
    <v-card>
      <v-tabs v-model="activeTab" bg-color="surface">
        <v-tab value="all_active">
          <v-icon start>mdi-format-list-bulleted</v-icon>
          全部任务
          <v-badge
            v-if="stats.downloading + stats.queued + stats.error > 0"
            :content="stats.downloading + stats.queued + stats.error"
            color="primary"
            class="ms-2"
          />
        </v-tab>
        
        <v-tab value="downloading">
          <v-icon start>mdi-download</v-icon>
          下载中
          <v-badge
            v-if="stats.downloading > 0"
            :content="stats.downloading"
            color="success"
            class="ms-2"
          />
        </v-tab>
        
        <v-tab value="queued">
          <v-icon start>mdi-clock-outline</v-icon>
          排队中
          <v-badge
            v-if="stats.queued > 0"
            :content="stats.queued"
            color="info"
            class="ms-2"
          />
        </v-tab>
        
        <v-tab value="error">
          <v-icon start>mdi-alert-circle</v-icon>
          异常/失败
          <v-badge
            v-if="stats.error > 0"
            :content="stats.error"
            color="error"
            class="ms-2"
          />
        </v-tab>
        
        <v-tab value="recent_completed">
          <v-icon start>mdi-history</v-icon>
          最近完成
          <v-badge
            v-if="stats.recent_completed > 0"
            :content="stats.recent_completed"
            color="grey"
            class="ms-2"
          />
        </v-tab>
      </v-tabs>
      
      <!-- P3: VabHub 过滤说明 -->
      <v-alert
        type="info"
        variant="tonal"
        class="ma-4"
      >
        <v-icon start>mdi-information</v-icon>
        仅显示打上 VabHub 标签的下载任务，刷流/无标签任务不会出现在此处。
        需要纳入管理的任务，可在下载器中手动添加标签。
        已整理完成的任务会自动隐藏，保持界面清爽。
      </v-alert>
      
      <v-divider />
      
      <!-- 标签页内容 - DOWNLOAD-CENTER-UI-1 重构 -->
      <v-window v-model="activeTab">
        <v-window-item value="all_active">
          <v-card-text class="pa-0">
            <!-- 过滤工具栏 -->
            <v-card variant="flat" color="grey-lighten-5" class="rounded-0 mb-2">
              <v-card-text class="pa-3">
                <v-row align="center">
                  <v-col cols="12" sm="6" md="4">
                    <v-text-field
                      v-model="filters.search"
                      label="搜索下载项"
                      prepend-inner-icon="mdi-magnify"
                      clearable
                      variant="outlined"
                      density="compact"
                      hide-details
                      @update:model-value="handleFilterChange"
                    />
                  </v-col>
                  
                  <v-col cols="12" sm="6" md="3">
                    <v-chip-group
                      v-model="mediaTypeFilter"
                      mandatory
                      selected-class="short-chip-active"
                      @update:model-value="handleFilterChange"
                    >
                      <v-chip value="all" size="small" variant="outlined">
                        全部
                      </v-chip>
                      <v-chip
                        value="short_drama"
                        size="small"
                        color="purple"
                        variant="flat"
                        prepend-icon="mdi-drama-masks"
                      >
                        短剧
                      </v-chip>
                    </v-chip-group>
                  </v-col>
                  
                  <v-col cols="12" sm="6" md="5" class="d-flex ga-2">
                    <v-btn
                      prepend-icon="mdi-pause-all"
                      variant="outlined"
                      color="warning"
                      size="small"
                      @click="pauseAll"
                      :disabled="selectedDownloads.length === 0"
                    >
                      全部暂停
                    </v-btn>
                    <v-btn
                      prepend-icon="mdi-speedometer"
                      variant="outlined"
                      color="info"
                      size="small"
                      @click="handleBatchSpeedLimit"
                      :disabled="selectedDownloads.length === 0"
                    >
                      批量限速
                    </v-btn>
                    <v-btn
                      prepend-icon="mdi-delete-sweep"
                      variant="outlined"
                      color="error"
                      size="small"
                      @click="clearCompleted"
                    >
                      清理已完成
                    </v-btn>
                    <v-spacer />
                    <v-btn
                      icon
                      variant="text"
                      @click="refreshData"
                      :loading="loading"
                    >
                      <v-icon>mdi-refresh</v-icon>
                    </v-btn>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
            
            <!-- P3 卡片UI强化：内联下载列表 -->
            <!-- TODO: DOWNLOAD-CENTER-UI-1 - 重构技术债务：4个tab中存在重复的内联卡片UI代码(~250行)，未来需要提取为可复用组件 -->
            <div class="download-list">
              <!-- 刷新按钮和加载状态 -->
              <div class="d-flex align-center pa-4">
                <v-btn
                  variant="text"
                  :loading="loading"
                  @click="refreshData"
                  prepend-icon="mdi-refresh"
                >
                  刷新
                </v-btn>
                <v-spacer />
                <div class="text-caption text-medium-emphasis">
                  共 {{ filteredDownloads.length }} 个任务
                </div>
              </div>

              <!-- 任务列表 -->
              <v-list v-if="filteredDownloads.length > 0" class="pa-0">
                <DownloadTaskCard
                  v-for="download in filteredDownloads"
                  :key="download.id"
                  :task="download"
                  :selected="selectedDownloads.includes(download.id)"
                  :show-selection="true"
                  @toggleSelection="toggleSelection"
                  @pause="handlePauseTask"
                  @resume="handleResumeTask"
                  @queueTop="handleQueueTop"
                  @delete="handleDeleteTask"
                  @speedLimit="handleSpeedLimit"
                  @openOrganize="handleOpenOrganize"
                />
              </v-list>

              <!-- 空状态 -->
              <v-empty-state
                v-else-if="!loading"
                icon="mdi-download-off"
                title="暂无下载任务"
                text="当前没有符合条件的下载任务"
                class="pa-8"
              >
                <v-btn @click="refreshData">刷新</v-btn>
              </v-empty-state>

              <!-- 加载状态 -->
              <v-skeleton-loader
                v-if="loading"
                type="list-item-three-line@4"
                class="pa-4"
              />
            </div>
          </v-card-text>
        </v-window-item>
        
        <v-window-item value="downloading">
          <v-card-text class="pa-0">
            <!-- 下载中任务列表 - P3 卡片UI强化 -->
            <div class="download-list">
              <div class="d-flex align-center pa-4">
                <v-btn
                  variant="text"
                  :loading="loading"
                  @click="refreshData"
                  prepend-icon="mdi-refresh"
                >
                  刷新
                </v-btn>
                <v-spacer />
                <div class="text-caption text-medium-emphasis">
                  共 {{ filteredDownloads.length }} 个下载中任务
                </div>
              </div>
              
              <!-- 使用 DownloadTaskCard 组件 -->
              <v-list v-if="filteredDownloads.length > 0" class="pa-0">
                <DownloadTaskCard
                  v-for="download in filteredDownloads"
                  :key="download.id"
                  :task="download"
                  :selected="selectedDownloads.includes(download.id)"
                  :show-selection="true"
                  @toggleSelection="toggleSelection"
                  @pause="handlePauseTask"
                  @resume="handleResumeTask"
                  @queueTop="handleQueueTop"
                  @delete="handleDeleteTask"
                  @speedLimit="handleSpeedLimit"
                  @openOrganize="handleOpenOrganize"
                />
              </v-list>

              <v-empty-state
                v-else-if="!loading"
                icon="mdi-download-off"
                title="暂无下载中任务"
                text="当前没有正在下载的任务"
                class="pa-8"
              >
                <v-btn @click="refreshData">刷新</v-btn>
              </v-empty-state>

              <v-skeleton-loader
                v-if="loading"
                type="list-item-three-line@4"
                class="pa-4"
              />
            </div>
          </v-card-text>
        </v-window-item>
        
        <v-window-item value="queued">
          <v-card-text class="pa-0">
            <!-- 排队中任务列表 - P3 卡片UI强化 -->
            <div class="download-list">
              <div class="d-flex align-center pa-4">
                <v-btn
                  variant="text"
                  :loading="loading"
                  @click="refreshData"
                  prepend-icon="mdi-refresh"
                >
                  刷新
                </v-btn>
                <v-spacer />
                <div class="text-caption text-medium-emphasis">
                  共 {{ filteredDownloads.length }} 个排队任务
                </div>
              </div>
              
              <!-- 使用 DownloadTaskCard 组件 -->
              <v-list v-if="filteredDownloads.length > 0" class="pa-0">
                <DownloadTaskCard
                  v-for="download in filteredDownloads"
                  :key="download.id"
                  :task="download"
                  :selected="selectedDownloads.includes(download.id)"
                  :show-selection="true"
                  @toggleSelection="toggleSelection"
                  @pause="handlePauseTask"
                  @resume="handleResumeTask"
                  @queueTop="handleQueueTop"
                  @delete="handleDeleteTask"
                  @speedLimit="handleSpeedLimit"
                  @openOrganize="handleOpenOrganize"
                />
              </v-list>

              <v-empty-state
                v-else-if="!loading"
                icon="mdi-clock-outline"
                title="暂无排队任务"
                text="当前没有排队中的任务"
                class="pa-8"
              >
                <v-btn @click="refreshData">刷新</v-btn>
              </v-empty-state>

              <v-skeleton-loader
                v-if="loading"
                type="list-item-two-line@3"
                class="pa-4"
              />
            </div>
          </v-card-text>
        </v-window-item>
        
        <v-window-item value="error">
          <v-card-text class="pa-0">
            <!-- 异常/失败任务列表 - P3 卡片UI强化 -->
            <div class="download-list">
              <div class="d-flex align-center pa-4">
                <v-btn
                  variant="text"
                  :loading="loading"
                  @click="refreshData"
                  prepend-icon="mdi-refresh"
                >
                  刷新
                </v-btn>
                <v-spacer />
                <div class="text-caption text-medium-emphasis">
                  共 {{ filteredDownloads.length }} 个异常任务
                </div>
              </div>
              
              <!-- 使用 DownloadTaskCard 组件 -->
              <v-list v-if="filteredDownloads.length > 0" class="pa-0">
                <DownloadTaskCard
                  v-for="download in filteredDownloads"
                  :key="download.id"
                  :task="download"
                  :selected="selectedDownloads.includes(download.id)"
                  :show-selection="true"
                  @toggleSelection="toggleSelection"
                  @pause="handlePauseTask"
                  @resume="handleResumeTask"
                  @queueTop="handleQueueTop"
                  @delete="handleDeleteTask"
                  @speedLimit="handleSpeedLimit"
                  @openOrganize="handleOpenOrganize"
                />
              </v-list>

              <v-empty-state
                v-else-if="!loading"
                icon="mdi-alert-circle"
                title="暂无异常任务"
                text="当前没有异常或失败的任务"
                class="pa-8"
              >
                <v-btn @click="refreshData">刷新</v-btn>
              </v-empty-state>

              <v-skeleton-loader
                v-if="loading"
                type="list-item-two-line@3"
                class="pa-4"
              />
            </div>
          </v-card-text>
        </v-window-item>
        
        <v-window-item value="recent_completed">
          <v-card-text class="pa-0">
            <!-- 最近完成任务列表 - P3 卡片UI强化 -->
            <v-alert
              type="info"
              variant="tonal"
              class="ma-4 download-complete-alert"
              text="最近完成的任务将显示在这里。完整的下载历史和整理记录请前往「媒体整理」页面查看。"
            >
              <template v-slot:append>
                <v-btn
                  variant="text"
                  color="info"
                  class="quick-nav-btn"
                  @click="navigateToTransferHistory"
                >
                  查看整理记录
                  <v-icon end>mdi-arrow-right</v-icon>
                </v-btn>
              </template>
            </v-alert>
            
            <div class="download-list">
              <div class="d-flex align-center pa-4">
                <v-btn
                  variant="text"
                  :loading="loading"
                  @click="refreshData"
                  prepend-icon="mdi-refresh"
                >
                  刷新
                </v-btn>
                <v-spacer />
                <div class="text-caption text-medium-emphasis">
                  共 {{ filteredDownloads.length }} 个最近完成任务
                </div>
              </div>
              
              <!-- 使用 DownloadTaskCard 组件 -->
              <v-list v-if="filteredDownloads.length > 0" class="pa-0">
                <DownloadTaskCard
                  v-for="download in filteredDownloads"
                  :key="download.id"
                  :task="download"
                  :selected="selectedDownloads.includes(download.id)"
                  :show-selection="true"
                  @toggleSelection="toggleSelection"
                  @pause="handlePauseTask"
                  @resume="handleResumeTask"
                  @queueTop="handleQueueTop"
                  @delete="handleDeleteTask"
                  @speedLimit="handleSpeedLimit"
                  @openOrganize="handleOpenOrganize"
                />
              </v-list>

              <v-empty-state
                v-else-if="!loading"
                icon="mdi-check-circle"
                title="暂无最近完成任务"
                text="最近没有完成的下载任务"
                class="pa-8"
              >
                <v-btn @click="refreshData">刷新</v-btn>
              </v-empty-state>

              <v-skeleton-loader
                v-if="loading"
                type="list-item-two-line@3"
                class="pa-4"
              />
            </div>
          </v-card-text>
        </v-window-item>
      </v-window>
  </v-card>

  <!-- P4 串联流程：媒体整理对话框 -->
  <v-dialog
    v-model="mediaOrganizeDialog"
    max-width="800px"
    persistent
  >
    <v-card v-if="organizingDownload">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2" color="primary">mdi-folder-move</v-icon>
        媒体整理
      </v-card-title>
      
      <v-card-text>
        <div class="mb-4">
          <h3 class="text-h6 mb-2">{{ organizingDownload.title || organizingDownload.name }}</h3>
          <div class="d-flex align-center ga-2">
            <v-chip
              v-if="organizingDownload.site_name"
              size="small"
              variant="tonal"
              :color="getSiteColor(organizingDownload.site_name)"
            >
              {{ organizingDownload.site_name }}
            </v-chip>
            <v-chip
              v-if="organizingDownload.is_short_drama"
              size="small"
              variant="tonal"
              color="purple"
            >
              短剧
            </v-chip>
            <span class="text-caption text-medium-emphasis">
              {{ formatSize(organizingDownload.total_size || 0) }}
            </span>
          </div>
        </div>

        <v-divider class="mb-4" />

        <!-- P4: 媒体整理表单 -->
        <v-form ref="organizeForm">
          <v-row>
            <v-col cols="12" md="6">
              <v-select
                label="媒体类型"
                :items="[
                  { title: '电影', value: 'movie' },
                  { title: '剧集', value: 'tv' },
                  { title: '纪录片', value: 'documentary' },
                  { title: '动画', value: 'anime' },
                  { title: '短剧', value: 'short_drama' }
                ]"
                v-model="organizeForm.media_type"
                variant="outlined"
                density="compact"
              />
            </v-col>
            
            <v-col cols="12" md="6">
              <v-select
                label="目标文件夹"
                :items="[
                  { title: '电影', value: '/movies' },
                  { title: '剧集', value: '/tv' },
                  { title: '纪录片', value: '/documentaries' },
                  { title: '动画', value: '/anime' },
                  { title: '短剧', value: '/short_dramas' }
                ]"
                v-model="organizeForm.target_folder"
                variant="outlined"
                density="compact"
              />
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                label="标题"
                v-model="organizeForm.title"
                variant="outlined"
                density="compact"
                :placeholder="organizingDownload.title || organizingDownload.name"
              />
            </v-col>
            
            <v-col cols="12" md="6">
              <v-text-field
                label="年份"
                v-model="organizeForm.year"
                type="number"
                variant="outlined"
                density="compact"
                placeholder="2024"
              />
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="12">
              <v-textarea
                label="描述"
                v-model="organizeForm.description"
                variant="outlined"
                density="compact"
                rows="3"
                placeholder="添加媒体描述信息..."
              />
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="12">
              <v-checkbox
                label="整理后删除原文件"
                v-model="organizeForm.delete_source"
                color="warning"
                density="compact"
              />
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          variant="text"
          @click="mediaOrganizeDialog = false"
        >
          取消
        </v-btn>
        <v-btn
          variant="tonal"
          color="primary"
          @click="handleMediaOrganize(organizeForm)"
          :loading="organizeLoading"
        >
          开始整理
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
    
    <!-- 速度限制对话框 -->
    <SpeedLimitDialog
      v-model="speedLimitDialog"
      :task-id="speedLimitTask?.id"
      :task-ids="speedLimitTask?.id ? undefined : selectedDownloads"
      :downloader="speedLimitDownloader"
      :current-download-limit="speedLimitTask?.download_limit"
      :current-upload-limit="speedLimitTask?.upload_limit"
      @saved="handleSpeedLimitSaved"
    />
  </div>
</template>

<script setup lang="ts">
// 移除未使用的导入
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { downloadApi } from '@/services/api'
import { useToast } from '@/composables/useToast'
import PageHeader from '@/components/common/PageHeader.vue'
import DownloadTaskCard from '@/components/download/DownloadTaskCard.vue'
import SpeedLimitDialog from '@/components/downloads/SpeedLimitDialog.vue'
import { useWebSocket } from '@/composables/useWebSocket'

const toast = useToast()
const route = useRoute()
const router = useRouter()
const loading = ref(false)
const downloads = ref<any[]>([])
const downloadMap = ref<Map<string, any>>(new Map())
const activeTab = ref('all_active')  // DOWNLOAD-CENTER-UI-1: 默认显示全部任务
const selectedDownloads = ref<string[]>([])

// 速度限制对话框
const speedLimitDialog = ref(false)
const speedLimitTask = ref<any>(null)
const speedLimitDownloader = ref<string>('')

// 过滤条件
const filters = ref({
  search: ''  // vabhubOnly 已移除，因为只显示带VABHUB标签的任务是唯一选择
})
const mediaTypeFilter = ref(
  typeof route.query.media_type === 'string' ? (route.query.media_type as string) : 'all'
)

const matchesDownloadFilters = (download: any) => {
  if (filters.value.search) {
    const search = filters.value.search.toLowerCase()
    if (!download.title?.toLowerCase().includes(search)) {
      return false
    }
  }
  if (mediaTypeFilter.value === 'short_drama' && download.media_type !== 'short_drama') {
    return false
  }
  return true
}

// WebSocket连接 - 移除未使用的subscribe
const { isConnected } = useWebSocket({
  topics: ['downloads'],
  onMessage: (message) => {
    if (message.type === 'download_update') {
      // 更新单个下载任务
      const download = message.data
      if (download && download.id) {
        downloadMap.value.set(download.id, download)
        updateDownloadsList()
      }
    } else if (message.type === 'download_progress') {
      // 更新下载进度
      const progress = message.data
      if (progress && progress.task_id) {
        const existing = downloadMap.value.get(progress.task_id)
        if (existing) {
          Object.assign(existing, progress)
          updateDownloadsList()
        }
      }
    } else if (message.type === 'download_list') {
      // 更新整个列表
      if (message.data && Array.isArray(message.data)) {
        message.data.forEach((download: any) => {
          if (download && download.id) {
            downloadMap.value.set(download.id, download)
          }
        })
        updateDownloadsList()
      }
    }
  },
  onConnect: () => {
    console.log('[Downloads] WebSocket已连接，开始接收实时更新')
    // 连接成功后，请求最新列表
    refreshData()
  },
  onDisconnect: () => {
    console.log('[Downloads] WebSocket已断开，使用轮询模式')
    // 断开后，启动轮询作为备选方案
    startPolling()
  },
  onError: (error) => {
    console.error('[Downloads] WebSocket错误:', error)
  }
})

// 统计信息 - DOWNLOAD-CENTER-UI-1 重构
const stats = computed(() => {
  const all = Array.from(downloadMap.value.values())
  return {
    downloading: all.filter(d => d.status === 'downloading').length,
    queued: all.filter(d => d.status === 'queued' || d.status === 'checking' || d.status === 'allocating').length,
    error: all.filter(d => d.status === 'failed' || d.status === 'error' || d.status === 'stalled').length,
    recent_completed: all.filter(d => d.status === 'completed').length
  }
})

// 总下载速度
const totalSpeed = computed(() => {
  const downloading = Array.from(downloadMap.value.values())
    .filter(d => d.status === 'downloading')
  return downloading.reduce((sum, d) => sum + ((d.speed_mbps || 0) * 1024 * 1024), 0)
})

// 格式化速度
const formatSpeed = (bytes: number) => {
  if (!bytes || bytes === 0) return '0 B/s'
  if (bytes < 1024) return `${bytes.toFixed(0)} B/s`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB/s`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(2)} MB/s`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB/s`
}

// P3 卡片UI强化辅助方法
const getSiteColor = (siteName: string) => {
  const siteColors: Record<string, string> = {
    'PTer': 'blue',
    'HDF': 'green',
    'TTG': 'orange',
    'HDChina': 'red',
    'CHD': 'purple'
  }
  return siteColors[siteName] || 'grey'
}

const formatSize = (bytes: number) => {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 过滤变化处理
const handleFilterChange = () => {
  // 过滤逻辑已通过computed实现
}

// P3 选择管理 - 移除未使用的函数
const toggleSelection = (id: string) => {
  const index = selectedDownloads.value.indexOf(id)
  if (index > -1) {
    selectedDownloads.value.splice(index, 1)
  } else {
    selectedDownloads.value.push(id)
  }
}

// P4 串联流程：响应式变量
const organizeLoading = ref(false)
const organizeForm = ref({
  task_id: '',
  media_type: '',
  target_folder: '',
  title: '',
  source_path: '',
  year: '',
  description: '',
  delete_source: false
})

const handleDeleteTask = (id: string) => {
  // TODO: 实现删除任务逻辑
  console.log('删除任务:', id)
}

const handlePauseTask = (id: string) => {
  // TODO: 实现暂停任务逻辑
  console.log('暂停任务:', id)
}

const handleResumeTask = (id: string) => {
  // TODO: 实现恢复任务逻辑
  console.log('恢复任务:', id)
}

// DOWNLOAD-CENTER-UI-2: 手动整理处理器
const handleOpenOrganize = (taskId: string) => {
  // 找到对应的下载任务
  const task = downloads.value.find(d => d.id === taskId)
  if (task) {
    // 设置当前整理任务并打开手动整理对话框
    organizeForm.value.task_id = taskId
    organizeForm.value.title = task.title || task.name || '未知任务'
    organizeForm.value.source_path = task.save_path || '' // 可从任务信息获取
    mediaOrganizeDialog.value = true
  }
}

// P4: 媒体整理对话框
const mediaOrganizeDialog = ref(false)
const organizingDownload = ref<any>(null)

const handleMediaOrganize = (organizeData: any) => {
  // TODO: 调用媒体整理API
  console.log('媒体整理数据:', organizeData)
  mediaOrganizeDialog.value = false
  organizingDownload.value = null
  
  // P4: 整理完成后跳转到媒体详情页
  if (organizeData.mediaId) {
    router.push(`/media/${organizeData.mediaId}`)
  }
}

// P4: 快速导航到媒体整理记录
const navigateToTransferHistory = () => {
  router.push('/transfer-history')
}

// DOWNLOAD-CENTER-UI-1: 统一的过滤下载列表 - 替换旧的分类列表
const filteredDownloads = computed(() => {
  const allDownloads = downloads.value
  
  // 根据当前Tab进行状态过滤
  let statusFiltered = allDownloads
  if (activeTab.value === 'downloading') {
    statusFiltered = allDownloads.filter(d => d.status === 'downloading')
  } else if (activeTab.value === 'queued') {
    statusFiltered = allDownloads.filter(d => d.status === 'queued' || d.status === 'checking' || d.status === 'allocating')
  } else if (activeTab.value === 'error') {
    statusFiltered = allDownloads.filter(d => d.status === 'failed' || d.status === 'error' || d.status === 'stalled')
  } else if (activeTab.value === 'recent_completed') {
    statusFiltered = allDownloads.filter(d => d.status === 'completed')
  }
  // all_active 不需要状态过滤
  
  // 应用搜索和媒体类型过滤
  return statusFiltered.filter(matchesDownloadFilters)
})

// 更新下载列表
const updateDownloadsList = () => {
  downloads.value = Array.from(downloadMap.value.values())
    .sort((a, b) => {
      const timeA = new Date(a.created_at || 0).getTime()
      const timeB = new Date(b.created_at || 0).getTime()
      return timeB - timeA
    })
}

// 批量操作 - 移除未使用的函数和变量引用
const pauseAll = async () => {
  if (selectedDownloads.value.length === 0) {
    toast.warning('请先选择要暂停的下载任务')
    return
  }
  
  await handleBatchPause(selectedDownloads.value)
}

const handleBatchPause = async (ids: string[]) => {
  try {
    await downloadApi.batchPause(ids)
    toast.success(`已暂停 ${ids.length} 个任务`)
    selectedDownloads.value = []
    refreshData()
  } catch (error: any) {
    toast.error('批量暂停失败：' + (error.message || '未知错误'))
  }
}

// 清理已完成任务 - 修复未定义的变量引用
const clearCompleted = async () => {
  if (!confirm('确定要清理所有已完成的下载任务吗？')) {
    return
  }
  
  try {
    const allDownloads = Array.from(downloadMap.value.values())
    const completed = allDownloads.filter(d => d.status === 'completed').map(d => d.id)
    
    if (completed.length === 0) {
      toast.info('没有已完成的任务')
      return
    }
    
    await downloadApi.batchDelete(completed, false)
    toast.success('已清理所有已完成的任务')
    refreshData()
  } catch (error: any) {
    toast.error('清理失败：' + (error.message || '未知错误'))
  }
}

// 队列管理 - 只保留 handleQueueTop（在组件中使用）
const handleQueueTop = async (id: string) => {
  try {
    await downloadApi.queueMoveTop(id)
    toast.success('置顶成功')
    refreshData()
  } catch (error: any) {
    toast.error('置顶失败：' + (error.message || '未知错误'))
  }
}

// 速度限制处理
const handleSpeedLimit = (download: any) => {
  speedLimitTask.value = download
  speedLimitDownloader.value = download.downloader || 'qBittorrent'
  speedLimitDialog.value = true
}

const handleSpeedLimitSaved = () => {
  speedLimitDialog.value = false
  speedLimitTask.value = null
  refreshData()
}

// 批量速度限制
const handleBatchSpeedLimit = () => {
  if (selectedDownloads.value.length === 0) {
    toast.warning('请先选择要设置速度限制的下载任务')
    return
  }
  
  speedLimitTask.value = { id: null } // 批量操作，id为null
  speedLimitDialog.value = true
}

// 轮询备选方案
let pollingInterval: ReturnType<typeof setInterval> | null = null

const startPolling = () => {
  if (pollingInterval) {
    return
  }
  
  // 每5秒轮询一次
  pollingInterval = setInterval(() => {
    if (!isConnected.value) {
      refreshData()
    }
  }, 5000)
}

const stopPolling = () => {
  if (pollingInterval) {
    clearInterval(pollingInterval)
    pollingInterval = null
  }
}

const refreshData = async () => {
  loading.value = true
  try {
    const params: any = {
      vabhub_only: true  // 只显示带VABHUB标签的任务（唯一选择）
    }
    
    // P3: 根据Tab类型设置不同的过滤策略
    if (activeTab.value === 'recent_completed') {
      // 最近完成Tab：显示所有完成的任务，不受hide_organized限制
      params.status = 'completed'
      params.recent_hours = 24  // P3: 限制最近24小时内的完成任务
    } else {
      // 其他Tab：自动隐藏已整理完成的任务
      params.hide_organized = true
      
      // DOWNLOAD-CENTER-UI-1: 根据当前Tab设置状态过滤
      if (activeTab.value !== 'all_active') {
        params.status = activeTab.value
      }
    }
    
    const response = await downloadApi.getDownloads(params)
    // 处理统一响应格式
    let newDownloads: any[] = []
    if (response.data?.items) {
      newDownloads = response.data.items
    } else if (Array.isArray(response.data)) {
      newDownloads = response.data
    }
    
    // 更新下载映射
    newDownloads.forEach((download: any) => {
      downloadMap.value.set(download.id, download)
    })
    
    updateDownloadsList()
  } catch (error: any) {
    console.error('加载下载列表失败:', error)
    toast.error('加载下载列表失败：' + (error.message || '未知错误'))
    downloads.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  refreshData()
})

onUnmounted(() => {
  stopPolling()
})

watch(
  () => route.query.media_type,
  (val) => {
    mediaTypeFilter.value = typeof val === 'string' ? (val as string) : 'all'
  }
)

watch(mediaTypeFilter, (val) => {
  const query = { ...route.query }
  if (val && val !== 'all') {
    query.media_type = val
  } else {
    delete query.media_type
  }
  router.replace({ query })
})

// DOWNLOAD-CENTER-UI-1: 监听Tab变化，刷新数据
watch(activeTab, () => {
  refreshData()
})
</script>

<style scoped>
.downloads-page {
  padding: 24px;
}

.stat-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.12);
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 0.875rem;
  opacity: 0.9;
}

/* P3 卡片UI强化样式 */
.download-list {
  background: transparent;
}

.download-item {
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  transition: background-color 0.2s ease;
}

.download-item:hover {
  background-color: rgba(0, 0, 0, 0.02);
}

.download-item.selected {
  background-color: rgba(25, 118, 210, 0.08);
}

.download-title {
  line-height: 1.4;
}

/* P3 UI强化：站点和标签chips样式 */
.site-chip, .hr-chip, .short-drama-chip, .label-chip {
  font-weight: 500;
  letter-spacing: 0.025em;
}

.site-chip {
  background: linear-gradient(135deg, var(--v-theme-surface-variant), var(--v-theme-surface));
}

.hr-chip {
  font-weight: 600;
}

.hr-chip.v-chip--variant-flat {
  box-shadow: 0 2px 4px rgba(var(--v-theme-error), 0.2);
}

.short-drama-chip {
  background: linear-gradient(135deg, rgba(156, 39, 176, 0.1), rgba(156, 39, 176, 0.05));
}

.label-chip {
  opacity: 0.8;
}

/* P3 进度条优化样式 */
.progress-section {
  min-height: 60px;
}

.progress-info, .speed-info {
  display: flex;
  align-items: center;
  gap: 4px;
}

.v-progress-linear ::v-deep(.v-progress-linear__buffer) {
  transition: width 0.3s ease;
}

.v-progress-linear ::v-deep(.v-progress-linear__determinate) {
  transition: width 0.3s ease;
}

.v-progress-linear ::v-deep(.v-progress-linear__content) {
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

/* P3 操作按钮优化 */
.v-btn--icon.v-btn--size-small {
  width: 32px;
  height: 32px;
  transition: all 0.2s ease;
}

.v-btn--icon.v-btn--size-small:hover {
  transform: scale(1.1);
}

/* 响应式优化 */
@media (max-width: 768px) {
  .download-item {
    padding: 8px 12px;
  }
  
  .site-chip, .hr-chip, .short-drama-chip, .label-chip {
    font-size: 10px;
    height: 20px;
  }
  
  .progress-section {
    min-height: 50px;
  }
  
  .v-btn--icon.v-btn--size-small {
    width: 28px;
    height: 28px;
  }
}

/* P4 串联流程：下载完成自动跳转提示 */
.download-complete-alert {
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateY(-10px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* P4 媒体整理状态回显 */
.media-status-badge {
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* P4 快速导航按钮 */
.quick-nav-btn {
  background: linear-gradient(135deg, var(--v-theme-primary), var(--v-theme-primary-darken-1));
  color: white;
  font-weight: 600;
  transition: all 0.3s ease;
}

.quick-nav-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.3);
}

/* P5 QA验收：性能优化 */
.download-item {
  will-change: background-color;
}

.v-progress-linear {
  will-change: width;
}

/* 动画性能优化 */
@media (prefers-reduced-motion: reduce) {
  .download-item,
  .v-progress-linear ::v-deep(.v-progress-linear__buffer),
  .v-progress-linear ::v-deep(.v-progress-linear__determinate),
  .v-btn--icon.v-btn--size-small {
    transition: none;
  }
}
</style>
