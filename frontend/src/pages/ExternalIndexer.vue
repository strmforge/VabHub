<template>
  <div class="external-indexer-page">
    <PageHeader
      title="外部索引管理"
      subtitle="外部 PT 索引引擎配置与状态监控"
    >
      <template #actions>
        <v-btn
          color="primary"
          prepend-icon="mdi-refresh"
          @click="refreshAll"
          :loading="refreshing"
        >
          刷新状态
        </v-btn>
      </template>
    </PageHeader>

    <!-- 开发者模式提示 -->
    <v-alert
      v-if="isDevMode()"
      type="info"
      variant="tonal"
      density="compact"
      class="mb-4"
    >
      <template #prepend>
        <v-icon>mdi-information</v-icon>
      </template>
      <div class="text-caption">
        开发者模式页面 · 普通用户部署时请不要开启 VITE_DEV_MODE。
      </div>
    </v-alert>

    <!-- 配置概览卡片 -->
    <v-card variant="outlined" class="mb-4">
      <v-card-title class="d-flex align-center justify-space-between">
        <span>配置概览</span>
        <v-chip
          :color="settings.enabled ? 'success' : 'error'"
          size="small"
          variant="flat"
        >
          {{ settings.enabled ? '已启用' : '未启用' }}
        </v-chip>
      </v-card-title>
      <v-card-text>
        <div v-if="settingsLoading" class="text-center py-8">
          <v-progress-circular indeterminate color="primary" size="48" />
          <div class="mt-4 text-body-2 text-medium-emphasis">加载配置中...</div>
        </div>
        <v-simple-table v-else>
          <tbody>
            <tr>
              <td class="text-medium-emphasis" style="width: 150px">启用状态</td>
              <td>
                <v-chip
                  :color="settings.enabled ? 'success' : 'error'"
                  size="small"
                  variant="flat"
                >
                  {{ settings.enabled ? '已启用' : '未启用' }}
                </v-chip>
              </td>
            </tr>
            <tr>
              <td class="text-medium-emphasis">模块路径</td>
              <td>
                <code class="text-body-2">{{ settings.module || '(未配置)' }}</code>
              </td>
            </tr>
            <tr>
              <td class="text-medium-emphasis">引擎地址</td>
              <td>
                <code class="text-body-2">{{ settings.engine_base_url || '(未配置)' }}</code>
              </td>
            </tr>
            <tr>
              <td class="text-medium-emphasis">超时时间</td>
              <td>{{ settings.timeout_seconds }} 秒</td>
            </tr>
            <tr>
              <td class="text-medium-emphasis">最小结果阈值</td>
              <td>{{ settings.min_results }} 条</td>
            </tr>
          </tbody>
        </v-simple-table>
        <v-alert
          v-if="!settings.enabled"
          type="warning"
          variant="tonal"
          class="mt-4"
        >
          <strong>当前外部索引处于关闭状态</strong>
          <div class="text-body-2 mt-1">
            如需启用，请设置环境变量 <code>EXTERNAL_INDEXER_ENABLED=true</code> 并配置
            <code>EXTERNAL_INDEXER_MODULE</code>。
          </div>
        </v-alert>
      </v-card-text>
    </v-card>

    <!-- 运行状态卡片 -->
    <v-card variant="outlined" class="mb-4">
      <v-card-title class="d-flex align-center justify-space-between">
        <span>运行状态</span>
        <v-btn
          icon="mdi-refresh"
          variant="text"
          size="small"
          @click="loadStatus"
          :loading="statusLoading"
        />
      </v-card-title>
      <v-card-text>
        <div v-if="statusLoading" class="text-center py-8">
          <v-progress-circular indeterminate color="primary" size="48" />
          <div class="mt-4 text-body-2 text-medium-emphasis">加载状态中...</div>
        </div>
        <div v-else>
          <v-simple-table>
            <tbody>
              <tr>
                <td class="text-medium-emphasis" style="width: 150px">运行时加载</td>
                <td>
                  <v-chip
                    :color="status.runtime_loaded ? 'success' : 'error'"
                    size="small"
                    variant="flat"
                  >
                    {{ status.runtime_loaded ? '成功' : '失败' }}
                  </v-chip>
                </td>
              </tr>
              <tr>
                <td class="text-medium-emphasis">引擎模块</td>
                <td>
                  <v-chip
                    :color="status.has_engine ? 'success' : 'error'"
                    size="small"
                    variant="flat"
                  >
                    {{ status.has_engine ? '已加载' : '未加载' }}
                  </v-chip>
                </td>
              </tr>
              <tr>
                <td class="text-medium-emphasis">最近错误</td>
                <td>
                  <span v-if="status.last_error" class="text-error">
                    {{ status.last_error }}
                  </span>
                  <span v-else class="text-success">最近无错误</span>
                </td>
              </tr>
              <tr>
                <td class="text-medium-emphasis">说明</td>
                <td class="text-body-2">{{ status.notes }}</td>
              </tr>
            </tbody>
          </v-simple-table>
        </div>
      </v-card-text>
    </v-card>

    <!-- 站点列表卡片 -->
    <v-card variant="outlined" class="mb-4">
      <v-card-title class="d-flex align-center justify-space-between">
        <span>支持的站点</span>
        <v-chip size="small" variant="flat" color="primary">
          {{ sites.length }} 个站点
        </v-chip>
      </v-card-title>
      <v-card-text>
        <div v-if="sitesLoading" class="text-center py-8">
          <v-progress-circular indeterminate color="primary" size="48" />
          <div class="mt-4 text-body-2 text-medium-emphasis">加载站点中...</div>
        </div>
        <div v-else-if="sites.length === 0" class="text-center py-8 text-medium-emphasis">
          暂无已配置的站点
        </div>
        <v-chip-group v-else>
          <v-chip
            v-for="site in sites"
            :key="site"
            size="small"
            variant="outlined"
          >
            {{ site }}
          </v-chip>
        </v-chip-group>
      </v-card-text>
    </v-card>

    <!-- 调试测试区域 -->
    <v-card variant="outlined">
      <v-card-title>调试测试</v-card-title>
      <v-card-text>
        <v-form @submit.prevent="testSearch">
          <v-row>
            <v-col cols="12" md="3">
              <v-text-field
                v-model="testForm.siteId"
                label="站点 ID"
                variant="outlined"
                density="compact"
                placeholder="例如: test-site"
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="testForm.keyword"
                label="搜索关键词"
                variant="outlined"
                density="compact"
                placeholder="例如: test"
              />
            </v-col>
            <v-col cols="12" md="2">
              <v-text-field
                v-model.number="testForm.page"
                label="页码"
                variant="outlined"
                density="compact"
                type="number"
                min="1"
              />
            </v-col>
            <v-col cols="12" md="1">
              <v-btn
                type="submit"
                color="primary"
                block
                :loading="testLoading"
                :disabled="!testForm.siteId || !testForm.keyword"
              >
                测试
              </v-btn>
            </v-col>
          </v-row>
        </v-form>

        <!-- 测试结果 -->
        <div v-if="testResults.length > 0" class="mt-4">
          <v-divider class="mb-4" />
          <div class="text-subtitle-2 mb-2">测试结果 ({{ testResults.length }} 条)</div>
          <v-data-table
            :headers="testResultHeaders"
            :items="testResults"
            :items-per-page="10"
            class="elevation-0"
            density="compact"
          >
            <template v-slot:item.title_raw="{ item }">
              <div class="text-body-2" style="max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                {{ item.title_raw }}
              </div>
            </template>
            <template v-slot:item.size_bytes="{ item }">
              {{ formatSize(item.size_bytes) }}
            </template>
            <template v-slot:item.published_at="{ item }">
              {{ formatDateTime(item.published_at) }}
            </template>
            <template v-slot:item.source="{ item }">
              <ResultSourceChip :source="item.source" size="x-small" />
            </template>
          </v-data-table>
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'vue-toastification'
import PageHeader from '@/components/common/PageHeader.vue'
import ResultSourceChip from '@/components/common/ResultSourceChip.vue'
import api from '@/services/api'
import { isDevMode } from '@/utils/devMode'

const toast = useToast()

// 配置数据
const settings = ref({
  enabled: false,
  module: '',
  engine_base_url: null as string | null,
  timeout_seconds: 15,
  min_results: 20,
})
const settingsLoading = ref(false)

// 状态数据
const status = ref({
  enabled: false,
  runtime_loaded: false,
  has_engine: false,
  last_error: null as string | null,
  notes: '',
})
const statusLoading = ref(false)

// 站点列表
const sites = ref<string[]>([])
const sitesLoading = ref(false)

// 刷新状态
const refreshing = ref(false)

// 测试表单
const testForm = ref({
  siteId: '',
  keyword: '',
  page: 1,
})
const testResults = ref<any[]>([])
const testLoading = ref(false)

// 测试结果表格列
const testResultHeaders = [
  { title: '标题', key: 'title_raw', sortable: false },
  { title: '站点', key: 'site_id', sortable: false },
  { title: '种子ID', key: 'torrent_id', sortable: false },
  { title: '大小', key: 'size_bytes', sortable: false },
  { title: '做种', key: 'seeders', sortable: false },
  { title: '下载', key: 'leechers', sortable: false },
  { title: '发布时间', key: 'published_at', sortable: false },
  { title: '来源', key: 'source', sortable: false },
]

// 加载配置
const loadSettings = async () => {
  settingsLoading.value = true
  try {
    const response = await api.get('/api/ext-indexer/settings')
    settings.value = response.data
  } catch (error: any) {
    console.error('加载配置失败:', error)
    toast.error('加载配置失败: ' + (error.response?.data?.error || error.message))
  } finally {
    settingsLoading.value = false
  }
}

// 加载状态
const loadStatus = async () => {
  statusLoading.value = true
  try {
    const response = await api.get('/api/ext-indexer/status')
    status.value = response.data
  } catch (error: any) {
    console.error('加载状态失败:', error)
    toast.error('加载状态失败: ' + (error.response?.data?.error || error.message))
  } finally {
    statusLoading.value = false
  }
}

// 加载站点列表
const loadSites = async () => {
  sitesLoading.value = true
  try {
    const response = await api.get('/api/ext-indexer/sites')
    sites.value = response.data.sites || []
  } catch (error: any) {
    console.error('加载站点列表失败:', error)
    toast.error('加载站点列表失败: ' + (error.response?.data?.error || error.message))
  } finally {
    sitesLoading.value = false
  }
}

// 刷新全部
const refreshAll = async () => {
  refreshing.value = true
  try {
    await Promise.all([loadSettings(), loadStatus(), loadSites()])
    toast.success('刷新成功')
  } catch (error) {
    console.error('刷新失败:', error)
  } finally {
    refreshing.value = false
  }
}

// 测试搜索
const testSearch = async () => {
  if (!testForm.value.siteId || !testForm.value.keyword) {
    toast.warning('请填写站点ID和搜索关键词')
    return
  }

  testLoading.value = true
  testResults.value = []
  try {
    const params = new URLSearchParams({
      site: testForm.value.siteId,
      q: testForm.value.keyword,
      page: testForm.value.page.toString(),
    })
    const response = await api.get(`/api/debug/ext-indexer/search?${params}`)
    testResults.value = response.data || []
    if (testResults.value.length === 0) {
      toast.info('未找到结果')
    } else {
      toast.success(`找到 ${testResults.value.length} 条结果`)
    }
  } catch (error: any) {
    console.error('测试搜索失败:', error)
    toast.error('测试搜索失败: ' + (error.response?.data?.error || error.message))
  } finally {
    testLoading.value = false
  }
}

// 格式化大小
const formatSize = (bytes: number | null | undefined): string => {
  if (!bytes) return '-'
  const gb = bytes / (1024 ** 3)
  if (gb >= 1) return `${gb.toFixed(2)} GB`
  const mb = bytes / (1024 ** 2)
  if (mb >= 1) return `${mb.toFixed(2)} MB`
  const kb = bytes / 1024
  return `${kb.toFixed(2)} KB`
}

// 格式化日期时间
const formatDateTime = (date: string | null | undefined): string => {
  if (!date) return '-'
  try {
    return new Date(date).toLocaleString('zh-CN')
  } catch {
    return date
  }
}

// 初始化
onMounted(() => {
  refreshAll()
})
</script>

<style scoped>
.external-indexer-page {
  padding: 24px;
}

code {
  background-color: rgba(var(--v-theme-surface-variant), 0.3);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.875rem;
}
</style>

