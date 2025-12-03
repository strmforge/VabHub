<template>
  <div class="subscriptions-page">
    <!-- 页面标题 -->
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold">{{ pageTitle }}</h1>
        <p class="text-body-1 text-medium-emphasis mt-2">{{ pageDescription }}</p>
      </div>
      <div class="d-flex ga-2">
        <v-btn
          variant="outlined"
          prepend-icon="mdi-cog"
          :to="{ name: 'Settings', hash: '#rule-center' }"
        >
          规则中心
        </v-btn>
        <v-btn
          color="primary"
          prepend-icon="mdi-robot"
          :to="{ name: 'AiSubsAssistant' }"
        >
          AI 订阅助手
        </v-btn>
      </div>
    </div>
    
    <!-- 过滤和搜索 -->
    <v-card variant="outlined" class="mb-4 filter-card">
      <v-card-text class="py-3">
        <v-row align="center" dense>
          <v-col cols="12" md="5">
            <v-text-field
              v-model="searchQuery"
              placeholder="搜索订阅..."
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              hide-details
              clearable
              class="filter-input"
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="statusFilter"
              :items="statusOptions"
              label="状态"
              variant="outlined"
              density="compact"
              hide-details
              class="filter-select"
            />
          </v-col>
          <v-col v-if="!currentMediaType" cols="12" md="4">
            <v-select
              v-model="typeFilter"
              :items="typeOptions"
              label="类型"
              variant="outlined"
              density="compact"
              hide-details
              class="filter-select"
            />
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  
    <!-- 订阅列表 - 卡片展示 -->
    <template v-if="loading">
      <v-card>
        <v-card-text class="d-flex justify-center align-center" style="min-height: 400px;">
          <div class="text-center">
            <v-progress-circular indeterminate color="primary" size="64" />
            <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
          </div>
        </v-card-text>
      </v-card>
    </template>
    
    <template v-else-if="filteredSubscriptions.length === 0">
      <v-card variant="outlined" class="subscription-empty-card">
        <v-card-text class="text-center pa-12">
          <v-icon size="80" color="grey-darken-1" class="mb-4">mdi-clipboard-text-off</v-icon>
          <div class="text-h5 font-weight-medium mb-2">暂无订阅</div>
          <div class="text-body-2 text-medium-emphasis">
            使用顶部的"创建订阅"按钮添加您的第一个订阅
          </div>
        </v-card-text>
      </v-card>
    </template>
    
    <template v-else>
      <v-row>
        <v-col
          v-for="subscription in filteredSubscriptions"
          :key="subscription.id"
          cols="12"
          sm="6"
          md="4"
          lg="3"
        >
          <SubscriptionCard
            :subscription="subscription"
            @edit="editSubscription"
            @delete="deleteSubscription"
            @search="handleSearchSubscription"
            @toggle-status="handleToggleSubscriptionStatus"
            @check-subscription="handleCheckSubscription"
          />
        </v-col>
      </v-row>
    </template>
    
    <!-- 创建/编辑对话框 -->
    <SubscriptionDialog
      v-model="showCreateDialog"
      :subscription="editingSubscription"
      @saved="handleSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/services/api'
import SubscriptionDialog from '@/components/subscription/SubscriptionDialog.vue'
import SubscriptionCard from '@/components/subscription/SubscriptionCard.vue'

const route = useRoute()

const loading = ref(false)
const subscriptions = ref<any[]>([])
const searchQuery = ref('')
const statusFilter = ref<string | null>(null)
const typeFilter = ref<string | null>(null)
const showCreateDialog = ref(false)
const editingSubscription = ref<any>(null)

const statusOptions = [
  { title: '全部', value: null },
  { title: '活跃', value: 'active' },
  { title: '暂停', value: 'paused' },
  { title: '完成', value: 'completed' }
]

const typeOptions = [
  { title: '全部', value: null },
  { title: '电影', value: 'movie' },
  { title: '电视剧', value: 'tv' },
  { title: '短剧', value: 'short_drama' },
  { title: '动漫', value: 'anime' },
  { title: '音乐', value: 'music' }
]

// 从路由 meta 获取当前媒体类型
const currentMediaType = computed(() => {
  return (route.meta.mediaType as string) || null
})

// 页面标题和描述
const pageTitles: Record<string, { title: string; description: string }> = {
  movie: { title: '电影订阅', description: '管理您的电影订阅，查看下载进度' },
  tv: { title: '电视剧订阅', description: '管理您的电视剧订阅，查看集数进度' },
  music: { title: '音乐订阅', description: '管理您的音乐订阅，查看榜单和自动循环' },
  book: { title: '书籍订阅', description: '管理您的书籍订阅，查看小说和有声书' }
}

const pageTitle = computed(() => {
  if (currentMediaType.value && pageTitles[currentMediaType.value]) {
    return pageTitles[currentMediaType.value].title
  }
  return '订阅管理'
})

const pageDescription = computed(() => {
  if (currentMediaType.value && pageTitles[currentMediaType.value]) {
    return pageTitles[currentMediaType.value].description
  }
  return '管理您的媒体订阅'
})

// 过滤后的订阅列表
const filteredSubscriptions = computed(() => {
  let result = subscriptions.value
  
  // 状态过滤
  if (statusFilter.value) {
    result = result.filter(s => s.status === statusFilter.value)
  }
  
  // 类型过滤
  if (typeFilter.value) {
    result = result.filter(s => s.media_type === typeFilter.value)
  }
  
  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(s => 
      s.title?.toLowerCase().includes(query) ||
      s.original_title?.toLowerCase().includes(query)
    )
  }
  
  console.log('过滤后的订阅数量:', result.length, '原始数量:', subscriptions.value.length)
  return result
})

const loadSubscriptions = async () => {
  loading.value = true
  try {
    // 优先使用路由 meta 中的媒体类型，其次使用 query
    const mediaTypeFromMeta = currentMediaType.value
    const mediaTypeQuery = route.query.media_type as string | undefined
    const params: any = {}
    
    if (mediaTypeFromMeta) {
      // 根据 meta 中的类型做映射（tv 包含 tv/anime/short_drama）
      if (mediaTypeFromMeta === 'tv') {
        params.media_type = ['tv', 'anime', 'short_drama']
      } else {
        params.media_type = mediaTypeFromMeta
      }
      typeFilter.value = null // 隐藏类型过滤器，因为已经按路由分类
    } else if (mediaTypeQuery && mediaTypeQuery !== 'all') {
      params.media_type = mediaTypeQuery
      typeFilter.value = mediaTypeQuery
    }
    
    // 根据媒体类型选择正确的API端点
    let endpoint = '/subscriptions'
    if (mediaTypeFromMeta === 'movie') {
      endpoint = '/subscriptions/movies'
    } else if (mediaTypeFromMeta === 'tv') {
      endpoint = '/subscriptions/tv'
    } else if (mediaTypeFromMeta === 'music') {
      endpoint = '/subscriptions/music'
    } else if (mediaTypeFromMeta === 'book') {
      endpoint = '/subscriptions/books'
    }
    
    const response = await api.get(endpoint, { params })
    console.log('订阅列表响应:', response)
    // 统一响应格式：response.data 已经是 data 字段的内容
    // 如果是分页响应，data 包含 {items, total, page, page_size, total_pages}
    // 如果是列表响应，data 是数组或对象
    if (response && response.data) {
      // 检查是否是分页响应
      if (response.data.items && Array.isArray(response.data.items)) {
        subscriptions.value = response.data.items
        // 可以在这里保存分页信息
        console.log('订阅数量:', subscriptions.value.length, '总计:', response.data.total)
      } else if (Array.isArray(response.data)) {
        subscriptions.value = response.data
        console.log('订阅数量:', subscriptions.value.length)
      } else {
        subscriptions.value = []
        console.warn('订阅列表数据格式不正确')
      }
    } else {
      subscriptions.value = []
      console.warn('订阅列表数据为空')
    }
  } catch (error: any) {
    console.error('加载订阅列表失败:', error)
    console.error('错误详情:', error.message || error.response?.data || '未知错误')
    subscriptions.value = []
    // 显示错误提示（错误消息已经在API拦截器中提取）
    if (error.message) {
      alert('加载失败：' + error.message)
    } else {
      alert('API调用失败，请检查后端服务是否运行')
    }
  } finally {
    loading.value = false
  }
}

const editSubscription = (item: any) => {
  editingSubscription.value = { ...item }
  showCreateDialog.value = true
}

const deleteSubscription = async (item: any) => {
  try {
    await api.delete(`/subscriptions/${item.id || item}`)
    await loadSubscriptions()
  } catch (error: any) {
    console.error('删除订阅失败:', error)
    // 统一响应格式：错误消息已经在API拦截器中提取
    alert('删除失败：' + (error.message || error.error_message || '未知错误'))
  }
}

const handleSaved = async () => {
  showCreateDialog.value = false
  editingSubscription.value = null
  await loadSubscriptions()
}

// 执行订阅搜索
const handleSearchSubscription = async (subscriptionId: number) => {
  try {
    const response = await api.post(`/subscriptions/${subscriptionId}/search`)
    console.log('订阅搜索执行成功:', response)
    // 显示成功提示
    alert('搜索任务已提交')
  } catch (error: any) {
    console.error('执行订阅搜索失败:', error)
    alert('执行搜索失败：' + (error.response?.data?.detail || '未知错误'))
  }
}

// 手动检查订阅（VIDEO-AUTOLOOP-1）
const handleCheckSubscription = async (subscriptionId: number) => {
  try {
    const response = await api.post(`/subscriptions/${subscriptionId}/check`)
    console.log('订阅检查执行成功:', response)
    
    // 显示详细的成功提示
    const result = response.data?.data || {}
    const message = result.message || '检查完成'
    const downloadedCount = result.downloaded_count || 0
    const candidatesFound = result.candidates_found || 0
    
    let alertMessage = `✅ 订阅检查完成\n`
    alertMessage += `📋 ${message}\n`
    alertMessage += `🔍 找到候选: ${candidatesFound} 个\n`
    alertMessage += `⬇️ 创建下载: ${downloadedCount} 个`
    
    if (result.security_settings) {
      alertMessage += `\n🛡️ 安全策略: ${result.security_settings.allow_hr ? '允许HR' : '禁止HR'}, `
      alertMessage += `${result.security_settings.allow_h3h5 ? '允许H3/H5' : '禁止H3/H5'}, `
      alertMessage += `${result.security_settings.strict_free_only ? '只下Free' : '允许非Free'}`
    }
    
    alert(alertMessage)
  } catch (error: any) {
    console.error('执行订阅检查失败:', error)
    alert('❌ 检查失败：' + (error.response?.data?.detail || '未知错误'))
  }
}

// 切换订阅状态
const handleToggleSubscriptionStatus = async (subscriptionId: number, currentStatus: string) => {
  try {
    const newStatus = currentStatus === 'active' ? 'paused' : 'active'
    const endpoint = newStatus === 'active' 
      ? `/subscriptions/${subscriptionId}/enable`
      : `/subscriptions/${subscriptionId}/disable`
    
    const response = await api.post(endpoint)
    console.log('订阅状态更新成功:', response)
    // 刷新列表
    await loadSubscriptions()
  } catch (error: any) {
    console.error('更新订阅状态失败:', error)
    alert('更新状态失败：' + (error.response?.data?.detail || '未知错误'))
  }
}

onMounted(() => {
  console.log('订阅管理页面已加载')
  console.log('开始加载订阅列表...')
  loadSubscriptions()
})

// 监听路由变化，重新加载订阅
watch(
  () => route.meta.mediaType,
  () => {
    loadSubscriptions()
  }
)

watch(
  () => route.query.media_type,
  (val) => {
    if (!currentMediaType.value) {
      typeFilter.value = typeof val === 'string' ? val : null
      loadSubscriptions()
    }
  }
)

// 监听订阅列表变化
watch(subscriptions, (newVal) => {
  console.log('订阅列表已更新，数量:', newVal.length)
}, { immediate: true })
</script>

<style scoped lang="scss">
.subscriptions-page {
  width: 100%;
}

.subscription-empty-card {
  background: rgba(var(--v-theme-surface-variant), 0.4);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(var(--v-border-color), 0.12);
}

.filter-card {
  background: rgba(var(--v-theme-surface), 0.8);
  backdrop-filter: blur(10px);
}

.filter-input,
.filter-select {
  background: rgba(var(--v-theme-surface), 0.5);
}

.subscription-card {
  transition: all 0.3s ease;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.subscription-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
}

.subscription-paused {
  opacity: 0.7;
}

.subscription-card .v-card-title {
  font-size: 1.1rem;
  font-weight: 600;
}

.subscription-card .v-card-text {
  flex-grow: 1;
}
</style>
