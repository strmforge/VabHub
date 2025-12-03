<template>
  <v-card
    class="reading-item-card"
    elevation="2"
    @click="$emit('click')"
  >
    <div class="d-flex">
      <!-- 封面 -->
      <v-img
        :src="item.cover_url || '/placeholder-book.jpg'"
        width="120"
        height="160"
        cover
        class="reading-cover"
      >
        <template v-slot:placeholder>
          <div class="d-flex align-center justify-center fill-height">
            <v-icon size="48" color="grey-lighten-1">
              {{ getMediaIcon(item.media_type) }}
            </v-icon>
          </div>
        </template>
        <div class="media-type-chip">
          <v-chip
            :color="getMediaColor(item.media_type)"
            size="x-small"
            variant="flat"
          >
            {{ getMediaLabel(item.media_type) }}
          </v-chip>
        </div>
        <div v-if="item.is_finished" class="finished-badge">
          <v-chip color="success" size="x-small" variant="flat">
            已读完
          </v-chip>
        </div>
      </v-img>

      <!-- 内容 -->
      <div class="flex-grow-1 pa-3 d-flex flex-column">
        <div class="text-h6 font-weight-medium mb-1 text-truncate" :title="item.title">
          {{ item.title }}
        </div>
        <div v-if="item.sub_title" class="text-caption text-medium-emphasis mb-1">
          {{ item.sub_title }}
        </div>
        <div v-if="item.source_label" class="text-caption text-disabled mb-2">
          {{ item.source_label }}
        </div>
        <div class="text-body-2 mb-1">
          <span v-if="type === 'ongoing'">
            {{ (item as ReadingOngoingItem).progress_label }}
          </span>
          <span v-else>
            {{ (item as ReadingHistoryItem).last_position_label }}
          </span>
        </div>
        <!-- 进度条 -->
        <v-progress-linear
          v-if="item.progress_percent != null"
          :model-value="item.progress_percent"
          :color="item.is_finished ? 'success' : 'primary'"
          height="4"
          rounded
          class="mb-2"
        />
        <div class="text-caption text-medium-emphasis mb-2">
          {{ formatDate(item.last_read_at) }}
        </div>
        <v-spacer />
        <v-btn
          v-if="type === 'ongoing' && !item.is_finished"
          color="primary"
          variant="flat"
          size="small"
          block
          @click.stop="$emit('click')"
        >
          继续{{ getMediaAction(item.media_type) }}
        </v-btn>
        <v-btn
          v-else
          color="primary"
          variant="outlined"
          size="small"
          block
          @click.stop="$emit('click')"
        >
          查看
        </v-btn>
      </div>
    </div>
  </v-card>
</template>

<script setup lang="ts">
import type {
  ReadingOngoingItem,
  ReadingHistoryItem,
  ReadingMediaType
} from '@/types/readingHub'

defineProps<{
  item: ReadingOngoingItem | ReadingHistoryItem
  type: 'ongoing' | 'history'
}>()

defineEmits<{
  click: []
}>()

// 获取媒体类型图标
const getMediaIcon = (type: ReadingMediaType): string => {
  const icons = {
    NOVEL: 'mdi-book-open-page-variant',
    AUDIOBOOK: 'mdi-headphones',
    MANGA: 'mdi-book-open-variant'
  }
  return icons[type] || 'mdi-book'
}

// 获取媒体类型颜色
const getMediaColor = (type: ReadingMediaType): string => {
  const colors = {
    NOVEL: 'blue',
    AUDIOBOOK: 'purple',
    MANGA: 'orange'
  }
  return colors[type] || 'grey'
}

// 获取媒体类型标签
const getMediaLabel = (type: ReadingMediaType): string => {
  const labels = {
    NOVEL: '小说',
    AUDIOBOOK: '有声书',
    MANGA: '漫画'
  }
  return labels[type] || type
}

// 获取媒体操作动词
const getMediaAction = (type: ReadingMediaType): string => {
  const actions = {
    NOVEL: '阅读',
    AUDIOBOOK: '收听',
    MANGA: '阅读'
  }
  return actions[type] || '查看'
}

// 格式化日期
const formatDate = (dateStr: string): string => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) {
    return '今天'
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days} 天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}
</script>

<style scoped lang="scss">
.reading-item-card {
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  height: 100%;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2) !important;
  }

  .reading-cover {
    position: relative;
    flex-shrink: 0;

    .media-type-chip {
      position: absolute;
      top: 8px;
      left: 8px;
    }

    .finished-badge {
      position: absolute;
      top: 8px;
      right: 8px;
    }
  }
}
</style>

