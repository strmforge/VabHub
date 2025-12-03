<template>
  <div>
    <!-- 目录选择 -->
    <v-row class="mb-4">
      <v-col cols="12" md="4">
        <v-select
          v-model="selectedDirectoryId"
          :items="directoryOptions"
          label="选择存储目录"
          variant="outlined"
          @update:model-value="loadTrends"
        />
      </v-col>
      <v-col cols="12" md="4">
        <v-select
          v-model="selectedDays"
          :items="daysOptions"
          label="时间范围"
          variant="outlined"
          @update:model-value="loadTrends"
        />
      </v-col>
      <v-col cols="12" md="4" class="d-flex align-center">
        <v-btn
          color="primary"
          prepend-icon="mdi-refresh"
          @click="loadTrends"
          :loading="loading"
        >
          刷新
        </v-btn>
      </v-col>
    </v-row>

    <!-- 趋势图表 -->
    <v-card v-if="selectedDirectoryId && trendsData">
      <v-card-title>
        <v-icon color="primary" class="mr-2">mdi-chart-timeline-variant</v-icon>
        存储使用趋势
      </v-card-title>

      <v-card-text>
        <div v-if="trendsData.trends && trendsData.trends.length > 0">
          <StorageUsageChart
            :trends="trendsData.trends"
            :days="trendsData.days"
          />
        </div>
        <v-alert
          v-else
          type="info"
          variant="tonal"
        >
          暂无趋势数据，请等待定时任务记录使用历史。
        </v-alert>
      </v-card-text>
    </v-card>

    <!-- 未选择目录提示 -->
    <v-alert
      v-else
      type="info"
      variant="tonal"
    >
      请选择一个存储目录查看使用趋势。
    </v-alert>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { storageMonitorApi } from '@/services/api'
import { useToast } from '@/composables/useToast'
import StorageUsageChart from './StorageUsageChart.vue'

const props = defineProps<{
  directories: any[]
  loading: boolean
}>()

const emit = defineEmits<{
  refresh: []
}>()

const { showToast } = useToast()

const selectedDirectoryId = ref<number | null>(null)
const selectedDays = ref(7)
const trendsData = ref<any>(null)
const loadingTrends = ref(false)

const directoryOptions = computed(() => {
  return props.directories
    .filter(d => d.enabled)
    .map(d => ({
      title: d.name,
      value: d.id
    }))
})

const daysOptions = [
  { title: '最近7天', value: 7 },
  { title: '最近14天', value: 14 },
  { title: '最近30天', value: 30 },
  { title: '最近60天', value: 60 }
]

// 加载趋势数据
const loadTrends = async () => {
  if (!selectedDirectoryId.value) {
    return
  }

  try {
    loadingTrends.value = true
    const response = await storageMonitorApi.getDirectoryTrends(
      selectedDirectoryId.value,
      selectedDays.value
    )
    trendsData.value = response.data
  } catch (error: any) {
    console.error('加载趋势数据失败:', error)
    showToast('加载趋势数据失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    loadingTrends.value = false
  }
}

// 监听目录变化
watch(() => props.directories, (newDirs) => {
  if (newDirs.length > 0 && !selectedDirectoryId.value) {
    const firstEnabled = newDirs.find(d => d.enabled)
    if (firstEnabled) {
      selectedDirectoryId.value = firstEnabled.id
      loadTrends()
    }
  }
}, { immediate: true })
</script>

