<template>
  <div
    class="novel-reader"
    :class="[`theme-${preferences.theme}`, `font-${preferences.fontSize}`]"
  >
    <v-container fluid class="pa-0">
      <v-row no-gutters class="fill-height">
        <!-- 左侧：章节列表（桌面端） -->
        <v-col
          cols="12"
          md="3"
          class="border-e novel-reader-chapter-list-desktop"
        >
          <v-card flat height="100vh" class="d-flex flex-column">
            <v-card-title class="d-flex align-center">
              <router-link
                :to="{ name: 'WorkDetail', params: { ebookId: ebookId } }"
                class="text-decoration-none text-primary"
              >
                <v-icon class="mr-2">mdi-arrow-left</v-icon>
              </router-link>
              <span class="text-h6">章节列表</span>
            </v-card-title>
            <v-divider />
            <v-card-text class="flex-grow-1 overflow-y-auto pa-0">
              <v-list density="compact" v-if="chapters.length > 0">
                <v-list-item
                  v-for="chapter in chapters"
                  :key="chapter.index"
                  :active="currentChapterIndex === chapter.index"
                  @click="switchChapter(chapter.index)"
                  :class="['cursor-pointer', 'chapter-item', getChapterState(chapter.index)]"
                >
                  <template v-slot:prepend>
                    <v-icon
                      v-if="getChapterState(chapter.index) === 'read'"
                      size="small"
                      color="success"
                    >
                      mdi-check
                    </v-icon>
                    <v-icon
                      v-else-if="getChapterState(chapter.index) === 'current'"
                      size="small"
                      color="primary"
                    >
                      mdi-book-open-page-variant
                    </v-icon>
                  </template>
                  <v-list-item-title class="text-body-2">
                    {{ chapter.title || `第 ${chapter.index + 1} 章` }}
                  </v-list-item-title>
                  <v-list-item-subtitle v-if="chapter.length" class="text-caption">
                    {{ formatLength(chapter.length) }}
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
              <div v-else-if="loadingChapters" class="text-center pa-4">
                <v-progress-circular indeterminate color="primary" />
                <div class="text-caption mt-2">加载章节列表...</div>
              </div>
              <div v-else class="text-center pa-4 text-medium-emphasis">
                暂无章节
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- 右侧：正文阅读区域 -->
        <v-col cols="12" md="9">
          <v-card flat height="100vh" class="d-flex flex-column">
            <!-- 顶部工具栏（移动端显示章节按钮） -->
            <div class="reader-toolbar">
              <div class="left">
                <div class="title">{{ workTitle || '加载中...' }}</div>
                <div class="chapter">{{ currentChapterTitle || '' }}</div>
              </div>
              <div class="right">
                <!-- 移动端章节按钮 -->
                <v-btn
                  icon
                  variant="text"
                  class="novel-reader-chapter-button-mobile"
                  @click="showChapterDrawer = true"
                >
                  <v-icon>mdi-menu</v-icon>
                  <v-tooltip activator="parent">章节列表</v-tooltip>
                </v-btn>

                <!-- 返回按钮（移动端） -->
                <router-link
                  :to="{ name: 'WorkDetail', params: { ebookId: ebookId } }"
                  class="text-decoration-none novel-reader-chapter-button-mobile"
                >
                  <v-btn icon variant="text">
                    <v-icon>mdi-arrow-left</v-icon>
                    <v-tooltip activator="parent">返回</v-tooltip>
                  </v-btn>
                </router-link>

                <!-- 搜索按钮 -->
                <v-btn
                  icon
                  variant="text"
                  @click="openSearchDialog"
                >
                  <v-icon>mdi-magnify</v-icon>
                  <v-tooltip activator="parent">搜索</v-tooltip>
                </v-btn>

                <!-- 主题切换 -->
                <v-btn
                  icon
                  variant="text"
                  @click="cycleTheme"
                >
                  <v-icon>mdi-theme-light-dark</v-icon>
                  <v-tooltip activator="parent">切换主题</v-tooltip>
                </v-btn>

                <!-- 字号减小 -->
                <v-btn
                  icon
                  variant="text"
                  :disabled="isMinFontSize"
                  @click="decreaseFontSize"
                >
                  <span style="font-size: 0.9rem; font-weight: bold;">A-</span>
                  <v-tooltip activator="parent">减小字号</v-tooltip>
                </v-btn>

                <!-- 字号增大 -->
                <v-btn
                  icon
                  variant="text"
                  :disabled="isMaxFontSize"
                  @click="increaseFontSize"
                >
                  <span style="font-size: 0.9rem; font-weight: bold;">A+</span>
                  <v-tooltip activator="parent">增大字号</v-tooltip>
                </v-btn>

                <!-- 标记为已读完 -->
                <v-btn
                  icon
                  variant="text"
                  :disabled="isFinished"
                  @click="markAsFinished"
                >
                  <v-icon>mdi-check-circle-outline</v-icon>
                  <v-tooltip activator="parent">标记为已读完</v-tooltip>
                </v-btn>
              </div>
            </div>

            <!-- 正文内容 -->
            <v-card-text
              ref="contentRef"
              class="flex-grow-1 overflow-y-auto novel-reader-content novel-reader-content-mobile"
              @scroll="handleScroll"
            >
              <div v-if="loadingContent" class="text-center pa-8">
                <v-progress-circular indeterminate color="primary" />
                <div class="text-body-2 mt-4">加载章节内容...</div>
              </div>
              <div v-else-if="currentContent" class="novel-reader-content">
                <pre>{{ currentContent }}</pre>
              </div>
              <div v-else class="text-center pa-8 text-medium-emphasis">
                暂无内容
              </div>
            </v-card-text>

            <!-- 底部：导航按钮（桌面端） -->
            <v-card-actions class="border-t d-none d-md-flex">
              <v-btn
                :disabled="currentChapterIndex <= 0"
                prepend-icon="mdi-chevron-left"
                @click="goToPreviousChapter"
              >
                上一章
              </v-btn>
              <v-spacer />
              <v-btn
                icon
                variant="text"
                @click="scrollToTop"
              >
                <v-icon>mdi-arrow-up</v-icon>
                <v-tooltip activator="parent">回到顶部</v-tooltip>
              </v-btn>
              <v-spacer />
              <v-btn
                :disabled="currentChapterIndex >= chapters.length - 1"
                append-icon="mdi-chevron-right"
                @click="goToNextChapter"
              >
                下一章
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-col>
      </v-row>
    </v-container>

    <!-- 移动端底部导航栏 -->
    <div class="novel-reader-bottom-nav">
      <v-btn
        :disabled="currentChapterIndex <= 0"
        prepend-icon="mdi-chevron-left"
        @click="goToPreviousChapter"
        class="nav-button"
        size="small"
      >
        上一章
      </v-btn>
      <v-btn
        icon
        variant="text"
        @click="scrollToTop"
        size="small"
      >
        <v-icon>mdi-arrow-up</v-icon>
      </v-btn>
      <v-btn
        :disabled="currentChapterIndex >= chapters.length - 1"
        append-icon="mdi-chevron-right"
        @click="goToNextChapter"
        class="nav-button"
        size="small"
      >
        下一章
      </v-btn>
    </div>

    <!-- 移动端章节列表抽屉 -->
    <v-navigation-drawer
      v-model="showChapterDrawer"
      temporary
      location="left"
      width="280"
    >
      <v-card-title class="d-flex align-center">
        <span class="text-h6">章节列表</span>
        <v-spacer />
        <v-btn icon variant="text" @click="showChapterDrawer = false">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      <v-divider />
      <v-card-text class="pa-0">
        <v-list density="compact" v-if="chapters.length > 0">
          <v-list-item
            v-for="chapter in chapters"
            :key="chapter.index"
            :active="currentChapterIndex === chapter.index"
            @click="switchChapter(chapter.index); showChapterDrawer = false"
            :class="['cursor-pointer', 'chapter-item', getChapterState(chapter.index)]"
          >
            <template v-slot:prepend>
              <v-icon
                v-if="getChapterState(chapter.index) === 'read'"
                size="small"
                color="success"
              >
                mdi-check
              </v-icon>
              <v-icon
                v-else-if="getChapterState(chapter.index) === 'current'"
                size="small"
                color="primary"
              >
                mdi-book-open-page-variant
              </v-icon>
            </template>
            <v-list-item-title class="text-body-2">
              {{ chapter.title || `第 ${chapter.index + 1} 章` }}
            </v-list-item-title>
            <v-list-item-subtitle v-if="chapter.length" class="text-caption">
              {{ formatLength(chapter.length) }}
            </v-list-item-subtitle>
          </v-list-item>
        </v-list>
        <div v-else-if="loadingChapters" class="text-center pa-4">
          <v-progress-circular indeterminate color="primary" />
          <div class="text-caption mt-2">加载章节列表...</div>
        </div>
        <div v-else class="text-center pa-4 text-medium-emphasis">
          暂无章节
        </div>
      </v-card-text>
    </v-navigation-drawer>

    <!-- 搜索对话框 -->
    <v-dialog
      v-model="showSearchDialog"
      max-width="800"
      scrollable
    >
      <v-card>
        <v-card-title class="d-flex align-center">
          <span class="text-h6">书内搜索</span>
          <v-spacer />
          <v-btn icon variant="text" @click="showSearchDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <!-- 搜索输入 -->
          <div class="d-flex gap-2 mb-4">
            <v-text-field
              v-model="searchQuery"
              label="搜索关键字"
              variant="outlined"
              density="compact"
              prepend-inner-icon="mdi-magnify"
              @keyup.enter="performSearch"
              clearable
              autofocus
            />
            <v-btn
              color="primary"
              @click="performSearch"
              :loading="searching"
            >
              搜索
            </v-btn>
          </div>

          <!-- 搜索结果 -->
          <div v-if="searchResults.length > 0">
            <div class="text-caption text-medium-emphasis mb-2">
              找到 {{ searchResults.length }} 个结果
            </div>
            <v-list density="compact">
              <v-list-item
                v-for="(hit, index) in searchResults"
                :key="index"
                @click="goToSearchResult(hit)"
                class="cursor-pointer"
              >
                <v-list-item-title class="text-body-2 font-weight-medium mb-1">
                  {{ hit.chapter_title || `第 ${hit.chapter_index + 1} 章` }}
                </v-list-item-title>
                <v-list-item-subtitle class="text-body-2" style="white-space: normal;">
                  <span v-html="highlightSnippet(hit.snippet, searchQuery)"></span>
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </div>
          <div v-else-if="searchPerformed && !searching" class="text-center pa-8 text-medium-emphasis">
            未找到匹配结果
          </div>
          <div v-else-if="searching" class="text-center pa-8">
            <v-progress-circular indeterminate color="primary" />
            <div class="text-body-2 mt-4">搜索中...</div>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showSearchDialog = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { novelReaderApi, novelSearchApi } from '@/services/api'
import { useToast } from '@/composables/useToast'
import { useNovelReaderPreferences } from '@/composables/useNovelReaderPreferences'
import type { NovelChapterSummary, NovelChapterTextResponse, UserNovelReadingProgress, NovelSearchHit } from '@/types/novel'

const route = useRoute()
const router = useRouter()
const toast = useToast()

// 阅读器偏好设置
const {
  preferences,
  cycleTheme,
  decreaseFontSize,
  increaseFontSize,
  isMinFontSize,
  isMaxFontSize
} = useNovelReaderPreferences()

// 路由参数
const ebookId = computed(() => {
  const id = route.params.ebookId
  return typeof id === 'string' ? parseInt(id, 10) : (Array.isArray(id) ? parseInt(id[0], 10) : id)
})

// 状态
const chapters = ref<NovelChapterSummary[]>([])
const currentChapterIndex = ref(0)
const currentContent = ref('')
const currentChapterTitle = ref('')
const workTitle = ref('')
const loadingChapters = ref(false)
const loadingContent = ref(false)
const readingProgress = ref<UserNovelReadingProgress | null>(null)
const contentRef = ref<HTMLElement | null>(null)
const showChapterDrawer = ref(false)

// 搜索相关状态
const showSearchDialog = ref(false)
const searchQuery = ref('')
const searchResults = ref<NovelSearchHit[]>([])
const searching = ref(false)
const searchPerformed = ref(false)
const lastSearchQuery = ref('')

// 进度保存节流
let lastProgressSaveTime = 0
const PROGRESS_SAVE_INTERVAL = 3000 // 3 秒
let progressSaveTimer: ReturnType<typeof setTimeout> | null = null

// 是否已完成
const isFinished = computed(() => readingProgress.value?.is_finished || false)

// 加载章节列表
const loadChapters = async () => {
  if (!ebookId.value) return
  
  loadingChapters.value = true
  try {
    const data = await novelReaderApi.getChapters(ebookId.value)
    chapters.value = data || []
    
    // 如果有章节，加载阅读进度
    if (chapters.value.length > 0) {
      await loadReadingProgress()
    }
  } catch (err: any) {
    console.error('加载章节列表失败:', err)
    toast.error(err.response?.data?.detail || err.message || '加载章节列表失败')
  } finally {
    loadingChapters.value = false
  }
}

// 加载阅读进度
const loadReadingProgress = async () => {
  if (!ebookId.value) return
  
  try {
    const progress = await novelReaderApi.getReadingProgress(ebookId.value)
    readingProgress.value = progress
    
    // 确定初始章节
    if (progress.is_finished && chapters.value.length > 0) {
      // 已完成：跳到最后一章
      currentChapterIndex.value = chapters.value.length - 1
    } else {
      // 未完成：跳到上次阅读的章节
      currentChapterIndex.value = Math.min(
        progress.current_chapter_index || 0,
        chapters.value.length - 1
      )
    }
    
    // 加载当前章节
    await loadChapterContent(currentChapterIndex.value)
    
    // 恢复滚动位置
    await nextTick()
    restoreScrollPosition()
  } catch (err: any) {
    console.error('加载阅读进度失败:', err)
    // 失败时默认从第一章开始
    if (chapters.value.length > 0) {
      currentChapterIndex.value = 0
      await loadChapterContent(0)
    }
  }
}

// 加载章节内容
const loadChapterContent = async (chapterIndex: number) => {
  if (!ebookId.value || chapterIndex < 0 || chapterIndex >= chapters.value.length) return
  
  loadingContent.value = true
  try {
    const data = await novelReaderApi.getChapterText(ebookId.value, chapterIndex)
    currentContent.value = data.content || ''
    currentChapterTitle.value = data.title || ''
    
    // 更新工作标题（首次加载时）
    if (!workTitle.value && data.ebook_id) {
      // 可以从路由或其他地方获取，这里简化处理
      workTitle.value = `作品 #${data.ebook_id}`
    }
    
    // 重置滚动位置（新章节）
    await nextTick()
    if (contentRef.value) {
      contentRef.value.scrollTop = 0
    }
  } catch (err: any) {
    console.error('加载章节内容失败:', err)
    toast.error(err.response?.data?.detail || err.message || '加载章节内容失败')
    currentContent.value = ''
    currentChapterTitle.value = ''
  } finally {
    loadingContent.value = false
  }
}

// 切换章节
const switchChapter = async (chapterIndex: number) => {
  if (chapterIndex === currentChapterIndex.value) return
  
  // 保存当前章节进度（使用当前滚动位置）
  if (contentRef.value) {
    const element = contentRef.value
    const scrollTop = element.scrollTop
    const scrollHeight = element.scrollHeight
    const clientHeight = element.clientHeight
    
    if (scrollHeight > clientHeight) {
      const scrollRatio = scrollTop / (scrollHeight - clientHeight)
      const offset = Math.floor(Math.max(0, Math.min(1, scrollRatio)) * 1000)
      await saveProgress(currentChapterIndex.value, offset)
    } else {
      await saveProgress(currentChapterIndex.value, 0)
    }
  } else {
    await saveProgress(currentChapterIndex.value, 0)
  }
  
  // 切换到新章节
  currentChapterIndex.value = chapterIndex
  await loadChapterContent(chapterIndex)
}

// 上一章
const goToPreviousChapter = async () => {
  if (currentChapterIndex.value <= 0) return
  await switchChapter(currentChapterIndex.value - 1)
}

// 下一章
const goToNextChapter = async () => {
  if (currentChapterIndex.value >= chapters.value.length - 1) return
  await switchChapter(currentChapterIndex.value + 1)
}

// 回到顶部
const scrollToTop = () => {
  if (contentRef.value) {
    contentRef.value.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

// 处理滚动
const handleScroll = () => {
  if (!contentRef.value) return
  
  // 节流保存进度
  const now = Date.now()
  if (now - lastProgressSaveTime < PROGRESS_SAVE_INTERVAL) {
    // 清除之前的定时器
    if (progressSaveTimer) {
      clearTimeout(progressSaveTimer)
    }
    // 设置新的定时器
    progressSaveTimer = setTimeout(() => {
      saveProgressFromScroll()
    }, PROGRESS_SAVE_INTERVAL)
    return
  }
  
  saveProgressFromScroll()
  lastProgressSaveTime = now
}

// 从滚动位置保存进度（使用滚动比例）
const saveProgressFromScroll = () => {
  if (!contentRef.value) return
  
  const element = contentRef.value
  const scrollTop = element.scrollTop
  const scrollHeight = element.scrollHeight
  const clientHeight = element.clientHeight
  
  if (scrollHeight <= clientHeight) {
    // 内容不足一屏，视为已读完
    saveProgress(currentChapterIndex.value, 1.0)
    return
  }
  
  // 计算滚动比例（0-1）
  const scrollRatio = scrollTop / (scrollHeight - clientHeight)
  // 限制在 0-1 范围内
  const clampedRatio = Math.max(0, Math.min(1, scrollRatio))
  
  // 转换为后端存储格式（0-1000，表示 0-100%）
  const offset = Math.floor(clampedRatio * 1000)
  
  saveProgress(currentChapterIndex.value, offset)
}

// 保存进度
const saveProgress = async (chapterIndex: number, offset: number) => {
  if (!ebookId.value) return
  
  try {
    await novelReaderApi.updateReadingProgress(ebookId.value, {
      current_chapter_index: chapterIndex,
      chapter_offset: offset,
      is_finished: false
    })
  } catch (err: any) {
    console.error('保存阅读进度失败:', err)
    // 静默失败，不影响阅读体验
  }
}

// 恢复滚动位置（使用滚动比例）
const restoreScrollPosition = () => {
  if (!contentRef.value || !readingProgress.value) return
  
  const progress = readingProgress.value
  if (progress.current_chapter_index !== currentChapterIndex.value) {
    // 章节已切换，不需要恢复
    return
  }
  
  // 恢复滚动位置
  const element = contentRef.value
  const scrollHeight = element.scrollHeight
  const clientHeight = element.clientHeight
  
  if (scrollHeight <= clientHeight) return
  
  // 将 offset 转换回滚动比例
  // offset 是 0-1000 的百分比值，表示 0-100%
  const scrollRatio = progress.chapter_offset / 1000
  const maxScroll = scrollHeight - clientHeight
  element.scrollTop = Math.floor(scrollRatio * maxScroll)
}

// 监听主题和字号变化，重新恢复滚动位置（保持阅读位置）
watch(
  [() => preferences.theme, () => preferences.fontSize],
  () => {
    // 主题或字号变化后，等待 DOM 更新，然后恢复滚动位置
    nextTick(() => {
      if (contentRef.value && readingProgress.value) {
        restoreScrollPosition()
      }
    })
  }
)

// 标记为已读完
const markAsFinished = async () => {
  if (!ebookId.value) return
  
  try {
    await novelReaderApi.updateReadingProgress(ebookId.value, {
      current_chapter_index: currentChapterIndex.value,
      chapter_offset: 999999,
      is_finished: true
    })
    
    readingProgress.value = {
      ...readingProgress.value!,
      is_finished: true
    }
    
    toast.success('已标记为已读完')
  } catch (err: any) {
    console.error('标记为已读完失败:', err)
    toast.error(err.response?.data?.detail || err.message || '操作失败')
  }
}

// 格式化长度
const formatLength = (length: number): string => {
  if (length < 1000) {
    return `${length} 字`
  } else {
    return `${(length / 1000).toFixed(1)}k 字`
  }
}

// 章节状态计算
type ChapterReadState = 'read' | 'current' | 'unread'

const getChapterState = (chapterIndex: number): ChapterReadState => {
  if (isFinished.value) {
    // 全书读完，当前章节可保持 current，其他为 read
    if (chapterIndex === currentChapterIndex.value) return 'current'
    return 'read'
  }

  if (chapterIndex < currentChapterIndex.value) return 'read'
  if (chapterIndex === currentChapterIndex.value) return 'current'
  return 'unread'
}

// 打开搜索对话框
const openSearchDialog = () => {
  showSearchDialog.value = true
  searchQuery.value = ''
  searchResults.value = []
  searchPerformed.value = false
}

// 执行搜索
const performSearch = async () => {
  const query = searchQuery.value.trim()
  
  if (!query) {
    toast.error('请输入搜索关键字')
    return
  }

  // 如果与上一次搜索相同，使用缓存（可选）
  if (query === lastSearchQuery.value && searchResults.value.length > 0) {
    return
  }

  if (!ebookId.value) {
    toast.error('无法搜索：作品 ID 无效')
    return
  }

  searching.value = true
  searchPerformed.value = false
  
  try {
    const results = await novelSearchApi.searchInBook(ebookId.value, {
      q: query,
      max_hits: 50
    })
    
    searchResults.value = results
    searchPerformed.value = true
    lastSearchQuery.value = query
  } catch (err: any) {
    console.error('搜索失败:', err)
    toast.error(err.response?.data?.detail || err.message || '搜索失败')
    searchResults.value = []
    searchPerformed.value = true
  } finally {
    searching.value = false
  }
}

// 高亮搜索结果片段
const highlightSnippet = (snippet: string, query: string): string => {
  if (!query) return snippet
  
  // 简单的高亮：将关键字用 <mark> 标签包裹
  const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
  return snippet.replace(regex, '<mark>$1</mark>')
}

// 跳转到搜索结果
const goToSearchResult = async (hit: NovelSearchHit) => {
  // 切换到对应章节
  await switchChapter(hit.chapter_index)
  
  // 关闭搜索对话框
  showSearchDialog.value = false
  
  // v1 不强求滚到精确句子，只滚动到章节顶部即可
  await nextTick()
  scrollToTop()
}

// 初始化
onMounted(async () => {
  await loadChapters()
})

// 清理
onUnmounted(() => {
  if (progressSaveTimer) {
    clearTimeout(progressSaveTimer)
  }
})
</script>

<style scoped>
.novel-reader-page {
  height: 100vh;
  overflow: hidden;
}

.border-e {
  border-right: 1px solid rgba(var(--v-border-opacity), var(--v-border-opacity));
}

.cursor-pointer {
  cursor: pointer;
}

.novel-content {
  max-width: 800px;
  margin: 0 auto;
}

.novel-content pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
}
</style>
