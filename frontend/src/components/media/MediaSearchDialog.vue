<template>
  <v-dialog
    v-model="modelValue"
    max-width="1200"
    scrollable
    persistent
  >
    <v-card>
      <v-card-item class="py-3">
        <template #prepend>
          <v-icon icon="mdi-magnify" class="me-2" />
        </template>
        <v-card-title class="text-h6">
          搜索并选择媒体
        </v-card-title>
        <v-card-subtitle>
          {{ mediaType === 'movie' ? '搜索电影' : '搜索电视剧' }}
        </v-card-subtitle>
        <template #append>
          <v-btn
            icon="mdi-close"
            variant="text"
            size="small"
            @click="modelValue = false"
          />
        </template>
      </v-card-item>

      <v-card-text>
        <!-- 搜索框 -->
        <v-text-field
          v-model="searchQuery"
          placeholder="输入电影或电视剧名称..."
          prepend-inner-icon="mdi-magnify"
          variant="outlined"
          density="compact"
          clearable
          @keydown.enter="handleSearch"
          class="mb-4"
        >
          <template #append>
            <v-btn
              color="primary"
              @click="handleSearch"
              :loading="searching"
            >
              搜索
            </v-btn>
          </template>
        </v-text-field>

        <!-- 搜索结果 -->
        <div v-if="searching" class="text-center py-12">
          <v-progress-circular indeterminate color="primary" size="64" />
          <div class="mt-4 text-body-1 text-medium-emphasis">搜索中...</div>
        </div>

        <div v-else-if="searchResults.length === 0 && searchQuery" class="text-center py-12">
          <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-magnify</v-icon>
          <div class="text-h6 text-medium-emphasis mb-2">未找到结果</div>
          <div class="text-body-2 text-medium-emphasis">请尝试使用其他关键词搜索</div>
        </div>

        <div v-else-if="searchResults.length > 0">
          <v-row>
            <v-col
              v-for="media in searchResults"
              :key="media.id"
              cols="6"
              sm="4"
              md="3"
              lg="2"
            >
              <v-card
                class="media-select-card"
                @click="selectMedia(media)"
                :class="{ 'media-selected': selectedMedia?.id === media.id }"
              >
                <v-img
                  :src="getPosterUrl(media.poster_path)"
                  aspect-ratio="2/3"
                  cover
                  class="media-select-poster"
                >
                  <template #placeholder>
                    <v-skeleton-loader type="image" />
                  </template>
                  <div class="media-select-overlay">
                    <v-icon
                      :icon="selectedMedia?.id === media.id ? 'mdi-check-circle' : 'mdi-plus-circle'"
                      :color="selectedMedia?.id === media.id ? 'success' : 'white'"
                      size="48"
                    />
                  </div>
                </v-img>
                <v-card-text class="pa-2">
                  <div class="text-body-2 font-weight-bold text-truncate">
                    {{ media.title || media.name }}
                  </div>
                  <div v-if="media.release_date || media.first_air_date" class="text-caption text-medium-emphasis">
                    {{ getYear(media.release_date || media.first_air_date) }}
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </div>

        <div v-else class="text-center py-12">
          <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-movie-search-outline</v-icon>
          <div class="text-h6 text-medium-emphasis mb-2">搜索媒体</div>
          <div class="text-body-2 text-medium-emphasis">在上方输入框输入电影或电视剧名称进行搜索</div>
        </div>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn @click="modelValue = false">取消</v-btn>
        <v-btn
          color="primary"
          :disabled="!selectedMedia"
          @click="handleConfirm"
        >
          确认选择
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import api from '@/services/api'

interface Props {
  modelValue: boolean
  mediaType: 'movie' | 'tv'
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'select': [media: any]
}>()

const searchQuery = ref('')
const searching = ref(false)
const searchResults = ref<any[]>([])
const selectedMedia = ref<any>(null)

const modelValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 搜索媒体
const handleSearch = async () => {
  if (!searchQuery.value.trim()) return

  searching.value = true
  try {
    const response = await api.get('/media/search', {
      params: {
        query: searchQuery.value,
        type: props.mediaType
      }
    })
    searchResults.value = response.data || []
  } catch (error: any) {
    console.error('搜索媒体失败:', error)
    searchResults.value = []
  } finally {
    searching.value = false
  }
}

// 选择媒体
const selectMedia = (media: any) => {
  selectedMedia.value = media
}

// 确认选择
const handleConfirm = () => {
  if (selectedMedia.value) {
    emit('select', selectedMedia.value)
    modelValue.value = false
  }
}

// 获取海报URL
const getPosterUrl = (posterPath: string | null) => {
  if (!posterPath) return '/placeholder-poster.jpg'
  if (posterPath.startsWith('http')) return posterPath
  return `https://image.tmdb.org/t/p/w500${posterPath}`
}

// 获取年份
const getYear = (date: string) => {
  if (!date) return ''
  return new Date(date).getFullYear().toString()
}
</script>

<style scoped lang="scss">
.media-select-card {
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
  }
}

.media-selected {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: 2px;
}

.media-select-poster {
  position: relative;
}

.media-select-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.media-select-card:hover .media-select-overlay,
.media-selected .media-select-overlay {
  opacity: 1;
}
</style>

