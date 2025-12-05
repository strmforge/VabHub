<template>
  <div class="media-detail-page">
    <!-- 加载状态 -->
    <div v-if="loading" class="d-flex justify-center align-center" style="min-height: 400px">
      <v-progress-circular indeterminate color="primary" size="64" />
    </div>

    <!-- 错误状态 -->
    <v-alert v-else-if="error" type="error" class="ma-4">
      {{ error }}
    </v-alert>

    <!-- 媒体详情 -->
    <div v-else-if="mediaDetails">
      <!-- 背景图 -->
      <div
        v-if="mediaDetails.backdrop"
        class="media-backdrop"
        :style="{ backgroundImage: `url(${mediaDetails.backdrop})` }"
      />

      <v-container fluid class="media-content">
        <!-- 头部信息 -->
        <v-row class="mb-6">
          <v-col cols="12" md="3">
            <!-- 海报 -->
            <v-card class="media-poster-card" elevation="4">
              <LazyImage
                :src="mediaDetails.poster || '/placeholder-poster.jpg'"
                aspect-ratio="2/3"
                :cover="true"
                image-class="media-poster"
              />
            </v-card>
          </v-col>

          <v-col cols="12" md="9">
            <!-- 标题和基本信息 -->
            <div class="media-header">
              <h1 class="text-h3 font-weight-bold mb-2">
                {{ mediaDetails.title }}
              </h1>
              <div v-if="mediaDetails.original_title && mediaDetails.original_title !== mediaDetails.title" class="text-h6 text-medium-emphasis mb-4">
                {{ mediaDetails.original_title }}
              </div>

              <!-- 元信息 -->
              <div class="d-flex flex-wrap align-center gap-4 mb-4">
                <div v-if="mediaDetails.vote_average" class="d-flex align-center">
                  <v-icon color="warning" class="me-1">mdi-star</v-icon>
                  <span class="text-h6">{{ mediaDetails.vote_average.toFixed(1) }}</span>
                </div>
                <div v-if="mediaDetails.year" class="text-body-1">
                  {{ mediaDetails.year }}
                </div>
                <div v-if="mediaDetails.runtime" class="text-body-1">
                  {{ formatRuntime(mediaDetails.runtime) }}
                </div>
                <div v-if="mediaDetails.genres && mediaDetails.genres.length > 0" class="d-flex flex-wrap gap-2">
                  <v-chip
                    v-for="genre in mediaDetails.genres"
                    :key="genre"
                    size="small"
                    variant="outlined"
                  >
                    {{ genre }}
                  </v-chip>
                </div>
              </div>

              <!-- 操作按钮 -->
              <v-row class="mt-4" justify="start" align="center" wrap="wrap" gap="2">
                <!-- 网页播放（115） -->
                <v-btn
                  v-if="has115"
                  color="primary"
                  prepend-icon="mdi-play-circle"
                  @click="goRemote115Player"
                  class="mb-2"
                >
                  网页播放（115）
                </v-btn>

                <!-- 在媒体库中播放（Emby / Jellyfin） -->
                <v-btn
                  v-if="hasLocal"
                  color="secondary"
                  variant="outlined"
                  prepend-icon="mdi-television-play"
                  @click="openInMediaLibrary"
                  class="mb-2"
                >
                  在媒体库中播放
                </v-btn>

                <!-- 其他操作按钮 -->
                <v-btn
                  color="primary"
                  variant="text"
                  prepend-icon="mdi-bookmark-plus"
                  @click="handleSubscribe"
                  :loading="subscribing"
                  class="mb-2"
                >
                  订阅
                </v-btn>
                <v-btn
                  variant="text"
                  prepend-icon="mdi-share-variant"
                  @click="handleShare"
                  class="mb-2"
                >
                  分享
                </v-btn>
              </v-row>

              <!-- 简介 -->
              <div v-if="mediaDetails.overview" class="text-body-1">
                <p class="text-medium-emphasis">{{ mediaDetails.overview }}</p>
              </div>
            </div>
          </v-col>
        </v-row>

        <!-- 标签页 -->
        <v-tabs v-model="activeTab" class="mb-4">
          <v-tab value="overview">概览</v-tab>
          <v-tab value="credits">演职员</v-tab>
          <v-tab v-if="mediaType === 'tv'" value="seasons">季信息</v-tab>
          <v-tab value="similar">类似推荐</v-tab>
          <v-tab value="recommendations">推荐内容</v-tab>
        </v-tabs>

        <v-window v-model="activeTab">
          <!-- 概览 -->
          <v-window-item value="overview">
            <v-row>
              <v-col cols="12" md="8">
                <v-card>
                  <v-card-title>详细信息</v-card-title>
                  <v-card-text>
                    <v-list>
                      <v-list-item v-if="mediaDetails.imdb_id">
                        <v-list-item-title>IMDB ID</v-list-item-title>
                        <v-list-item-subtitle>{{ mediaDetails.imdb_id }}</v-list-item-subtitle>
                      </v-list-item>
                      <v-list-item v-if="mediaDetails.tvdb_id">
                        <v-list-item-title>TVDB ID</v-list-item-title>
                        <v-list-item-subtitle>{{ mediaDetails.tvdb_id }}</v-list-item-subtitle>
                      </v-list-item>
                      <v-list-item v-if="mediaDetails.release_date">
                        <v-list-item-title>发布日期</v-list-item-title>
                        <v-list-item-subtitle>{{ formatDate(mediaDetails.release_date) }}</v-list-item-subtitle>
                      </v-list-item>
                    </v-list>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-window-item>

          <!-- 演职员 -->
          <v-window-item value="credits">
            <div v-if="creditsLoading" class="d-flex justify-center py-8">
              <v-progress-circular indeterminate color="primary" />
            </div>
            <div v-else-if="credits">
              <!-- 演员 -->
              <v-card class="mb-4">
                <v-card-title>演员</v-card-title>
                <v-card-text>
                  <v-row>
                    <v-col
                      v-for="actor in credits.cast"
                      :key="actor.id"
                      cols="6"
                      sm="4"
                      md="3"
                      lg="2"
                    >
                      <v-card
                        class="actor-card"
                        @click="goToPerson(actor.id)"
                        style="cursor: pointer"
                      >
                        <LazyImage
                          :src="actor.profile_path || '/placeholder-person.jpg'"
                          aspect-ratio="2/3"
                          :cover="true"
                        />
                        <v-card-text class="pa-2">
                          <div class="text-body-2 font-weight-bold text-truncate">
                            {{ actor.name }}
                          </div>
                          <div class="text-caption text-medium-emphasis text-truncate">
                            {{ actor.character }}
                          </div>
                        </v-card-text>
                      </v-card>
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>

              <!-- 工作人员 -->
              <v-card
                v-for="(members, dept) in credits.crew"
                :key="dept"
                class="mb-4"
              >
                <v-card-title>{{ dept }}</v-card-title>
                <v-card-text>
                  <v-list>
                    <v-list-item
                      v-for="member in members"
                      :key="member.id"
                      @click="goToPerson(member.id)"
                      style="cursor: pointer"
                    >
                      <template #prepend>
                        <v-avatar size="40" class="me-3">
                          <v-img
                            :src="member.profile_path || '/placeholder-person.jpg'"
                            cover
                          >
                            <template #placeholder>
                              <v-skeleton-loader type="avatar" />
                            </template>
                          </v-img>
                        </v-avatar>
                      </template>
                      <v-list-item-title>{{ member.name }}</v-list-item-title>
                      <v-list-item-subtitle>{{ member.job }}</v-list-item-subtitle>
                    </v-list-item>
                  </v-list>
                </v-card-text>
              </v-card>
            </div>
          </v-window-item>

          <!-- 季信息（仅电视剧） -->
          <v-window-item v-if="mediaType === 'tv'" value="seasons">
            <div v-if="seasonsLoading" class="d-flex justify-center py-8">
              <v-progress-circular indeterminate color="primary" />
            </div>
            <v-row v-else-if="seasons">
              <v-col
                v-for="season in seasons"
                :key="season.season_number"
                cols="12"
                sm="6"
                md="4"
                lg="3"
              >
                <v-card>
                  <LazyImage
                    v-if="season.poster_path"
                    :src="`https://image.tmdb.org/t/p/w500${season.poster_path}`"
                    aspect-ratio="2/3"
                    :cover="true"
                  />
                  <v-card-title>
                    第 {{ season.season_number }} 季
                    <span v-if="season.name && season.name !== `Season ${season.season_number}`">
                      - {{ season.name }}
                    </span>
                  </v-card-title>
                  <v-card-text>
                    <div v-if="season.episode_count" class="text-body-2 mb-2">
                      {{ season.episode_count }} 集
                    </div>
                    <div v-if="season.air_date" class="text-caption text-medium-emphasis">
                      {{ formatDate(season.air_date) }}
                    </div>
                    <div v-if="season.overview" class="text-body-2 mt-2">
                      {{ season.overview }}
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-window-item>

          <!-- 类似推荐 -->
          <v-window-item value="similar">
            <div v-if="similarLoading" class="d-flex justify-center py-8">
              <v-progress-circular indeterminate color="primary" />
            </div>
            <v-row v-else-if="similarMedia && similarMedia.length > 0">
              <v-col
                v-for="media in similarMedia"
                :key="media.id"
                cols="6"
                sm="4"
                md="3"
                lg="2"
              >
                <v-card
                  class="media-card"
                  @click="goToMedia(media.tmdb_id, mediaType)"
                  style="cursor: pointer"
                >
                  <LazyImage
                    :src="media.poster_path || '/placeholder-poster.jpg'"
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
            <v-alert v-else type="info">暂无类似推荐</v-alert>
          </v-window-item>

          <!-- 推荐内容 -->
          <v-window-item value="recommendations">
            <div v-if="recommendationsLoading" class="d-flex justify-center py-8">
              <v-progress-circular indeterminate color="primary" />
            </div>
            <v-row v-else-if="recommendedMedia && recommendedMedia.length > 0">
              <v-col
                v-for="media in recommendedMedia"
                :key="media.id"
                cols="6"
                sm="4"
                md="3"
                lg="2"
              >
                <v-card
                  class="media-card"
                  @click="goToMedia(media.tmdb_id, mediaType)"
                  style="cursor: pointer"
                >
                  <LazyImage
                    :src="media.poster_path || '/placeholder-poster.jpg'"
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
            <v-alert v-else type="info">暂无推荐内容</v-alert>
          </v-window-item>
        </v-window>
      </v-container>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import { mediaApi, playerWallApi } from '@/services/api'
import { useMediaPlayActions } from '@/composables/useMediaPlayActions'
import LazyImage from '@/components/common/LazyImage.vue'

const route = useRoute()
const router = useRouter()
const toast = useToast()
const { play } = useMediaPlayActions()

// 路由参数
const tmdbId = computed(() => parseInt(route.params.tmdbId as string))
const mediaType = computed(() => (route.params.type as string) || 'movie')

// 状态
const loading = ref(true)
const error = ref<string | null>(null)
const mediaDetails = ref<any>(null)
const credits = ref<any>(null)
const creditsLoading = ref(false)
const seasons = ref<any[]>([])
const seasonsLoading = ref(false)
const similarMedia = ref<any[]>([])
const similarLoading = ref(false)
const recommendedMedia = ref<any[]>([])
const recommendationsLoading = ref(false)
const subscribing = ref(false)

// 源信息
const sourceInfo = ref<{ has_local: boolean; has_115: boolean; workId?: number } | null>(null)
const sourceInfoLoading = ref(false)

// 标签页
const activeTab = ref('overview')

// 计算属性
const hasLocal = computed(() => !!sourceInfo.value?.has_local)
const has115 = computed(() => !!sourceInfo.value?.has_115)
const workId = computed(() => {
  // 优先使用 sourceInfo 中的 workId，否则使用 mediaDetails 中的 id
  return sourceInfo.value?.workId || mediaDetails.value?.id || null
})

// 加载媒体详情
const loadMediaDetails = async () => {
  try {
    loading.value = true
    error.value = null
    
    // 并行加载主要数据、季信息（如果是电视剧）、演职员表、类似推荐、推荐内容
    const promises: Promise<any>[] = [
      mediaApi.getMediaDetails(tmdbId.value, mediaType.value as 'movie' | 'tv'),
      mediaApi.getMediaCredits(tmdbId.value, mediaType.value as 'movie' | 'tv').catch(() => null), // 允许失败
      mediaApi.getSimilarMedia(tmdbId.value, mediaType.value as 'movie' | 'tv').catch(() => null), // 允许失败
      mediaApi.getRecommendedMedia(tmdbId.value, mediaType.value as 'movie' | 'tv').catch(() => null) // 允许失败
    ]
    
    if (mediaType.value === 'tv') {
      promises.push(mediaApi.getTVSeasons(tmdbId.value).catch(() => null)) // 允许失败
    }
    
    const results = await Promise.allSettled(promises)
    
    // 处理主要数据
    if (results[0].status === 'fulfilled') {
      mediaDetails.value = results[0].value.data
    } else {
      throw results[0].reason
    }
    
    // 处理演职员表（索引1）
    if (results[1]?.status === 'fulfilled' && results[1].value?.data) {
      credits.value = results[1].value.data
      creditsLoading.value = false
    } else if (results[1]?.status === 'rejected') {
      console.warn('加载演职员表失败:', results[1].reason)
      credits.value = null
      creditsLoading.value = false
    }
    
    // 处理类似推荐（索引2）
    if (results[2]?.status === 'fulfilled' && results[2].value?.data) {
      similarMedia.value = results[2].value.data || []
      similarLoading.value = false
    } else if (results[2]?.status === 'rejected') {
      console.warn('加载类似推荐失败:', results[2].reason)
      similarMedia.value = []
      similarLoading.value = false
    }
    
    // 处理推荐内容（索引3）
    if (results[3]?.status === 'fulfilled' && results[3].value?.data) {
      recommendedMedia.value = results[3].value.data || []
      recommendationsLoading.value = false
    } else if (results[3]?.status === 'rejected') {
      console.warn('加载推荐内容失败:', results[3].reason)
      recommendedMedia.value = []
      recommendationsLoading.value = false
    }
    
    // 加载源信息
    await loadSourceInfo()
    
    // 处理季信息（如果是电视剧，索引4）
    if (mediaType.value === 'tv') {
      const seasonIndex = 4
      if (results[seasonIndex]?.status === 'fulfilled' && results[seasonIndex].value?.data) {
        seasons.value = results[seasonIndex].value.data || []
        seasonsLoading.value = false
      } else if (results[seasonIndex]?.status === 'rejected') {
        const errMsg = results[seasonIndex].reason.message || '加载季信息失败'
        console.warn('加载季信息失败:', errMsg)
        seasons.value = []
        seasonsLoading.value = false
      }
    }
  } catch (err: any) {
    const errMsg = err.message || '加载媒体详情失败'
    error.value = errMsg
    toast.error(errMsg)
    console.error('加载媒体详情失败:', err)
  } finally {
    loading.value = false
  }
}

// 加载演职员表（如果未在初始加载中获取）
const loadCredits = async () => {
  if (credits.value !== null) return // 已加载或已尝试加载
  
  try {
    creditsLoading.value = true
    const response = await mediaApi.getMediaCredits(tmdbId.value, mediaType.value as 'movie' | 'tv')
    credits.value = response.data
  } catch (err: any) {
    console.error('加载演职员表失败:', err)
    toast.error('加载演职员表失败: ' + (err.message || '未知错误'))
    credits.value = null // 设置为null以便重试
  } finally {
    creditsLoading.value = false
  }
}

// 加载季信息（已集成到loadMediaDetails中，此函数保留用于单独调用）
const loadSeasons = async () => {
  if (seasons.value && seasons.value.length > 0) return // 已加载
  
  try {
    seasonsLoading.value = true
    const response = await mediaApi.getTVSeasons(tmdbId.value)
    seasons.value = response.data || []
  } catch (err: any) {
    console.error('加载季信息失败:', err)
    toast.error('加载季信息失败: ' + (err.message || '未知错误'))
  } finally {
    seasonsLoading.value = false
  }
}

// 加载类似媒体
const loadSimilar = async () => {
  if (similarMedia.value.length > 0) return // 已加载
  
  try {
    similarLoading.value = true
    const response = await mediaApi.getSimilarMedia(tmdbId.value, mediaType.value as 'movie' | 'tv')
    similarMedia.value = response.data || []
  } catch (err: any) {
    console.error('加载类似推荐失败:', err)
    toast.error('加载类似推荐失败: ' + (err.message || '未知错误'))
    similarMedia.value = [] // 设置为空数组以便重试
  } finally {
    similarLoading.value = false
  }
}

// 加载推荐内容
const loadRecommendations = async () => {
  if (recommendedMedia.value.length > 0) return // 已加载
  
  try {
    recommendationsLoading.value = true
    const response = await mediaApi.getRecommendedMedia(tmdbId.value, mediaType.value as 'movie' | 'tv')
    recommendedMedia.value = response.data || []
  } catch (err: any) {
    console.error('加载推荐内容失败:', err)
    toast.error('加载推荐内容失败: ' + (err.message || '未知错误'))
    recommendedMedia.value = [] // 设置为空数组以便重试
  } finally {
    recommendationsLoading.value = false
  }
}

// 标签页切换（数据已在初始加载中获取，这里只处理未成功加载的情况）
watch(activeTab, (newTab) => {
  if (newTab === 'credits' && credits.value === null && !creditsLoading.value) {
    loadCredits()
  } else if (newTab === 'similar' && similarMedia.value.length === 0 && !similarLoading.value) {
    loadSimilar()
  } else if (newTab === 'recommendations' && recommendedMedia.value.length === 0 && !recommendationsLoading.value) {
    loadRecommendations()
  }
})

// 订阅
const handleSubscribe = async () => {
  if (!mediaDetails.value) return
  
  try {
    subscribing.value = true
    // 跳转到订阅页面，并预填充媒体信息
    router.push({
      name: 'Subscriptions',
      query: {
        action: 'create',
        tmdb_id: mediaDetails.value.tmdb_id,
        media_type: mediaType.value,
        title: mediaDetails.value.title
      }
    })
  } catch (err: any) {
    toast.error('订阅失败')
  } finally {
    subscribing.value = false
  }
}

// 跳转到 115 播放页面（使用统一播放逻辑）
const goRemote115Player = () => {
  if (!workId.value) {
    toast.error('无法获取作品 ID')
    return
  }
  
  // 使用统一的播放逻辑，优先选择115源
  play({
    workId: workId.value,
    source: {
      has_local: hasLocal.value,
      has_115: has115.value
    },
    preferredSource: '115' // 明确指定使用115源
  })
}

// 在媒体库中播放
const openInMediaLibrary = () => {
  // TODO: 实现跳转到 Emby/Jellyfin 的逻辑
  // 例如：window.open(detail.value.embyPlayUrl, '_blank')
  toast.info('媒体库播放功能开发中')
}

// 加载源信息
const loadSourceInfo = async () => {
  if (!tmdbId.value || !mediaDetails.value) return
  
  try {
    sourceInfoLoading.value = true
    // 从电视墙 API 获取源信息（通过 tmdb_id 或标题匹配）
    const response = await playerWallApi.getList({
      page: 1,
      page_size: 100,
      keyword: mediaDetails.value.title,
      media_type: mediaType.value
    })
    
    // 尝试通过标题和年份匹配
    const item = response.items?.find(i => {
      const work = i.work
      const titleMatch = work.title === mediaDetails.value?.title || 
                        work.title === mediaDetails.value?.original_title
      const yearMatch = !work.year || !mediaDetails.value?.year || 
                       work.year === parseInt(mediaDetails.value.year)
      return titleMatch && yearMatch
    })
    
    if (item) {
      sourceInfo.value = {
        ...item.source,
        workId: item.work.id
      }
    } else {
      // 如果没有找到，默认设置为 false
      sourceInfo.value = { has_local: false, has_115: false }
    }
  } catch (err: any) {
    console.error('加载源信息失败:', err)
    // 失败时默认设置为 false
    sourceInfo.value = { has_local: false, has_115: false }
  } finally {
    sourceInfoLoading.value = false
  }
}

// 分享
const handleShare = () => {
  // TODO: 实现分享功能
  if (navigator.share) {
    navigator.share({
      title: mediaDetails.value?.title,
      text: mediaDetails.value?.overview,
      url: window.location.href
    })
  } else {
    // 复制链接
    navigator.clipboard.writeText(window.location.href)
    toast.success('链接已复制到剪贴板')
  }
}

// 跳转到人物详情
const goToPerson = (personId: number) => {
  router.push(`/person/${personId}`)
}

// 跳转到媒体详情
const goToMedia = (id: number, type: string) => {
  router.push(`/media/${type}/${id}`)
}

// 格式化运行时间
const formatRuntime = (minutes: number) => {
  if (!minutes) return ''
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  if (hours > 0) {
    return `${hours}小时${mins}分钟`
  }
  return `${mins}分钟`
}

// 格式化日期
const formatDate = (date: string) => {
  if (!date) return ''
  return new Date(date).toLocaleDateString('zh-CN')
}

// 获取年份
const getYear = (date: string) => {
  if (!date) return ''
  return new Date(date).getFullYear().toString()
}

// 初始化
onMounted(() => {
  loadMediaDetails()
})
</script>

<style scoped lang="scss">
.media-detail-page {
  position: relative;
  min-height: 100vh;
}

.media-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  filter: blur(20px);
  opacity: 0.3;
  z-index: 0;
  pointer-events: none;
}

.media-content {
  position: relative;
  z-index: 1;
  background: rgba(var(--v-theme-surface), 0.95);
  backdrop-filter: blur(10px);
}

.media-poster-card {
  position: sticky;
  top: 20px;
}

.media-poster {
  border-radius: 8px;
}

.media-header {
  color: rgb(var(--v-theme-on-surface));
}

.actor-card,
.media-card {
  transition: transform 0.2s ease;
  
  &:hover {
    transform: translateY(-4px);
  }
}
</style>

