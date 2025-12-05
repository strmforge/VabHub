<template>
  <div class="rss-subscriptions-page">
    <!-- 页面标题 -->
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold">RSS订阅管理</h1>
        <p class="text-body-1 text-medium-emphasis mt-2">管理您的RSS订阅源</p>
      </div>
      <v-btn
        color="primary"
        prepend-icon="mdi-plus"
        size="large"
        @click="handleCreate"
      >
        创建RSS订阅
      </v-btn>
    </div>
    
    <!-- 过滤和搜索 -->
    <v-card variant="outlined" class="mb-4 filter-card">
      <v-card-text class="py-3">
        <v-row align="center" dense>
          <v-col cols="12" md="5">
            <v-text-field
              v-model="searchQuery"
              placeholder="搜索RSS订阅..."
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
              clearable
              class="filter-select"
            />
          </v-col>
          <v-col cols="12" md="4">
            <v-btn
              color="primary"
              variant="flat"
              prepend-icon="mdi-refresh"
              @click="loadSubscriptions"
              :loading="loading"
            >
              刷新
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  
    <!-- RSS订阅列表 -->
    <template v-if="loading && subscriptions.length === 0">
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
      <v-card variant="outlined" class="rss-subscription-empty-card">
        <v-card-text class="text-center pa-12">
          <v-icon size="80" color="grey-darken-1" class="mb-4">mdi-rss-off</v-icon>
          <div class="text-h5 font-weight-medium mb-2">暂无RSS订阅</div>
          <div class="text-body-2 text-medium-emphasis mb-4">
            使用顶部的"创建RSS订阅"按钮添加您的第一个RSS订阅源
          </div>
          <v-btn
            color="primary"
            prepend-icon="mdi-plus"
            @click="handleCreate"
          >
            创建RSS订阅
          </v-btn>
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
          <RSSSubscriptionCard
            :subscription="subscription"
            @view="handleViewDetail"
            @edit="handleEdit"
            @delete="handleDelete"
            @check="handleCheck"
          />
        </v-col>
      </v-row>

      <!-- 分页 -->
      <v-pagination
        v-if="totalPages > 1"
        v-model="currentPage"
        :length="totalPages"
        :total-visible="7"
        class="mt-4"
        @update:model-value="loadSubscriptions"
      />
    </template>

    <!-- 创建/编辑对话框 -->
    <RSSSubscriptionDialog
      v-model="showDialog"
      :subscription="editingSubscription"
      @saved="handleSaved"
    />

    <!-- 详情对话框 -->
    <RSSSubscriptionDetailDialog
      v-model="showDetailDialog"
      :subscription="viewingSubscription"
      @edit="handleEdit"
      @checked="handleChecked"
    />

    <!-- 删除确认对话框 -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title class="text-h6">确认删除</v-card-title>
        <v-card-text>
          确定要删除RSS订阅 "{{ deletingSubscription?.name }}" 吗？
          <br />
          <span class="text-error text-caption">此操作不可撤销</span>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showDeleteDialog = false">
            取消
          </v-btn>
          <v-btn
            color="error"
            variant="flat"
            :loading="deleting"
            @click="confirmDelete"
          >
            删除
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { rssApi } from '@/services/api'
import { useToast } from '@/composables/useToast'
import RSSSubscriptionCard from '@/components/rss/RSSSubscriptionCard.vue'
import RSSSubscriptionDialog from '@/components/rss/RSSSubscriptionDialog.vue'
import RSSSubscriptionDetailDialog from '@/components/rss/RSSSubscriptionDetailDialog.vue'

interface RSSSubscription {
  id: number
  name: string
  url: string
  site_id?: number
  enabled: boolean
  interval: number
  last_check?: string
  next_check?: string
  last_item_hash?: string
  filter_rules?: any
  download_rules?: any
  total_items: number
  downloaded_items: number
  skipped_items: number
  error_count: number
  description?: string
  created_at: string
  updated_at: string
}

const { showSuccess, showError, showInfo } = useToast()

const loading = ref(false)
const subscriptions = ref<RSSSubscription[]>([])
const searchQuery = ref('')
const statusFilter = ref<string | null>(null)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const showDialog = ref(false)
const editingSubscription = ref<RSSSubscription | null>(null)

const showDetailDialog = ref(false)
const viewingSubscription = ref<RSSSubscription | null>(null)

const showDeleteDialog = ref(false)
const deletingSubscription = ref<RSSSubscription | null>(null)
const deleting = ref(false)

const statusOptions = [
  { title: '全部', value: null },
  { title: '启用', value: 'enabled' },
  { title: '禁用', value: 'disabled' }
]

const filteredSubscriptions = computed(() => {
  let result = subscriptions.value

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(sub => 
      sub.name.toLowerCase().includes(query) ||
      sub.url.toLowerCase().includes(query) ||
      (sub.description && sub.description.toLowerCase().includes(query))
    )
  }

  // 状态过滤
  if (statusFilter.value === 'enabled') {
    result = result.filter(sub => sub.enabled)
  } else if (statusFilter.value === 'disabled') {
    result = result.filter(sub => !sub.enabled)
  }

  return result
})

const totalPages = computed(() => {
  return Math.ceil(total.value / pageSize.value)
})

const loadSubscriptions = async () => {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (statusFilter.value === 'enabled') {
      params.enabled = true
    } else if (statusFilter.value === 'disabled') {
      params.enabled = false
    }

    const response = await rssApi.getRSSSubscriptions(params)
    
    if (response.data.items) {
      subscriptions.value = response.data.items
      total.value = response.data.total || 0
    } else {
      subscriptions.value = Array.isArray(response.data) ? response.data : []
      total.value = subscriptions.value.length
    }
  } catch (error: any) {
    showError(error.message || '加载RSS订阅列表失败')
    console.error('加载RSS订阅列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  editingSubscription.value = null
  showDialog.value = true
}

const handleViewDetail = (subscription: RSSSubscription) => {
  viewingSubscription.value = subscription
  showDetailDialog.value = true
}

const handleEdit = (subscription: RSSSubscription) => {
  editingSubscription.value = subscription
  showDialog.value = true
  showDetailDialog.value = false
}

const handleDelete = (subscription: RSSSubscription) => {
  deletingSubscription.value = subscription
  showDeleteDialog.value = true
}

const confirmDelete = async () => {
  if (!deletingSubscription.value) return

  deleting.value = true
  try {
    await rssApi.deleteRSSSubscription(deletingSubscription.value.id)
    showSuccess('删除成功')
    showDeleteDialog.value = false
    deletingSubscription.value = null
    await loadSubscriptions()
  } catch (error: any) {
    showError(error.message || '删除失败')
    console.error('删除RSS订阅失败:', error)
  } finally {
    deleting.value = false
  }
}

const handleCheck = async (subscription: RSSSubscription) => {
  try {
    showInfo('正在检查更新...')
    const response = await rssApi.checkRSSUpdates(subscription.id)
    const data = response.data
    
    showSuccess(
      `检查完成：新项 ${data.new_items || 0}，处理 ${data.processed_items || 0}，下载 ${data.downloaded_items || 0}`
    )
    await loadSubscriptions()
  } catch (error: any) {
    showError(error.message || '检查更新失败')
    console.error('检查RSS更新失败:', error)
  }
}

// 接收 Dialog 组件返回的订阅对象（类型可能与本地定义有差异）
const handleSaved = async (subscription: Partial<RSSSubscription> & { name: string; url: string }) => {
  try {
    if (editingSubscription.value?.id) {
      // 更新
      await rssApi.updateRSSSubscription(editingSubscription.value.id, subscription)
      showSuccess('更新成功')
      // 如果正在查看详情，更新查看的订阅
      if (viewingSubscription.value?.id === editingSubscription.value.id) {
        viewingSubscription.value = await rssApi.getRSSSubscription(editingSubscription.value.id).then(r => r.data)
      }
    } else {
      // 创建
      await rssApi.createRSSSubscription(subscription)
      showSuccess('创建成功')
    }
    await loadSubscriptions()
  } catch (error: any) {
    showError(error.message || '保存失败')
    console.error('保存RSS订阅失败:', error)
  }
}

const handleChecked = async () => {
  await loadSubscriptions()
  // 刷新详情中的订阅信息
  if (viewingSubscription.value?.id) {
    try {
      const response = await rssApi.getRSSSubscription(viewingSubscription.value.id)
      viewingSubscription.value = response.data
    } catch (error) {
      console.error('刷新订阅详情失败:', error)
    }
  }
}

onMounted(() => {
  loadSubscriptions()
})
</script>

<style scoped>
.rss-subscriptions-page {
  padding: 24px;
}

.filter-card {
  background: rgba(var(--v-theme-surface), 0.5);
}

.rss-subscription-empty-card {
  min-height: 400px;
}
</style>

