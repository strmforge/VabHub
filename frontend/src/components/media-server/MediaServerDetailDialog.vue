<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="1000"
    scrollable
  >
    <v-card v-if="serverData">
      <v-card-title class="d-flex align-center justify-space-between">
        <span class="text-h5">{{ serverData.name }}</span>
        <v-btn
          icon="mdi-close"
          variant="text"
          size="small"
          @click="$emit('update:modelValue', false)"
        />
      </v-card-title>

      <v-card-text>
        <v-tabs v-model="activeTab" bg-color="surface">
          <v-tab value="info">
            <v-icon start>mdi-information</v-icon>
            服务器信息
          </v-tab>
          <v-tab value="sync">
            <v-icon start>mdi-sync</v-icon>
            同步历史
          </v-tab>
          <v-tab value="playback">
            <v-icon start>mdi-play</v-icon>
            播放会话
          </v-tab>
        </v-tabs>

        <v-window v-model="activeTab" class="mt-4">
          <!-- 服务器信息标签页 -->
          <v-window-item value="info">
            <v-row>
              <v-col cols="12" md="6">
                <v-card variant="outlined">
                  <v-card-title class="text-subtitle-1">基本信息</v-card-title>
                  <v-card-text>
                    <div class="mb-3">
                      <div class="text-caption text-medium-emphasis">服务器名称</div>
                      <div class="text-body-1">{{ serverData.name }}</div>
                    </div>
                    <div class="mb-3">
                      <div class="text-caption text-medium-emphasis">服务器类型</div>
                      <v-chip
                        :color="getServerTypeColor(serverData.server_type)"
                        size="small"
                        variant="flat"
                      >
                        {{ getServerTypeText(serverData.server_type) }}
                      </v-chip>
                    </div>
                    <div class="mb-3">
                      <div class="text-caption text-medium-emphasis">服务器地址</div>
                      <div class="text-body-1">{{ serverData.url }}</div>
                    </div>
                    <div class="mb-3">
                      <div class="text-caption text-medium-emphasis">状态</div>
                      <v-chip
                        :color="getStatusColor(serverData.status)"
                        size="small"
                        variant="flat"
                      >
                        {{ getStatusText(serverData.status) }}
                      </v-chip>
                    </div>
                    <div class="mb-3">
                      <div class="text-caption text-medium-emphasis">启用状态</div>
                      <v-chip
                        :color="serverData.enabled ? 'success' : 'grey'"
                        size="small"
                        variant="flat"
                      >
                        {{ serverData.enabled ? '启用' : '禁用' }}
                      </v-chip>
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>

              <v-col cols="12" md="6">
                <v-card variant="outlined">
                  <v-card-title class="text-subtitle-1">同步配置</v-card-title>
                  <v-card-text>
                    <div class="mb-3">
                      <div class="text-caption text-medium-emphasis">自动同步</div>
                      <v-chip
                        :color="serverData.sync_enabled ? 'success' : 'grey'"
                        size="small"
                        variant="flat"
                      >
                        {{ serverData.sync_enabled ? '启用' : '禁用' }}
                      </v-chip>
                    </div>
                    <div class="mb-3">
                      <div class="text-caption text-medium-emphasis">同步间隔</div>
                      <div class="text-body-1">{{ formatDuration(serverData.sync_interval || 3600) }}</div>
                    </div>
                    <div class="mb-3">
                      <div class="text-caption text-medium-emphasis">同步观看状态</div>
                      <v-chip
                        :color="serverData.sync_watched_status ? 'success' : 'grey'"
                        size="small"
                        variant="flat"
                      >
                        {{ serverData.sync_watched_status ? '启用' : '禁用' }}
                      </v-chip>
                    </div>
                    <div class="mb-3">
                      <div class="text-caption text-medium-emphasis">同步播放状态</div>
                      <v-chip
                        :color="serverData.sync_playback_status ? 'success' : 'grey'"
                        size="small"
                        variant="flat"
                      >
                        {{ serverData.sync_playback_status ? '启用' : '禁用' }}
                      </v-chip>
                    </div>
                    <div class="mb-3">
                      <div class="text-caption text-medium-emphasis">同步元数据</div>
                      <v-chip
                        :color="serverData.sync_metadata ? 'success' : 'grey'"
                        size="small"
                        variant="flat"
                      >
                        {{ serverData.sync_metadata ? '启用' : '禁用' }}
                      </v-chip>
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>

              <v-col cols="12">
                <v-card variant="outlined">
                  <v-card-title class="text-subtitle-1">媒体统计</v-card-title>
                  <v-card-text>
                    <v-row>
                      <v-col cols="12" sm="4">
                        <div class="text-center">
                          <div class="text-h4 text-primary">{{ serverData.total_movies || 0 }}</div>
                          <div class="text-caption text-medium-emphasis">电影</div>
                        </div>
                      </v-col>
                      <v-col cols="12" sm="4">
                        <div class="text-center">
                          <div class="text-h4 text-success">{{ serverData.total_tv_shows || 0 }}</div>
                          <div class="text-caption text-medium-emphasis">剧集</div>
                        </div>
                      </v-col>
                      <v-col cols="12" sm="4">
                        <div class="text-center">
                          <div class="text-h4 text-info">{{ serverData.total_episodes || 0 }}</div>
                          <div class="text-caption text-medium-emphasis">剧集数</div>
                        </div>
                      </v-col>
                    </v-row>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-window-item>

          <!-- 同步历史标签页 -->
          <v-window-item value="sync">
            <MediaServerSyncHistory
              :server-id="serverId"
              :loading="loadingSyncHistory"
            />
          </v-window-item>

          <!-- 播放会话标签页 -->
          <v-window-item value="playback">
            <MediaServerPlaybackSessions
              :server-id="serverId"
              :loading="loadingPlayback"
            />
          </v-window-item>
        </v-window>
      </v-card-text>

      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn
          color="primary"
          prepend-icon="mdi-check-circle"
          @click="checkConnection"
          :loading="checking"
        >
          检查连接
        </v-btn>
        <v-btn
          color="success"
          prepend-icon="mdi-sync"
          @click="syncLibraries"
          :loading="syncing"
        >
          同步媒体库
        </v-btn>
        <v-btn
          variant="text"
          @click="$emit('update:modelValue', false)"
        >
          关闭
        </v-btn>
      </v-card-actions>
    </v-card>

    <!-- 加载状态 -->
    <v-card v-else>
      <v-card-text class="text-center py-8">
        <v-progress-circular indeterminate color="primary"></v-progress-circular>
        <div class="mt-4 text-body-2 text-medium-emphasis">加载中...</div>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { mediaServerApi } from '@/services/api'
import { useToast } from '@/composables/useToast'
import MediaServerSyncHistory from './MediaServerSyncHistory.vue'
import MediaServerPlaybackSessions from './MediaServerPlaybackSessions.vue'

const props = defineProps<{
  modelValue: boolean
  serverId: number | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  refresh: []
}>()

const { showToast } = useToast()

const serverData = ref<any>(null)
const activeTab = ref('info')
const loading = ref(false)
const loadingSyncHistory = ref(false)
const loadingPlayback = ref(false)
const checking = ref(false)
const syncing = ref(false)

// 加载服务器详情
const loadServerDetails = async () => {
  if (!props.serverId) return

  try {
    loading.value = true
    const response = await mediaServerApi.getMediaServer(props.serverId)
    serverData.value = response.data
  } catch (error: any) {
    console.error('加载服务器详情失败:', error)
    showToast('加载服务器详情失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    loading.value = false
  }
}

// 检查连接
const checkConnection = async () => {
  if (!props.serverId) return

  try {
    checking.value = true
    await mediaServerApi.checkConnection(props.serverId)
    showToast('连接检查成功', 'success')
    await loadServerDetails()
    emit('refresh')
  } catch (error: any) {
    showToast('连接检查失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    checking.value = false
  }
}

// 同步媒体库
const syncLibraries = async () => {
  if (!props.serverId) return

  try {
    syncing.value = true
    await mediaServerApi.syncLibraries(props.serverId)
    showToast('媒体库同步已启动', 'success')
    await loadServerDetails()
    emit('refresh')
  } catch (error: any) {
    showToast('同步失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    syncing.value = false
  }
}

// 监听对话框打开
watch(() => props.modelValue, (newVal) => {
  if (newVal && props.serverId) {
    loadServerDetails()
    activeTab.value = 'info'
  }
})

// 监听serverId变化
watch(() => props.serverId, (newId) => {
  if (newId && props.modelValue) {
    loadServerDetails()
  }
})

// 获取服务器类型颜色
const getServerTypeColor = (type: string): string => {
  switch (type?.toLowerCase()) {
    case 'plex':
      return 'orange'
    case 'jellyfin':
      return 'purple'
    case 'emby':
      return 'blue'
    default:
      return 'grey'
  }
}

// 获取服务器类型文本
const getServerTypeText = (type: string): string => {
  switch (type?.toLowerCase()) {
    case 'plex':
      return 'Plex'
    case 'jellyfin':
      return 'Jellyfin'
    case 'emby':
      return 'Emby'
    default:
      return type || '未知'
  }
}

// 获取状态颜色
const getStatusColor = (status: string): string => {
  switch (status) {
    case 'online':
      return 'success'
    case 'offline':
      return 'error'
    case 'error':
      return 'error'
    default:
      return 'grey'
  }
}

// 获取状态文本
const getStatusText = (status: string): string => {
  switch (status) {
    case 'online':
      return '在线'
    case 'offline':
      return '离线'
    case 'error':
      return '错误'
    default:
      return '未知'
  }
}

// 格式化时长
const formatDuration = (seconds: number): string => {
  if (seconds < 60) {
    return `${seconds}秒`
  } else if (seconds < 3600) {
    return `${Math.floor(seconds / 60)}分钟`
  } else {
    return `${Math.floor(seconds / 3600)}小时`
  }
}
</script>

