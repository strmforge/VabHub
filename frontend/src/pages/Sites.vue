<template>
  <div class="sites-page">
    <PageHeader
      title="站点管理"
      subtitle="PT站点配置和管理"
    />

    <v-container fluid class="pa-4">
      <!-- 操作栏 -->
      <v-card variant="outlined" class="mb-4">
        <v-card-text class="pa-3">
          <div class="d-flex align-center justify-space-between flex-wrap ga-2">
            <div class="d-flex align-center ga-2">
              <v-btn
                color="primary"
                prepend-icon="mdi-plus"
                @click="showSiteDialog = true"
              >
                添加站点
              </v-btn>
              <v-btn
                color="secondary"
                prepend-icon="mdi-cloud-sync"
                @click="showCookieCloudDialog = true"
              >
                CookieCloud同步
              </v-btn>
              <v-btn
                color="success"
                prepend-icon="mdi-check-all"
                @click="handleBatchCheckin"
                :loading="batchCheckinLoading"
              >
                批量签到
              </v-btn>
            </div>
            <div class="d-flex align-center ga-2">
              <v-text-field
                v-model="searchQuery"
                prepend-inner-icon="mdi-magnify"
                placeholder="搜索站点..."
                variant="outlined"
                density="compact"
                hide-details
                style="max-width: 300px;"
                clearable
              />
              <v-btn
                icon="mdi-refresh"
                variant="text"
                @click="loadSites"
                :loading="loading"
              />
            </div>
          </div>
        </v-card-text>
      </v-card>

      <!-- 站点列表 -->
      <div v-if="loading" class="text-center py-12">
        <v-progress-circular indeterminate color="primary" size="64" />
        <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
      </div>

      <div v-else-if="filteredSites.length === 0" class="text-center py-12">
        <v-icon size="80" color="grey-darken-1" class="mb-4">mdi-web-off</v-icon>
        <div class="text-h5 font-weight-medium mb-2">暂无站点</div>
        <div class="text-body-2 text-medium-emphasis mb-4">
          使用"添加站点"按钮添加您的第一个PT站点
        </div>
      </div>

      <v-row v-else>
        <v-col
          v-for="site in filteredSites"
          :key="site.id"
          cols="12"
          sm="6"
          md="4"
          lg="3"
        >
          <SiteCard
            :site="site"
            @edit="editSite"
            @delete="deleteSite"
            @test="testSite"
            @checkin="checkinSite"
            @toggle-status="toggleSiteStatus"
            @domain-manage="handleDomainManage"
            @ai-debug="handleAIDebug"
          />
        </v-col>
      </v-row>
    </v-container>

    <!-- 站点对话框 -->
    <SiteDialog
      v-model="showSiteDialog"
      :site="editingSite"
      @saved="handleSiteSaved"
    />

    <!-- CookieCloud同步对话框 -->
    <CookieCloudSyncDialog
      v-model="showCookieCloudDialog"
      @synced="handleCookieCloudSynced"
    />

    <!-- 域名管理对话框 -->
    <SiteDomainDialog
      v-model="showDomainDialog"
      :site-id="domainManageSite?.id || 0"
      :site-name="domainManageSite?.name || ''"
    />

    <!-- Phase AI-3: AI 配置调试对话框 - 仅在开发者模式显示 -->
    <SiteAIAdapterDebugDialog
      v-if="isDevMode()"
      v-model="showAIDebugDialog"
      :site="aiDebugSite"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import PageHeader from '@/components/common/PageHeader.vue'
import SiteCard from '@/components/site/SiteCard.vue'
import SiteDialog from '@/components/site/SiteDialog.vue'
import CookieCloudSyncDialog from '@/components/site/CookieCloudSyncDialog.vue'
import SiteDomainDialog from '@/components/site/SiteDomainDialog.vue'
import SiteAIAdapterDebugDialog from '@/components/site/SiteAIAdapterDebugDialog.vue'  // Phase AI-3
import { isDevMode } from '@/utils/devMode'

const loading = ref(false)
const batchCheckinLoading = ref(false)
const sites = ref<any[]>([])
const searchQuery = ref('')
const showSiteDialog = ref(false)
const showCookieCloudDialog = ref(false)
const showDomainDialog = ref(false)
const showAIDebugDialog = ref(false)  // Phase AI-3
const editingSite = ref<any>(null)
const domainManageSite = ref<any>(null)
const aiDebugSite = ref<any>(null)  // Phase AI-3

const filteredSites = computed(() => {
  if (!searchQuery.value) {
    return sites.value
  }
  const query = searchQuery.value.toLowerCase()
  return sites.value.filter(site =>
    site.name.toLowerCase().includes(query) ||
    site.url.toLowerCase().includes(query)
  )
})

const loadSites = async () => {
  loading.value = true
  try {
    const response = await api.get('/sites')
    sites.value = response.data
  } catch (error: any) {
    console.error('加载站点列表失败:', error)
    alert('加载失败：' + (error.response?.data?.detail || '未知错误'))
  } finally {
    loading.value = false
  }
}

const editSite = (site: any) => {
  editingSite.value = site
  showSiteDialog.value = true
}

const deleteSite = async (site: any) => {
  if (!confirm(`确定要删除站点"${site.name}"吗？`)) {
    return
  }

  try {
    await api.delete(`/sites/${site.id}`)
    await loadSites()
  } catch (error: any) {
    console.error('删除站点失败:', error)
    alert('删除失败：' + (error.response?.data?.detail || '未知错误'))
  }
}

const testSite = async (site: any) => {
  try {
    const response = await api.post(`/sites/${site.id}/test`)
    alert(response.data.message || '测试完成')
  } catch (error: any) {
    console.error('测试站点失败:', error)
    alert('测试失败：' + (error.response?.data?.detail || '未知错误'))
  }
}

const checkinSite = async (site: any) => {
  try {
    const response = await api.post(`/sites/${site.id}/checkin`)
    alert(response.data.message || '签到完成')
    await loadSites()
  } catch (error: any) {
    console.error('签到失败:', error)
    alert('签到失败：' + (error.response?.data?.detail || '未知错误'))
  }
}

const toggleSiteStatus = async (site: any) => {
  try {
    await api.put(`/sites/${site.id}`, {
      ...site,
      is_active: !site.is_active
    })
    await loadSites()
  } catch (error: any) {
    console.error('更新站点状态失败:', error)
    alert('更新失败：' + (error.response?.data?.detail || '未知错误'))
  }
}

const handleBatchCheckin = async () => {
  batchCheckinLoading.value = true
  try {
    const response = await api.post('/sites/batch-checkin')
    alert(response.data.message || '批量签到完成')
    await loadSites()
  } catch (error: any) {
    console.error('批量签到失败:', error)
    alert('批量签到失败：' + (error.response?.data?.detail || '未知错误'))
  } finally {
    batchCheckinLoading.value = false
  }
}

const handleSiteSaved = () => {
  loadSites()
  editingSite.value = null
}

const handleCookieCloudSynced = () => {
  loadSites()
}

const handleDomainManage = (site: any) => {
  domainManageSite.value = site
  showDomainDialog.value = true
}

const handleAIDebug = (site: any) => {
  aiDebugSite.value = site
  showAIDebugDialog.value = true
}

onMounted(() => {
  loadSites()
})
</script>

<style scoped>
.sites-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
}
</style>
