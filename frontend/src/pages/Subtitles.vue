<template>
  <div class="subtitles-page">
    <!-- 页面标题 -->
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold">字幕管理</h1>
        <p class="text-body-1 text-medium-emphasis mt-2">管理媒体文件字幕</p>
      </div>
      <v-btn
        color="primary"
        prepend-icon="mdi-plus"
        size="large"
        @click="showDownloadDialog = true"
      >
        下载字幕
      </v-btn>
    </div>

    <!-- 搜索和过滤 -->
    <v-card variant="outlined" class="mb-4">
      <v-card-text class="py-3">
        <v-row align="center" dense>
          <v-col cols="12" md="5">
            <v-text-field
              v-model="searchQuery"
              placeholder="搜索媒体文件路径..."
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              hide-details
              clearable
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="languageFilter"
              :items="languageOptions"
              label="语言"
              variant="outlined"
              density="compact"
              hide-details
              clearable
            />
          </v-col>
          <v-col cols="12" md="4">
            <v-btn
              color="primary"
              variant="flat"
              prepend-icon="mdi-refresh"
              :loading="loading"
              @click="loadSubtitles"
            >
              刷新
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- 字幕列表 -->
    <template v-if="loading && subtitles.length === 0">
      <v-card>
        <v-card-text class="d-flex justify-center align-center" style="min-height: 400px;">
          <div class="text-center">
            <v-progress-circular indeterminate color="primary" size="64" />
            <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
          </div>
        </v-card-text>
      </v-card>
    </template>

    <template v-else-if="filteredSubtitles.length === 0">
      <v-card variant="outlined">
        <v-card-text class="text-center pa-12">
          <v-icon size="80" color="grey-darken-1" class="mb-4">mdi-subtitles-outline</v-icon>
          <div class="text-h5 font-weight-medium mb-2">暂无字幕</div>
          <div class="text-body-2 text-medium-emphasis mb-4">
            使用顶部的"下载字幕"按钮为媒体文件下载字幕
          </div>
          <v-btn
            color="primary"
            prepend-icon="mdi-plus"
            @click="showDownloadDialog = true"
          >
            下载字幕
          </v-btn>
        </v-card-text>
      </v-card>
    </template>

    <template v-else>
      <v-card variant="outlined">
        <v-list>
          <template v-for="(subtitle, index) in filteredSubtitles" :key="subtitle.id">
            <v-list-item>
              <template #prepend>
                <v-icon color="primary" class="me-3">mdi-subtitles</v-icon>
              </template>

              <v-list-item-title class="text-body-1 font-weight-medium">
                {{ subtitle.media_title }}
                <span v-if="subtitle.media_year" class="text-caption text-medium-emphasis">
                  ({{ subtitle.media_year }})
                </span>
                <span v-if="subtitle.season && subtitle.episode" class="text-caption text-medium-emphasis">
                  S{{ subtitle.season }}E{{ subtitle.episode }}
                </span>
              </v-list-item-title>

              <v-list-item-subtitle class="mt-1">
                <div class="d-flex align-center flex-wrap gap-2">
                  <v-chip
                    :color="getLanguageColor(subtitle.language_code)"
                    size="x-small"
                    variant="flat"
                  >
                    {{ subtitle.language }}
                  </v-chip>
                  <v-chip
                    size="x-small"
                    variant="outlined"
                  >
                    {{ subtitle.format }}
                  </v-chip>
                  <v-chip
                    size="x-small"
                    variant="outlined"
                  >
                    {{ subtitle.source }}
                  </v-chip>
                  <span v-if="subtitle.is_embedded" class="text-caption text-medium-emphasis">
                    <v-icon size="14" class="me-1">mdi-check-circle</v-icon>
                    内嵌
                  </span>
                  <span v-if="subtitle.is_forced" class="text-caption text-medium-emphasis">
                    <v-icon size="14" class="me-1">mdi-alert-circle</v-icon>
                    强制
                  </span>
                  <span class="text-caption text-medium-emphasis">
                    <v-icon size="14" class="me-1">mdi-file</v-icon>
                    {{ subtitle.subtitle_path }}
                  </span>
                </div>
              </v-list-item-subtitle>

              <template #append>
                <v-menu>
                  <template #activator="{ props }">
                    <v-btn
                      icon="mdi-dots-vertical"
                      variant="text"
                      size="small"
                      v-bind="props"
                    />
                  </template>
                  <v-list>
                    <v-list-item
                      prepend-icon="mdi-eye"
                      title="查看详情"
                      @click="viewSubtitle(subtitle)"
                    />
                    <v-list-item
                      prepend-icon="mdi-download"
                      title="重新下载"
                      @click="downloadSubtitle(subtitle.media_file_path, subtitle.language_code)"
                    />
                    <v-list-item
                      prepend-icon="mdi-delete"
                      title="删除"
                      @click="deleteSubtitle(subtitle)"
                    />
                  </v-list>
                </v-menu>
              </template>
            </v-list-item>
            <v-divider v-if="index < filteredSubtitles.length - 1" />
          </template>
        </v-list>
      </v-card>

      <!-- 分页 -->
      <v-pagination
        v-if="totalPages > 1"
        v-model="currentPage"
        :length="totalPages"
        :total-visible="7"
        class="mt-4"
        @update:model-value="loadSubtitles"
      />
    </template>

    <!-- 下载字幕对话框 -->
    <v-dialog v-model="showDownloadDialog" max-width="600">
      <v-card>
        <v-card-title>下载字幕</v-card-title>
        <v-card-text>
          <v-form ref="downloadFormRef">
            <v-text-field
              v-model="downloadForm.mediaFilePath"
              label="媒体文件路径 *"
              variant="outlined"
              prepend-inner-icon="mdi-file"
              :rules="[v => !!v || '请输入媒体文件路径']"
              required
              class="mb-4"
            />
            <v-select
              v-model="downloadForm.language"
              :items="languageOptions"
              label="语言 *"
              variant="outlined"
              prepend-inner-icon="mdi-translate"
              :rules="[v => !!v || '请选择语言']"
              required
              class="mb-4"
            />
            <v-text-field
              v-model="downloadForm.savePath"
              label="保存路径（可选）"
              variant="outlined"
              prepend-inner-icon="mdi-folder"
              hint="留空则自动保存到媒体文件同目录"
            />
            <v-switch
              v-model="downloadForm.forceDownload"
              label="强制下载（忽略自动下载设置）"
              color="primary"
              hide-details
              class="mt-2"
            />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showDownloadDialog = false">
            取消
          </v-btn>
          <v-btn
            color="primary"
            variant="flat"
            :loading="downloading"
            @click="handleDownload"
          >
            下载
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 搜索字幕对话框 -->
    <v-dialog v-model="showSearchDialog" max-width="800">
      <v-card>
        <v-card-title>搜索字幕</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="searchForm.mediaFilePath"
            label="媒体文件路径 *"
            variant="outlined"
            prepend-inner-icon="mdi-file"
            required
            class="mb-4"
          />
          <v-select
            v-model="searchForm.language"
            :items="languageOptions"
            label="语言 *"
            variant="outlined"
            required
            class="mb-4"
          />
          <v-btn
            color="primary"
            prepend-icon="mdi-magnify"
            :loading="searching"
            @click="handleSearch"
            class="mb-4"
          >
            搜索字幕
          </v-btn>

          <!-- 搜索结果 -->
          <v-card
            v-if="searchResults.length > 0"
            variant="outlined"
            class="mt-4"
          >
            <v-card-title>搜索结果</v-card-title>
            <v-card-text>
              <v-list>
                <v-list-item
                  v-for="(result, index) in searchResults"
                  :key="index"
                >
                  <v-list-item-title>{{ result.title }}</v-list-item-title>
                  <v-list-item-subtitle>
                    <div class="d-flex align-center flex-wrap gap-2 mt-1">
                      <v-chip size="x-small">{{ result.language }}</v-chip>
                      <v-chip size="x-small" variant="outlined">{{ result.format }}</v-chip>
                      <v-chip size="x-small" variant="outlined">{{ result.source }}</v-chip>
                      <span class="text-caption">{{ formatFileSize(result.file_size) }}</span>
                      <span v-if="result.rating" class="text-caption">
                        <v-icon size="14" class="me-1">mdi-star</v-icon>
                        {{ result.rating }}
                      </span>
                    </div>
                  </v-list-item-subtitle>
                  <template #append>
                    <v-btn
                      size="small"
                      color="primary"
                      prepend-icon="mdi-download"
                      @click="downloadFromSearch(result)"
                    >
                      下载
                    </v-btn>
                  </template>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showSearchDialog = false">
            关闭
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 字幕详情对话框 -->
    <v-dialog v-model="showDetailDialog" max-width="600">
      <v-card v-if="selectedSubtitle">
        <v-card-title>字幕详情</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12">
              <div class="text-caption text-medium-emphasis mb-1">媒体文件</div>
              <div class="text-body-1 font-weight-medium">{{ selectedSubtitle.media_title }}</div>
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-caption text-medium-emphasis mb-1">语言</div>
              <div class="text-body-1">{{ selectedSubtitle.language }}</div>
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-caption text-medium-emphasis mb-1">格式</div>
              <div class="text-body-1">{{ selectedSubtitle.format }}</div>
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-caption text-medium-emphasis mb-1">来源</div>
              <div class="text-body-1">{{ selectedSubtitle.source }}</div>
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-caption text-medium-emphasis mb-1">字幕路径</div>
              <div class="text-body-2">{{ selectedSubtitle.subtitle_path }}</div>
            </v-col>
            <v-col cols="12">
              <div class="text-caption text-medium-emphasis mb-1">下载时间</div>
              <div class="text-body-2">{{ formatDate(selectedSubtitle.downloaded_at) }}</div>
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showDetailDialog = false">
            关闭
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { subtitleApi } from '@/services/api'
import { useToast } from '@/composables/useToast'

interface Subtitle {
  id: number
  media_file_path: string
  media_type: string
  media_title: string
  media_year?: number
  season?: number
  episode?: number
  subtitle_path: string
  language: string
  language_code: string
  format: string
  source: string
  source_id?: string
  download_url?: string
  file_size?: number
  rating?: number
  downloads?: number
  is_embedded: boolean
  is_external: boolean
  is_forced: boolean
  is_hearing_impaired: boolean
  downloaded_at: string
  created_at: string
  updated_at: string
}

interface SubtitleInfo {
  title: string
  language: string
  language_code: string
  format: string
  download_url: string
  file_size: number
  rating?: number
  downloads?: number
  source: string
  source_id: string
  is_forced: boolean
  is_hearing_impaired: boolean
}

const { showSuccess, showError } = useToast()

const loading = ref(false)
const subtitles = ref<Subtitle[]>([])
const searchQuery = ref('')
const languageFilter = ref<string | null>(null)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const showDownloadDialog = ref(false)
const downloading = ref(false)
const downloadFormRef = ref()
const downloadForm = ref({
  mediaFilePath: '',
  language: 'zh',
  savePath: '',
  forceDownload: true
})

const showSearchDialog = ref(false)
const searching = ref(false)
const searchForm = ref({
  mediaFilePath: '',
  language: 'zh'
})
const searchResults = ref<SubtitleInfo[]>([])

const showDetailDialog = ref(false)
const selectedSubtitle = ref<Subtitle | null>(null)

const languageOptions = [
  { title: '全部', value: null },
  { title: '中文', value: 'zh' },
  { title: '英文', value: 'en' },
  { title: '日文', value: 'ja' },
  { title: '韩文', value: 'ko' }
]

const filteredSubtitles = computed(() => {
  let result = subtitles.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(sub =>
      sub.media_file_path.toLowerCase().includes(query) ||
      sub.media_title.toLowerCase().includes(query)
    )
  }

  if (languageFilter.value) {
    result = result.filter(sub => sub.language_code === languageFilter.value)
  }

  return result
})

const totalPages = computed(() => {
  return Math.ceil(total.value / pageSize.value)
})

const loadSubtitles = async () => {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (languageFilter.value) {
      params.language = languageFilter.value
    }

    const response = await subtitleApi.getSubtitles(params)
    
    if (response.data.items) {
      subtitles.value = response.data.items
      total.value = response.data.total || 0
    } else {
      subtitles.value = Array.isArray(response.data) ? response.data : []
      total.value = subtitles.value.length
    }
  } catch (error: any) {
    showError(error.message || '加载字幕列表失败')
    console.error('加载字幕列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleDownload = async () => {
  const { valid } = await downloadFormRef.value.validate()
  if (!valid) {
    showError('请填写所有必填项')
    return
  }

  downloading.value = true
  try {
    const response = await subtitleApi.downloadSubtitle({
      media_file_path: downloadForm.value.mediaFilePath,
      language: downloadForm.value.language,
      save_path: downloadForm.value.savePath || undefined,
      force_download: downloadForm.value.forceDownload
    })
    if (response.data) {
      showSuccess('下载成功')
      showDownloadDialog.value = false
      downloadForm.value = {
        mediaFilePath: '',
        language: 'zh',
        savePath: '',
        forceDownload: true
      }
      await loadSubtitles()
    } else {
      throw new Error('未获取到下载结果')
    }
  } catch (error: any) {
    const errorMsg = error.response?.data?.error_message || error.message || '下载失败'
    showError(errorMsg)
    console.error('下载字幕失败:', error)
  } finally {
    downloading.value = false
  }
}

const handleSearch = async () => {
  if (!searchForm.value.mediaFilePath || !searchForm.value.language) {
    showError('请填写媒体文件路径和语言')
    return
  }

  searching.value = true
  searchResults.value = []
  try {
    const response = await subtitleApi.searchSubtitles({
      media_file_path: searchForm.value.mediaFilePath,
      language: searchForm.value.language
    })
    if (response.data) {
      searchResults.value = Array.isArray(response.data) ? response.data : []
      if (searchResults.value.length === 0) {
        showError('未找到匹配的字幕')
      } else {
        showSuccess(`找到 ${searchResults.value.length} 个字幕`)
      }
    } else {
      throw new Error('未获取到搜索结果')
    }
  } catch (error: any) {
    const errorMsg = error.response?.data?.error_message || error.message || '搜索失败'
    showError(errorMsg)
    console.error('搜索字幕失败:', error)
  } finally {
    searching.value = false
  }
}

const downloadFromSearch = async (result: SubtitleInfo) => {
  try {
    // 从搜索结果下载字幕
    const response = await subtitleApi.downloadSubtitle({
      media_file_path: searchForm.value.mediaFilePath,
      language: result.language_code,
      force_download: true
    })
    if (response.data) {
      showSuccess('下载成功')
      await loadSubtitles()
    } else {
      throw new Error('未获取到下载结果')
    }
  } catch (error: any) {
    const errorMsg = error.response?.data?.error_message || error.message || '下载失败'
    showError(errorMsg)
    console.error('下载字幕失败:', error)
  }
}

const downloadSubtitle = async (mediaFilePath: string, language: string) => {
  try {
    await subtitleApi.downloadSubtitle({
      media_file_path: mediaFilePath,
      language: language,
      force_download: true
    })
    showSuccess('下载成功')
    await loadSubtitles()
  } catch (error: any) {
    showError(error.message || '下载失败')
  }
}

const deleteSubtitle = async (subtitle: Subtitle) => {
  if (!confirm(`确定要删除字幕 "${subtitle.media_title}" 吗？`)) {
    return
  }

  try {
    await subtitleApi.deleteSubtitle(subtitle.id)
    showSuccess('删除成功')
    await loadSubtitles()
  } catch (error: any) {
    showError(error.message || '删除失败')
  }
}

const viewSubtitle = (subtitle: Subtitle) => {
  selectedSubtitle.value = subtitle
  showDetailDialog.value = true
}

const getLanguageColor = (code: string) => {
  const colors: Record<string, string> = {
    zh: 'primary',
    en: 'info',
    ja: 'warning',
    ko: 'error'
  }
  return colors[code] || 'grey'
}

const formatFileSize = (bytes?: number) => {
  if (!bytes) return '未知'
  const kb = bytes / 1024
  if (kb < 1024) return `${kb.toFixed(2)} KB`
  const mb = kb / 1024
  return `${mb.toFixed(2)} MB`
}

const formatDate = (date: string) => {
  try {
    return new Date(date).toLocaleString('zh-CN')
  } catch {
    return date
  }
}

onMounted(() => {
  loadSubtitles()
})
</script>

<style scoped>
.subtitles-page {
  padding: 24px;
}
</style>

