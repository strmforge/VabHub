<template>
  <v-card
    class="work-poster-card"
    elevation="2"
    rounded="xl"
    @click="$emit('click')"
  >
    <!-- 海报图 -->
    <div class="poster-wrapper">
      <v-img
        :src="work.poster_url || '/default-poster.jpg'"
        :lazy-src="work.poster_url || '/default-poster.jpg'"
        aspect-ratio="2/3"
        cover
        class="poster-image"
      >
        <template v-slot:placeholder>
          <div class="d-flex align-center justify-center fill-height bg-grey-lighten-4">
            <v-icon size="48" color="grey-lighten-2">mdi-image-off</v-icon>
          </div>
        </template>
        <template v-slot:error>
          <div class="d-flex align-center justify-center fill-height bg-grey-lighten-4">
            <v-icon size="48" color="grey-lighten-2">mdi-image-off</v-icon>
          </div>
        </template>

        <!-- 角标 -->
        <div class="poster-badges">
          <!-- 源状态角标 -->
          <v-chip
            v-if="source.has_local"
            color="teal"
            text-color="white"
            size="x-small"
            class="mr-1 mb-1"
          >
            本地
          </v-chip>
          <v-chip
            v-if="source.has_115"
            color="deep-purple"
            text-color="white"
            size="x-small"
            class="mb-1"
          >
            115
          </v-chip>
          
          <!-- 订阅状态角标 -->
          <v-chip
            v-if="status.has_subscription"
            :color="status.subscription_status === 'active' ? 'blue' : 'grey'"
            text-color="white"
            size="x-small"
            class="mr-1 mb-1"
            :title="`订阅状态: ${getSubscriptionStatusText(status.subscription_status)}`"
          >
            <v-icon size="12" class="mr-1">mdi-bell</v-icon>
            {{ getSubscriptionStatusText(status.subscription_status) }}
          </v-chip>
          
          <!-- 下载状态角标 -->
          <v-chip
            v-if="status.has_active_downloads"
            color="orange"
            text-color="white"
            size="x-small"
            class="mr-1 mb-1"
            :title="`下载中: ${status.download_count || 0} 个任务`"
          >
            <v-icon size="12" class="mr-1">mdi-download</v-icon>
            {{ status.download_count || 1 }}
          </v-chip>
          
          <!-- HR风险角标 -->
          <v-chip
            v-if="status.hr_risk"
            :color="getHrRiskColor(status.hr_level)"
            text-color="white"
            size="x-small"
            class="mb-1"
            :title="`HR风险: ${getHrRiskText(status.hr_level)}`"
          >
            <v-icon size="12" class="mr-1">mdi-alert</v-icon>
            HR
          </v-chip>
        </div>

        <!-- 悬停覆盖层 -->
        <div class="poster-overlay">
          <div class="d-flex flex-column gap-2">
            <!-- 播放按钮 -->
            <v-btn
              v-if="source.has_115 || source.has_local"
              color="primary"
              variant="elevated"
              size="large"
              prepend-icon="mdi-play-circle"
              @click.stop="handlePlay"
            >
              {{ getPlayButtonText() }}
            </v-btn>
            
            <!-- 详情按钮 -->
            <v-btn
              color="secondary"
              variant="elevated"
              size="default"
              prepend-icon="mdi-information"
              @click.stop="$emit('click')"
            >
              详情
            </v-btn>
          </div>
        </div>
      </v-img>
    </div>

    <!-- 文字信息 -->
    <v-card-text class="pa-2">
      <div class="text-body-2 font-weight-medium" :title="work.title" style="display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.4;">
        {{ work.title }}
      </div>
      <div class="text-caption text-medium-emphasis mt-1">
        <span v-if="work.year">{{ work.year }}</span>
        <span v-if="work.year && work.media_type" class="mx-1">·</span>
        <span>{{ getMediaTypeName(work.media_type) }}</span>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import type { PlayerWallWorkSummary, PlayerWallSourceInfo, PlayerWallStatusInfo } from '@/types/playerWall'

defineProps<{
  work: PlayerWallWorkSummary
  source: PlayerWallSourceInfo
  status: PlayerWallStatusInfo
}>()

defineEmits<{
  click: []
  play: []
}>()

const getMediaTypeName = (type: string): string => {
  const typeMap: Record<string, string> = {
    movie: '电影',
    tv: '电视剧',
    short_drama: '短剧',
    anime: '动漫',
    music: '音乐'
  }
  return typeMap[type] || type
}

const getSubscriptionStatusText = (status?: string): string => {
  const statusMap: Record<string, string> = {
    active: '订阅中',
    completed: '已完成',
    paused: '已暂停'
  }
  return statusMap[status || 'active'] || '已订阅'
}

const getHrRiskColor = (level?: string): string => {
  const colorMap: Record<string, string> = {
    low: 'warning',
    medium: 'orange',
    high: 'red'
  }
  return colorMap[level || 'medium'] || 'warning'
}

const getHrRiskText = (level?: string): string => {
  const textMap: Record<string, string> = {
    low: '低风险',
    medium: '中风险',
    high: '高风险'
  }
  return textMap[level || 'medium'] || '有风险'
}

const getPlayButtonText = (): string => {
  if (props.source.has_115 && props.source.has_local) {
    return '115播放'
  } else if (props.source.has_115) {
    return '115播放'
  } else if (props.source.has_local) {
    return '本地播放'
  }
  return '播放'
}

const handlePlay = () => {
  emit('play')
}
</script>

<style scoped lang="scss">
.work-poster-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 12px;
  overflow: hidden;

  &:hover {
    transform: translateY(-4px) scale(1.02);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2) !important;
    elevation: 4;
  }
}

.poster-wrapper {
  position: relative;
  overflow: hidden;
  border-radius: 12px 12px 0 0;
}

.poster-image {
  border-radius: 12px 12px 0 0;
}

.poster-badges {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  z-index: 2;
}

.poster-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
  z-index: 1;
}

.work-poster-card:hover .poster-overlay {
  opacity: 1;
}
</style>

