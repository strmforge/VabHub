<template>
  <v-card
    class="library-preview-card"
    :class="{ 'cursor-pointer': clickable }"
    @click="$emit('click')"
    hover
    elevation="2"
  >
    <!-- 封面图片 -->
    <v-img
      :src="coverUrl"
      :lazy-src="coverUrl"
      height="280"
      cover
      class="bg-grey-lighten-3"
    >
      <template v-slot:placeholder>
        <div class="d-flex align-center justify-center fill-height">
          <v-icon size="48" color="grey-lighten-1">{{ mediaTypeIcon }}</v-icon>
        </div>
      </template>
      <template v-slot:error>
        <div class="d-flex align-center justify-center fill-height">
          <v-icon size="48" color="grey-lighten-1">{{ mediaTypeIcon }}</v-icon>
        </div>
      </template>
      
      <!-- 媒体类型标签 -->
      <v-chip
        :color="mediaTypeColor"
        size="small"
        class="ma-2"
        variant="flat"
      >
        <v-icon start size="small">{{ mediaTypeIcon }}</v-icon>
        {{ mediaTypeLabel }}
      </v-chip>
    </v-img>

    <!-- 内容信息 -->
    <v-card-title class="text-body-1 line-clamp-2">
      {{ item.title }}
    </v-card-title>

    <v-card-subtitle>
      <div class="d-flex flex-column gap-1">
        <!-- 年份 -->
        <div v-if="item.year" class="d-flex align-center">
          <v-icon size="small" class="mr-1">mdi-calendar</v-icon>
          <span>{{ item.year }}</span>
        </div>

        <!-- 作者（电子书/有声书） -->
        <div v-if="item.extra?.author" class="d-flex align-center">
          <v-icon size="small" class="mr-1">mdi-account</v-icon>
          <span>{{ item.extra.author }}</span>
        </div>

        <!-- 系列（电子书/有声书/漫画） -->
        <div v-if="item.extra?.series" class="d-flex align-center">
          <v-icon size="small" class="mr-1">mdi-book-multiple</v-icon>
          <span>{{ item.extra.series }}</span>
          <span v-if="item.media_type === 'comic' && item.extra?.volume_index" class="ml-1 text-caption text-medium-emphasis">
            · 第{{ item.extra.volume_index }}卷
          </span>
        </div>
        
        <!-- 卷号（漫画） -->
        <div v-if="item.media_type === 'comic' && item.extra?.volume_index && !item.extra?.series" class="d-flex align-center">
          <v-icon size="small" class="mr-1">mdi-book-open-page-variant</v-icon>
          <span>第{{ item.extra.volume_index }}卷</span>
        </div>
        
        <!-- 作画（漫画） -->
        <div v-if="item.media_type === 'comic' && item.extra?.illustrator" class="d-flex align-center">
          <v-icon size="small" class="mr-1">mdi-draw-pen</v-icon>
          <span>{{ item.extra.illustrator }}</span>
        </div>
        
        <!-- 地区（漫画） -->
        <div v-if="item.media_type === 'comic' && item.extra?.region" class="d-flex align-center text-caption text-medium-emphasis">
          <v-icon size="x-small" class="mr-1">mdi-earth</v-icon>
          <span>{{ item.extra.region }}</span>
        </div>
        
        <!-- 专辑（音乐） -->
        <div v-if="item.media_type === 'music' && item.extra?.album" class="d-flex align-center">
          <v-icon size="small" class="mr-1">mdi-album</v-icon>
          <span>{{ item.extra.album }}</span>
        </div>
        
        <!-- 风格（音乐） -->
        <div v-if="item.media_type === 'music' && item.extra?.genre" class="d-flex align-center text-caption text-medium-emphasis">
          <v-icon size="x-small" class="mr-1">mdi-music-note</v-icon>
          <span>{{ item.extra.genre }}</span>
        </div>

        <!-- 朗读者（有声书） -->
        <div v-if="item.extra?.narrator" class="d-flex align-center">
          <v-icon size="small" class="mr-1">mdi-microphone</v-icon>
          <span>{{ item.extra.narrator }}</span>
        </div>

        <!-- 时长（有声书）- 增强显示 -->
        <div v-if="item.media_type === 'audiobook' && item.extra?.duration_seconds" class="d-flex align-center">
          <v-icon size="small" class="mr-1" color="orange">mdi-headphones</v-icon>
          <span class="font-weight-medium">有声 • {{ formatDuration(item.extra.duration_seconds) }}</span>
        </div>
        
        <!-- 音频质量（有声书）- 可选显示 -->
        <div v-if="item.media_type === 'audiobook' && hasAudioQuality(item.extra)" class="d-flex align-center text-caption text-medium-emphasis">
          <v-icon size="x-small" class="mr-1">mdi-information-outline</v-icon>
          <span>{{ formatAudioQuality({
            bitrate_kbps: item.extra?.bitrate_kbps,
            sample_rate_hz: item.extra?.sample_rate_hz,
            channels: item.extra?.channels
          }) }}</span>
        </div>

        <!-- 评分（Movie/TV/Anime） -->
        <div v-if="item.extra?.rating" class="d-flex align-center">
          <v-icon size="small" class="mr-1" color="warning">mdi-star</v-icon>
          <span>{{ item.extra.rating.toFixed(1) }}</span>
        </div>
      </div>
    </v-card-subtitle>

    <!-- 作品形态徽章（仅对 ebook 类型） -->
    <v-card-actions v-if="item.media_type === 'ebook' && hasWorkFormats" class="pt-0 pb-2 px-4">
      <div class="d-flex align-center gap-1 flex-wrap">
        <v-chip
          v-if="item.work_formats?.has_ebook"
          size="x-small"
          color="success"
          variant="flat"
          class="text-caption"
        >
          <v-icon start size="x-small">mdi-book-open-variant</v-icon>
          书
        </v-chip>
        <v-chip
          v-if="item.work_formats?.has_audiobook"
          size="x-small"
          color="orange"
          variant="flat"
          class="text-caption"
        >
          <v-icon start size="x-small">mdi-headphones</v-icon>
          有声
        </v-chip>
        <v-chip
          v-if="item.work_formats?.has_comic"
          size="x-small"
          color="pink"
          variant="flat"
          class="text-caption"
        >
          <v-icon start size="x-small">mdi-book-open-page-variant</v-icon>
          漫画
        </v-chip>
        <v-chip
          v-if="item.work_formats?.has_music"
          size="x-small"
          color="teal"
          variant="flat"
          class="text-caption"
        >
          <v-icon start size="x-small">mdi-music</v-icon>
          音乐
        </v-chip>
      </div>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { LibraryPreviewItem, MediaType } from '@/types/library'
import { formatDuration, formatAudioQuality } from '@/utils/formatters'

interface Props {
  item: LibraryPreviewItem
  clickable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  clickable: true
})

defineEmits<{
  click: []
}>()

// 封面 URL
const coverUrl = computed(() => {
  return props.item.cover_url || '/default-cover.png'
})

// 媒体类型相关
const mediaTypeLabel = computed(() => {
  const labels: Record<MediaType, string> = {
    movie: '电影',
    tv: '剧集',
    anime: '动漫',
    ebook: '电子书',
    audiobook: '有声书',
    comic: '漫画',
    music: '音乐'
  }
  return labels[props.item.media_type] || props.item.media_type
})

const mediaTypeIcon = computed(() => {
  const icons: Record<MediaType, string> = {
    movie: 'mdi-movie',
    tv: 'mdi-television',
    anime: 'mdi-animation',
    ebook: 'mdi-book-open-variant',
    audiobook: 'mdi-headphones',
    comic: 'mdi-book-open-page-variant',
    music: 'mdi-music'
  }
  return icons[props.item.media_type] || 'mdi-file'
})

const mediaTypeColor = computed(() => {
  const colors: Record<MediaType, string> = {
    movie: 'primary',
    tv: 'info',
    anime: 'purple',
    ebook: 'success',
    audiobook: 'orange',
    comic: 'pink',
    music: 'teal'
  }
  return colors[props.item.media_type] || 'grey'
})

// 检查是否有音频质量信息
const hasAudioQuality = (extra: any): boolean => {
  if (!extra) return false
  return (
    (extra.bitrate_kbps != null && !isNaN(extra.bitrate_kbps)) ||
    (extra.sample_rate_hz != null && !isNaN(extra.sample_rate_hz)) ||
    (extra.channels != null && !isNaN(extra.channels))
  )
}

// 检查是否有作品形态信息需要显示
const hasWorkFormats = computed(() => {
  const formats = props.item.work_formats
  if (!formats) return false
  return formats.has_ebook || formats.has_audiobook || formats.has_comic || formats.has_music
})
</script>

<style lang="scss" scoped>
.library-preview-card {
  height: 100%;
  transition: transform 0.2s, box-shadow 0.2s;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15) !important;
  }
}

.cursor-pointer {
  cursor: pointer;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>

