<template>
  <div>
    <v-data-table
      :headers="headers"
      :items="playbackSessions"
      :loading="loading"
      class="elevation-0"
    >
      <template v-slot:item.media_type="{ item }">
        <v-chip
          :color="getMediaTypeColor(item.media_type)"
          size="small"
          variant="flat"
        >
          {{ getMediaTypeText(item.media_type) }}
        </v-chip>
      </template>

      <template v-slot:item.progress_percent="{ item }">
        <v-progress-linear
          :model-value="item.progress_percent || 0"
          :color="getProgressColor(item.progress_percent || 0)"
          height="20"
          rounded
        >
          <template v-slot:default>
            <strong class="text-white">{{ (item.progress_percent || 0).toFixed(1) }}%</strong>
          </template>
        </v-progress-linear>
      </template>

      <template v-slot:item.started_at="{ item }">
        {{ formatDateTime(item.started_at) }}
      </template>

      <template v-slot:item.last_activity="{ item }">
        {{ item.last_activity ? formatDateTime(item.last_activity) : '-' }}
      </template>

      <template v-slot:no-data>
        <div class="text-center py-8">
          <v-icon size="64" color="grey-lighten-1">mdi-play-circle-outline</v-icon>
          <div class="text-h6 mt-4 text-medium-emphasis">暂无播放会话</div>
        </div>
      </template>
    </v-data-table>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { mediaServerApi } from '@/services/api'
import { useToast } from '@/composables/useToast'

const props = defineProps<{
  serverId: number | null
  loading: boolean
}>()

const { showToast } = useToast()

const playbackSessions = ref<any[]>([])

const headers = [
  { title: '用户', key: 'user_name', sortable: true },
  { title: '媒体标题', key: 'title', sortable: true },
  { title: '媒体类型', key: 'media_type', sortable: true },
  { title: '播放进度', key: 'progress_percent', sortable: true },
  { title: '开始时间', key: 'started_at', sortable: true },
  { title: '最后活动', key: 'last_activity', sortable: true }
]

// 加载播放会话
const loadPlaybackSessions = async () => {
  if (!props.serverId) return

  try {
    const response = await mediaServerApi.getPlaybackSessions(props.serverId)
    playbackSessions.value = response.data || []
  } catch (error: any) {
    console.error('加载播放会话失败:', error)
    showToast('加载播放会话失败: ' + (error.message || '未知错误'), 'error')
  }
}

// 获取媒体类型颜色
const getMediaTypeColor = (type: string): string => {
  switch (type?.toLowerCase()) {
    case 'movie':
      return 'primary'
    case 'episode':
      return 'success'
    case 'music':
      return 'info'
    default:
      return 'grey'
  }
}

// 获取媒体类型文本
const getMediaTypeText = (type: string): string => {
  switch (type?.toLowerCase()) {
    case 'movie':
      return '电影'
    case 'episode':
      return '剧集'
    case 'music':
      return '音乐'
    default:
      return type || '未知'
  }
}

// 获取进度颜色
const getProgressColor = (percent: number): string => {
  if (percent >= 90) return 'success'
  if (percent >= 50) return 'info'
  return 'primary'
}

// 格式化日期时间
const formatDateTime = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 监听serverId变化
watch(() => props.serverId, (newId) => {
  if (newId) {
    loadPlaybackSessions()
  }
}, { immediate: true })

onMounted(() => {
  if (props.serverId) {
    loadPlaybackSessions()
  }
})
</script>

