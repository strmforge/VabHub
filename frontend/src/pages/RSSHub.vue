<template>
  <div class="rsshub-page">
    <PageHeader
      title="RSSHub订阅管理"
      subtitle="管理RSSHub榜单和更新源订阅"
    />
    
    <!-- 加载状态 -->
    <div v-if="loading" class="text-center py-12">
      <v-progress-circular indeterminate color="primary" size="64" />
      <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
    </div>
    
    <!-- 内容区域 -->
    <div v-else>
      <!-- ① 榜单源 -->
      <v-card variant="outlined" class="mb-6">
        <v-card-title class="d-flex align-center">
          <v-icon class="me-2" color="primary">mdi-trophy</v-icon>
          <span>榜单源</span>
          <v-spacer />
          <v-chip size="small" color="primary" variant="flat">
            {{ rankSources.length }} 个源
          </v-chip>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-row v-if="rankSources.length === 0">
            <v-col cols="12">
              <div class="text-center py-8 text-medium-emphasis">
                <v-icon size="48" color="grey-lighten-1" class="mb-2">mdi-trophy-outline</v-icon>
                <div>暂无榜单源</div>
              </div>
            </v-col>
          </v-row>
          <v-row v-else>
            <v-col
              v-for="source in rankSources"
              :key="source.id"
              cols="12"
              sm="6"
              md="4"
              lg="3"
            >
              <RSSHubSourceCard
                :source="source"
                :enabled="source.enabled"
                @toggle="handleToggleSource"
                @preview="handlePreviewSource"
              />
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
      
      <!-- ② 更新源 -->
      <v-card variant="outlined" class="mb-6">
        <v-card-title class="d-flex align-center">
          <v-icon class="me-2" color="success">mdi-update</v-icon>
          <span>更新源</span>
          <v-spacer />
          <v-chip size="small" color="success" variant="flat">
            {{ updateSources.length }} 个源
          </v-chip>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-row v-if="updateSources.length === 0">
            <v-col cols="12">
              <div class="text-center py-8 text-medium-emphasis">
                <v-icon size="48" color="grey-lighten-1" class="mb-2">mdi-update</v-icon>
                <div>暂无更新源</div>
              </div>
            </v-col>
          </v-row>
          <v-row v-else>
            <v-col
              v-for="source in updateSources"
              :key="source.id"
              cols="12"
              sm="6"
              md="4"
              lg="3"
            >
              <RSSHubSourceCard
                :source="source"
                :enabled="source.enabled"
                @toggle="handleToggleSource"
                @preview="handlePreviewSource"
              />
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
      
      <!-- ③ 组合订阅 -->
      <v-card variant="outlined">
        <v-card-title class="d-flex align-center">
          <v-icon class="me-2" color="info">mdi-view-dashboard</v-icon>
          <span>组合订阅</span>
          <v-spacer />
          <v-chip size="small" color="info" variant="flat">
            {{ composites.length }} 个组合
          </v-chip>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-row v-if="composites.length === 0">
            <v-col cols="12">
              <div class="text-center py-8 text-medium-emphasis">
                <v-icon size="48" color="grey-lighten-1" class="mb-2">mdi-view-dashboard-outline</v-icon>
                <div>暂无组合订阅</div>
              </div>
            </v-col>
          </v-row>
          <v-row v-else>
            <v-col
              v-for="composite in composites"
              :key="composite.id"
              cols="12"
              sm="6"
              md="4"
              lg="3"
            >
              <RSSHubCompositeCard
                :composite="composite"
                :enabled="composite.enabled"
                @toggle="handleToggleComposite"
              />
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- ④ 健康检查 -->
      <v-card variant="outlined" class="mt-6">
        <v-card-title class="d-flex align-center">
          <v-icon class="me-2" color="warning">mdi-heart-pulse</v-icon>
          <span>订阅健康检查</span>
          <v-spacer />
          <v-chip size="small" color="warning" variant="flat">
            {{ healthItems.length }} 条记录
          </v-chip>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-row class="mb-4" align="center" dense>
            <v-col cols="12" md="3">
              <v-text-field
                v-model="healthFilters.userId"
                label="用户ID"
                type="number"
                density="compact"
                variant="outlined"
                hide-details
              />
            </v-col>
            <v-col cols="12" md="3">
              <v-select
                v-model="healthFilters.targetType"
                :items="healthTargetTypeOptions"
                label="目标类型"
                density="compact"
                variant="outlined"
                hide-details
              />
            </v-col>
            <v-col cols="12" md="2">
              <v-text-field
                v-model.number="healthFilters.limit"
                label="数量上限"
                type="number"
                min="1"
                max="500"
                density="compact"
                variant="outlined"
                hide-details
              />
            </v-col>
            <v-col cols="12" md="2">
              <v-switch
                v-model="healthFilters.onlyLegacy"
                label="仅 legacy"
                inset
                density="compact"
                hide-details
              />
            </v-col>
            <v-col cols="12" md="2" class="text-end">
              <v-btn
                color="primary"
                prepend-icon="mdi-refresh"
                :loading="healthLoading"
                @click="loadHealth"
              >
                刷新
              </v-btn>
            </v-col>
          </v-row>

          <div v-if="healthLoading" class="text-center py-8">
            <v-progress-circular indeterminate color="primary" />
            <div class="mt-2 text-body-2 text-medium-emphasis">加载健康信息...</div>
          </div>

          <div v-else-if="healthItems.length === 0" class="text-center py-8 text-medium-emphasis">
            <v-icon size="48" color="grey-lighten-1" class="mb-2">mdi-heart-off</v-icon>
            <div>暂无需要关注的订阅</div>
          </div>

          <v-table v-else class="health-table">
            <thead>
              <tr>
                <th class="text-left">用户</th>
                <th class="text-left">类型</th>
                <th class="text-left">目标</th>
                <th class="text-left">健康状态</th>
                <th class="text-left">最后错误</th>
                <th class="text-left">更新时间</th>
                <th class="text-left">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in healthItems" :key="`${item.user_id}-${item.target_id}`">
                <td>
                  <div class="text-body-2">{{ item.user_id }}</div>
                  <div class="text-caption text-medium-emphasis">{{ item.username || 'unknown' }}</div>
                </td>
                <td>
                  <v-chip
                    size="small"
                    :color="item.target_type === 'source' ? 'primary' : 'info'"
                    class="text-white"
                  >
                    {{ item.target_type === 'source' ? '榜单源' : '组合' }}
                  </v-chip>
                </td>
                <td>
                  <div class="text-body-2">{{ item.target_name || item.target_id }}</div>
                  <div class="text-caption text-medium-emphasis">{{ item.target_id }}</div>
                </td>
                <td>
                  <v-chip
                    size="small"
                    :color="item.is_legacy_placeholder ? 'warning' : (item.last_error_code ? 'error' : 'success')"
                    variant="flat"
                  >
                    <template v-if="item.is_legacy_placeholder">Legacy 占位</template>
                    <template v-else-if="item.last_error_code">异常</template>
                    <template v-else>正常</template>
                  </v-chip>
                </td>
                <td>
                  <div class="text-body-2">{{ item.last_error_code || '-' }}</div>
                  <div class="text-caption text-medium-emphasis truncate-text">
                    {{ item.last_error_message || '-' }}
                  </div>
                </td>
                <td>
                  <div class="text-body-2">{{ item.updated_at || '-' }}</div>
                  <div class="text-caption text-medium-emphasis">
                    {{ item.last_checked_at || '-' }}
                  </div>
                </td>
                <td>
                  <v-btn
                    variant="text"
                    size="small"
                    color="primary"
                    @click="handleReenableFromHealth(item)"
                  >
                    重新启用
                  </v-btn>
                  <v-btn
                    variant="text"
                    size="small"
                    color="secondary"
                    @click="handleNavigateToSubscription(item)"
                  >
                    订阅详情
                  </v-btn>
                </td>
              </tr>
            </tbody>
          </v-table>
        </v-card-text>
      </v-card>
    </div>
    
    <!-- 预览对话框 -->
    <v-dialog v-model="showPreviewDialog" max-width="800">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="me-2">mdi-eye</v-icon>
          <span>预览: {{ previewSourceName }}</span>
          <v-spacer />
          <v-btn icon variant="text" @click="showPreviewDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <div v-if="previewLoading" class="text-center py-8">
            <v-progress-circular indeterminate color="primary" />
            <div class="mt-4 text-body-2 text-medium-emphasis">加载预览内容...</div>
          </div>
          <div v-else-if="previewItems.length === 0" class="text-center py-8 text-medium-emphasis">
            <v-icon size="48" color="grey-lighten-1" class="mb-2">mdi-information-outline</v-icon>
            <div>暂无预览内容</div>
          </div>
          <v-list v-else>
            <v-list-item
              v-for="(item, index) in previewItems"
              :key="index"
              :title="item.title"
              :subtitle="item.description"
            >
              <template #prepend>
                <v-avatar color="primary" size="32" class="me-3">
                  {{ index + 1 }}
                </v-avatar>
              </template>
              <template #append>
                <div class="text-caption text-medium-emphasis">
                  {{ item.pub_date || '未知时间' }}
                </div>
              </template>
            </v-list-item>
          </v-list>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showPreviewDialog = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { useToast } from '@/composables/useToast'
import PageHeader from '@/components/common/PageHeader.vue'
import RSSHubSourceCard from '@/components/rsshub/RSSHubSourceCard.vue'
import RSSHubCompositeCard from '@/components/rsshub/RSSHubCompositeCard.vue'

const { showSuccess, showError } = useToast()
const router = useRouter()
const loading = ref(false)
const sources = ref<any[]>([])
const composites = ref<any[]>([])

// 预览相关
const showPreviewDialog = ref(false)
const previewLoading = ref(false)
const previewItems = ref<any[]>([])
const previewSourceName = ref('')

// 健康检查
const healthLoading = ref(false)
const healthItems = ref<any[]>([])
const healthFilters = reactive({
  userId: '',
  targetType: 'all',
  onlyLegacy: true,
  limit: 50
})
const healthTargetTypeOptions = [
  { title: '全部', value: 'all' },
  { title: '榜单源', value: 'source' },
  { title: '组合订阅', value: 'composite' }
]

// 计算属性：按group分组源
const rankSources = computed(() => {
  return sources.value.filter(s => s.group === 'rank')
})

const updateSources = computed(() => {
  return sources.value.filter(s => s.group === 'update')
})

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    // 并行加载源和组合订阅
    const [sourcesResponse, compositesResponse] = await Promise.all([
      api.get('/rsshub/sources'),
      api.get('/rsshub/composites')
    ])
    
    sources.value = sourcesResponse.data || []
    composites.value = compositesResponse.data || []
  } catch (error: any) {
    console.error('加载RSSHub数据失败:', error)
    showError('加载失败：' + (error.message || '未知错误'))
    sources.value = []
    composites.value = []
  } finally {
    loading.value = false
  }
}

const loadHealth = async () => {
  healthLoading.value = true
  try {
    const params: Record<string, any> = {
      limit: healthFilters.limit || 50
    }
    if (healthFilters.userId) {
      const parsed = Number(healthFilters.userId)
      if (!Number.isNaN(parsed)) {
        params.user_id = parsed
      }
    }
    if (healthFilters.targetType !== 'all') {
      params.target_type = healthFilters.targetType
    }
    if (healthFilters.onlyLegacy) {
      params.only_legacy = true
    }

    const response = await api.get('/rsshub/subscriptions/health', { params })
    if (response.data?.items) {
      healthItems.value = response.data.items
    } else if (Array.isArray(response.data)) {
      healthItems.value = response.data
    } else {
      healthItems.value = []
    }
  } catch (error: any) {
    console.error('加载健康列表失败:', error)
    showError('加载健康列表失败：' + (error.message || '未知错误'))
    healthItems.value = []
  } finally {
    healthLoading.value = false
  }
}

// 切换源订阅状态
const handleToggleSource = async (sourceId: string, enabled: boolean) => {
  try {
    await api.post(`/rsshub/subscriptions/source/${sourceId}/toggle`, {
      enabled
    })
    
    // 更新本地状态
    const source = sources.value.find(s => s.id === sourceId)
    if (source) {
      source.enabled = enabled
    }
    
    showSuccess(enabled ? '已启用订阅' : '已禁用订阅')
  } catch (error: any) {
    console.error('切换订阅状态失败:', error)
    showError('操作失败：' + (error.message || '未知错误'))
  }
}

// 切换组合订阅状态
const handleToggleComposite = async (compositeId: string, enabled: boolean) => {
  try {
    await api.post(`/rsshub/subscriptions/composite/${compositeId}/toggle`, {
      enabled
    })
    
    // 更新本地状态
    const composite = composites.value.find(c => c.id === compositeId)
    if (composite) {
      composite.enabled = enabled
    }
    
    showSuccess(enabled ? '已启用组合订阅' : '已禁用组合订阅')
  } catch (error: any) {
    console.error('切换组合订阅状态失败:', error)
    showError('操作失败：' + (error.message || '未知错误'))
  }
}

// 预览源内容
const handlePreviewSource = async (sourceId: string, sourceName: string) => {
  previewSourceName.value = sourceName
  showPreviewDialog.value = true
  previewLoading.value = true
  previewItems.value = []
  
  try {
    const response = await api.get(`/rsshub/sources/${sourceId}/preview`, {
      params: { limit: 10 }
    })
    
    previewItems.value = response.data || []
  } catch (error: any) {
    console.error('预览源内容失败:', error)
    showError('预览失败：' + (error.message || '未知错误'))
    previewItems.value = []
  } finally {
    previewLoading.value = false
  }
}

const handleReenableFromHealth = async (item: any) => {
  try {
    await api.post(`/rsshub/subscriptions/${item.target_type}/${item.target_id}/toggle`, {
      enabled: true
    })
    showSuccess('已尝试重新启用订阅')
    await loadHealth()
  } catch (error: any) {
    console.error('重新启用订阅失败:', error)
    showError('重新启用失败：' + (error.message || '未知错误'))
  }
}

const handleNavigateToSubscription = (item: any) => {
  router.push({
    name: 'Subscriptions',
    query: {
      focusTarget: item.target_id,
      userId: item.user_id
    }
  })
}

onMounted(() => {
  loadData()
  loadHealth()
})
</script>

<style scoped lang="scss">
.rsshub-page {
  padding: 24px;
}

.health-table .truncate-text {
  max-width: 220px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>

