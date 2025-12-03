<template>
  <div class="music-library">
    <!-- 统计卡片 -->
    <v-row class="mb-4">
      <v-col cols="12" sm="6" md="3">
        <v-card variant="elevated" color="primary">
          <v-card-text class="pa-4 text-center">
            <v-icon size="32" class="mb-2">mdi-music</v-icon>
            <div class="stat-number">{{ stats.total_tracks || 0 }}</div>
            <div class="stat-label">总曲目数</div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card variant="elevated" color="success">
          <v-card-text class="pa-4 text-center">
            <v-icon size="32" class="mb-2">mdi-account-music</v-icon>
            <div class="stat-number">{{ stats.total_artists || 0 }}</div>
            <div class="stat-label">艺术家数</div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card variant="elevated" color="info">
          <v-card-text class="pa-4 text-center">
            <v-icon size="32" class="mb-2">mdi-album</v-icon>
            <div class="stat-number">{{ stats.total_albums || 0 }}</div>
            <div class="stat-label">专辑数</div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card variant="elevated" color="warning">
          <v-card-text class="pa-4 text-center">
            <v-icon size="32" class="mb-2">mdi-harddisk</v-icon>
            <div class="stat-number">{{ formatBytes(stats.total_size_mb || 0) }}</div>
            <div class="stat-label">总存储空间</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    
    <!-- 操作工具栏 -->
    <v-card class="mb-4">
      <v-card-text>
        <v-row align="center">
          <v-col cols="12" md="6">
            <v-text-field
              v-model="scanPath"
              label="扫描路径"
              variant="outlined"
              density="compact"
              prepend-inner-icon="mdi-folder"
              hide-details
            />
          </v-col>
          <v-col cols="12" md="6" class="d-flex align-center">
            <v-checkbox
              v-model="recursiveScan"
              label="递归扫描"
              density="compact"
              class="me-4"
            />
            <v-btn
              color="primary"
              prepend-icon="mdi-magnify-scan"
              :loading="scanning"
              @click="handleScan"
            >
              扫描音乐库
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
    
    <!-- 音乐列表 -->
    <v-card>
      <v-card-title>音乐库</v-card-title>
      <v-card-text>
        <div v-if="loading" class="text-center py-8">
          <v-progress-circular indeterminate color="primary" />
        </div>
        <div v-else-if="tracks.length === 0" class="text-center py-12">
          <v-icon size="64" color="grey">mdi-music-off</v-icon>
          <div class="text-h6 mt-4">暂无音乐</div>
          <div class="text-body-2 text-medium-emphasis mt-2">
            点击"扫描音乐库"按钮开始扫描本地音乐文件
          </div>
        </div>
        <v-data-table
          v-else
          :headers="headers"
          :items="tracks"
          :loading="loading"
          item-value="id"
        >
          <template v-slot:item.title="{ item }">
            <div class="d-flex align-center">
              <v-avatar size="40" rounded class="me-3">
                <v-img v-if="item.cover_url" :src="item.cover_url" />
                <v-icon v-else>mdi-music</v-icon>
              </v-avatar>
              <div>
                <div class="font-weight-medium">{{ item.title }}</div>
                <div class="text-caption text-medium-emphasis">{{ item.artist }}</div>
              </div>
            </div>
          </template>
          <template v-slot:item.duration="{ item }">
            {{ formatDuration(item.duration) }}
          </template>
          <template v-slot:item.actions="{ item }">
            <v-btn icon variant="text" size="small" @click="playTrack(item)">
              <v-icon>mdi-play</v-icon>
            </v-btn>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'vue-toastification'
import api from '@/services/api'

const toast = useToast()

const loading = ref(false)
const scanning = ref(false)
const scanPath = ref('')
const recursiveScan = ref(true)
const stats = ref<any>({})
const tracks = ref<any[]>([])

const headers = [
  { title: '歌曲', key: 'title', sortable: true },
  { title: '专辑', key: 'album', sortable: true },
  { title: '时长', key: 'duration', sortable: false },
  { title: '操作', key: 'actions', sortable: false }
]

const loadStats = async () => {
  try {
    const response = await api.get('/music/library/stats')
    stats.value = response.data || {}
  } catch (error) {
    console.error('加载音乐库统计失败:', error)
  }
}

const handleScan = async () => {
  if (!scanPath.value) {
    toast.warning('请输入扫描路径')
    return
  }
  
  scanning.value = true
  try {
    await api.post('/music/library/scan', {
      path: scanPath.value,
      recursive: recursiveScan.value
    })
    toast.success('扫描完成')
    await loadStats()
    // TODO: 加载音乐列表
  } catch (error: any) {
    toast.error(error.message || '扫描失败')
  } finally {
    scanning.value = false
  }
}

const formatBytes = (mb: number): string => {
  if (mb < 1024) return `${mb.toFixed(2)} MB`
  return `${(mb / 1024).toFixed(2)} GB`
}

const formatDuration = (seconds: number): string => {
  if (!seconds) return '-'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const playTrack = (track: any) => {
  // TODO: 实现播放功能
  toast.info(`播放: ${track.title}`)
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.stat-number {
  font-size: 24px;
  font-weight: bold;
  margin: 8px 0;
}

.stat-label {
  font-size: 14px;
  opacity: 0.8;
}
</style>

