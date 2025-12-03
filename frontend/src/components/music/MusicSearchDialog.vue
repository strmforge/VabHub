<template>
  <v-dialog
    v-model="modelValue"
    max-width="800"
    scrollable
    persistent
  >
    <v-card>
      <v-card-item class="py-3">
        <template #prepend>
          <v-icon icon="mdi-music-search" class="me-2" />
        </template>
        <v-card-title class="text-h6">
          搜索音乐
        </v-card-title>
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
        <v-form>
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="searchQuery"
                label="搜索关键词"
                prepend-inner-icon="mdi-magnify"
                variant="outlined"
                density="compact"
                @keydown.enter="handleSearch"
                clearable
              />
            </v-col>
            <v-col cols="12" md="3">
              <v-select
                v-model="searchType"
                :items="searchTypes"
                label="搜索类型"
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col cols="12" md="3">
              <v-select
                v-model="platform"
                :items="platforms"
                label="平台"
                variant="outlined"
                density="compact"
                clearable
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="12" class="text-right">
              <v-btn
                color="primary"
                prepend-icon="mdi-magnify"
                @click="handleSearch"
                :loading="loading"
              >
                搜索
              </v-btn>
            </v-col>
          </v-row>
        </v-form>

        <!-- 搜索结果 -->
        <div v-if="loading" class="text-center py-12">
          <v-progress-circular indeterminate color="primary" size="64" />
          <div class="mt-4 text-body-1 text-medium-emphasis">搜索中...</div>
        </div>

        <div v-else-if="searchResults.length > 0" class="mt-4">
          <v-list density="comfortable">
            <v-list-item
              v-for="(result, index) in searchResults"
              :key="index"
              class="music-search-item"
            >
              <template #prepend>
                <v-avatar
                  size="64"
                  rounded="lg"
                  class="me-3"
                >
                  <v-img
                    v-if="result.cover_url"
                    :src="result.cover_url"
                    cover
                  />
                  <v-icon v-else size="32">mdi-music</v-icon>
                </v-avatar>
              </template>

              <v-list-item-title class="font-weight-bold">
                {{ result.title }}
              </v-list-item-title>
              <v-list-item-subtitle>
                <div class="d-flex align-center flex-wrap ga-2 mt-2">
                  <span class="text-body-2">{{ result.artist }}</span>
                  <span v-if="result.album" class="text-caption text-medium-emphasis">
                    • {{ result.album }}
                  </span>
                  <v-chip
                    :color="getPlatformColor(result.platform)"
                    size="x-small"
                    variant="flat"
                  >
                    {{ getPlatformName(result.platform) }}
                  </v-chip>
                  <span v-if="result.duration" class="text-caption text-medium-emphasis">
                    {{ formatDuration(result.duration) }}
                  </span>
                </div>
              </v-list-item-subtitle>

              <template #append>
                <v-btn
                  icon="mdi-check"
                  size="small"
                  variant="text"
                  color="primary"
                  @click="selectMusic(result)"
                />
              </template>
            </v-list-item>
          </v-list>
        </div>

        <div v-else-if="hasSearched" class="text-center py-12">
          <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-music-off</v-icon>
          <div class="text-h6 text-medium-emphasis mb-2">未找到结果</div>
          <div class="text-body-2 text-medium-emphasis">请尝试其他关键词</div>
        </div>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          variant="text"
          @click="modelValue = false"
        >
          关闭
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
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'select': [music: any]
}>()

const searchQuery = ref('')
const searchType = ref('all')
const platform = ref<string | null>(null)
const loading = ref(false)
const searchResults = ref<any[]>([])
const hasSearched = ref(false)

const modelValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const searchTypes = [
  { title: '全部', value: 'all' },
  { title: '歌曲', value: 'song' },
  { title: '专辑', value: 'album' },
  { title: '艺术家', value: 'artist' }
]

const platforms = [
  { title: 'Spotify', value: 'spotify' },
  { title: 'Apple Music', value: 'apple_music' },
  { title: 'QQ音乐', value: 'qq_music' },
  { title: '网易云音乐', value: 'netease' }
]

const handleSearch = async () => {
  if (!searchQuery.value.trim()) {
    return
  }

  loading.value = true
  hasSearched.value = true
  try {
    const response = await api.post('/music/search', {
      query: searchQuery.value,
      type: searchType.value,
      platform: platform.value,
      limit: 20
    })
    searchResults.value = response.data
  } catch (error: any) {
    console.error('搜索音乐失败:', error)
    alert('搜索失败：' + (error.response?.data?.detail || '未知错误'))
    searchResults.value = []
  } finally {
    loading.value = false
  }
}

const selectMusic = (music: any) => {
  emit('select', music)
  modelValue.value = false
}

const getPlatformColor = (platform: string) => {
  const colors: Record<string, string> = {
    spotify: 'success',
    apple_music: 'pink',
    qq_music: 'primary',
    netease: 'red'
  }
  return colors[platform] || 'grey'
}

const getPlatformName = (platform: string) => {
  const names: Record<string, string> = {
    spotify: 'Spotify',
    apple_music: 'Apple Music',
    qq_music: 'QQ音乐',
    netease: '网易云'
  }
  return names[platform] || platform
}

const formatDuration = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.music-search-item {
  border-bottom: 1px solid rgba(var(--v-border-color), 0.12);
  cursor: pointer;
  transition: background-color 0.2s;
}

.music-search-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.1);
}
</style>

