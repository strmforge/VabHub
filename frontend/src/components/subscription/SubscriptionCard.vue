<template>
  <v-hover v-slot="{ isHovering, props: hoverProps }">
    <v-card
      v-bind="hoverProps"
      :class="{
        'subscription-card': true,
        'subscription-paused': subscription.status === 'paused',
        'subscription-card-hover': isHovering
      }"
      :style="cardStyle"
      @click="handleCardClick"
    >
      <!-- 背景图片 -->
      <template v-if="backgroundImage">
        <v-img
          :src="backgroundImage"
          aspect-ratio="3/2"
          cover
          position="top"
          class="subscription-card-background"
          loading="lazy"
          :lazy-src="backgroundImage"
        >
          <template #default>
            <div class="subscription-card-overlay"></div>
          </template>
        </v-img>
      </template>
      
      <!-- 暂停遮罩 -->
      <div
        v-if="subscription.status === 'paused'"
        class="subscription-paused-overlay"
      />
      
      <!-- 卡片内容 -->
      <v-card-text class="subscription-card-content pa-3">
        <div class="d-flex align-start">
          <!-- 左侧：海报 -->
          <div
            v-if="posterImage || imageLoaded"
            class="subscription-poster me-3"
          >
            <v-img
              v-if="posterImage"
              :src="posterImage"
              aspect-ratio="2/3"
              width="48"
              cover
              class="subscription-poster-img rounded"
              loading="lazy"
              :lazy-src="posterImage"
              @load="imageLoaded = true"
            >
              <template #placeholder>
                <v-skeleton-loader
                  type="image"
                  class="subscription-poster-skeleton"
                />
              </template>
              <template #error>
                <v-icon size="24" color="grey-lighten-1">mdi-image-off</v-icon>
              </template>
            </v-img>
            <v-skeleton-loader
              v-else
              type="image"
              width="48"
              height="72"
              class="subscription-poster-skeleton rounded"
            />
          </div>
          
          <!-- 右侧：信息 -->
          <div class="subscription-info flex-grow-1 min-w-0">
            <!-- 年份 -->
            <div
              v-if="subscription.year"
              class="text-body-2 text-white font-weight-medium mb-1"
            >
              {{ subscription.year }}
            </div>
            
            <!-- 标题 -->
            <div class="text-h6 text-white font-weight-bold mb-2 line-clamp-2">
              {{ subscription.title }}
            </div>
            
            <!-- 标签 -->
            <div class="d-flex align-center flex-wrap ga-1 mb-2">
              <v-chip
                :color="getStatusColor(subscription.status)"
                size="x-small"
                variant="flat"
              >
                {{ getStatusText(subscription.status) }}
              </v-chip>
              <v-chip
                :color="mediaTypeChip.color"
                :variant="mediaTypeChip.variant"
                class="text-white"
              >
                <v-icon v-if="mediaTypeChip.icon" size="14" class="me-1">
                  {{ mediaTypeChip.icon }}
                </v-icon>
                {{ mediaTypeChip.text }}
              </v-chip>
              <v-chip
                v-if="subscription.media_type === 'tv' && subscription.season"
                size="x-small"
                variant="flat"
                color="info"
                class="text-white"
              >
                第 {{ subscription.season }} 季
              </v-chip>
            </div>
            <div class="d-flex flex-wrap ga-1 mb-1">
              <v-chip
                v-if="subscription.strict_free_only"
                size="x-small"
                variant="flat"
                color="success"
                class="text-white"
              >
                <v-icon size="12" class="me-1">mdi-shield-check</v-icon>
                只下Free
              </v-chip>
              <v-chip
                v-else-if="subscription.allow_hr || subscription.allow_h3h5"
                size="x-small"
                variant="flat"
                color="warning"
                class="text-white"
              >
                <v-icon size="12" class="me-1">mdi-alert</v-icon>
                允许风险
              </v-chip>
              <v-chip
                v-else
                size="x-small"
                variant="flat"
                color="success"
                class="text-white"
              >
                <v-icon size="12" class="me-1">mdi-shield-check</v-icon>
                安全模式
              </v-chip>
            </div>
            <div
              v-if="shortDramaMeta"
              class="text-caption text-white d-flex align-center ga-1"
            >
              <v-icon size="14">mdi-drama-masks</v-icon>
              {{ formatShortDramaMeta(shortDramaMeta) }}
            </div>
            
            <!-- 电视剧集数进度 -->
            <div
              v-if="isTvShow && subscription.total_episode"
              class="episode-progress mt-2"
            >
              <div class="d-flex align-center justify-space-between mb-1">
                <span class="text-caption text-white">
                  <v-icon size="14" class="me-1">mdi-playlist-check</v-icon>
                  集数进度
                </span>
                <span class="text-caption text-white font-weight-bold">
                  {{ episodeProgressText }}
                </span>
              </div>
              <v-progress-linear
                :model-value="episodeProgressPercent"
                color="primary"
                height="6"
                rounded
                class="episode-progress-bar"
              />
            </div>
            
            <!-- 质量信息 -->
            <div
              v-if="subscription.quality || subscription.resolution"
              class="text-caption text-white-darken-1 mt-1"
            >
              <v-icon size="12" class="me-1">mdi-quality-high</v-icon>
              {{ subscription.quality || subscription.resolution }}
            </div>
          </div>
        </div>
        
        <!-- 操作按钮 -->
        <div class="subscription-actions d-flex justify-end ga-1 mt-2">
          <v-tooltip text="手动检查订阅" location="top">
            <template #activator="{ props: tooltipProps }">
              <v-btn
                v-bind="tooltipProps"
                icon="mdi-shield-check"
                size="small"
                variant="text"
                color="warning"
                @click.stop="handleCheckSubscription"
                :loading="checking"
              />
            </template>
          </v-tooltip>
          
          <v-tooltip text="执行搜索" location="top">
            <template #activator="{ props: tooltipProps }">
              <v-btn
                v-bind="tooltipProps"
                icon="mdi-magnify"
                size="small"
                variant="text"
                color="white"
                @click.stop="handleSearch"
                :loading="searching"
              />
            </template>
          </v-tooltip>
          
          <v-tooltip :text="subscription.status === 'active' ? '暂停订阅' : '启用订阅'" location="top">
            <template #activator="{ props: tooltipProps }">
              <v-btn
                v-bind="tooltipProps"
                :icon="subscription.status === 'active' ? 'mdi-pause' : 'mdi-play'"
                size="small"
                variant="text"
                color="white"
                @click.stop="handleToggleStatus"
                :loading="toggling"
              />
            </template>
          </v-tooltip>
          
          <v-tooltip text="编辑订阅" location="top">
            <template #activator="{ props: tooltipProps }">
              <v-btn
                v-bind="tooltipProps"
                icon="mdi-pencil"
                size="small"
                variant="text"
                color="white"
                @click.stop="handleEdit"
              />
            </template>
          </v-tooltip>
          
          <v-tooltip text="删除订阅" location="top">
            <template #activator="{ props: tooltipProps }">
              <v-btn
                v-bind="tooltipProps"
                icon="mdi-delete"
                size="small"
                variant="text"
                color="white"
                @click.stop="handleDelete"
              />
            </template>
          </v-tooltip>
        </div>
      </v-card-text>
    </v-card>
  </v-hover>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps({
  subscription: {
    type: Object as () => any,
    required: true
  }
})

const emit = defineEmits(['edit', 'delete', 'click', 'search', 'toggle-status', 'check-subscription'])

const imageLoaded = ref(false)
const searching = ref(false)
const toggling = ref(false)
const checking = ref(false)

// 背景图片
const backgroundImage = computed(() => {
  return props.subscription.backdrop || props.subscription.poster || null
})

// 海报图片
const posterImage = computed(() => {
  return props.subscription.poster || null
})

// 卡片样式
const cardStyle = computed(() => {
  if (!backgroundImage) {
    return {}
  }
  return {
    minHeight: '150px'
  }
})

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    active: 'success',
    paused: 'warning',
    completed: 'info'
  }
  return colors[status] || 'grey'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    active: '活跃',
    paused: '暂停',
    completed: '完成'
  }
  return texts[status] || status
}

const getMediaTypeText = (type: string) => {
  const types: Record<string, string> = {
    movie: '电影',
    tv: '电视剧',
    short_drama: '短剧',
    anime: '动漫',
    music: '音乐'
  }
  return types[type] || type
}

const mediaTypeChip = computed(() => {
  const map: Record<string, { text: string; color: string; icon?: string; variant: 'flat' | 'outlined' }> = {
    movie: { text: '电影', color: 'deep-orange', variant: 'outlined' },
    tv: { text: '电视剧', color: 'blue', variant: 'outlined' },
    anime: { text: '动漫', color: 'teal', variant: 'outlined' },
    music: { text: '音乐', color: 'green', variant: 'outlined' },
    short_drama: { text: '短剧', color: 'purple', icon: 'mdi-drama-masks', variant: 'flat' }
  }
  return map[props.subscription.media_type] || { text: getMediaTypeText(props.subscription.media_type), color: 'grey', variant: 'outlined' }
})

const shortDramaMeta = computed(() => {
  if (props.subscription.media_type !== 'short_drama') return null
  return props.subscription.extra_metadata?.short_drama || props.subscription.short_drama_metadata || null
})

// 是否是电视剧类型（包括 tv/anime/short_drama）
const isTvShow = computed(() => {
  return ['tv', 'anime', 'short_drama'].includes(props.subscription.media_type)
})

// 集数进度文本
const episodeProgressText = computed(() => {
  const total = props.subscription.total_episode || 0
  const downloaded = props.subscription.downloaded_episode || props.subscription.start_episode || 0
  if (total > 0) {
    return `${downloaded} / ${total} 集`
  }
  return `${downloaded} 集`
})

// 集数进度百分比
const episodeProgressPercent = computed(() => {
  const total = props.subscription.total_episode || 0
  const downloaded = props.subscription.downloaded_episode || props.subscription.start_episode || 0
  if (total > 0) {
    return Math.min(100, Math.round((downloaded / total) * 100))
  }
  return 0
})

const formatShortDramaMeta = (meta: Record<string, any>) => {
  if (!meta) return ''
  const episodes = meta.total_episodes ? `${meta.total_episodes}集` : ''
  const duration = meta.episode_duration ? `${Math.round(meta.episode_duration / 60)}分钟/集` : ''
  return [episodes, duration].filter(Boolean).join(' · ') || '短剧'
}

const handleCardClick = () => {
  emit('click', props.subscription)
}

const handleEdit = () => {
  emit('edit', props.subscription)
}

const handleDelete = () => {
  if (confirm(`确定要删除订阅"${props.subscription.title}"吗？`)) {
    emit('delete', props.subscription)
  }
}

const handleSearch = async () => {
  searching.value = true
  try {
    emit('search', props.subscription.id)
    // 等待一下再重置loading状态，给用户反馈
    setTimeout(() => {
      searching.value = false
    }, 1000)
  } catch (error) {
    searching.value = false
  }
}

const handleCheckSubscription = async () => {
  checking.value = true
  try {
    emit('check-subscription', props.subscription.id)
    // 等待一下再重置loading状态，给用户反馈
    setTimeout(() => {
      checking.value = false
    }, 2000)
  } catch (error) {
    checking.value = false
  }
}

const handleToggleStatus = async () => {
  toggling.value = true
  try {
    emit('toggle-status', props.subscription.id, props.subscription.status)
    // 等待一下再重置loading状态
    setTimeout(() => {
      toggling.value = false
    }, 500)
  } catch (error) {
    toggling.value = false
  }
}
</script>

<style scoped lang="scss">
.subscription-card {
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
}

.subscription-card-hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
}

.subscription-card-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
}

.subscription-card-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(180deg, rgba(31, 41, 55, 0.47) 0%, rgb(31, 41, 55) 100%);
  z-index: 1;
}

.subscription-paused-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 193, 7, 0.3);
  z-index: 2;
  pointer-events: none;
}

.subscription-card-content {
  position: relative;
  z-index: 3;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.subscription-poster {
  flex-shrink: 0;
}

.subscription-poster-img {
  width: 48px;
  height: 72px;
  object-fit: cover;
  border-radius: 4px;
}

.subscription-poster-skeleton {
  width: 48px;
  height: 72px;
}

.subscription-info {
  min-width: 0;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.subscription-actions {
  margin-top: auto;
}

.subscription-paused {
  opacity: 0.8;
}

.episode-progress {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  padding: 8px;
}

.episode-progress-bar {
  background: rgba(255, 255, 255, 0.2);
}
</style>

