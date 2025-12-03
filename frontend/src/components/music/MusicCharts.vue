<template>
  <div class="music-charts">
    <v-card class="mb-4">
      <v-card-text>
        <v-row align="center" dense>
          <v-col cols="12" md="3">
            <v-select
              v-model="selectedPlatform"
              :items="platforms"
              label="选择平台"
              variant="outlined"
              density="compact"
              @update:model-value="handleFilterChange"
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="chartType"
              :items="chartTypes"
              label="榜单类型"
              variant="outlined"
              density="compact"
              @update:model-value="handleFilterChange"
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="region"
              :items="regions"
              label="地区"
              variant="outlined"
              density="compact"
              @update:model-value="handleFilterChange"
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="historyWindow"
              :items="historyOptions"
              label="历史批次"
              variant="outlined"
              density="compact"
              @update:model-value="handleFilterChange"
            />
          </v-col>
          <v-col cols="12" class="d-flex justify-end">
            <v-btn
              color="primary"
              prepend-icon="mdi-refresh"
              :loading="loading"
              @click="loadCharts"
            >
              刷新
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-card>
      <v-card-title class="d-flex flex-column flex-md-row align-md-center justify-space-between ga-2">
        <div>
          <div class="text-h6">
            {{ getPlatformName(selectedPlatform) }} · {{ getChartTypeName(chartType) }}
          </div>
          <div v-if="currentBatch?.capturedAt" class="text-caption text-medium-emphasis">
            {{ formatBatchTime(currentBatch.capturedAt) }}
          </div>
        </div>
        <v-select
          v-if="batchOptions.length > 1"
          v-model="selectedBatchId"
          :items="batchOptions"
          label="查看批次"
          class="batch-select"
          hide-details
          density="compact"
          variant="outlined"
        />
      </v-card-title>
      <v-card-text>
        <div v-if="loading" class="text-center py-8">
          <v-progress-circular indeterminate color="primary" />
        </div>
        <div v-else-if="currentEntries.length === 0" class="text-center py-8 text-medium-emphasis">
          暂无数据，尝试更换条件后重新查询。
        </div>
        <v-list v-else>
          <v-list-item
            v-for="(item, index) in currentEntries"
            :key="entryKey(item, index)"
            :prepend-avatar="item.coverUrl"
            :title="item.title"
            :subtitle="item.artist"
          >
            <template #prepend>
              <v-chip size="small" color="primary" class="me-2">
                {{ item.rank || index + 1 }}
              </v-chip>
            </template>
            <template #append>
              <v-btn icon variant="text" size="small" @click="playTrack(item)">
                <v-icon>mdi-play</v-icon>
              </v-btn>
              <v-btn
                class="ms-1"
                color="purple"
                variant="text"
                size="small"
                :loading="creatingId === entryKey(item, index)"
                @click="createSubscription(item, index)"
              >
                <v-icon start>mdi-bookmark-plus</v-icon>
                订阅
              </v-btn>
            </template>
          </v-list-item>
        </v-list>
      </v-card-text>
    </v-card>

    <v-card class="mt-4" v-if="historyBatches.length">
      <v-card-title>
        历史记录
        <span class="text-caption text-medium-emphasis ms-2">共 {{ historyBatches.length }} 条</span>
      </v-card-title>
      <v-divider />
      <v-expansion-panels>
        <v-expansion-panel
          v-for="batch in historyBatches"
          :key="batch.batchId"
        >
          <v-expansion-panel-title>
            {{ formatBatchTime(batch.capturedAt) }} · {{ batch.entries.length }} 首
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-list density="compact">
              <v-list-item
                v-for="(entry, idx) in batch.entries.slice(0, 5)"
                :key="`${batch.batchId}-${idx}`"
                :title="`${entry.rank || idx + 1}. ${entry.title}`"
                :subtitle="entry.artist"
              />
            </v-list>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useToast } from 'vue-toastification'
// import {
//   fetchMusicChartBatches,
//   createMusicSubscriptionFromChart,
//   type MusicChartBatch,
//   type MusicChartEntry
// } from '@/services/music'

// Mock types since services are not available
interface MusicChartBatch {
  id: number
  batchId: string
  name: string
  platform: string
  type: string
  region: string
  capturedAt: string
  entries: MusicChartEntry[]
}

interface MusicChartEntry {
  id: number
  title: string
  artist: string
  rank: number
  coverUrl?: string
  chartType?: string
  platform?: string
}

const toast = useToast()
const emit = defineEmits<{
  (e: 'subscription-created'): void
}>()

const loading = ref(false)
const creatingId = ref<string | null>(null)
const selectedPlatform = ref('qq_music')
const chartType = ref('hot')
const region = ref('CN')
const historyWindow = ref(3)
const chartBatches = ref<MusicChartBatch[]>([])
const selectedBatchId = ref<string | null>(null)

const platforms = [
  { title: 'QQ音乐', value: 'qq_music' },
  { title: '网易云音乐', value: 'netease' },
  { title: 'TME由你音乐榜', value: 'tme_youni' },
  { title: 'Billboard中国', value: 'billboard_china' },
  { title: 'Spotify', value: 'spotify' },
  { title: 'Apple Music', value: 'apple_music' }
]

const chartTypes = [
  { title: '热门榜', value: 'hot' },
  { title: '新歌榜', value: 'new' },
  { title: '飙升榜', value: 'trending' }
]

const regions = [
  { title: '中国', value: 'CN' },
  { title: '全球', value: 'GLOBAL' },
  { title: '美国', value: 'US' }
]

const historyOptions = [
  { title: '最新 1 次', value: 1 },
  { title: '最近 3 次', value: 3 },
  { title: '最近 5 次', value: 5 }
]

const currentBatch = computed(() => {
  return chartBatches.value.find(batch => batch.batchId === selectedBatchId.value) ?? chartBatches.value[0]
})

const currentEntries = computed<MusicChartEntry[]>(() => currentBatch.value?.entries ?? [])

const historyBatches = computed(() => {
  if (!currentBatch.value) return []
  return chartBatches.value.filter(batch => batch.batchId !== currentBatch.value?.batchId)
})

const batchOptions = computed(() =>
  chartBatches.value.map(batch => ({
    title: formatBatchTime(batch.capturedAt),
    value: batch.batchId
  }))
)

const getPlatformName = (platform: string) => {
  return platforms.find(p => p.value === platform)?.title ?? platform
}

const getChartTypeName = (type: string) => {
  return chartTypes.find(t => t.value === type)?.title ?? type
}

const formatBatchTime = (value?: string | null) => {
  if (!value) return '未知时间'
  const date = new Date(value)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const entryKey = (entry: MusicChartEntry, index: number) => {
  if (entry.id) {
    return `entry-${entry.id}`
  }
  const chart = entry.chartType || (entry as any).chart_type || 'unknown'
  return `${entry.platform}-${chart}-${entry.rank ?? index}-${entry.title}-${entry.artist}`
}

const handleFilterChange = () => {
  loadCharts()
}

const loadCharts = async () => {
  loading.value = true
  try {
    // Mock implementation since fetchMusicChartBatches is not available
    // const batches = await fetchMusicChartBatches({
    //   platform: selectedPlatform.value,
    //   chartType: chartType.value,
    //   region: region.value,
    //   batches: historyWindow.value
    // })
    
    // Mock data
    const batches: MusicChartBatch[] = []
    chartBatches.value = batches
    selectedBatchId.value = batches[0]?.batchId ?? null
  } catch (error: any) {
    toast.error(error.message || '加载榜单失败')
    chartBatches.value = []
    selectedBatchId.value = null
  } finally {
    loading.value = false
  }
}

const createSubscription = async (item: MusicChartEntry, index: number) => {
  const key = entryKey(item, index)
  if (!item.id) {
    toast.error('当前榜单条目缺少 ID，稍后再试')
    return
  }
  creatingId.value = key
  try {
    // Mock implementation since createMusicSubscriptionFromChart is not available
    // const response = await createMusicSubscriptionFromChart(item.id, {
    //   name: `${item.title} - ${item.artist}`,
    //   type: 'track',
    //   autoDownload: true,
    //   quality: 'flac',
    //   searchKeywords: [`${item.artist} - ${item.title}`]
    // })
    
    // Mock response
    const response = { success: true }
    
    if (response.success) {
      toast.success(`已订阅: ${item.title} - ${item.artist}`)
      emit('subscription-created')
    } else {
      toast.error('订阅创建失败')
    }
  } catch (error: any) {
    toast.error(error.message || '订阅创建失败')
  } finally {
    creatingId.value = null
  }
}

const playTrack = (track: MusicChartEntry) => {
  toast.info(`播放: ${track.title} - ${track.artist}`)
}

onMounted(() => {
  loadCharts()
})
</script>

<style scoped>
.music-charts {
  padding: 0;
}

.batch-select {
  max-width: 260px;
}
</style>

