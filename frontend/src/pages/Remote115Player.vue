<template>
  <div class="remote-115-player-page">
    <!-- 顶部 PageHeader -->
    <div class="player-header">
      <v-btn
        icon
        variant="text"
        @click="router.back()"
        class="mr-4"
      >
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
      <div class="flex-grow-1">
        <div class="text-h6">{{ playOptions?.file_name || '加载中...' }}</div>
        <div v-if="workYear" class="text-caption text-medium-emphasis">{{ workYear }}</div>
      </div>
      <v-chip color="deep-purple" text-color="white" size="small">
        115 远程播放
      </v-chip>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="d-flex justify-center align-center" style="min-height: 400px">
      <v-progress-circular indeterminate color="primary" size="64" />
      <div class="ml-4 text-body-1">加载播放信息...</div>
    </div>

    <!-- 错误状态 -->
    <v-alert
      v-else-if="error"
      type="error"
      variant="tonal"
      class="ma-4"
    >
      {{ error }}
    </v-alert>

    <!-- 播放器区域 -->
    <div v-else-if="playOptions" class="player-container">
      <v-row no-gutters class="fill-height">
        <!-- 左侧：视频播放器（桌面端 2/3，移动端全宽） -->
        <v-col cols="12" md="8" class="player-video-col">
          <div class="video-wrapper">
            <video
              ref="videoEl"
              controls
              playsinline
              class="video-player"
              style="aspect-ratio: 16/9;"
              @canplay="onVideoCanPlay"
              @timeupdate="onTimeUpdate"
              @ended="onVideoEnded"
            >
              <track
                v-for="subtitle in playOptions.subtitles"
                :key="subtitle.sid"
                kind="subtitles"
                :label="subtitle.title"
                :srclang="subtitle.language"
                :src="subtitle.url"
                :default="subtitle.is_default"
              />
            </video>
          </div>
        </v-col>

        <!-- 右侧：信息与控制面板（桌面端 1/3，移动端隐藏） -->
        <v-col cols="12" md="4" class="d-none d-md-block player-control-col">
          <v-card class="control-panel" elevation="2">
            <!-- 清晰度选择 -->
            <v-card-title class="text-subtitle-1">清晰度</v-card-title>
            <v-card-text>
              <v-chip-group
                v-model="selectedQualityIndex"
                mandatory
                @update:model-value="onQualityChange"
              >
                <v-chip
                  v-for="(quality, index) in playOptions.qualities"
                  :key="quality.id"
                  :value="index"
                  size="small"
                  :color="selectedQualityIndex === index ? 'primary' : 'default'"
                >
                  {{ quality.title }}
                </v-chip>
              </v-chip-group>
            </v-card-text>

            <v-divider />

            <!-- 字幕选择 -->
            <v-card-title class="text-subtitle-1">字幕</v-card-title>
            <v-card-text>
              <v-select
                v-model="selectedSubtitleId"
                :items="subtitleOptions"
                variant="outlined"
                density="compact"
                hide-details
                @update:model-value="onSubtitleChange"
              />
            </v-card-text>

            <v-divider />

            <!-- 文件信息 -->
            <v-card-title class="text-subtitle-1">文件信息</v-card-title>
            <v-card-text>
              <div class="text-body-2 mb-2">
                <div class="mb-1">
                  <span class="text-medium-emphasis">文件名：</span>
                  <span>{{ playOptions.file_name }}</span>
                </div>
                <div class="mb-1">
                  <span class="text-medium-emphasis">时长：</span>
                  <span>{{ formatDuration(playOptions.duration) }}</span>
                </div>
                <div class="mb-1">
                  <span class="text-medium-emphasis">当前清晰度：</span>
                  <span>{{ currentQuality?.title || '未知' }}</span>
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- 移动端：底部控制按钮 -->
      <div class="d-md-none mobile-controls">
        <v-bottom-sheet v-model="showMobileControls">
          <template v-slot:activator="{ props }">
            <v-btn
              v-bind="props"
              icon
              variant="text"
              class="control-btn"
            >
              <v-icon>mdi-cog</v-icon>
            </v-btn>
          </template>
          <v-card>
            <v-card-title>播放设置</v-card-title>
            <v-card-text>
              <!-- 清晰度 -->
              <div class="mb-4">
                <div class="text-subtitle-2 mb-2">清晰度</div>
                <v-chip-group
                  v-model="selectedQualityIndex"
                  mandatory
                  @update:model-value="onQualityChange"
                >
                  <v-chip
                    v-for="(quality, index) in playOptions.qualities"
                    :key="quality.id"
                    :value="index"
                    size="small"
                  >
                    {{ quality.title }}
                  </v-chip>
                </v-chip-group>
              </div>

              <!-- 字幕 -->
              <div class="mb-4">
                <div class="text-subtitle-2 mb-2">字幕</div>
                <v-select
                  v-model="selectedSubtitleId"
                  :items="subtitleOptions"
                  variant="outlined"
                  density="compact"
                  hide-details
                  @update:model-value="onSubtitleChange"
                />
              </div>

              <!-- 文件信息 -->
              <div>
                <div class="text-subtitle-2 mb-2">文件信息</div>
                <div class="text-body-2">
                  <div class="mb-1">文件名：{{ playOptions.file_name }}</div>
                  <div class="mb-1">时长：{{ formatDuration(playOptions.duration) }}</div>
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-bottom-sheet>
      </div>
    </div>

    <!-- 底部提示条 -->
    <div v-if="playOptions && !loading" class="player-footer">
      <div class="text-caption text-medium-emphasis">
        <span v-if="currentQuality">当前清晰度：{{ currentQuality.title }}</span>
        <span v-if="remainingTime" class="ml-4">剩余时间：{{ formatDuration(remainingTime) }}</span>
        <span class="ml-4">已同步到 115 观看历史</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { remote115Api } from '@/services/api'
import type { Remote115VideoPlayOptions, Remote115VideoQuality } from '@/types/remote115'
import Hls from 'hls.js'

const route = useRoute()
const router = useRouter()
const toast = useToast()

const workId = computed(() => parseInt(route.params.workId as string))
const workYear = ref<number | null>(null)

// 状态
const loading = ref(true)
const error = ref<string | null>(null)
const playOptions = ref<Remote115VideoPlayOptions | null>(null)

// 视频元素
const videoEl = ref<HTMLVideoElement | null>(null)
let hlsInstance: Hls | null = null

// 清晰度
const selectedQualityIndex = ref(0)
const currentQuality = computed(() => {
  if (!playOptions.value) return null
  return playOptions.value.qualities[selectedQualityIndex.value] || null
})

// 字幕
const selectedSubtitleId = ref<string | null>(null)
const subtitleOptions = computed(() => {
  if (!playOptions.value) return []
  const options = [
    { title: '关闭字幕', value: null }
  ]
  playOptions.value.subtitles.forEach(sub => {
    options.push({
      title: sub.title || sub.language || '字幕',
      value: sub.sid
    })
  })
  return options
})

// 移动端控制面板
const showMobileControls = ref(false)

// 剩余时间
const remainingTime = ref(0)

// 进度同步
let lastProgressUpdate = 0
const PROGRESS_UPDATE_INTERVAL = 15000 // 15秒
let progressUpdateTimer: ReturnType<typeof setInterval> | null = null

// 加载播放选项
const loadPlayOptions = async () => {
  try {
    loading.value = true
    error.value = null

    const response = await remote115Api.getPlayOptions(workId.value)
    playOptions.value = response.data

    // 选择默认清晰度（分辨率最高的）
    if (playOptions.value.qualities.length > 0) {
      const sortedQualities = [...playOptions.value.qualities].sort((a, b) => {
        const resolutionA = a.height * a.width
        const resolutionB = b.height * b.width
        return resolutionB - resolutionA
      })
      const defaultIndex = playOptions.value.qualities.findIndex(q => q.id === sortedQualities[0].id)
      selectedQualityIndex.value = defaultIndex >= 0 ? defaultIndex : 0
    }

    // 选择默认字幕
    const defaultSubtitle = playOptions.value.subtitles.find(s => s.is_default)
    if (defaultSubtitle) {
      selectedSubtitleId.value = defaultSubtitle.sid
    }

    // 初始化视频源
    await nextTick()
    await initializeVideoSource()
  } catch (err: any) {
    console.error('加载播放选项失败:', err)
    error.value = err.response?.data?.detail || err.message || '加载播放选项失败'
    toast.error(error.value)
  } finally {
    loading.value = false
  }
}

// 初始化视频源
const initializeVideoSource = async () => {
  if (!videoEl.value || !playOptions.value || !currentQuality.value) return

  const quality = currentQuality.value
  const url = quality.url

  // 清理旧的 HLS 实例
  if (hlsInstance) {
    hlsInstance.destroy()
    hlsInstance = null
  }

  // 判断是否为 HLS
  const isHLS = url.endsWith('.m3u8') || url.includes('.m3u8')

  if (isHLS) {
    // 检查浏览器原生支持
    if (videoEl.value.canPlayType('application/vnd.apple.mpegurl')) {
      // 使用原生 HLS
      videoEl.value.src = url
    } else if (Hls.isSupported()) {
      // 使用 hls.js
      hlsInstance = new Hls({
        enableWorker: true,
        lowLatencyMode: false
      })
      hlsInstance.loadSource(url)
      hlsInstance.attachMedia(videoEl.value)
      
      hlsInstance.on(Hls.Events.ERROR, (event, data) => {
        console.error('HLS 错误:', data)
        if (data.fatal) {
          switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              console.error('网络错误，尝试恢复...')
              hlsInstance?.startLoad()
              break
            case Hls.ErrorTypes.MEDIA_ERROR:
              console.error('媒体错误，尝试恢复...')
              hlsInstance?.recoverMediaError()
              break
            default:
              console.error('致命错误，无法恢复')
              hlsInstance?.destroy()
              hlsInstance = null
              break
          }
        }
      })
    } else {
      toast.error('当前浏览器不支持 HLS 播放')
    }
  } else {
    // 直接使用 MP4 等格式
    videoEl.value.src = url
  }
}

// 视频可以播放
const onVideoCanPlay = () => {
  if (!videoEl.value || !playOptions.value) return

  // 恢复观看进度
  if (playOptions.value.progress && playOptions.value.progress.position > 0) {
    const position = playOptions.value.progress.position
    // 延迟一点再 seek，确保视频已准备好
    setTimeout(() => {
      if (videoEl.value) {
        videoEl.value.currentTime = position
      }
    }, 500)
  }

  // 开始进度同步
  startProgressSync()
}

// 时间更新
const onTimeUpdate = () => {
  if (!videoEl.value || !playOptions.value) return

  const currentTime = videoEl.value.currentTime
  const duration = videoEl.value.duration

  if (duration > 0) {
    remainingTime.value = Math.floor(duration - currentTime)
  }
}

// 视频播放结束
const onVideoEnded = async () => {
  if (!playOptions.value) return

  try {
    await remote115Api.updateProgress(workId.value, {
      position: 0,
      finished: true
    })
    console.log('已标记为播放完成')
  } catch (err: any) {
    console.error('更新播放完成状态失败:', err)
  }
}

// 开始进度同步
const startProgressSync = () => {
  if (progressUpdateTimer) {
    clearInterval(progressUpdateTimer)
  }

  progressUpdateTimer = setInterval(async () => {
    if (!videoEl.value || !playOptions.value) return

    const currentTime = Math.floor(videoEl.value.currentTime)
    const now = Date.now()

    // 每 15 秒或进度变化超过 10 秒时更新
    if (now - lastProgressUpdate >= PROGRESS_UPDATE_INTERVAL || 
        Math.abs(currentTime - lastProgressUpdate) >= 10) {
      try {
        await remote115Api.updateProgress(workId.value, {
          position: currentTime,
          finished: false
        })
        lastProgressUpdate = currentTime
      } catch (err: any) {
        console.error('更新观看进度失败:', err)
        // 不打扰用户，只记录错误
      }
    }
  }, 5000) // 每 5 秒检查一次
}

// 切换清晰度
const onQualityChange = async (index: number) => {
  if (!videoEl.value || !playOptions.value) return

  // 记住当前播放位置
  const prevTime = videoEl.value.currentTime

  // 更新清晰度索引
  selectedQualityIndex.value = index

  // 重新初始化视频源
  await initializeVideoSource()

  // 恢复播放位置
  await nextTick()
  if (videoEl.value) {
    videoEl.value.currentTime = prevTime
  }
}

// 切换字幕
const onSubtitleChange = (subtitleId: string | null) => {
  if (!videoEl.value) return

  const tracks = videoEl.value.textTracks
  for (let i = 0; i < tracks.length; i++) {
    const track = tracks[i]
    if (subtitleId && track.id === subtitleId) {
      track.mode = 'showing'
    } else {
      track.mode = 'disabled'
    }
  }
}

// 格式化时长
const formatDuration = (seconds: number): string => {
  if (!seconds || seconds < 0) return '00:00'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 清理
onBeforeUnmount(() => {
  if (hlsInstance) {
    hlsInstance.destroy()
    hlsInstance = null
  }
  if (progressUpdateTimer) {
    clearInterval(progressUpdateTimer)
    progressUpdateTimer = null
  }
})

// 初始化
onMounted(() => {
  loadPlayOptions()
})
</script>

<style scoped lang="scss">
.remote-115-player-page {
  min-height: 100vh;
  background-color: #000;
  color: #fff;
}

.player-header {
  display: flex;
  align-items: center;
  padding: 16px;
  background-color: rgba(0, 0, 0, 0.8);
  position: sticky;
  top: 0;
  z-index: 10;
}

.player-container {
  padding: 16px;
  min-height: calc(100vh - 200px);
}

.player-video-col {
  padding: 0 8px;
}

.video-wrapper {
  position: relative;
  width: 100%;
  padding-bottom: 56.25%; // 16:9
  background-color: #000;
  border-radius: 12px;
  overflow: hidden;
}

.video-player {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.player-control-col {
  padding: 0 8px;
}

.control-panel {
  height: 100%;
  border-radius: 12px;
  background-color: rgba(255, 255, 255, 0.05);
}

.mobile-controls {
  position: fixed;
  bottom: 80px;
  right: 16px;
  z-index: 100;
}

.player-footer {
  padding: 12px 16px;
  background-color: rgba(0, 0, 0, 0.8);
  text-align: center;
}

@media (max-width: 960px) {
  .player-container {
    padding: 8px;
  }

  .video-wrapper {
    padding-bottom: 56.25%;
  }
}
</style>

