<!--
站点卡片组件 (SITE-MANAGER-1)
显示站点的基本信息、健康状态、统计数据和操作按钮
-->

<template>
  <v-card
    :class="[
      'site-card',
      {
        'site-card--disabled': !site.enabled,
        'site-card--compact': compact,
        'site-card--loading': localLoading
      }
    ]"
    :elevation="hovered ? 8 : 2"
    @mouseenter="hovered = true"
    @mouseleave="hovered = false"
    @click="$emit('click', site)"
  >
    <!-- 卡片头部：站点图标和基本信息 -->
    <v-card-item class="site-card__header">
      <template #prepend>
        <v-avatar
          :size="compact ? 40 : 48"
          :class="[
            'site-card__avatar',
            {
              'site-card__avatar--online': healthStatus === 'OK',
              'site-card__avatar--warning': healthStatus === 'WARN',
              'site-card__avatar--error': healthStatus === 'ERROR'
            }
          ]"
        >
          <img
            v-if="site.icon_url"
            :src="site.icon_url"
            :alt="site.name"
            @error="onImageError"
          />
          <v-icon v-else size="24">
            {{ getCategoryIcon(site.category) }}
          </v-icon>
        </v-avatar>
      </template>

      <v-card-title class="site-card__title">
        <div class="d-flex align-center">
          <span class="text-truncate">{{ site.name }}</span>
          <v-chip
            v-if="site.priority > 0"
            :color="getPriorityColor(site.priority)"
            size="x-small"
            class="ml-2"
          >
            P{{ site.priority }}
          </v-chip>
        </div>
      </v-card-title>

      <v-card-subtitle class="site-card__subtitle">
        <div class="d-flex align-center text-caption">
          <v-icon size="12" class="mr-1">mdi-earth</v-icon>
          <span class="text-truncate">{{ site.domain || site.url }}</span>
        </div>
        <div v-if="site.key" class="d-flex align-center text-caption mt-1">
          <v-icon size="12" class="mr-1">mdi-key</v-icon>
          <span>{{ site.key }}</span>
        </div>
      </v-card-subtitle>

      <template #append>
        <div class="d-flex flex-column align-end">
          <!-- 健康状态指示器 -->
          <v-chip
            :color="getHealthColor(healthStatus)"
            :variant="healthStatus === HealthStatus.OK ? 'flat' : 'outlined'"
            size="x-small"
            class="mb-1"
          >
            <v-icon start size="12">{{ getHealthIcon(healthStatus) }}</v-icon>
            {{ getHealthText(healthStatus) }}
          </v-chip>

          <!-- 启用开关 -->
          <v-switch
            :model-value="site.enabled"
            :disabled="localLoading"
            density="compact"
            hide-details
            @click.stop
            @update:model-value="onToggleEnabled"
          />
        </div>
      </template>
    </v-card-item>

    <!-- 卡片内容：统计信息和标签 -->
    <v-card-text v-if="!compact" class="site-card__content">
      <!-- 健康检查结果 -->
      <div v-if="showHealth && site.stats" class="site-card__stats mb-2">
        <div class="d-flex align-center justify-space-between mb-1">
          <span class="text-caption text-medium-emphasis">健康状态</span>
          <span class="text-caption">
            <v-icon size="12" class="mr-1">mdi-clock</v-icon>
            {{ formatResponseTime(site.stats.avg_response_time) }}
          </span>
        </div>
        <div class="d-flex align-center justify-space-between">
          <span class="text-caption text-medium-emphasis">成功率</span>
          <span class="text-caption">
            {{ getSuccessRate(site.stats) }}%
          </span>
        </div>
      </div>

      <!-- 流量统计 -->
      <div v-if="showStats && site.stats" class="site-card__traffic mb-2">
        <div class="d-flex align-center justify-space-between mb-1">
          <span class="text-caption text-medium-emphasis">上传</span>
          <span class="text-caption text-success">
            {{ formatBytes(site.stats.upload_bytes) }}
          </span>
        </div>
        <div class="d-flex align-center justify-space-between">
          <span class="text-caption text-medium-emphasis">下载</span>
          <span class="text-caption text-info">
            {{ formatBytes(site.stats.download_bytes) }}
          </span>
        </div>
      </div>

      <!-- 标签 -->
      <div v-if="showTags && site.tags" class="site-card__tags">
        <v-chip
          v-for="tag in getTagList(site.tags)"
          :key="tag"
          size="x-small"
          variant="outlined"
          class="mr-1 mb-1"
        >
          {{ tag }}
        </v-chip>
      </div>
    </v-card-text>

    <!-- 卡片操作：快捷操作按钮 -->
    <v-card-actions v-if="!compact" class="site-card__actions">
      <v-spacer />

      <!-- 优先级调整 -->
      <v-btn
        :icon="true"
        size="small"
        variant="text"
        :disabled="localLoading || site.priority <= 0"
        @click.stop="onAdjustPriority(-1)"
      >
        <v-icon>mdi-chevron-down</v-icon>
        <v-tooltip activator="parent">降低优先级</v-tooltip>
      </v-btn>

      <v-btn
        :icon="true"
        size="small"
        variant="text"
        :disabled="localLoading"
        @click.stop="onAdjustPriority(1)"
      >
        <v-icon>mdi-chevron-up</v-icon>
        <v-tooltip activator="parent">提高优先级</v-tooltip>
      </v-btn>

      <!-- 健康检查 -->
      <v-btn
        :icon="true"
        size="small"
        variant="text"
        :color="healthStatus === HealthStatus.OK ? 'success' : 'warning'"
        :disabled="localLoading"
        :loading="healthChecking"
        @click.stop="onHealthCheck"
      >
        <v-icon>mdi-heart-pulse</v-icon>
        <v-tooltip activator="parent">健康检查</v-tooltip>
      </v-btn>

      <!-- 更多操作 -->
      <v-menu>
        <template #activator="{ props }">
          <v-btn
            v-bind="props"
            :icon="true"
            size="small"
            variant="text"
            @click.stop
          >
            <v-icon>mdi-dots-vertical</v-icon>
          </v-btn>
        </template>

        <v-list density="compact">
          <v-list-item
            prepend-icon="mdi-pencil"
            title="编辑站点"
            @click="onEdit"
          />
          <v-list-item
            prepend-icon="mdi-export"
            title="导出配置"
            @click="onExport"
          />
          <v-divider />
          <v-list-item
            prepend-icon="mdi-delete"
            title="删除站点"
            class="text-error"
            @click="onDelete"
          />
        </v-list>
      </v-menu>
    </v-card-actions>

    <!-- 加载遮罩 -->
    <v-overlay
      v-model="localLoading"
      contained
      class="align-center justify-center"
    >
      <v-progress-circular indeterminate size="24" />
    </v-overlay>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useSiteManagerStore } from '@/stores/siteManager'
import type { SiteBrief } from '@/types/siteManager'
import { HealthStatus } from '@/types/siteManager'

interface Props {
  site: SiteBrief
  compact?: boolean
  showStats?: boolean
  showHealth?: boolean
  showTags?: boolean
  loading?: boolean
}

interface Emits {
  (e: 'click', site: SiteBrief): void
  (e: 'edit', site: SiteBrief): void
  (e: 'delete', site: SiteBrief): void
  (e: 'export', site: SiteBrief): void
}

const props = withDefaults(defineProps<Props>(), {
  compact: false,
  showStats: true,
  showHealth: true,
  showTags: true,
  loading: false
})

const emit = defineEmits<Emits>()

const siteManagerStore = useSiteManagerStore()

// 响应式状态
const hovered = ref(false)
const healthChecking = ref(false)
const localLoading = ref(props.loading)

// 监听 props.loading 变化
watch(() => props.loading, (newValue) => {
  localLoading.value = newValue
})

// 计算属性
const healthStatus = computed((): HealthStatus => {
  const status = props.site.stats?.health_status
  // Handle both enum and string types during transition
  if (status === undefined || status === null) return HealthStatus.UNKNOWN
  if (typeof status === 'string') {
    switch (status) {
      case 'OK': return HealthStatus.OK
      case 'WARN': return HealthStatus.WARN
      case 'ERROR': return HealthStatus.ERROR
      default: return HealthStatus.UNKNOWN
    }
  }
  return status as HealthStatus
})

// 方法
const onImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
}

const onToggleEnabled = async () => {
  try {
    await siteManagerStore.toggleSiteEnabled(props.site.id)
  } catch (error) {
    console.error('切换启用状态失败:', error)
  }
}

const onAdjustPriority = async (delta: number) => {
  try {
    await siteManagerStore.adjustSitePriority(props.site.id, delta)
  } catch (error) {
    console.error('调整优先级失败:', error)
  }
}

const onHealthCheck = async () => {
  healthChecking.value = true
  try {
    await siteManagerStore.checkSiteHealth(props.site.id)
  } catch (error) {
    console.error('健康检查失败:', error)
  } finally {
    healthChecking.value = false
  }
}

const onEdit = () => {
  emit('edit', props.site)
}

const onDelete = () => {
  emit('delete', props.site)
}

const onExport = () => {
  emit('export', props.site)
}

// 工具方法
const getCategoryIcon = (category?: string): string => {
  const iconMap: Record<string, string> = {
    pt: 'mdi-server',
    bt: 'mdi-download',
    novel: 'mdi-book-open',
    comic: 'mdi-image',
    music: 'mdi-music',
    movie: 'mdi-movie',
    game: 'mdi-gamepad'
  }
  return iconMap[category || ''] || 'mdi-web'
}

const getHealthColor = (status: HealthStatus): string => {
  const colorMap: Record<HealthStatus, string> = {
    OK: 'success',
    WARN: 'warning',
    ERROR: 'error',
    UNKNOWN: 'grey'
  }
  return colorMap[status]
}

const getHealthIcon = (status: HealthStatus): string => {
  const iconMap: Record<HealthStatus, string> = {
    OK: 'mdi-check-circle',
    WARN: 'mdi-alert-circle',
    ERROR: 'mdi-close-circle',
    UNKNOWN: 'mdi-help-circle'
  }
  return iconMap[status]
}

const getHealthText = (status: HealthStatus): string => {
  const textMap: Record<HealthStatus, string> = {
    OK: '正常',
    WARN: '警告',
    ERROR: '错误',
    UNKNOWN: '未知'
  }
  return textMap[status]
}

const getPriorityColor = (priority: number): string => {
  if (priority >= 5) return 'error'
  if (priority >= 3) return 'warning'
  return 'info'
}

const getSuccessRate = (stats: any): string => {
  if (!stats.total_requests || stats.total_requests === 0) return '0'
  return ((stats.successful_requests / stats.total_requests) * 100).toFixed(1)
}

const formatResponseTime = (time?: number): string => {
  if (!time) return '未知'
  return `${time}ms`
}

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
}

const getTagList = (tags: string | string[]): string[] => {
  if (Array.isArray(tags)) return tags
  return tags.split(',').map(tag => tag.trim()).filter(Boolean)
}
</script>

<style lang="scss" scoped>
.site-card {
  transition: all 0.3s ease;
  cursor: pointer;
  user-select: none;

  &:hover {
    transform: translateY(-2px);
  }

  &--disabled {
    opacity: 0.6;
    filter: grayscale(0.5);
  }

  &--compact {
    .site-card__content,
    .site-card__actions {
      display: none;
    }
  }

  &--loading {
    pointer-events: none;
  }

  &__header {
    padding: 16px;
  }

  &__avatar {
    border: 2px solid transparent;
    transition: all 0.3s ease;

    &--online {
      border-color: rgb(var(--v-theme-success));
      box-shadow: 0 0 8px rgba(var(--v-theme-success), 0.3);
    }

    &--warning {
      border-color: rgb(var(--v-theme-warning));
      box-shadow: 0 0 8px rgba(var(--v-theme-warning), 0.3);
    }

    &--error {
      border-color: rgb(var(--v-theme-error));
      box-shadow: 0 0 8px rgba(var(--v-theme-error), 0.3);
    }
  }

  &__title {
    font-size: 1rem;
    font-weight: 600;
    line-height: 1.2;
    padding: 0;
  }

  &__subtitle {
    font-size: 0.875rem;
    padding: 0;
    margin-top: 4px;
  }

  &__content {
    padding: 0 16px 16px;
  }

  &__stats,
  &__traffic {
    background: rgba(var(--v-theme-surface-variant), 0.5);
    border-radius: 8px;
    padding: 8px;
  }

  &__tags {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }

  &__actions {
    padding: 8px 16px 16px;
    gap: 4px;
  }
}

// 响应式设计
@media (max-width: 960px) {
  .site-card {
    &__title {
      font-size: 0.9rem;
    }

    &__subtitle {
      font-size: 0.8rem;
    }
  }
}

@media (max-width: 600px) {
  .site-card {
    &__header {
      padding: 12px;
    }

    &__content {
      padding: 0 12px 12px;
    }

    &__actions {
      padding: 8px 12px 12px;
    }
  }
}
</style>
