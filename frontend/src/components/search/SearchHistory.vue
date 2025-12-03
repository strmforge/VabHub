<template>
  <v-card>
    <v-card-title class="d-flex align-center justify-space-between">
      <span>搜索历史</span>
      <div>
        <v-btn
          icon="mdi-delete-sweep"
          size="small"
          variant="text"
          @click="handleClear"
          :loading="clearing"
        />
        <v-btn
          icon="mdi-refresh"
          size="small"
          variant="text"
          @click="loadHistory"
          :loading="loading"
        />
      </div>
    </v-card-title>

    <v-card-text>
      <div v-if="loading" class="text-center py-4">
        <v-progress-circular indeterminate color="primary" size="32" />
      </div>

      <div v-else-if="history.length === 0" class="text-center py-8 text-medium-emphasis">
        暂无搜索历史
      </div>

      <v-list v-else density="compact">
        <v-list-item
          v-for="item in history"
          :key="item.id"
          @click="handleSelect(item)"
          class="search-history-item"
        >
          <template #prepend>
            <v-icon>mdi-clock-outline</v-icon>
          </template>

          <v-list-item-title>{{ item.query }}</v-list-item-title>
          <v-list-item-subtitle>
            <div class="d-flex align-center flex-wrap ga-2 mt-1">
              <v-chip
                v-if="item.media_type"
                size="x-small"
                variant="flat"
                color="primary"
              >
                {{ getMediaTypeLabel(item.media_type) }}
              </v-chip>
              <span class="text-caption">
                {{ item.result_count }} 个结果
              </span>
              <span class="text-caption text-medium-emphasis">
                {{ formatDate(item.searched_at) }}
              </span>
            </div>
          </v-list-item-subtitle>

          <template #append>
            <v-btn
              icon="mdi-delete"
              size="x-small"
              variant="text"
              @click.stop="handleDelete(item)"
            />
          </template>
        </v-list-item>
      </v-list>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/services/api'

interface SearchHistoryItem {
  id: number
  query: string
  media_type: string | null
  filters: any
  result_count: number
  searched_at: string
}

const props = defineProps<{
  limit?: number
}>()

const emit = defineEmits<{
  'select': [item: SearchHistoryItem]
}>()

const loading = ref(false)
const clearing = ref(false)
const history = ref<SearchHistoryItem[]>([])

const loadHistory = async () => {
  loading.value = true
  try {
    const response = await api.get('/search/history', {
      params: {
        limit: props.limit || 20
      }
    })
    history.value = response.data
  } catch (error: any) {
    console.error('加载搜索历史失败:', error)
    history.value = []
  } finally {
    loading.value = false
  }
}

const handleSelect = (item: SearchHistoryItem) => {
  emit('select', item)
}

const handleDelete = async (item: SearchHistoryItem) => {
  if (!confirm(`确定要删除搜索记录"${item.query}"吗？`)) {
    return
  }

  try {
    await api.delete(`/search/history/${item.id}`)
    await loadHistory()
  } catch (error: any) {
    console.error('删除搜索历史失败:', error)
    alert('删除失败：' + (error.response?.data?.detail || '未知错误'))
  }
}

const handleClear = async () => {
  if (!confirm('确定要清空所有搜索历史吗？')) {
    return
  }

  clearing.value = true
  try {
    await api.delete('/search/history')
    history.value = []
    alert('搜索历史已清空')
  } catch (error: any) {
    console.error('清空搜索历史失败:', error)
    alert('清空失败：' + (error.response?.data?.detail || '未知错误'))
  } finally {
    clearing.value = false
  }
}

const getMediaTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    movie: '电影',
    tv: '电视剧',
    anime: '动漫'
  }
  return labels[type] || type
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (minutes < 1) return '刚刚'
    if (minutes < 60) return `${minutes}分钟前`
    if (hours < 24) return `${hours}小时前`
    if (days < 7) return `${days}天前`
    return date.toLocaleDateString('zh-CN')
  } catch {
    return dateStr
  }
}

onMounted(() => {
  loadHistory()
})

defineExpose({
  loadHistory
})
</script>

<style scoped>
.search-history-item {
  cursor: pointer;
  transition: background-color 0.2s;
}

.search-history-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.1);
}
</style>

