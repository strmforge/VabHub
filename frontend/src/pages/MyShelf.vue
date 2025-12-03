<template>
  <div class="my-shelf-page">
    <!-- 页面头部 -->
    <v-container>
      <div class="d-flex justify-space-between align-center mb-4">
        <div>
          <h1 class="text-h4 mb-1">我的书架</h1>
          <p class="text-body-2 text-medium-emphasis">快速继续阅读或收听正在进行的小说</p>
        </div>
        <div>
          <v-btn
            variant="outlined"
            prepend-icon="mdi-book-open-variant"
            @click="$router.push({ name: 'NovelCenter' })"
            class="mr-2"
          >
            小说中心
          </v-btn>
          <v-btn
            variant="outlined"
            prepend-icon="mdi-headphones"
            @click="$router.push({ name: 'AudiobookCenter' })"
            class="mr-2"
          >
            有声书中心
          </v-btn>
          <v-btn
            variant="outlined"
            prepend-icon="mdi-heart"
            @click="$router.push({ name: 'ReadingFavoriteShelf' })"
            color="yellow"
          >
            我的收藏
          </v-btn>
        </div>
      </div>

      <!-- 筛选区域 -->
      <v-card class="mb-4">
        <v-card-text>
          <div class="d-flex align-center flex-wrap gap-4">
            <!-- 状态切换 Tab -->
            <v-tabs v-model="activeStatus" @update:model-value="handleStatusChange">
              <v-tab value="active">进行中</v-tab>
              <v-tab value="finished">已完成</v-tab>
              <v-tab value="all">全部</v-tab>
            </v-tabs>

            <!-- 关键字搜索 -->
            <v-text-field
              v-model="filters.keyword"
              placeholder="搜索标题或作者..."
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              hide-details
              style="max-width: 300px;"
              @keyup.enter="loadItems"
              clearable
            />

            <!-- 搜索按钮 -->
            <v-btn
              color="primary"
              prepend-icon="mdi-magnify"
              @click="loadItems"
            >
              搜索
            </v-btn>
          </div>
        </v-card-text>
      </v-card>

      <!-- 加载状态 -->
      <div v-if="loading" class="text-center py-8">
        <v-progress-circular indeterminate color="primary" />
        <p class="text-body-2 text-medium-emphasis mt-2">加载中...</p>
      </div>

      <!-- 空状态 -->
      <v-card v-else-if="items.length === 0" class="text-center py-8">
        <v-card-text>
          <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-bookshelf</v-icon>
          <p class="text-h6 mb-2">暂无作品</p>
          <p class="text-body-2 text-medium-emphasis mb-6">
            {{ activeStatus === 'active' ? '没有进行中的作品，从下面开始添加内容吧' : 
               activeStatus === 'finished' ? '没有已完成的作品，继续努力吧' : 
               '书架还是空的，从下面开始添加内容吧' }}
          </p>
          
          <!-- 快捷入口按钮组 -->
          <div class="d-flex flex-wrap gap-3 justify-center">
            <v-btn
              color="primary"
              prepend-icon="mdi-book-open-variant"
              @click="$router.push({ name: 'NovelCenter' })"
              variant="flat"
            >
              去小说中心看看
            </v-btn>
            <v-btn
              color="info"
              prepend-icon="mdi-headphones"
              @click="$router.push({ name: 'AudiobookCenter' })"
              variant="flat"
            >
              去有声书中心看看
            </v-btn>
            <v-btn
              color="success"
              prepend-icon="mdi-image-multiple"
              @click="$router.push({ name: 'MangaCenter' })"
              variant="flat"
            >
              去漫画中心看看
            </v-btn>
          </div>
          
          <!-- 额外提示 -->
          <p class="text-caption text-medium-emphasis mt-4">
            或者从阅读中心查看更多推荐内容
          </p>
          <v-btn
            variant="text"
            prepend-icon="mdi-view-dashboard"
            @click="$router.push({ name: 'ReadingHubPage' })"
            size="small"
          >
            前往阅读中心
          </v-btn>
        </v-card-text>
      </v-card>

      <!-- 作品列表 -->
      <div v-else>
        <v-row>
          <v-col
            v-for="item in items"
            :key="item.work.ebook_id"
            cols="12"
            md="6"
            lg="4"
          >
            <v-card class="h-100">
              <v-card-text>
                <div class="d-flex">
                  <!-- 左侧：封面占位 -->
                  <div class="mr-4">
                    <v-avatar
                      size="80"
                      rounded="lg"
                      :color="item.work.cover_url ? undefined : 'primary'"
                    >
                      <v-img
                        v-if="item.work.cover_url"
                        :src="item.work.cover_url"
                        cover
                      />
                      <span v-else class="text-h5">
                        {{ item.work.title.charAt(0) }}
                      </span>
                    </v-avatar>
                  </div>

                  <!-- 中间：作品信息 -->
                  <div class="flex-grow-1">
                    <router-link
                      :to="{ name: 'WorkDetail', params: { ebookId: item.work.ebook_id } }"
                      class="text-decoration-none"
                    >
                      <h3 class="text-h6 mb-1 text-primary">{{ item.work.title }}</h3>
                    </router-link>
                    <div v-if="item.work.original_title" class="text-caption text-medium-emphasis mb-1">
                      {{ item.work.original_title }}
                    </div>
                    <div class="text-caption text-medium-emphasis mb-2">
                      <span v-if="item.work.author">{{ item.work.author }}</span>
                      <span v-if="item.work.series" class="ml-2">· {{ item.work.series }}</span>
                    </div>

                    <!-- 最近活动时间 -->
                    <div class="text-caption text-medium-emphasis mb-2">
                      <v-icon size="small" class="mr-1">mdi-clock-outline</v-icon>
                      {{ getLastActivityTime(item) }}
                    </div>

                    <!-- 阅读进度 -->
                    <div class="mb-2">
                      <div class="text-caption text-medium-emphasis mb-1">阅读：</div>
                      <div v-if="!item.reading.has_progress">
                        <v-chip size="x-small" variant="outlined" color="default">
                          未开始阅读
                        </v-chip>
                      </div>
                      <div v-else-if="item.reading.is_finished">
                        <v-chip size="x-small" variant="flat" color="success">
                          已读完
                        </v-chip>
                      </div>
                      <div v-else>
                        <div class="text-body-2 mb-1">
                          已读 {{ item.reading.progress_percent.toFixed(1) }}%
                        </div>
                        <div v-if="item.reading.current_chapter_title" class="text-caption text-medium-emphasis">
                          {{ item.reading.current_chapter_title }}
                        </div>
                      </div>
                    </div>

                    <!-- 听书进度 -->
                    <div class="mb-2">
                      <div class="text-caption text-medium-emphasis mb-1">听书：</div>
                      <div v-if="!item.listening.has_progress">
                        <v-chip size="x-small" variant="outlined" color="default">
                          未开始听书
                        </v-chip>
                      </div>
                      <div v-else-if="item.listening.is_finished">
                        <v-chip size="x-small" variant="flat" color="success">
                          已听完
                        </v-chip>
                      </div>
                      <div v-else>
                        <div class="text-body-2 mb-1">
                          已听 {{ item.listening.progress_percent.toFixed(1) }}%
                        </div>
                        <div v-if="item.listening.current_chapter_title" class="text-caption text-medium-emphasis">
                          {{ item.listening.current_chapter_title }}
                        </div>
                      </div>
                    </div>

                    <!-- TTS 状态 -->
                    <div v-if="item.tts.has_audiobook" class="mb-2">
                      <v-chip
                        v-if="item.tts.has_tts_audiobook"
                        size="x-small"
                        variant="flat"
                        color="primary"
                      >
                        TTS 有声书
                      </v-chip>
                      <v-chip
                        v-else
                        size="x-small"
                        variant="outlined"
                        color="default"
                      >
                        有声书可用
                      </v-chip>
                    </div>
                  </div>
                </div>

                <!-- 操作按钮 -->
                <div class="d-flex gap-2 mt-3">
                  <v-btn
                    :color="item.reading.has_progress ? 'primary' : 'default'"
                    :variant="item.reading.has_progress ? 'flat' : 'outlined'"
                    size="small"
                    prepend-icon="mdi-book-open-page-variant"
                    @click="handleContinueReading(item)"
                    class="flex-grow-1"
                  >
                    {{ item.reading.has_progress ? '继续阅读' : '开始阅读' }}
                  </v-btn>
                  <v-btn
                    v-if="item.listening.has_progress || item.tts.has_audiobook"
                    color="info"
                    variant="flat"
                    size="small"
                    prepend-icon="mdi-headphones"
                    @click="handleContinueListening(item)"
                    class="flex-grow-1"
                  >
                    {{ item.listening.has_progress ? '继续收听' : '开始收听' }}
                  </v-btn>
                  <v-btn
                    v-else-if="item.work.ebook_id"
                    color="secondary"
                    variant="outlined"
                    size="small"
                    prepend-icon="mdi-text-to-speech"
                    @click="handleGenerateTTS(item)"
                    class="flex-grow-1"
                  >
                    生成 TTS
                  </v-btn>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- 分页 -->
        <div class="d-flex justify-center mt-4">
          <v-pagination
            v-model="currentPage"
            :length="totalPages"
            :total-visible="7"
            @update:model-value="handlePageChange"
          />
        </div>
      </div>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { myShelfApi, ttsUserApi } from '@/services/api'
import type { MyShelfItem } from '@/types/novel'

const router = useRouter()
const route = useRoute()

// 状态
const items = ref<MyShelfItem[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

// 筛选
const activeStatus = ref<string>('active')
const filters = ref({
  keyword: ''
})

// 加载数据
const loadItems = async () => {
  loading.value = true
  try {
    const response = await myShelfApi.getList({
      page: currentPage.value,
      page_size: pageSize.value,
      status: activeStatus.value === 'all' ? undefined : activeStatus.value,
      keyword: filters.value.keyword || undefined
    })
    items.value = response.items || []
    total.value = response.total || 0
  } catch (error) {
    console.error('加载我的书架失败:', error)
  } finally {
    loading.value = false
  }
}

// 状态切换
const handleStatusChange = () => {
  currentPage.value = 1
  loadItems()
}

// 分页切换
const handlePageChange = () => {
  loadItems()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// 继续阅读
const handleContinueReading = (item: MyShelfItem) => {
  router.push({
    name: 'NovelReader',
    params: { ebookId: item.work.ebook_id }
  })
}

// 继续收听
const handleContinueListening = (item: MyShelfItem) => {
  router.push({
    name: 'WorkDetail',
    params: { ebookId: item.work.ebook_id },
    query: { tab: 'audiobook' }
  })
}

// 生成 TTS
const handleGenerateTTS = async (item: MyShelfItem) => {
  try {
    await ttsUserApi.enqueueForWork(item.work.ebook_id)
    // 可以显示成功提示
    loadItems() // 刷新列表以更新 TTS 状态
  } catch (error) {
    console.error('生成 TTS 失败:', error)
  }
}

// 获取最近活动时间
const getLastActivityTime = (item: MyShelfItem): string => {
  const times: (string | null)[] = []
  if (item.reading.last_read_at) {
    times.push(item.reading.last_read_at)
  }
  if (item.listening.last_listened_at) {
    times.push(item.listening.last_listened_at)
  }
  
  if (times.length === 0) {
    return '暂无活动'
  }
  
  const maxTime = times
    .filter(t => t !== null)
    .map(t => new Date(t!).getTime())
    .reduce((a, b) => Math.max(a, b), 0)
  
  if (maxTime === 0) {
    return '暂无活动'
  }
  
  const date = new Date(maxTime)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  
  if (diffMins < 1) {
    return '刚刚'
  } else if (diffMins < 60) {
    return `${diffMins} 分钟前`
  } else if (diffHours < 24) {
    return `${diffHours} 小时前`
  } else if (diffDays < 7) {
    return `${diffDays} 天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}

// 初始化
onMounted(() => {
  // 处理来自 ReadingHub 统计卡片的 status 查询参数
  const statusFromQuery = route.query.status as string
  if (statusFromQuery && ['active', 'finished', 'all'].includes(statusFromQuery)) {
    activeStatus.value = statusFromQuery
  }
  
  loadItems()
})
</script>

<style scoped>
.my-shelf-page {
  min-height: 100vh;
  background-color: rgb(var(--v-theme-surface));
}
</style>

