<template>
  <div class="manga-remote-explorer-page">
    <!-- 顶部 PageHeader -->
    <PageHeader title="远程漫画源" subtitle="浏览和导入远程漫画到本地">
      <template #actions>
        <v-btn
          color="primary"
          variant="elevated"
          prepend-icon="mdi-download-multiple"
          @click="openDownloadJobsDialog"
        >
          下载任务
          <v-badge
            v-if="downloadJobs.filter(job => job.status === 'PENDING' || job.status === 'RUNNING').length > 0"
            :content="downloadJobs.filter(job => job.status === 'PENDING' || job.status === 'RUNNING').length"
            color="orange"
            inline
          />
        </v-btn>
        <!-- 聚合搜索开关 -->
        <v-switch
          v-model="aggregatedSearch"
          label="搜索所有源"
          variant="outlined"
          density="compact"
          hide-details
          class="mr-4"
          color="primary"
        />
        <v-select
          v-model="selectedSourceId"
          :items="sourceOptions"
          item-title="name"
          item-value="id"
          label="选择源"
          variant="outlined"
          density="compact"
          hide-details
          class="mr-4"
          style="max-width: 200px;"
          :disabled="aggregatedSearch"
        />
        <v-select
          v-model="selectedLibraryId"
          :items="libraryOptions"
          item-title="name"
          item-value="id"
          label="选择库/书架"
          variant="outlined"
          density="compact"
          hide-details
          class="mr-4"
          style="max-width: 220px;"
          :loading="loadingLibraries"
          :disabled="!selectedSourceId || libraryOptions.length === 0 || aggregatedSearch"
          clearable
        />
        <v-text-field
          v-model="searchQuery"
          variant="outlined"
          density="compact"
          placeholder="搜索漫画..."
          prepend-inner-icon="mdi-magnify"
          hide-details
          clearable
          style="max-width: 300px;"
          @keyup.enter="performSearch"
        />
        <v-btn
          color="primary"
          prepend-icon="mdi-magnify"
          @click="performSearch"
          :loading="searching"
        >
          {{ aggregatedSearch ? '聚合搜索' : '搜索' }}
        </v-btn>
      </template>
    </PageHeader>

    <!-- 内容区域 -->
    <v-container fluid>
      <!-- 加载状态 -->
      <div v-if="loadingSources" class="text-center py-12">
        <v-progress-circular indeterminate color="primary" size="64" />
        <div class="mt-4 text-body-1 text-medium-emphasis">加载源列表...</div>
      </div>

      <!-- 错误状态 -->
      <v-alert
        v-else-if="error"
        type="error"
        variant="tonal"
        class="mb-4"
      >
        {{ error }}
      </v-alert>

      <!-- 搜索结果 -->
      <div v-else>
        <!-- 聚合搜索结果统计 -->
        <div v-if="aggregatedSearchResult" class="mb-4">
          <div class="text-body-2 text-medium-emphasis">
            聚合搜索"{{ aggregatedSearchResult.query }}"：共 {{ aggregatedSearchResult.total_items }} 个结果
            <span v-if="aggregatedSearchResult.successful_sources < aggregatedSearchResult.total_sources">
              （{{ aggregatedSearchResult.successful_sources }}/{{ aggregatedSearchResult.total_sources }} 个源成功）
            </span>
          </div>
          <div v-if="aggregatedSearchResult.has_failures" class="text-caption text-warning mt-1">
            <v-icon size="small" color="warning">mdi-alert</v-icon>
            部分源搜索失败，请查看下方详细信息
          </div>
        </div>

        <!-- 单源搜索结果统计 -->
        <div v-else-if="searchResult" class="mb-4 text-body-2 text-medium-emphasis">
          找到 {{ searchResult.total }} 个结果
          <span v-if="searchResult.items.length < searchResult.total">
            （显示前 {{ searchResult.items.length }} 个）
          </span>
        </div>

        <!-- 聚合搜索结果列表 -->
        <div v-if="aggregatedSearchResult && aggregatedSearchResult.results_by_source.length > 0">
          <v-expansion-panels variant="accordion" class="mb-4">
            <v-expansion-panel
              v-for="sourceResult in aggregatedSearchResult.results_by_source"
              :key="sourceResult.source_id"
              :title="sourceResult.source_name"
            >
              <v-expansion-panel-text>
                <!-- 源状态指示 -->
                <div class="mb-3 d-flex justify-space-between align-center">
                  <div>
                    <v-chip
                      :color="sourceResult.success ? 'success' : 'error'"
                      size="small"
                      variant="outlined"
                      class="mr-2"
                    >
                      {{ sourceResult.success ? '成功' : '失败' }}
                    </v-chip>
                    <span v-if="!sourceResult.success" class="text-caption text-error">
                      {{ sourceResult.error_message }}
                    </span>
                    <span v-else-if="sourceResult.result" class="text-caption text-medium-emphasis">
                      {{ sourceResult.result.total }} 个结果
                    </span>
                  </div>
                  <v-chip size="x-small" variant="outlined">
                    {{ getSourceTypeName(sourceResult.source_type) }}
                  </v-chip>
                </div>

                <!-- 该源的搜索结果 -->
                <v-row v-if="sourceResult.success && sourceResult.result && sourceResult.result.items.length > 0" dense>
                  <v-col
                    v-for="item in sourceResult.result.items"
                    :key="`${item.source_id}-${item.remote_id}`"
                    cols="6"
                    sm="4"
                    md="3"
                    lg="2"
                  >
                    <v-card
                      class="manga-card"
                      elevation="2"
                    >
                      <v-img
                        :src="item.cover_url || '/placeholder-manga.jpg'"
                        aspect-ratio="2/3"
                        cover
                        class="manga-cover"
                        @click="openDetail(item)"
                      >
                        <template v-slot:placeholder>
                          <div class="d-flex align-center justify-center fill-height">
                            <v-icon size="64" color="grey-lighten-1">mdi-book-open-page-variant</v-icon>
                          </div>
                        </template>
                      </v-img>
                      <v-card-text class="pa-2">
                        <div class="text-body-2 font-weight-medium text-truncate" :title="item.title" @click="openDetail(item)">
                          {{ item.title }}
                        </div>
                        <div class="text-caption text-medium-emphasis mt-1 d-flex justify-space-between align-center">
                          <div>
                            <span v-if="item.chapters_count">{{ item.chapters_count }} 话</span>
                          </div>
                          <div class="d-flex gap-1">
                            <v-btn
                              icon
                              size="x-small"
                              variant="text"
                              @click.stop="followRemote(item)"
                              title="追这部"
                              color="primary"
                            >
                              <v-icon size="small">mdi-heart-plus</v-icon>
                            </v-btn>
                            <v-btn
                              icon
                              size="x-small"
                              variant="text"
                              @click.stop="openExternal(item)"
                              title="在原站打开"
                              color="secondary"
                            >
                              <v-icon size="small">mdi-open-in-new</v-icon>
                            </v-btn>
                          </div>
                        </div>
                      </v-card-text>
                    </v-card>
                  </v-col>
                </v-row>
                <v-alert v-else-if="sourceResult.success && (!sourceResult.result || sourceResult.result.items.length === 0)" type="info" variant="tonal">
                  该源没有找到匹配的漫画
                </v-alert>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </div>

        <!-- 单源搜索结果列表 -->
        <v-row v-else-if="searchResult && searchResult.items.length > 0" dense>
          <v-col
            v-for="item in searchResult.items"
            :key="`${item.source_id}-${item.remote_id}`"
            cols="6"
            sm="4"
            md="3"
            lg="2"
          >
            <v-card
              class="manga-card"
              elevation="2"
            >
              <v-img
                :src="item.cover_url || '/placeholder-manga.jpg'"
                aspect-ratio="2/3"
                cover
                class="manga-cover"
                @click="openDetail(item)"
              >
                <template v-slot:placeholder>
                  <div class="d-flex align-center justify-center fill-height">
                    <v-icon size="64" color="grey-lighten-1">mdi-book-open-page-variant</v-icon>
                  </div>
                </template>
              </v-img>
              <v-card-text class="pa-2">
                <div class="text-body-2 font-weight-medium text-truncate" :title="item.title" @click="openDetail(item)">
                  {{ item.title }}
                </div>
                <div class="text-caption text-medium-emphasis mt-1 d-flex justify-space-between align-center">
                  <div>
                    <v-chip size="x-small" variant="outlined" class="mr-1">
                      {{ getSourceTypeName(item.source_type) }}
                    </v-chip>
                    <span v-if="item.chapters_count">{{ item.chapters_count }} 话</span>
                  </div>
                  <div class="d-flex gap-1">
                    <v-btn
                      icon
                      size="x-small"
                      variant="text"
                      @click.stop="followRemote(item)"
                      title="追这部"
                      color="primary"
                    >
                      <v-icon size="small">mdi-heart-plus</v-icon>
                    </v-btn>
                    <v-btn
                      icon
                      size="x-small"
                      variant="text"
                      @click.stop="openExternal(item)"
                      title="在原站打开"
                      color="secondary"
                    >
                      <v-icon size="small">mdi-open-in-new</v-icon>
                    </v-btn>
                  </div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- 空状态 -->
        <v-alert
          v-else-if="searchResult && searchResult.items.length === 0"
          type="info"
          variant="tonal"
          class="mt-4"
        >
          没有找到匹配的漫画
        </v-alert>

        <!-- 未搜索状态 -->
        <div v-else class="text-center py-12">
          <v-icon size="64" color="grey-lighten-1">mdi-book-search</v-icon>
          <div class="mt-4 text-body-1 text-medium-emphasis">请输入关键字搜索漫画</div>
        </div>

        <!-- 分页 -->
        <div v-if="searchResult && Math.ceil(searchResult.total / searchResult.page_size) > 1" class="d-flex justify-center align-center pa-4">
          <v-pagination
            v-model="currentPage"
            :length="Math.ceil(searchResult.total / searchResult.page_size)"
            :total-visible="7"
            @update:model-value="loadPage"
          />
        </div>
      </div>
    </v-container>

    <!-- 详情抽屉 -->
    <v-navigation-drawer
      v-model="showDetailDrawer"
      location="right"
      width="500"
      temporary
    >
      <div v-if="selectedSeries" class="pa-4">
        <div class="d-flex justify-space-between align-center mb-4">
          <h3 class="text-h6">漫画详情</h3>
          <v-btn icon variant="text" @click="showDetailDrawer = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </div>

        <v-divider class="mb-4" />

        <!-- 封面和基本信息 -->
        <div class="d-flex mb-4">
          <v-img
            :src="selectedSeries.cover_url || '/placeholder-manga.jpg'"
            width="120"
            height="180"
            cover
            class="mr-4"
            rounded
          />
          <div class="flex-grow-1">
            <h2 class="text-h5 mb-2">{{ selectedSeries.title }}</h2>
            <div v-if="selectedSeries.authors && selectedSeries.authors.length > 0" class="mb-2">
              <span class="text-caption text-medium-emphasis">作者：</span>
              <span>{{ selectedSeries.authors.join(', ') }}</span>
            </div>
            <div v-if="selectedSeries.status" class="mb-2">
              <v-chip size="small" variant="outlined">{{ selectedSeries.status }}</v-chip>
            </div>
            <div v-if="selectedSeries.chapters_count" class="mb-2">
              <span class="text-caption text-medium-emphasis">章节数：</span>
              <span>{{ selectedSeries.chapters_count }}</span>
            </div>
          </div>
        </div>

        <!-- 简介 -->
        <div v-if="selectedSeries.summary" class="mb-4">
          <h4 class="text-subtitle-2 mb-2">简介</h4>
          <p class="text-body-2">{{ selectedSeries.summary }}</p>
        </div>

        <!-- 标签 -->
        <div v-if="selectedSeries.tags && selectedSeries.tags.length > 0" class="mb-4">
          <h4 class="text-subtitle-2 mb-2">标签</h4>
          <div class="d-flex flex-wrap gap-2">
            <v-chip
              v-for="tag in selectedSeries.tags"
              :key="tag"
              size="small"
              variant="outlined"
            >
              {{ tag }}
            </v-chip>
          </div>
        </div>

        <!-- 章节列表 -->
        <div class="mb-4">
          <div class="d-flex justify-space-between align-center mb-2">
            <h4 class="text-subtitle-2">章节列表</h4>
            <v-btn
              icon
              size="small"
              variant="text"
              @click="loadChapters"
              :loading="loadingChapters"
            >
              <v-icon>mdi-refresh</v-icon>
            </v-btn>
          </div>
          <div v-if="loadingChapters" class="text-center py-4">
            <v-progress-circular indeterminate size="24" />
          </div>
          <v-list v-else-if="chapters.length > 0" density="compact">
            <v-list-item
              v-for="chapter in chapters"
              :key="chapter.remote_id"
              :title="chapter.title"
              :subtitle="chapter.number ? `第 ${chapter.number} 话` : ''"
            >
              <template v-slot:append>
              <v-btn
                icon
                size="small"
                variant="text"
                @click.stop="openImportDialog"
                title="导入到本地"
              >
                <v-icon>mdi-download</v-icon>
              </v-btn>
              </template>
            </v-list-item>
          </v-list>
          <v-alert v-else type="info" variant="tonal">
            暂无章节信息
          </v-alert>
        </div>

        <!-- 导入到本地按钮 -->
        <v-btn
          block
          color="primary"
          variant="elevated"
          prepend-icon="mdi-download"
          :loading="importing"
          @click="openImportDialog"
          class="mt-4"
        >
          导入到本地漫画库
        </v-btn>
      </div>
    </v-navigation-drawer>

    <!-- 下载任务对话框 -->
    <v-dialog v-model="showDownloadJobsDialog" max-width="900px" scrollable>
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-download-multiple</v-icon>
          下载任务
          <v-spacer />
          <v-btn icon variant="text" @click="showDownloadJobsDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>

        <v-divider />

        <v-card-text class="pa-4">
          <!-- 加载状态 -->
          <div v-if="loadingDownloadJobs" class="text-center py-8">
            <v-progress-circular indeterminate color="primary" size="48" />
            <div class="mt-2 text-body-2 text-medium-emphasis">加载下载任务...</div>
          </div>

          <!-- 任务列表 -->
          <div v-else-if="downloadJobs.length > 0">
            <v-list density="compact">
              <v-list-item
                v-for="job in downloadJobs"
                :key="job.id"
                class="mb-2"
                :border="job.status === 'RUNNING'"
              >
                <template #prepend>
                  <v-avatar :color="getJobStatusColor(job.status)" size="32">
                    <v-icon color="white" size="20">
                      {{ job.status === 'SUCCESS' ? 'mdi-check' : 
                         job.status === 'FAILED' ? 'mdi-close' : 
                         job.status === 'RUNNING' ? 'mdi-download' : 'mdi-clock-outline' }}
                    </v-icon>
                  </v-avatar>
                </template>

                <v-list-item-title class="font-weight-medium">
                  {{ job.remote_series_title }}
                  <v-chip
                    :color="getJobStatusColor(job.status)"
                    size="x-small"
                    class="ml-2"
                  >
                    {{ getJobStatusText(job.status) }}
                  </v-chip>
                </v-list-item-title>

                <v-list-item-subtitle>
                  <div class="d-flex align-center gap-4 mt-1">
                    <span>任务 #{{ job.id }}</span>
                    <span>{{ job.source_name }}</span>
                    <span>{{ job.mode === 'SERIES' ? '系列下载' : '章节下载' }}</span>
                  </div>
                  <div class="d-flex align-center gap-4 mt-1 text-caption text-medium-emphasis">
                    <span>创建: {{ new Date(job.created_at).toLocaleString() }}</span>
                    <span v-if="job.completed_at">
                      完成: {{ new Date(job.completed_at).toLocaleString() }}
                    </span>
                  </div>
                  <div v-if="job.error_message" class="text-caption text-error mt-1">
                    错误: {{ job.error_message }}
                  </div>
                  <!-- 进度显示 -->
                  <div v-if="job.progress && job.status === 'RUNNING'" class="mt-2">
                    <v-progress-linear
                      :model-value="job.progress.percentage"
                      :color="getJobStatusColor(job.status)"
                      height="4"
                    />
                    <div class="text-caption mt-1">
                      {{ job.progress.current }} / {{ job.progress.total }} ({{ job.progress.percentage }}%)
                    </div>
                  </div>
                </v-list-item-subtitle>

                <template #append>
                  <v-btn
                    v-if="job.status === 'SUCCESS'"
                    icon
                    size="small"
                    variant="text"
                    @click="router.push({ name: 'MangaLibraryPage', query: { highlight: job.target_series_id } })"
                    title="查看本地漫画"
                  >
                    <v-icon size="small">mdi-book-open-variant</v-icon>
                  </v-btn>
                </template>
              </v-list-item>
            </v-list>
          </div>

          <!-- 空状态 -->
          <div v-else class="text-center py-8">
            <v-icon size="64" color="grey-lighten-1">mdi-download-outline</v-icon>
            <div class="mt-2 text-body-1 text-medium-emphasis">暂无下载任务</div>
            <div class="text-caption text-medium-emphasis">
              在远程漫画页面点击"导入到本地漫画库"开始下载
            </div>
          </div>
        </v-card-text>

        <v-divider />

        <v-card-actions>
          <v-spacer />
          <v-btn @click="loadDownloadJobs" :loading="loadingDownloadJobs">
            <v-icon class="mr-1">mdi-refresh</v-icon>
            刷新
          </v-btn>
          <v-btn variant="text" @click="showDownloadJobsDialog = false">
            关闭
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { mangaRemoteApi, mangaLocalApi, mangaFollowApi } from '@/services/api'
import { mangaDownloadJobApi } from '@/services/mangaDownloadJobApi'
import type {
  RemoteMangaSourceInfo,
  RemoteMangaSeries,
  RemoteMangaChapter,
  RemoteMangaSearchResult,
  AggregatedSearchResult,
  MangaSourceType
} from '@/types/mangaSource'
import type {
  MangaDownloadJob,
  MangaDownloadJobStatus
} from '@/types/mangaDownloadJob'
import PageHeader from '@/components/common/PageHeader.vue'

const router = useRouter()
const toast = useToast()

// 状态
const loadingSources = ref(false)
const loadingLibraries = ref(false)
const error = ref<string | null>(null)
const sources = ref<RemoteMangaSourceInfo[]>([])
const selectedSourceId = ref<number | null>(null)
const libraries = ref<import('@/types/mangaSource').MangaLibraryInfo[]>([])
const selectedLibraryId = ref<string | null>(null)

// 聚合搜索
const aggregatedSearch = ref(false)
const aggregatedSearchResult = ref<AggregatedSearchResult | null>(null)

// 搜索
const searchQuery = ref('')
const searching = ref(false)
const searchResult = ref<RemoteMangaSearchResult | null>(null)
const currentPage = ref(1)

// 详情
const showDetailDrawer = ref(false)
const selectedSeries = ref<RemoteMangaSeries | null>(null)
const loadingChapters = ref(false)
const chapters = ref<RemoteMangaChapter[]>([])

// 导入对话框
const showImportDialog = ref(false)
const importing = ref(false)
const importMode = ref<'ALL' | 'LATEST_N' | 'SELECTED'>('ALL')
const importLatestN = ref(5)

// 下载任务状态
const downloadJobs = ref<MangaDownloadJob[]>([])
const showDownloadJobsDialog = ref(false)
const loadingDownloadJobs = ref(false)
const jobPollingInterval = ref<NodeJS.Timeout | null>(null)

// 源选项
const sourceOptions = computed(() => {
  return sources.value.map(s => ({
    id: s.id,
    name: s.name,
    type: s.type
  }))
})

const libraryOptions = computed(() => {
  return libraries.value
})

// 获取源类型名称
const getSourceTypeName = (type: MangaSourceType): string => {
  const typeMap: Record<MangaSourceType, string> = {
    OPDS: 'OPDS',
    SUWAYOMI: 'Suwayomi',
    KOMGA: 'Komga',
    GENERIC_HTTP: '通用 HTTP'
  }
  return typeMap[type] || type
}

// 获取任务状态显示文本
const getJobStatusText = (status: MangaDownloadJobStatus): string => {
  const statusMap: Record<MangaDownloadJobStatus, string> = {
    PENDING: '等待中',
    RUNNING: '下载中',
    SUCCESS: '已完成',
    FAILED: '失败'
  }
  return statusMap[status] || status
}

// 获取任务状态颜色
const getJobStatusColor = (status: MangaDownloadJobStatus): string => {
  const colorMap: Record<MangaDownloadJobStatus, string> = {
    PENDING: 'orange',
    RUNNING: 'blue',
    SUCCESS: 'green',
    FAILED: 'red'
  }
  return colorMap[status] || 'grey'
}

// 加载下载任务列表
const loadDownloadJobs = async () => {
  try {
    loadingDownloadJobs.value = true
    const result = await mangaDownloadJobApi.getUserJobs({ page_size: 50 })
    downloadJobs.value = result.items
  } catch (err: any) {
    console.error('加载下载任务失败:', err)
    toast.error('加载下载任务失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    loadingDownloadJobs.value = false
  }
}

// 开始轮询下载任务状态
const startJobPolling = () => {
  if (jobPollingInterval.value) {
    clearInterval(jobPollingInterval.value)
  }
  
  jobPollingInterval.value = setInterval(() => {
    if (downloadJobs.value.some(job => job.status === 'PENDING' || job.status === 'RUNNING')) {
      loadDownloadJobs()
    }
  }, 5000) // 每5秒轮询一次
}

// 停止轮询
const stopJobPolling = () => {
  if (jobPollingInterval.value) {
    clearInterval(jobPollingInterval.value)
    jobPollingInterval.value = null
  }
}

// 打开下载任务对话框
const openDownloadJobsDialog = async () => {
  showDownloadJobsDialog.value = true
  await loadDownloadJobs()
  startJobPolling()
}

// 加载源列表
const loadSources = async () => {
  try {
    loadingSources.value = true
    error.value = null

    const data = await mangaRemoteApi.listSources({ only_enabled: true })
    sources.value = data

    // 默认选择第一个源
    if (sources.value.length > 0 && !selectedSourceId.value) {
      selectedSourceId.value = sources.value[0].id
    }
  } catch (err: any) {
    console.error('加载源列表失败:', err)
    error.value = err.response?.data?.detail || err.message || '加载源列表失败'
    toast.error(error.value)
  } finally {
    loadingSources.value = false
  }
}

// 加载指定源的库/书架
const loadLibraries = async () => {
  if (!selectedSourceId.value) {
    libraries.value = []
    selectedLibraryId.value = null
    return
  }

  try {
    loadingLibraries.value = true
    const data = await mangaRemoteApi.listLibraries(selectedSourceId.value)
    libraries.value = data
    // 自动选择第一个库（可选）
    if (libraries.value.length > 0 && !selectedLibraryId.value) {
      selectedLibraryId.value = libraries.value[0].id
    }
  } catch (err: any) {
    console.error('加载库列表失败:', err)
    toast.error(err.response?.data?.detail || err.message || '加载库列表失败')
    libraries.value = []
    selectedLibraryId.value = null
  } finally {
    loadingLibraries.value = false
  }
}

// 执行搜索
const performSearch = async () => {
  if (!aggregatedSearch.value && !selectedSourceId.value) {
    toast.warning('请先选择源或启用聚合搜索')
    return
  }

  try {
    searching.value = true
    error.value = null

    if (aggregatedSearch.value) {
      // 聚合搜索
      const result = await mangaRemoteApi.aggregatedSearch({
        q: searchQuery.value,
        page: currentPage.value,
        page_size: 20
      })
      aggregatedSearchResult.value = result
      searchResult.value = null
    } else {
      // 单源搜索
      let result: RemoteMangaSearchResult

      if (!searchQuery.value.trim() && selectedLibraryId.value) {
        // 无关键字但选择了库：按库浏览
        result = await mangaRemoteApi.browseByLibrary({
          source_id: selectedSourceId.value!,
          library_id: selectedLibraryId.value,
          page: currentPage.value,
          page_size: 20
        })
      } else {
        // 默认按关键字搜索
        if (!searchQuery.value.trim()) {
          toast.warning('请输入搜索关键字或选择库进行浏览')
          return
        }

        result = await mangaRemoteApi.search({
          q: searchQuery.value,
          source_id: selectedSourceId.value!,
          page: currentPage.value,
          page_size: 20
        })
      }

      searchResult.value = result
      aggregatedSearchResult.value = null
    }
  } catch (err: any) {
    console.error('搜索失败:', err)
    error.value = err.response?.data?.detail || err.message || '搜索失败'
    toast.error(error.value)
    searchResult.value = null
    aggregatedSearchResult.value = null
  } finally {
    searching.value = false
  }
}

// 加载指定页
const loadPage = (page: number) => {
  currentPage.value = page
  performSearch()
}

// 打开详情
const openDetail = async (series: RemoteMangaSeries) => {
  selectedSeries.value = series
  showDetailDrawer.value = true
  chapters.value = []
  
  // 自动加载章节列表
  await loadChapters()
}

// 加载章节列表
const loadChapters = async () => {
  if (!selectedSeries.value) return

  try {
    loadingChapters.value = true
    const data = await mangaRemoteApi.getChapters(
      selectedSeries.value.source_id,
      selectedSeries.value.remote_id
    )
    chapters.value = data
  } catch (err: any) {
    console.error('加载章节列表失败:', err)
    toast.error(err.response?.data?.detail || err.message || '加载章节列表失败')
  } finally {
    loadingChapters.value = false
  }
}

// 监听源切换
watch(selectedSourceId, () => {
  // 切换源时清空搜索结果
  searchResult.value = null
  currentPage.value = 1
  libraries.value = []
  selectedLibraryId.value = null
  if (selectedSourceId.value) {
    loadLibraries()
  }
})

// 监听下载任务对话框关闭，停止轮询
watch(showDownloadJobsDialog, (newVal) => {
  if (!newVal) {
    stopJobPolling()
  }
})

// 组件销毁时清理轮询
onUnmounted(() => {
  stopJobPolling()
})

// 打开导入对话框
const openImportDialog = () => {
  if (!selectedSeries.value) return
  showImportDialog.value = true
}

// 快速导入（使用默认设置）
const quickImport = async (series: RemoteMangaSeries) => {
  // TODO: 实现导入对话框
  toast.info('导入功能待实现')
}

// 追更外部漫画
const followRemote = async (series: RemoteMangaSeries) => {
  try {
    await mangaFollowApi.followRemoteSeries({
      source_id: series.source_id,
      remote_series_id: series.remote_id
    })
    toast.success(`已开始追更《${series.title}》`)
  } catch (err: any) {
    console.error('追更失败:', err)
    const errorMessage = err.response?.data?.detail || err.message || '追更失败'
    toast.error(errorMessage)
  }
}

// 在原站打开
const openExternal = async (series: RemoteMangaSeries) => {
  try {
    const result = await mangaRemoteApi.getExternalUrl(series.source_id, series.remote_id)
    window.open(result.external_url, '_blank')
  } catch (err: any) {
    console.error('获取外部URL失败:', err)
    const errorMessage = err.response?.data?.detail || err.message || '获取外部URL失败'
    toast.error(errorMessage)
  }
}

// 执行导入（创建下载任务）
const performImport = async () => {
  if (!selectedSeries.value) return

  try {
    importing.value = true

    // 创建下载任务
    const job = await mangaDownloadJobApi.createJob({
      source_id: selectedSeries.value.source_id,
      remote_series_id: selectedSeries.value.remote_id,
      mode: importMode.value === 'ALL' || importMode.value === 'LATEST_N' ? 'SERIES' : 'CHAPTER',
      latest_n: importMode.value === 'LATEST_N' ? importLatestN.value : undefined
    })

    toast.success(`下载任务已创建 (#${job.id})，正在后台下载`)
    showImportDialog.value = false

    // 自动打开下载任务对话框显示状态
    await loadDownloadJobs()
    showDownloadJobsDialog.value = true
    startJobPolling()

  } catch (err: any) {
    console.error('创建下载任务失败:', err)
    toast.error('创建下载任务失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    importing.value = false
  }
}

// 初始化
onMounted(() => {
  loadSources()
})
</script>

<style scoped lang="scss">
.manga-remote-explorer-page {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.manga-card {
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2) !important;
  }

  .manga-cover {
    border-radius: 4px 4px 0 0;
  }
}
</style>

