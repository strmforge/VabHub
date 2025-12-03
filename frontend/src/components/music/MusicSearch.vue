<template>
  <div class="music-search">
    <!-- 搜索栏 -->
    <v-card class="mb-4">
      <v-card-text>
        <v-row align="center">
          <v-col cols="12" md="4">
            <v-text-field
              v-model="searchQuery"
              label="搜索音乐..."
              variant="outlined"
              density="compact"
              prepend-inner-icon="mdi-magnify"
              @keyup.enter="handleSearch"
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
          <v-col cols="12" md="2">
            <v-btn
              color="primary"
              block
              :loading="loading"
              @click="handleSearch"
            >
              搜索
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
    
    <!-- 搜索结果 -->
    <v-card v-if="results.length > 0">
      <v-card-title>搜索结果 ({{ results.length }})</v-card-title>
      <v-card-text>
        <v-list>
          <v-list-item
            v-for="item in results"
            :key="item.id"
            :prepend-avatar="item.cover_url"
            :title="item.title"
            :subtitle="`${item.artist}${item.album ? ' · ' + item.album : ''}`"
          >
            <template v-slot:append>
              <v-btn icon variant="text" size="small" @click="playTrack(item)">
                <v-icon>mdi-play</v-icon>
              </v-btn>
            </template>
          </v-list-item>
        </v-list>
      </v-card-text>
    </v-card>
    
    <!-- 空状态 -->
    <v-card v-else-if="!loading && searchQuery">
      <v-card-text class="text-center py-12">
        <v-icon size="64" color="grey">mdi-music-note-off</v-icon>
        <div class="text-h6 mt-4">未找到相关音乐</div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useToast } from 'vue-toastification'
import api from '@/services/api'

const toast = useToast()

const loading = ref(false)
const searchQuery = ref('')
const searchType = ref('all')
const platform = ref(null)
const results = ref<any[]>([])

const searchTypes = [
  { title: '全部', value: 'all' },
  { title: '歌曲', value: 'song' },
  { title: '专辑', value: 'album' },
  { title: '艺术家', value: 'artist' }
]

const platforms = [
  { title: '全部平台', value: null },
  { title: 'Spotify', value: 'spotify' },
  { title: 'Apple Music', value: 'apple_music' },
  { title: 'QQ音乐', value: 'qq_music' },
  { title: '网易云', value: 'netease' }
]

const handleSearch = async () => {
  if (!searchQuery.value) {
    toast.warning('请输入搜索关键词')
    return
  }
  
  loading.value = true
  try {
    const response = await api.post('/music/search', {
      query: searchQuery.value,
      type: searchType.value,
      platform: platform.value,
      limit: 50
    })
    results.value = response.data || []
  } catch (error: any) {
    toast.error(error.message || '搜索失败')
    results.value = []
  } finally {
    loading.value = false
  }
}

const playTrack = (track: any) => {
  // TODO: 实现播放功能
  toast.info(`播放: ${track.title}`)
}
</script>

<style scoped>
.music-search {
  padding: 0;
}
</style>

