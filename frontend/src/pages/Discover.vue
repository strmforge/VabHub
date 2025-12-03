<template>
  <div class="discover-page">
    <PageHeader
      title="发现"
      subtitle="探索新内容"
    >
      <template #actions>
        <v-btn
          icon="mdi-refresh"
          variant="text"
          @click="refreshData"
          :loading="loading"
        />
      </template>
    </PageHeader>

    <v-container fluid>
      <!-- 数据源选择 -->
      <v-tabs v-model="activeSource" class="mb-4">
        <v-tab value="tmdb">TMDB</v-tab>
        <v-tab value="douban">豆瓣</v-tab>
        <v-tab value="bangumi">Bangumi</v-tab>
      </v-tabs>

      <v-window v-model="activeSource">
        <!-- TMDB探索 -->
        <v-window-item value="tmdb">
          <v-row>
            <v-col cols="12" md="6">
              <v-card class="mb-4">
                <v-card-title>TMDB电影</v-card-title>
                <v-card-text>
                  <v-text-field
                    v-model="tmdbMovieQuery"
                    label="搜索电影"
                    prepend-inner-icon="mdi-magnify"
                    variant="outlined"
                    density="compact"
                    @keyup.enter="searchTMDBMovies"
                    @input="debouncedSearchTMDBMovies"
                  />
                  <v-btn
                    color="primary"
                    @click="searchTMDBMovies"
                    :loading="tmdbMovieLoading"
                    block
                  >
                    搜索
                  </v-btn>
                </v-card-text>
              </v-card>
            </v-col>
            <v-col cols="12" md="6">
              <v-card class="mb-4">
                <v-card-title>TMDB电视剧</v-card-title>
                <v-card-text>
                  <v-text-field
                    v-model="tmdbTVQuery"
                    label="搜索电视剧"
                    prepend-inner-icon="mdi-magnify"
                    variant="outlined"
                    density="compact"
                    @keyup.enter="searchTMDBTV"
                    @input="debouncedSearchTMDBTV"
                  />
                  <v-btn
                    color="primary"
                    @click="searchTMDBTV"
                    :loading="tmdbTVLoading"
                    block
                  >
                    搜索
                  </v-btn>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>

          <!-- TMDB搜索结果 -->
          <v-row v-if="tmdbResults.length > 0">
            <v-col
              v-for="media in tmdbResults"
              :key="media.id"
              cols="6"
              sm="4"
              md="3"
              lg="2"
            >
              <v-card
                class="media-card"
                @click="goToMedia(media.tmdb_id, currentMediaType)"
                style="cursor: pointer"
              >
                <LazyImage
                  :src="getPosterUrl(media.poster_path)"
                  aspect-ratio="2/3"
                  :cover="true"
                />
                <v-card-text class="pa-2">
                  <div class="text-body-2 font-weight-bold text-truncate">
                    {{ media.title }}
                  </div>
                  <div v-if="media.release_date" class="text-caption text-medium-emphasis">
                    {{ getYear(media.release_date) }}
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </v-window-item>

        <!-- 豆瓣探索 -->
        <v-window-item value="douban">
          <v-row>
            <v-col cols="12" md="6">
              <v-card class="mb-4">
                <v-card-title>豆瓣电影</v-card-title>
                <v-card-text>
                  <v-text-field
                    v-model="doubanMovieQuery"
                    label="搜索电影"
                    prepend-inner-icon="mdi-magnify"
                    variant="outlined"
                    density="compact"
                    @keyup.enter="searchDoubanMovies"
                    @input="debouncedSearchDoubanMovies"
                  />
                  <v-btn
                    color="primary"
                    @click="searchDoubanMovies"
                    :loading="doubanMovieLoading"
                    block
                  >
                    搜索
                  </v-btn>
                </v-card-text>
              </v-card>
            </v-col>
            <v-col cols="12" md="6">
              <v-card class="mb-4">
                <v-card-title>豆瓣电视剧</v-card-title>
                <v-card-text>
                  <v-text-field
                    v-model="doubanTVQuery"
                    label="搜索电视剧"
                    prepend-inner-icon="mdi-magnify"
                    variant="outlined"
                    density="compact"
                    @keyup.enter="searchDoubanTV"
                    @input="debouncedSearchDoubanTV"
                  />
                  <v-btn
                    color="primary"
                    @click="searchDoubanTV"
                    :loading="doubanTVLoading"
                    block
                  >
                    搜索
                  </v-btn>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>

          <!-- 豆瓣搜索结果 -->
          <v-row v-if="doubanResults.length > 0">
            <v-col
              v-for="media in doubanResults"
              :key="media.id"
              cols="6"
              sm="4"
              md="3"
              lg="2"
            >
              <v-card
                class="media-card"
                @click="goToDoubanDetail(media.id, currentDoubanType)"
                style="cursor: pointer"
              >
                <LazyImage
                  :src="media.poster || '/placeholder-poster.jpg'"
                  aspect-ratio="2/3"
                  :cover="true"
                />
                <v-card-text class="pa-2">
                  <div class="text-body-2 font-weight-bold text-truncate">
                    {{ media.title }}
                  </div>
                  <div v-if="media.year" class="text-caption text-medium-emphasis">
                    {{ media.year }}
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </v-window-item>

        <!-- Bangumi探索 -->
        <v-window-item value="bangumi">
          <!-- 标签页：搜索、每日放送、热门 -->
          <v-tabs v-model="bangumiActiveTab" class="mb-4">
            <v-tab value="search">搜索</v-tab>
            <v-tab value="calendar">每日放送</v-tab>
            <v-tab value="popular">热门</v-tab>
          </v-tabs>

          <v-window v-model="bangumiActiveTab">
            <!-- 搜索标签页 -->
            <v-window-item value="search">
              <v-card class="mb-4">
                <v-card-title>搜索动漫</v-card-title>
                <v-card-text>
                  <v-text-field
                    v-model="bangumiQuery"
                    label="搜索动漫"
                    prepend-inner-icon="mdi-magnify"
                    variant="outlined"
                    density="compact"
                    @keyup.enter="searchBangumi"
                    class="mb-3"
                  />
                  <v-btn
                    color="primary"
                    @click="searchBangumi"
                    :loading="bangumiLoading"
                    block
                  >
                    搜索
                  </v-btn>
                </v-card-text>
              </v-card>

              <!-- 搜索结果 -->
              <div v-if="bangumiLoading" class="d-flex justify-center py-8">
                <v-progress-circular indeterminate color="primary" />
              </div>
              <v-row v-else-if="bangumiResults.length > 0">
                <v-col
                  v-for="anime in bangumiResults"
                  :key="anime.id"
                  cols="6"
                  sm="4"
                  md="3"
                  lg="2"
                >
                  <v-card
                    class="media-card"
                    @click="openBangumiDetail(anime.id)"
                    style="cursor: pointer"
                  >
                    <LazyImage
                      :src="getBangumiImage(anime.images)"
                      aspect-ratio="2/3"
                      :cover="true"
                    />
                    <v-card-text class="pa-2">
                      <div class="text-body-2 font-weight-bold text-truncate">
                        {{ anime.name_cn || anime.name }}
                      </div>
                      <div v-if="anime.rating && anime.rating.score" class="text-caption text-medium-emphasis">
                        <v-icon size="small" color="warning" class="me-1">mdi-star</v-icon>
                        {{ anime.rating.score }}
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>
              <v-alert v-else-if="bangumiQuery && !bangumiLoading" type="info" variant="tonal">
                未找到相关动漫
              </v-alert>
            </v-window-item>

            <!-- 每日放送标签页 -->
            <v-window-item value="calendar">
              <v-card class="mb-4">
                <v-card-title class="d-flex align-center justify-space-between">
                  <span>每日放送</span>
                  <v-btn
                    color="primary"
                    prepend-icon="mdi-refresh"
                    @click="loadBangumiCalendar"
                    :loading="calendarLoading"
                    size="small"
                  >
                    刷新
                  </v-btn>
                </v-card-title>
                <v-card-text>
                  <div v-if="calendarLoading" class="d-flex justify-center py-8">
                    <v-progress-circular indeterminate color="primary" />
                  </div>
                  <div v-else-if="calendarData.length > 0">
                    <v-expansion-panels variant="accordion">
                      <v-expansion-panel
                        v-for="(dayData, index) in calendarData"
                        :key="index"
                      >
                        <v-expansion-panel-title>
                          <div class="d-flex align-center">
                            <v-icon class="me-2">{{ getDayIcon(dayData.weekday) }}</v-icon>
                            <span class="font-weight-bold">{{ dayData.weekday.cn }}</span>
                            <v-chip size="small" class="ms-2" color="primary" variant="flat">
                              {{ dayData.items.length }} 部
                            </v-chip>
                          </div>
                        </v-expansion-panel-title>
                        <v-expansion-panel-text>
                          <v-row>
                            <v-col
                              v-for="anime in dayData.items"
                              :key="anime.id"
                              cols="6"
                              sm="4"
                              md="3"
                              lg="2"
                            >
                              <v-card
                                class="media-card"
                                @click="openBangumiDetail(anime.id)"
                                style="cursor: pointer"
                              >
                                <v-img
                                  :src="getBangumiImage(anime.images)"
                                  aspect-ratio="2/3"
                                  cover
                                >
                                  <template #placeholder>
                                    <v-skeleton-loader type="image" />
                                  </template>
                                </v-img>
                                <v-card-text class="pa-2">
                                  <div class="text-body-2 font-weight-bold text-truncate">
                                    {{ anime.name_cn || anime.name }}
                                  </div>
                                  <div v-if="anime.rating && anime.rating.score" class="text-caption text-medium-emphasis">
                                    <v-icon size="small" color="warning" class="me-1">mdi-star</v-icon>
                                    {{ anime.rating.score }}
                                  </div>
                                </v-card-text>
                              </v-card>
                            </v-col>
                          </v-row>
                        </v-expansion-panel-text>
                      </v-expansion-panel>
                    </v-expansion-panels>
                  </div>
                  <v-alert v-else type="info" variant="tonal">
                    暂无每日放送数据，请点击刷新按钮加载
                  </v-alert>
                </v-card-text>
              </v-card>
            </v-window-item>

            <!-- 热门标签页 -->
            <v-window-item value="popular">
              <v-card class="mb-4">
                <v-card-title class="d-flex align-center justify-space-between">
                  <span>热门动漫</span>
                  <v-btn
                    color="primary"
                    prepend-icon="mdi-refresh"
                    @click="loadBangumiPopular"
                    :loading="popularLoading"
                    size="small"
                  >
                    刷新
                  </v-btn>
                </v-card-title>
                <v-card-text>
                  <div v-if="popularLoading" class="d-flex justify-center py-8">
                    <v-progress-circular indeterminate color="primary" />
                  </div>
                  <v-row v-else-if="popularResults.length > 0">
                    <v-col
                      v-for="anime in popularResults"
                      :key="anime.id"
                      cols="6"
                      sm="4"
                      md="3"
                      lg="2"
                    >
                      <v-card
                        class="media-card"
                        @click="openBangumiDetail(anime.id)"
                        style="cursor: pointer"
                      >
                        <v-img
                          :src="getBangumiImage(anime.images)"
                          aspect-ratio="2/3"
                          cover
                        >
                          <template #placeholder>
                            <v-skeleton-loader type="image" />
                          </template>
                        </v-img>
                        <v-card-text class="pa-2">
                          <div class="text-body-2 font-weight-bold text-truncate">
                            {{ anime.name_cn || anime.name }}
                          </div>
                          <div v-if="anime.rating && anime.rating.score" class="text-caption text-medium-emphasis">
                            <v-icon size="small" color="warning" class="me-1">mdi-star</v-icon>
                            {{ anime.rating.score }}
                          </div>
                        </v-card-text>
                      </v-card>
                    </v-col>
                  </v-row>
                  <v-alert v-else type="info" variant="tonal">
                    暂无热门动漫数据，请点击刷新按钮加载
                  </v-alert>
                </v-card-text>
              </v-card>
            </v-window-item>
          </v-window>
        </v-window-item>

        <!-- Bangumi详情对话框 -->
        <BangumiDetailDialog
          v-model="bangumiDetailDialog"
          :subject-id="selectedBangumiId"
        />
      </v-window>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import PageHeader from '@/components/common/PageHeader.vue'
import BangumiDetailDialog from '@/components/bangumi/BangumiDetailDialog.vue'
import LazyImage from '@/components/common/LazyImage.vue'
import { mediaApi, doubanApi, bangumiApi } from '@/services/api'
import { debounce } from '@/utils/debounce'

const router = useRouter()
const toast = useToast()

// 状态
const loading = ref(false)
const activeSource = ref('tmdb')

// TMDB搜索
const tmdbMovieQuery = ref('')
const tmdbTVQuery = ref('')
const tmdbMovieLoading = ref(false)
const tmdbTVLoading = ref(false)
const tmdbResults = ref<any[]>([])
const currentMediaType = ref<'movie' | 'tv'>('movie')

// 豆瓣搜索
const doubanMovieQuery = ref('')
const doubanTVQuery = ref('')
const doubanMovieLoading = ref(false)
const doubanTVLoading = ref(false)
const doubanResults = ref<any[]>([])
const currentDoubanType = ref('movie')

// Bangumi搜索
const bangumiQuery = ref('')
const bangumiLoading = ref(false)
const calendarLoading = ref(false)
const popularLoading = ref(false)
const bangumiResults = ref<any[]>([])
const popularResults = ref<any[]>([])
const calendarData = ref<any[]>([])
const bangumiActiveTab = ref('search')
const bangumiDetailDialog = ref(false)
const selectedBangumiId = ref<number | null>(null)

// 搜索TMDB电影
const searchTMDBMovies = async () => {
  if (!tmdbMovieQuery.value.trim()) {
    toast.warning('请输入搜索关键词')
    return
  }
  
  try {
    tmdbMovieLoading.value = true
    currentMediaType.value = 'movie'
    const response = await mediaApi.searchMedia({
      query: tmdbMovieQuery.value,
      type: 'movie'
    })
    tmdbResults.value = response.data || []
  } catch (err: any) {
    toast.error('搜索失败')
  } finally {
    tmdbMovieLoading.value = false
  }
}

// 防抖搜索TMDB电影（500ms延迟）
const debouncedSearchTMDBMovies = debounce(searchTMDBMovies, 500)

// 搜索TMDB电视剧
const searchTMDBTV = async () => {
  if (!tmdbTVQuery.value.trim()) {
    toast.warning('请输入搜索关键词')
    return
  }
  
  try {
    tmdbTVLoading.value = true
    currentMediaType.value = 'tv'
    const response = await mediaApi.searchMedia({
      query: tmdbTVQuery.value,
      type: 'tv'
    })
    tmdbResults.value = response.data || []
  } catch (err: any) {
    toast.error('搜索失败')
  } finally {
    tmdbTVLoading.value = false
  }
}

// 防抖搜索TMDB电视剧（500ms延迟）
const debouncedSearchTMDBTV = debounce(searchTMDBTV, 500)

// 搜索豆瓣电影
const searchDoubanMovies = async () => {
  if (!doubanMovieQuery.value.trim()) {
    toast.warning('请输入搜索关键词')
    return
  }
  
  try {
    doubanMovieLoading.value = true
    currentDoubanType.value = 'movie'
    const response = await doubanApi.searchDouban({
      query: doubanMovieQuery.value,
      media_type: 'movie'
    })
    doubanResults.value = response.data || []
  } catch (err: any) {
    toast.error('搜索失败')
  } finally {
    doubanMovieLoading.value = false
  }
}

// 防抖搜索豆瓣电影（500ms延迟）
const debouncedSearchDoubanMovies = debounce(searchDoubanMovies, 500)

// 搜索豆瓣电视剧
const searchDoubanTV = async () => {
  if (!doubanTVQuery.value.trim()) {
    toast.warning('请输入搜索关键词')
    return
  }
  
  try {
    doubanTVLoading.value = true
    currentDoubanType.value = 'tv'
    const response = await doubanApi.searchDouban({
      query: doubanTVQuery.value,
      media_type: 'tv'
    })
    doubanResults.value = response.data || []
  } catch (err: any) {
    toast.error('搜索失败')
  } finally {
    doubanTVLoading.value = false
  }
}

// 防抖搜索豆瓣电视剧（500ms延迟）
const debouncedSearchDoubanTV = debounce(searchDoubanTV, 500)

// 搜索Bangumi（带防抖）
const searchBangumi = async () => {
  if (!bangumiQuery.value.trim()) {
    toast.warning('请输入搜索关键词')
    return
  }
  
  try {
    bangumiLoading.value = true
    const response = await bangumiApi.searchAnime({
      query: bangumiQuery.value,
      limit: 20
    })
    bangumiResults.value = response.data || []
    if (bangumiResults.value.length === 0) {
      toast.info('未找到相关动漫')
    } else {
      toast.success(`找到 ${bangumiResults.value.length} 部动漫`)
    }
  } catch (err: any) {
    console.error('Bangumi搜索失败:', err)
    toast.error('搜索失败: ' + (err.message || '未知错误'))
  } finally {
    bangumiLoading.value = false
  }
}

// 防抖搜索函数（500ms延迟）
const debouncedSearchBangumi = debounce(searchBangumi, 500)

// 加载Bangumi每日放送
const loadBangumiCalendar = async () => {
  try {
    calendarLoading.value = true
    const response = await bangumiApi.getCalendar()
    const calendarItems = response.data || []
    
    // 按星期分组
    const weekdayMap: { [key: number]: { weekday: any, items: any[] } } = {}
    const weekdays = [
      { id: 0, cn: '星期日', en: 'Sunday' },
      { id: 1, cn: '星期一', en: 'Monday' },
      { id: 2, cn: '星期二', en: 'Tuesday' },
      { id: 3, cn: '星期三', en: 'Wednesday' },
      { id: 4, cn: '星期四', en: 'Thursday' },
      { id: 5, cn: '星期五', en: 'Friday' },
      { id: 6, cn: '星期六', en: 'Saturday' }
    ]
    
    calendarItems.forEach((item: any) => {
      const weekday = item.weekday || 0
      if (!weekdayMap[weekday]) {
        weekdayMap[weekday] = {
          weekday: weekdays[weekday],
          items: []
        }
      }
      weekdayMap[weekday].items.push(item)
    })
    
    // 转换为数组并按星期排序
    calendarData.value = Object.values(weekdayMap).sort((a, b) => a.weekday.id - b.weekday.id)
    
    toast.success(`加载成功，共 ${calendarItems.length} 部动漫`)
  } catch (err: any) {
    console.error('加载Bangumi每日放送失败:', err)
    toast.error('加载失败: ' + (err.message || '未知错误'))
  } finally {
    calendarLoading.value = false
  }
}

// 加载Bangumi热门
const loadBangumiPopular = async () => {
  try {
    popularLoading.value = true
    const response = await bangumiApi.getPopularAnime({ limit: 20 })
    popularResults.value = response.data || []
    toast.success(`加载成功，共 ${popularResults.value.length} 部热门动漫`)
  } catch (err: any) {
    console.error('加载Bangumi热门失败:', err)
    toast.error('加载失败: ' + (err.message || '未知错误'))
  } finally {
    popularLoading.value = false
  }
}

// 跳转到媒体详情
const goToMedia = (tmdbId: number, type: string) => {
  router.push(`/media/${type}/${tmdbId}`)
}

// 跳转到豆瓣详情（暂时显示信息）
const goToDoubanDetail = (subjectId: string, type: string) => {
  toast.info('豆瓣详情页面开发中')
  // TODO: 实现豆瓣详情页面
}

// 打开Bangumi详情对话框
const openBangumiDetail = (subjectId: number) => {
  selectedBangumiId.value = subjectId
  bangumiDetailDialog.value = true
}

// 获取星期图标
const getDayIcon = (weekday: any) => {
  const icons = [
    'mdi-calendar-weekend',
    'mdi-calendar-week-begin',
    'mdi-calendar-week',
    'mdi-calendar-week',
    'mdi-calendar-week',
    'mdi-calendar-week',
    'mdi-calendar-weekend'
  ]
  return icons[weekday?.id || 0] || 'mdi-calendar'
}

// 获取海报URL
const getPosterUrl = (posterPath: string | null) => {
  if (!posterPath) return '/placeholder-poster.jpg'
  if (posterPath.startsWith('http')) return posterPath
  return `https://image.tmdb.org/t/p/w500${posterPath}`
}

// 获取Bangumi图片
const getBangumiImage = (images: any) => {
  if (!images) return '/placeholder-poster.jpg'
  if (images.large) return images.large
  if (images.medium) return images.medium
  if (images.small) return images.small
  return '/placeholder-poster.jpg'
}

// 获取年份
const getYear = (date: string) => {
  if (!date) return ''
  return new Date(date).getFullYear().toString()
}

// 刷新数据
const refreshData = () => {
  tmdbResults.value = []
  doubanResults.value = []
  bangumiResults.value = []
  popularResults.value = []
  calendarData.value = []
  toast.success('已清空搜索结果')
}

// 初始化：自动加载热门动漫
onMounted(() => {
  // 切换到Bangumi标签页时自动加载热门
  // 这里不自动加载，让用户手动点击刷新按钮
})
</script>

<style scoped lang="scss">
.discover-page {
  min-height: 100vh;
}

.media-card {
  transition: transform 0.2s ease;
  
  &:hover {
    transform: translateY(-4px);
  }
}
</style>
