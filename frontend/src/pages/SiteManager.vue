<!--
站点管理页面 (SITE-MANAGER-1)
站点墙页面：列表展示、搜索过滤、批量操作
-->

<template>
  <div class="site-manager">
    <!-- 页面头部 -->
    <PageHeader
      title="站点管理"
      subtitle="管理和监控所有站点配置"
      :breadcrumbs="breadcrumbs"
    >
      <template #actions>
        <v-btn
          prepend-icon="mdi-refresh"
          :loading="siteManagerStore.loading"
          @click="refreshData"
        >
          刷新
        </v-btn>
        
        <v-btn
          prepend-icon="mdi-plus"
          color="primary"
          @click="showAddDialog = true"
        >
          添加站点
        </v-btn>
        
        <v-menu>
          <template #activator="{ props }">
            <v-btn
              v-bind="props"
              prepend-icon="mdi-dots-vertical"
              variant="outlined"
            >
              更多操作
            </v-btn>
          </template>
          
          <v-list>
            <v-list-item
              prepend-icon="mdi-download"
              title="导入站点"
              @click="showImportDialog = true"
            />
            <v-list-item
              prepend-icon="mdi-upload"
              title="导出站点"
              @click="showExportDialog = true"
            />
            <v-list-item
              prepend-icon="mdi-heart-pulse"
              title="批量健康检查"
              @click="showBatchHealthDialog = true"
            />
            <v-divider />
            <v-list-item
              prepend-icon="mdi-cog"
              title="显示设置"
              @click="showSettingsDialog = true"
            />
          </v-list>
        </v-menu>
      </template>
    </PageHeader>

    <!-- 统计卡片 -->
    <v-row class="mb-6">
      <v-col cols="12" sm="6" md="3">
        <StatCard
          title="总站点数"
          :value="siteManagerStore.stats.total_sites"
          icon="mdi-server"
          color="primary"
        />
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <StatCard
          title="启用站点"
          :value="siteManagerStore.stats.enabled_sites"
          icon="mdi-check-circle"
          color="success"
        />
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <StatCard
          title="健康站点"
          :value="siteManagerStore.healthySites.length"
          icon="mdi-heart-pulse"
          color="success"
        />
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <StatCard
          title="异常站点"
          :value="siteManagerStore.unhealthySites.length"
          icon="mdi-alert-circle"
          color="error"
        />
      </v-col>
    </v-row>

    <!-- 过滤工具栏 -->
    <FilterToolbar
      v-model:filter="siteManagerStore.filter"
      :categories="siteManagerStore.categories"
      :loading="siteManagerStore.loading"
      @reset="resetFilter"
      @search="applyFilter"
    >
      <!-- 自定义过滤器 -->
      <template #filters>
        <v-col cols="12" sm="6" md="3">
          <v-select
            v-model="siteManagerStore.filter.enabled"
            :items="[
              { title: '全部', value: null },
              { title: '启用', value: true },
              { title: '禁用', value: false }
            ]"
            label="启用状态"
            clearable
            hide-details
          />
        </v-col>
        
        <v-col cols="12" sm="6" md="3">
          <v-select
            v-model="siteManagerStore.filter.category"
            :items="[
              { title: '全部分类', value: null },
              ...siteManagerStore.categories.map((cat: any) => ({
                title: cat.name,
                value: cat.key
              }))
            ]"
            label="站点分类"
            clearable
            hide-details
          />
        </v-col>
        
        <v-col cols="12" sm="6" md="3">
          <v-select
            v-model="siteManagerStore.filter.health_status"
            :items="[
              { title: '全部状态', value: null },
              { title: '正常', value: 'OK' },
              { title: '警告', value: 'WARN' },
              { title: '错误', value: 'ERROR' }
            ]"
            label="健康状态"
            clearable
            hide-details
          />
        </v-col>
        
        <v-col cols="12" sm="6" md="3">
          <v-text-field
            v-model="siteManagerStore.filter.keyword"
            label="搜索关键词"
            placeholder="站点名称、域名或标识"
            clearable
            hide-details
            prepend-inner-icon="mdi-magnify"
          />
        </v-col>
      </template>
    </FilterToolbar>

    <!-- 视图切换和排序 -->
    <div class="d-flex align-center justify-space-between mb-4">
      <div class="d-flex align-center">
        <v-btn-toggle
          v-model="viewConfig.layout"
          variant="outlined"
          density="compact"
        >
          <v-btn value="grid" icon="mdi-grid">
            <v-tooltip activator="parent">网格视图</v-tooltip>
          </v-btn>
          <v-btn value="list" icon="mdi-view-list">
            <v-tooltip activator="parent">列表视图</v-tooltip>
          </v-btn>
        </v-btn-toggle>

        <v-select
          v-model="viewConfig.sortBy"
          :items="[
            { title: '优先级', value: 'priority' },
            { title: '名称', value: 'name' },
            { title: '创建时间', value: 'created_at' },
            { title: '健康状态', value: 'health_status' }
          ]"
          label="排序方式"
          density="compact"
          hide-details
          class="ml-4"
          style="max-width: 150px"
        />

        <v-btn
          :icon="true"
          variant="text"
          @click="toggleSortOrder"
        >
          <v-icon>
            {{ viewConfig.sortOrder === 'asc' ? 'mdi-sort-ascending' : 'mdi-sort-descending' }}
          </v-icon>
        </v-btn>
      </div>

      <div class="text-caption text-medium-emphasis">
        显示 {{ siteManagerStore.filteredSites.length }} / {{ siteManagerStore.sites.length }} 个站点
      </div>
    </div>

    <!-- 站点列表/网格 -->
    <div v-if="siteManagerStore.loading" class="text-center py-8">
      <v-progress-circular indeterminate size="48" />
      <div class="mt-4 text-medium-emphasis">加载站点列表中...</div>
    </div>

    <div v-else-if="siteManagerStore.filteredSites.length === 0" class="text-center py-8">
      <EmptyState
        title="没有找到站点"
        description="尝试调整过滤条件或添加新站点"
        icon="mdi-server-off"
      >
        <template #actions>
          <v-btn color="primary" @click="showAddDialog = true">
            添加第一个站点
          </v-btn>
        </template>
      </EmptyState>
    </div>

    <!-- 网格视图 -->
    <v-row v-else-if="viewConfig.layout === 'grid'">
      <v-col
        v-for="site in sortedSites"
        :key="site.id"
        :cols="getGridCols()"
        :sm="getGridCols('sm')"
        :md="getGridCols('md')"
        :lg="getGridCols('lg')"
        :xl="getGridCols('xl')"
      >
        <SiteCard
          :site="site"
          :compact="viewConfig.cardSize === 'small'"
          :show-stats="viewConfig.cardSize !== 'small'"
          :show-health="true"
          :show-tags="viewConfig.cardSize === 'large'"
          @click="onSiteClick"
          @edit="onSiteEdit"
          @delete="onSiteDelete"
          @export="onSiteExport"
        />
      </v-col>
    </v-row>

    <!-- 列表视图 -->
    <v-list v-else class="site-list">
      <v-list-item
        v-for="site in sortedSites"
        :key="site.id"
        class="site-list-item"
        @click="onSiteClick(site)"
      >
        <template #prepend>
          <v-avatar size="40">
            <img
              v-if="site.icon_url"
              :src="site.icon_url"
              :alt="site.name"
              @error="onImageError"
            />
            <v-icon v-else>
              {{ getCategoryIcon(site.category) }}
            </v-icon>
          </v-avatar>
        </template>

        <v-list-item-title class="d-flex align-center">
          <span>{{ site.name }}</span>
          <v-chip
            v-if="site.priority > 0"
            :color="getPriorityColor(site.priority)"
            size="x-small"
            class="ml-2"
          >
            P{{ site.priority }}
          </v-chip>
        </v-list-item-title>

        <v-list-item-subtitle>
          {{ site.domain || site.url }}
        </v-list-item-subtitle>

        <template #append>
          <div class="d-flex align-center">
            <v-chip
              :color="getHealthColor(site.stats?.health_status)"
              size="x-small"
              class="mr-2"
            >
              {{ getHealthText(site.stats?.health_status) }}
            </v-chip>

            <v-switch
              :model-value="site.enabled"
              density="compact"
              hide-details
              @click.stop
              @update:model-value="onToggleEnabled(site.id)"
            />

            <v-menu>
              <template #activator="{ props }">
                <v-btn
                  v-bind="props"
                  :icon="true"
                  variant="text"
                  @click.stop
                >
                  <v-icon>mdi-dots-vertical</v-icon>
                </v-btn>
              </template>

              <v-list density="compact">
                <v-list-item
                  prepend-icon="mdi-pencil"
                  title="编辑"
                  @click="onSiteEdit(site)"
                />
                <v-list-item
                  prepend-icon="mdi-heart-pulse"
                  title="健康检查"
                  @click="onHealthCheck(site.id)"
                />
                <v-list-item
                  prepend-icon="mdi-export"
                  title="导出"
                  @click="onSiteExport(site)"
                />
                <v-divider />
                <v-list-item
                  prepend-icon="mdi-delete"
                  title="删除"
                  class="text-error"
                  @click="onSiteDelete(site)"
                />
              </v-list>
            </v-menu>
          </div>
        </template>
      </v-list-item>
    </v-list>

    <!-- 对话框组件 -->
    <SiteAddEditDialog
      v-model="showAddDialog"
      :site="currentEditSite"
      @saved="onSiteSaved"
    />

    <SiteImportDialog
      v-model="showImportDialog"
      @imported="onSitesImported"
    />

    <SiteExportDialog
      v-model="showExportDialog"
      :sites="selectedSites"
    />

    <BatchHealthCheckDialog
      v-model="showBatchHealthDialog"
      :sites="siteManagerStore.filteredSites"
      @checked="onBatchHealthChecked"
    />

    <ViewSettingsDialog
      v-model="showSettingsDialog"
      :config="viewConfig"
      @updated="onViewConfigUpdated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useSiteManagerStore } from '@/stores/siteManager'
import { useAppStore } from '@/stores/app'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import FilterToolbar from '@/components/common/FilterToolbar.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SiteCard from '@/components/siteManager/SiteCard.vue'
import SiteAddEditDialog from '@/components/siteManager/SiteAddEditDialog.vue'
import SiteImportDialog from '@/components/siteManager/SiteImportDialog.vue'
import SiteExportDialog from '@/components/siteManager/SiteExportDialog.vue'
import BatchHealthCheckDialog from '@/components/siteManager/BatchHealthCheckDialog.vue'
import ViewSettingsDialog from '@/components/siteManager/ViewSettingsDialog.vue'
import type { SiteBrief, SiteDetail, SiteManagerViewConfig } from '@/types/siteManager'
import { HealthStatus } from '@/types/siteManager'

const siteManagerStore = useSiteManagerStore()
const appStore = useAppStore()

// 响应式状态
const showAddDialog = ref(false)
const showImportDialog = ref(false)
const showExportDialog = ref(false)
const showBatchHealthDialog = ref(false)
const showSettingsDialog = ref(false)
const currentEditSite = ref<SiteDetail | null>(null)
const selectedSites = ref<number[]>([])

// 视图配置
const viewConfig = ref<SiteManagerViewConfig>({
  layout: 'grid',
  cardSize: 'medium',
  sortBy: 'priority',
  sortOrder: 'desc',
  showDisabled: true,
  autoRefresh: false,
  refreshInterval: 60,
  virtualScroll: false,
  lazyLoadImages: true,
  pageSize: 50
})

// 面包屑导航
const breadcrumbs = computed(() => [
  { title: '首页', to: '/' },
  { title: '站点管理' }
])

// 排序后的站点列表
const sortedSites = computed(() => {
  const sites = [...siteManagerStore.filteredSites]
  
  return sites.sort((a, b) => {
    let aValue: any
    let bValue: any
    
    switch (viewConfig.value.sortBy) {
      case 'priority':
        aValue = a.priority
        bValue = b.priority
        break
      case 'name':
        aValue = a.name.toLowerCase()
        bValue = b.name.toLowerCase()
        break
      case 'created_at':
        aValue = new Date(a.created_at).getTime()
        bValue = new Date(b.created_at).getTime()
        break
      case 'health_status':
        aValue = a.stats?.health_status || 'UNKNOWN'
        bValue = b.stats?.health_status || 'UNKNOWN'
        break
      default:
        return 0
    }
    
    if (aValue < bValue) return viewConfig.value.sortOrder === 'asc' ? -1 : 1
    if (aValue > bValue) return viewConfig.value.sortOrder === 'asc' ? 1 : -1
    return 0
  })
})

// 方法
const refreshData = async () => {
  await siteManagerStore.initialize()
}

const resetFilter = () => {
  siteManagerStore.resetFilter()
}

const applyFilter = () => {
  // 过滤器已经在store中自动应用
}

const toggleSortOrder = () => {
  viewConfig.value.sortOrder = viewConfig.value.sortOrder === 'asc' ? 'desc' : 'asc'
}

const getGridCols = (size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl') => {
  const sizeMap = {
    small: { xs: 12, sm: 6, md: 4, lg: 3, xl: 2 },
    medium: { xs: 12, sm: 6, md: 4, lg: 3, xl: 3 },
    large: { xs: 12, sm: 6, md: 6, lg: 4, xl: 3 }
  }
  
  const cardSize = viewConfig.value.cardSize
  return sizeMap[cardSize][size || 'xs']
}

const onSiteClick = (_site: SiteBrief) => {
  // 显示站点详情抽屉
  currentEditSite.value = null
  showAddDialog.value = true
}

const onSiteEdit = (site: SiteBrief) => {
  currentEditSite.value = site as SiteDetail
  showAddDialog.value = true
}

const onSiteDelete = async (site: SiteBrief) => {
  const confirmed = await appStore.showConfirmDialog({
    title: '删除站点',
    message: `确定要删除站点 "${site.name}" 吗？此操作不可撤销。`,
    confirmText: '删除',
    cancelText: '取消',
    type: 'error'
  })
  
  if (confirmed) {
    try {
      await siteManagerStore.deleteSite(site.id)
      appStore.showSuccessMessage('站点删除成功')
    } catch (error) {
      appStore.showErrorMessage('删除站点失败')
    }
  }
}

const onSiteExport = (site: SiteBrief) => {
  selectedSites.value = [site.id]
  showExportDialog.value = true
}

const onToggleEnabled = async (siteId: number) => {
  try {
    await siteManagerStore.toggleSiteEnabled(siteId)
  } catch (error) {
    appStore.showErrorMessage('切换启用状态失败')
  }
}

const onHealthCheck = async (siteId: number) => {
  try {
    await siteManagerStore.checkSiteHealth(siteId)
    appStore.showSuccessMessage('健康检查完成')
  } catch (error) {
    appStore.showErrorMessage('健康检查失败')
  }
}

const onSiteSaved = () => {
  showAddDialog.value = false
  currentEditSite.value = null
  refreshData()
}

const onSitesImported = () => {
  showImportDialog.value = false
  refreshData()
}

const onBatchHealthChecked = () => {
  showBatchHealthDialog.value = false
  refreshData()
}

const onViewConfigUpdated = (config: SiteManagerViewConfig) => {
  viewConfig.value = config
  // 保存配置到本地存储
  localStorage.setItem('siteManager_viewConfig', JSON.stringify(config))
}

const onImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
}

// 工具方法
const getCategoryIcon = (category?: string): string => {
  const iconMap: Record<string, string> = {
    pt: 'mdi-server',
    bt: 'mdi-download',
    novel: 'mdi-book-open',
    comic: 'mdi-image',
    music: 'mdi-music',
    movie: 'mdi-movie',
    game: 'mdi-gamepad'
  }
  return iconMap[category || ''] || 'mdi-web'
}

const getHealthColor = (status?: HealthStatus) => {
  const colorMap: Record<HealthStatus, string> = {
    [HealthStatus.OK]: 'success',
    [HealthStatus.WARN]: 'warning',
    [HealthStatus.ERROR]: 'error',
    [HealthStatus.UNKNOWN]: 'grey'
  }
  return colorMap[status || HealthStatus.UNKNOWN]
}

const getHealthText = (status?: HealthStatus): string => {
  const textMap: Record<HealthStatus, string> = {
    OK: '正常',
    WARN: '警告',
    ERROR: '错误',
    UNKNOWN: '未知'
  }
  return textMap[status || 'UNKNOWN']
}

const getPriorityColor = (priority: number): string => {
  if (priority >= 5) return 'error'
  if (priority >= 3) return 'warning'
  return 'info'
}

// 生命周期
onMounted(async () => {
  // 加载保存的视图配置
  const savedConfig = localStorage.getItem('siteManager_viewConfig')
  if (savedConfig) {
    try {
      viewConfig.value = { ...viewConfig.value, ...JSON.parse(savedConfig) }
    } catch (error) {
      console.warn('加载视图配置失败:', error)
    }
  }
  
  // 初始化数据
  await refreshData()
})

// 监听过滤器变化，自动刷新
watch(
  () => siteManagerStore.filter,
  () => {
    // 过滤器变化时，store会自动重新过滤
  },
  { deep: true }
)
</script>

<style lang="scss" scoped>
.site-manager {
  padding: 0;
}

.site-list {
  background: transparent;
  
  &-item {
    margin-bottom: 8px;
    border-radius: 8px;
    background: rgb(var(--v-theme-surface));
    transition: all 0.3s ease;
    
    &:hover {
      transform: translateX(4px);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
  }
}

// 响应式设计
@media (max-width: 960px) {
  .site-manager {
    .v-btn-group {
      flex-wrap: wrap;
    }
  }
}

@media (max-width: 600px) {
  .site-manager {
    .d-flex.align-center.justify-space-between {
      flex-direction: column;
      align-items: flex-start;
      gap: 12px;
    }
  }
}
</style>
