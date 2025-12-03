<template>
  <div class="manga-reader-page">
    <!-- 顶部工具栏 -->
    <v-app-bar flat class="reader-header">
      <v-btn icon @click="router.back()">
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
      <v-toolbar-title class="text-h6 text-truncate">
        {{ series?.title || '加载中...' }}
        <span v-if="currentChapter"> - {{ currentChapter.title }}</span>
        <span v-if="readingProgress && !readingProgress.is_finished" class="text-caption text-medium-emphasis ml-2">
          （上次看到：第 {{ readingProgress.last_page_index }} 页）
        </span>
      </v-toolbar-title>
      <v-spacer />
      <v-btn
        v-if="hasRemoteSource"
        icon
        :loading="syncing"
        :title="'从源刷新章节'"
        @click="handleSyncFromRemote"
      >
        <v-icon>mdi-cloud-sync</v-icon>
      </v-btn>
      <v-select
        v-model="selectedChapterId"
        :items="readyChapters"
        item-title="title"
        item-value="id"
        variant="outlined"
        density="compact"
        hide-details
        style="max-width: 200px;"
        class="mr-2"
      />
      <v-btn
        icon
        @click="goToPreviousChapter"
        :disabled="!hasPreviousChapter"
      >
        <v-icon>mdi-chevron-up</v-icon>
      </v-btn>
      <v-btn
        icon
        @click="goToNextChapter"
        :disabled="!hasNextChapter"
      >
        <v-icon>mdi-chevron-down</v-icon>
      </v-btn>
    </v-app-bar>

    <!-- 内容区域 -->
    <v-main class="reader-main">
      <!-- 加载状态 -->
      <div v-if="loading" class="d-flex justify-center align-center fill-height">
        <v-progress-circular indeterminate color="primary" size="64" />
      </div>

      <!-- 错误状态 -->
      <v-alert
        v-else-if="error"
        type="error"
        variant="tonal"
        class="ma-4"
      >
        {{ error }}
      </v-alert>

      <!-- 章节未下载提示 -->
      <div v-else-if="currentChapter && currentChapter.status !== 'READY'" class="d-flex flex-column justify-center align-center fill-height pa-4">
        <v-icon size="64" color="warning">mdi-download-off</v-icon>
        <h3 class="mt-4">章节尚未下载</h3>
        <p class="text-medium-emphasis">当前章节状态：{{ getStatusText(currentChapter.status) }}</p>
        <v-btn
          color="primary"
          prepend-icon="mdi-download"
          :loading="downloading"
          @click="triggerDownload"
          class="mt-4"
        >
          触发下载
        </v-btn>
        <v-alert type="info" variant="tonal" class="mt-4" max-width="500">
          下载完成后请刷新页面查看
        </v-alert>
      </div>

      <!-- 页面列表 -->
      <div v-else-if="pages.length > 0" class="pages-container">
        <img
          v-for="page in pages"
          :key="page.index"
          :ref="el => { if (el) setPageRef(page.index, el) }"
          :src="page.image_url"
          :alt="`第 ${page.index} 页`"
          class="manga-page"
          loading="lazy"
          @load="onPageLoad(page.index)"
        />
      </div>

      <!-- 空状态 -->
      <div v-else class="d-flex justify-center align-center fill-height">
        <v-alert type="info" variant="tonal">
          暂无页面
        </v-alert>
      </div>
    </v-main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { mangaLocalApi, mangaProgressApi } from '@/services/api'
import type {
  MangaSeriesLocal,
  MangaChapterLocal,
  LocalMangaPage,
  MangaReadingProgress
} from '@/types/mangaLocal'

const route = useRoute()
const router = useRouter()
const toast = useToast()

// 状态
const loading = ref(false)
const error = ref<string | null>(null)
const series = ref<MangaSeriesLocal | null>(null)
const chapters = ref<MangaChapterLocal[]>([])
const currentChapter = ref<MangaChapterLocal | null>(null)
const pages = ref<LocalMangaPage[]>([])
const downloading = ref(false)

// 阅读进度
const readingProgress = ref<MangaReadingProgress | null>(null)
const currentPageIndex = ref(1)
let progressUpdateTimer: ReturnType<typeof setTimeout> | null = null
const PROGRESS_UPDATE_INTERVAL = 5000 // 5 秒更新一次进度

// 键盘导航状态
const pageRefs = ref<Map<number, HTMLElement>>(new Map())
const isAutoScrolling = ref(false)

// 预加载状态
const preloadedImages = ref<Map<string, HTMLImageElement>>(new Map())
const PRELOAD_COUNT = 3 // 预加载当前页之后3页

// 计算属性
const seriesId = computed(() => parseInt(route.params.series_id as string))
const chapterId = computed(() => {
  const id = route.params.chapter_id
  return id ? parseInt(id as string) : null
})

const readyChapters = computed(() => {
  return chapters.value
    .filter(ch => ch.status === 'READY')
    .map(ch => ({
      id: ch.id,
      title: ch.title || `第 ${ch.number || ch.id} 话`,
      number: ch.number
    }))
    .sort((a, b) => (a.number || 0) - (b.number || 0))
})

const hasRemoteSource = computed(() => {
  return !!(series.value && series.value.source_id && series.value.remote_series_id)
})

const syncing = ref(false)

const selectedChapterId = computed({
  get: () => currentChapter.value?.id || null,
  set: (value) => {
    if (value) {
      router.push({
        name: 'MangaReaderPage',
        params: { series_id: seriesId.value, chapter_id: value }
      })
    }
  }
})

const hasPreviousChapter = computed(() => {
  if (!currentChapter.value) return false
  const currentIndex = chapters.value.findIndex(ch => ch.id === currentChapter.value!.id)
  return currentIndex > 0
})

const hasNextChapter = computed(() => {
  if (!currentChapter.value) return false
  const currentIndex = chapters.value.findIndex(ch => ch.id === currentChapter.value!.id)
  return currentIndex < chapters.value.length - 1
})

// 获取状态文本
const getStatusText = (status: string): string => {
  const statusMap: Record<string, string> = {
    PENDING: '待下载',
    DOWNLOADING: '下载中',
    READY: '已就绪',
    FAILED: '下载失败'
  }
  return statusMap[status] || status
}

// 设置页面引用（用于键盘导航）
const setPageRef = (pageIndex: number, element: HTMLElement) => {
  pageRefs.value.set(pageIndex, element)
}

// 滚动到指定页面
const scrollToPage = (pageIndex: number) => {
  const element = pageRefs.value.get(pageIndex)
  if (element) {
    isAutoScrolling.value = true
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
    currentPageIndex.value = pageIndex
    
    // 更新阅读进度
    updateReadingProgress(pageIndex)
    
    // 重置自动滚动标记
    setTimeout(() => {
      isAutoScrolling.value = false
    }, 1000)
  }
}

// 键盘导航处理
const handleKeydown = (event: KeyboardEvent) => {
  // 如果用户正在输入框中，不处理键盘导航
  if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
    return
  }

  switch (event.key) {
    case 'ArrowUp':
    case 'ArrowLeft':
    case 'PageUp':
      event.preventDefault()
      goToPreviousPage()
      break
    case 'ArrowDown':
    case 'ArrowRight':
    case ' ':
    case 'PageDown':
      event.preventDefault()
      goToNextPage()
      break
    case 'Home':
      event.preventDefault()
      goToFirstPage()
      break
    case 'End':
      event.preventDefault()
      goToLastPage()
      break
    case 'n':
    case 'N':
      if (!event.ctrlKey && !event.metaKey) {
        event.preventDefault()
        goToNextChapter()
      }
      break
    case 'p':
    case 'P':
      if (!event.ctrlKey && !event.metaKey) {
        event.preventDefault()
        goToPreviousChapter()
      }
      break
  }
}

// 上一页
const goToPreviousPage = () => {
  if (currentPageIndex.value > 1) {
    scrollToPage(currentPageIndex.value - 1)
  }
}

// 下一页
const goToNextPage = () => {
  if (currentPageIndex.value < pages.value.length) {
    scrollToPage(currentPageIndex.value + 1)
  }
}

// 第一页
const goToFirstPage = () => {
  scrollToPage(1)
}

// 最后一页
const goToLastPage = () => {
  if (pages.value.length > 0) {
    scrollToPage(pages.value.length)
  }
}

// 预加载图片
const preloadImage = (imageUrl: string): Promise<void> => {
  return new Promise((resolve, reject) => {
    // 如果已经预加载过，直接返回
    if (preloadedImages.value.has(imageUrl)) {
      resolve()
      return
    }

    const img = new Image()
    img.onload = () => {
      preloadedImages.value.set(imageUrl, img)
      resolve()
    }
    img.onerror = reject
    img.src = imageUrl
  })
}

// 预加载当前页之后的图片
const preloadNextImages = async (currentPageIndex: number) => {
  const startIdx = currentPageIndex
  const endIdx = Math.min(currentPageIndex + PRELOAD_COUNT, pages.value.length)
  
  for (let i = startIdx + 1; i <= endIdx; i++) {
    const page = pages.value.find(p => p.index === i)
    if (page && page.image_url) {
      try {
        await preloadImage(page.image_url)
      } catch (error) {
        console.warn(`预加载第 ${i} 页失败:`, error)
      }
    }
  }
}

// 页面加载完成时触发预加载
const onPageLoad = (pageIndex: number) => {
  // 预加载接下来的图片
  preloadNextImages(pageIndex)
  
  // 更新当前页面索引（用于进度跟踪）
  if (!isAutoScrolling.value) {
    currentPageIndex.value = pageIndex
    updateReadingProgress(pageIndex)
  }
}

// 加载系列详情
const loadSeriesDetail = async () => {
  try {
    loading.value = true
    error.value = null

    // 并行加载系列详情和阅读进度
    const [detailResponse, progressResponse] = await Promise.all([
      mangaLocalApi.getSeriesDetail(seriesId.value),
      mangaProgressApi.getSeriesProgress(seriesId.value).catch(() => null)
    ])

    series.value = detailResponse.series
    chapters.value = detailResponse.chapters
    readingProgress.value = progressResponse

    // 选择章节
    let targetChapter: MangaChapterLocal | null = null

    if (chapterId.value) {
      // URL 中指定了章节，优先使用
      targetChapter = chapters.value.find(ch => ch.id === chapterId.value) || null
    } else if (readingProgress.value && readingProgress.value.chapter_id) {
      // 有阅读进度，尝试使用进度中的章节
      const progressChapter = chapters.value.find(ch => ch.id === readingProgress.value!.chapter_id)
      if (progressChapter && progressChapter.status === 'READY') {
        targetChapter = progressChapter
        // 更新路由
        router.replace({
          name: 'MangaReaderPage',
          params: { series_id: seriesId.value, chapter_id: progressChapter.id }
        })
      }
    }

    // 如果还没有目标章节，使用默认逻辑
    if (!targetChapter) {
      const readyChapters = chapters.value.filter(ch => ch.status === 'READY')
      if (readyChapters.length > 0) {
        const sorted = readyChapters.sort((a, b) => (b.number || 0) - (a.number || 0))
        targetChapter = sorted[0]
        router.replace({
          name: 'MangaReaderPage',
          params: { series_id: seriesId.value, chapter_id: sorted[0].id }
        })
      } else {
        targetChapter = chapters.value[0] || null
      }
    }

    currentChapter.value = targetChapter

    // 加载当前章节的页面
    if (currentChapter.value) {
      await loadChapterPages(currentChapter.value.id)
      
      // 如果有进度且是同一章节，恢复页码
      if (readingProgress.value && 
          readingProgress.value.chapter_id === currentChapter.value.id &&
          readingProgress.value.last_page_index > 1) {
        currentPageIndex.value = readingProgress.value.last_page_index
        // 延迟滚动到对应位置
        setTimeout(() => {
          scrollToPage(readingProgress.value!.last_page_index)
        }, 500)
      }
    }
  } catch (err: any) {
    console.error('加载系列详情失败:', err)
    error.value = err.response?.data?.detail || err.message || '加载失败'
    toast.error(error.value)
  } finally {
    loading.value = false
  }
}

const handleSyncFromRemote = async () => {
  if (!series.value) return
  try {
    syncing.value = true
    const result = await mangaLocalApi.syncSeriesRemote(series.value.id)
    if (result.had_error) {
      toast.error(result.error_message || '从源刷新章节失败')
    } else {
      const added = result.new_chapters_count || 0
      if (added > 0) {
        toast.success(`已从源刷新章节，新增 ${added} 话`)
      } else {
        toast.info('已从源刷新章节，无新增章节')
      }
      await loadSeriesDetail()
    }
  } catch (err: any) {
    console.error('从源刷新章节失败:', err)
    toast.error(err.response?.data?.detail || err.message || '从源刷新章节失败')
  } finally {
    syncing.value = false
  }
}

// 加载章节页面
const loadChapterPages = async (chapterId: number) => {
  try {
    const data = await mangaLocalApi.getChapterPages(chapterId)
    pages.value = data
  } catch (err: any) {
    console.error('加载章节页面失败:', err)
    toast.error(err.response?.data?.detail || err.message || '加载页面失败')
    pages.value = []
  }
}

// 触发下载
const triggerDownload = async () => {
  if (!currentChapter.value) return

  try {
    downloading.value = true
    await mangaLocalApi.downloadChapter(currentChapter.value.id)
    toast.success('下载已开始，请稍后刷新页面')
    
    // 轮询状态（简化版，只轮询一次）
    setTimeout(async () => {
      await loadSeriesDetail()
    }, 3000)
  } catch (err: any) {
    console.error('触发下载失败:', err)
    toast.error(err.response?.data?.detail || err.message || '下载失败')
  } finally {
    downloading.value = false
  }
}

// 上一话
const goToPreviousChapter = () => {
  if (!currentChapter.value) return
  const currentIndex = chapters.value.findIndex(ch => ch.id === currentChapter.value!.id)
  if (currentIndex > 0) {
    const prevChapter = chapters.value[currentIndex - 1]
    router.push({
      name: 'MangaReaderPage',
      params: { series_id: seriesId.value, chapter_id: prevChapter.id }
    })
  }
}

// 下一话
const goToNextChapter = () => {
  if (!currentChapter.value) return
  const currentIndex = chapters.value.findIndex(ch => ch.id === currentChapter.value!.id)
  if (currentIndex < chapters.value.length - 1) {
    const nextChapter = chapters.value[currentIndex + 1]
    router.push({
      name: 'MangaReaderPage',
      params: { series_id: seriesId.value, chapter_id: nextChapter.id }
    })
  }
}

// 页面引用（用于滚动定位） - 重复声明，删除

// 更新阅读进度（节流）
const updateProgress = () => {
  if (!currentChapter.value || !series.value) return

  if (progressUpdateTimer) {
    clearTimeout(progressUpdateTimer)
  }

  progressUpdateTimer = setTimeout(async () => {
    try {
      await mangaProgressApi.upsertSeriesProgress({
        series_id: seriesId.value,
        chapter_id: currentChapter.value!.id,
        last_page_index: currentPageIndex.value,
        total_pages: pages.value.length,
        is_finished: currentPageIndex.value >= pages.value.length
      })
    } catch (err: any) {
      console.error('更新阅读进度失败:', err)
      // 静默失败，不打扰用户
    }
  }, PROGRESS_UPDATE_INTERVAL)
}

// 监听路由变化
watch(() => route.params.chapter_id, async (newChapterId) => {
  if (newChapterId && series.value) {
    const chapter = chapters.value.find(ch => ch.id === parseInt(newChapterId as string))
    if (chapter) {
      currentChapter.value = chapter
      currentPageIndex.value = 1
      await loadChapterPages(chapter.id)
      
      // 如果有该章节的进度，恢复位置
      if (readingProgress.value && readingProgress.value.chapter_id === chapter.id) {
        currentPageIndex.value = readingProgress.value.last_page_index
        setTimeout(() => {
          scrollToPage(readingProgress.value!.last_page_index)
        }, 500)
      }
      
      // 更新进度
      updateProgress()
    }
  }
})

// 监听滚动（检测当前可见页面）
let scrollTimer: ReturnType<typeof setTimeout> | null = null
const handleScroll = () => {
  if (scrollTimer) {
    clearTimeout(scrollTimer)
  }
  
  scrollTimer = setTimeout(() => {
    // 简单的可见性检测：找到最接近视口中心的页面
    const container = document.querySelector('.pages-container')
    if (!container) return
    
    const containerRect = container.getBoundingClientRect()
    const viewportCenter = containerRect.top + window.innerHeight / 2
    
    let closestPage = 1
    let minDistance = Infinity
    
    pageRefs.forEach((el, index) => {
      const rect = el.getBoundingClientRect()
      const pageCenter = rect.top + rect.height / 2
      const distance = Math.abs(pageCenter - viewportCenter)
      
      if (distance < minDistance) {
        minDistance = distance
        closestPage = index
      }
    })
    
    if (closestPage !== currentPageIndex.value) {
      currentPageIndex.value = closestPage
      updateProgress()
    }
  }, 500)
}

// 监听滚动事件
onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true })
})

onBeforeUnmount(() => {
  const mainEl = document.querySelector('.reader-main')
  if (mainEl) {
    mainEl.removeEventListener('scroll', handleScroll)
  }
  if (progressUpdateTimer) {
    clearTimeout(progressUpdateTimer)
  }
  if (scrollTimer) {
    clearTimeout(scrollTimer)
  }
  // 离开时保存最终进度
  if (currentChapter.value && series.value) {
    mangaProgressApi.upsertSeriesProgress({
      series_id: seriesId.value,
      chapter_id: currentChapter.value.id,
      last_page_index: currentPageIndex.value,
      total_pages: pages.value.length,
      is_finished: currentPageIndex.value >= pages.value.length
    }).catch(err => console.error('保存最终进度失败:', err))
  }
})

// 初始化
onMounted(() => {
  loadSeriesDetail()
  // 添加键盘事件监听
  window.addEventListener('keydown', handleKeydown)
})

// 组件销毁时清理
onBeforeUnmount(() => {
  // 清理进度更新定时器
  if (progressUpdateTimer) {
    clearTimeout(progressUpdateTimer)
    progressUpdateTimer = null
  }
  // 移除键盘事件监听
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped lang="scss">
.manga-reader-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #000;
  color: #fff;

  .reader-header {
    background-color: rgba(0, 0, 0, 0.8);
    color: #fff;
  }

  .reader-main {
    flex-grow: 1;
    overflow-y: auto;
    background-color: #000;
  }

  .pages-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 16px;
    gap: 8px;
  }

  .manga-page {
    max-width: 100%;
    height: auto;
    display: block;
    background-color: #1e1e1e;
    border-radius: 4px;
  }
}
</style>

