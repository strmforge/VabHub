<template>
  <div class="music-center-page">
    <v-container>
      <PageHeader
        title="音乐库"
        subtitle="浏览和播放本地音乐"
      />

      <!-- 统计卡片 -->
      <v-row class="mb-4">
        <v-col cols="6" md="3">
          <v-card variant="outlined">
            <v-card-text class="text-center">
              <div class="text-h5 font-weight-bold text-primary">{{ stats.total_artists }}</div>
              <div class="text-caption text-medium-emphasis">艺术家</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="6" md="3">
          <v-card variant="outlined">
            <v-card-text class="text-center">
              <div class="text-h5 font-weight-bold text-info">{{ stats.total_albums }}</div>
              <div class="text-caption text-medium-emphasis">专辑</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="6" md="3">
          <v-card variant="outlined">
            <v-card-text class="text-center">
              <div class="text-h5 font-weight-bold text-success">{{ stats.total_tracks }}</div>
              <div class="text-caption text-medium-emphasis">曲目</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="6" md="3">
          <v-card variant="outlined">
            <v-card-text class="text-center">
              <div class="text-h5 font-weight-bold text-warning">{{ formatSize(stats.total_size_mb) }}</div>
              <div class="text-caption text-medium-emphasis">总大小</div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- 主标签页 -->
      <v-card>
        <v-tabs v-model="mainTab" color="primary">
          <v-tab value="library">
            <v-icon start>mdi-music-box-multiple</v-icon>
            我的音乐
          </v-tab>
          <v-tab value="charts">
            <v-icon start>mdi-chart-line</v-icon>
            榜单 & 订阅
          </v-tab>
          <v-tab value="tasks">
            <v-icon start>mdi-download</v-icon>
            音乐任务
          </v-tab>
        </v-tabs>

        <v-divider />

        <v-window v-model="mainTab">
          <!-- 我的音乐 Tab -->
          <v-window-item value="library">
            <v-tabs v-model="activeTab" color="secondary" class="px-4 pt-2">
              <v-tab value="albums">
                <v-icon start size="small">mdi-album</v-icon>
                专辑
              </v-tab>
              <v-tab value="artists">
                <v-icon start size="small">mdi-account-music</v-icon>
                艺术家
              </v-tab>
              <v-tab value="tracks">
                <v-icon start size="small">mdi-music-note</v-icon>
                曲目
              </v-tab>
            </v-tabs>

        <v-divider />

        <!-- 搜索栏 -->
        <v-card-text class="pb-0">
          <v-text-field
            v-model="keyword"
            label="搜索"
            density="compact"
            variant="outlined"
            clearable
            prepend-inner-icon="mdi-magnify"
            @keyup.enter="handleSearch"
            @click:clear="handleClear"
          />
        </v-card-text>

        <v-window v-model="activeTab">
          <!-- 专辑列表 -->
          <v-window-item value="albums">
            <v-card-text>
              <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-4" />
              
              <v-row v-if="!loading && albums.length > 0">
                <v-col
                  v-for="album in albums"
                  :key="album.id"
                  cols="6"
                  sm="4"
                  md="3"
                  lg="2"
                >
                  <v-card
                    variant="outlined"
                    class="album-card"
                    @click="openAlbum(album.id)"
                  >
                    <v-img
                      :src="album.cover_url || '/placeholder-album.png'"
                      aspect-ratio="1"
                      cover
                      class="album-cover"
                    >
                      <template v-slot:placeholder>
                        <div class="d-flex align-center justify-center fill-height bg-grey-lighten-3">
                          <v-icon size="48" color="grey">mdi-album</v-icon>
                        </div>
                      </template>
                    </v-img>
                    <v-card-text class="pa-2">
                      <div class="text-subtitle-2 text-truncate">{{ album.title }}</div>
                      <div class="text-caption text-medium-emphasis text-truncate">{{ album.artist_name }}</div>
                      <div class="text-caption text-medium-emphasis">
                        {{ album.track_count }} 首 · {{ album.year || '未知年份' }}
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>

              <div v-if="!loading && albums.length === 0" class="text-center py-8 text-medium-emphasis">
                暂无专辑
              </div>

              <!-- 分页 -->
              <div v-if="totalPages > 1" class="d-flex justify-center mt-4">
                <v-pagination
                  v-model="page"
                  :length="totalPages"
                  :total-visible="7"
                  @update:model-value="loadAlbums"
                />
              </div>
            </v-card-text>
          </v-window-item>

          <!-- 艺术家列表 -->
          <v-window-item value="artists">
            <v-card-text>
              <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-4" />
              
              <v-list v-if="!loading && artists.length > 0">
                <v-list-item
                  v-for="artist in artists"
                  :key="artist.id"
                  @click="filterByArtist(artist.name)"
                >
                  <template v-slot:prepend>
                    <v-avatar color="primary" size="40">
                      <v-icon>mdi-account-music</v-icon>
                    </v-avatar>
                  </template>
                  <v-list-item-title>{{ artist.name }}</v-list-item-title>
                  <v-list-item-subtitle>
                    {{ artist.album_count }} 张专辑 · {{ artist.track_count }} 首曲目
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>

              <div v-if="!loading && artists.length === 0" class="text-center py-8 text-medium-emphasis">
                暂无艺术家
              </div>

              <!-- 分页 -->
              <div v-if="artistTotalPages > 1" class="d-flex justify-center mt-4">
                <v-pagination
                  v-model="artistPage"
                  :length="artistTotalPages"
                  :total-visible="7"
                  @update:model-value="loadArtists"
                />
              </div>
            </v-card-text>
          </v-window-item>

          <!-- 曲目列表 -->
          <v-window-item value="tracks">
            <v-card-text>
              <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-4" />
              
              <v-data-table
                v-if="!loading"
                :headers="trackHeaders"
                :items="tracks"
                :items-per-page="20"
                class="elevation-0"
                no-data-text="暂无曲目"
              >
                <template v-slot:item.title="{ item }">
                  <div class="d-flex align-center">
                    <v-btn
                      icon
                      size="small"
                      variant="text"
                      color="primary"
                      @click.stop="playTrack(item)"
                      :disabled="!item.file_id"
                    >
                      <v-icon>mdi-play</v-icon>
                    </v-btn>
                    <span class="ml-2">{{ item.title }}</span>
                  </div>
                </template>
                <template v-slot:item.duration_seconds="{ item }">
                  {{ formatDuration(item.duration_seconds) }}
                </template>
                <template v-slot:item.bitrate_kbps="{ item }">
                  <v-chip v-if="item.bitrate_kbps" size="x-small" variant="outlined">
                    {{ item.bitrate_kbps }} kbps
                  </v-chip>
                </template>
              </v-data-table>

              <!-- 分页 -->
              <div v-if="trackTotalPages > 1" class="d-flex justify-center mt-4">
                <v-pagination
                  v-model="trackPage"
                  :length="trackTotalPages"
                  :total-visible="7"
                  @update:model-value="loadTracks"
                />
              </div>
            </v-card-text>
          </v-window-item>
        </v-window>
          </v-window-item>

          <!-- 榜单 & 订阅 Tab -->
          <v-window-item value="charts">
            <v-card-text>
              <v-row>
                <!-- 左侧：榜单选择 -->
                <v-col cols="12" md="4">
                  <v-card variant="outlined" class="mb-4">
                    <v-card-title class="text-subtitle-1">
                      <v-icon start>mdi-playlist-music</v-icon>
                      选择榜单
                    </v-card-title>
                    <v-card-text>
                      <v-select
                        v-model="selectedChartId"
                        :items="charts"
                        item-title="display_name"
                        item-value="id"
                        label="榜单"
                        density="compact"
                        variant="outlined"
                        :loading="chartsLoading"
                        @update:model-value="loadChartItems"
                      />
                    </v-card-text>
                  </v-card>

                  <!-- 我的订阅 -->
                  <v-card variant="outlined">
                    <v-card-title class="text-subtitle-1">
                      <v-icon start>mdi-bell-ring</v-icon>
                      我的订阅
                    </v-card-title>
                    <v-card-text class="pa-0">
                      <v-list v-if="subscriptions.length > 0" density="compact">
                        <v-list-item
                          v-for="sub in subscriptions"
                          :key="sub.id"
                        >
                          <v-list-item-title>{{ sub.chart_display_name }}</v-list-item-title>
                          <v-list-item-subtitle>
                            <v-chip size="x-small" :color="sub.status === 'active' ? 'success' : 'grey'" class="mr-1">
                              {{ sub.status === 'active' ? '活跃' : '暂停' }}
                            </v-chip>
                            <span v-if="sub.last_run_at" class="text-caption">
                              上次: {{ formatDate(sub.last_run_at) }}
                            </span>
                          </v-list-item-subtitle>
                          <template v-slot:append>
                            <v-btn
                              icon
                              size="x-small"
                              variant="text"
                              @click="runSubscriptionOnce(sub.id)"
                              :loading="runningSubscriptionId === sub.id"
                            >
                              <v-icon>mdi-play</v-icon>
                            </v-btn>
                            <v-btn
                              icon
                              size="x-small"
                              variant="text"
                              @click="toggleSubscription(sub)"
                            >
                              <v-icon>{{ sub.status === 'active' ? 'mdi-pause' : 'mdi-play-circle' }}</v-icon>
                            </v-btn>
                          </template>
                        </v-list-item>
                      </v-list>
                      <div v-else class="text-center py-4 text-medium-emphasis">
                        暂无订阅
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>

                <!-- 右侧：榜单条目 -->
                <v-col cols="12" md="8">
                  <v-card variant="outlined">
                    <v-card-title class="d-flex align-center">
                      <span>榜单曲目</span>
                      <v-spacer />
                      <v-btn
                        v-if="selectedChartId && !isChartSubscribed"
                        size="small"
                        color="primary"
                        variant="tonal"
                        @click="subscribeChart"
                      >
                        <v-icon start>mdi-bell-plus</v-icon>
                        订阅此榜单
                      </v-btn>
                      <v-chip v-else-if="isChartSubscribed" color="success" size="small">
                        <v-icon start>mdi-check</v-icon>
                        已订阅
                      </v-chip>
                    </v-card-title>
                    <v-card-text class="pa-0">
                      <v-progress-linear v-if="chartItemsLoading" indeterminate color="primary" />
                      <v-data-table
                        v-if="!chartItemsLoading"
                        :headers="chartItemHeaders"
                        :items="chartItems"
                        :items-per-page="20"
                        class="elevation-0"
                        no-data-text="请选择榜单"
                      >
                        <template v-slot:item.rank="{ item }">
                          <v-chip size="small" :color="item.rank && item.rank <= 3 ? 'warning' : 'default'">
                            {{ item.rank || '-' }}
                          </v-chip>
                        </template>
                        <template v-slot:item.duration_seconds="{ item }">
                          {{ formatDuration(item.duration_seconds) }}
                        </template>
                      </v-data-table>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>
            </v-card-text>
          </v-window-item>

          <!-- 音乐任务 Tab -->
          <v-window-item value="tasks">
            <v-card-text>
              <!-- 状态筛选 -->
              <div class="d-flex align-center mb-4 flex-wrap ga-2">
                <v-chip-group v-model="jobStatusFilter" multiple>
                  <v-chip filter value="pending" size="small">等待中</v-chip>
                  <v-chip filter value="searching" size="small">搜索中</v-chip>
                  <v-chip filter value="found" size="small">已找到</v-chip>
                  <v-chip filter value="downloading" size="small">下载中</v-chip>
                  <v-chip filter value="completed" size="small" color="success">已完成</v-chip>
                  <v-chip filter value="failed" size="small" color="error">失败</v-chip>
                </v-chip-group>
                <v-spacer />
                <v-btn
                  variant="text"
                  size="small"
                  @click="loadDownloadJobs"
                  :loading="jobsLoading"
                >
                  <v-icon start>mdi-refresh</v-icon>
                  刷新
                </v-btn>
              </div>

              <v-progress-linear v-if="jobsLoading" indeterminate color="primary" class="mb-4" />
              <v-data-table
                v-if="!jobsLoading"
                :headers="jobHeaders"
                :items="filteredDownloadJobs"
                :items-per-page="20"
                class="elevation-0"
                no-data-text="暂无任务"
              >
                <template v-slot:item.search_query="{ item }">
                  <div>
                    <div class="font-weight-medium">{{ item.chart_item_title || item.search_query }}</div>
                    <div class="text-caption text-grey">{{ item.chart_item_artist }}</div>
                  </div>
                </template>
                <template v-slot:item.status="{ item }">
                  <v-chip
                    size="small"
                    :color="getJobStatusColor(item.status)"
                  >
                    {{ getJobStatusText(item.status) }}
                  </v-chip>
                  <v-tooltip v-if="item.last_error" location="top">
                    <template v-slot:activator="{ props }">
                      <v-icon v-bind="props" size="small" color="error" class="ml-1">mdi-alert-circle</v-icon>
                    </template>
                    {{ item.last_error }}
                  </v-tooltip>
                </template>
                <template v-slot:item.matched_site="{ item }">
                  <span v-if="item.matched_site">
                    {{ item.matched_site }}
                    <v-chip v-if="item.matched_seeders" size="x-small" class="ml-1">
                      {{ item.matched_seeders }} 种
                    </v-chip>
                  </span>
                  <span v-else class="text-grey">-</span>
                </template>
                <template v-slot:item.quality_score="{ item }">
                  <span v-if="item.quality_score">{{ item.quality_score.toFixed(1) }}</span>
                  <span v-else class="text-grey">-</span>
                </template>
                <template v-slot:item.created_at="{ item }">
                  {{ formatDate(item.created_at) }}
                </template>
                <template v-slot:item.actions="{ item }">
                  <v-btn
                    v-if="item.status === 'failed' || item.status === 'not_found'"
                    icon
                    size="x-small"
                    variant="text"
                    @click="retryJob(item.id)"
                    :disabled="item.retry_count >= item.max_retries"
                  >
                    <v-icon>mdi-refresh</v-icon>
                    <v-tooltip activator="parent" location="top">重试</v-tooltip>
                  </v-btn>
                  <v-btn
                    v-if="!['completed', 'skipped_duplicate'].includes(item.status)"
                    icon
                    size="x-small"
                    variant="text"
                    @click="skipJob(item.id)"
                  >
                    <v-icon>mdi-skip-next</v-icon>
                    <v-tooltip activator="parent" location="top">跳过</v-tooltip>
                  </v-btn>
                </template>
              </v-data-table>
            </v-card-text>
          </v-window-item>
        </v-window>
      </v-card>

      <!-- 迷你播放器 -->
      <v-card
        v-if="currentTrack"
        class="mini-player mt-4"
        variant="elevated"
      >
        <v-card-text class="d-flex align-center">
          <v-avatar size="48" class="mr-3">
            <v-icon>mdi-music-note</v-icon>
          </v-avatar>
          <div class="flex-grow-1">
            <div class="text-subtitle-2">{{ currentTrack.title }}</div>
            <div class="text-caption text-medium-emphasis">{{ currentTrack.artist_name }}</div>
          </div>
          <audio
            ref="audioEl"
            :src="currentAudioSrc"
            controls
            style="max-width: 300px;"
            @ended="onEnded"
          />
        </v-card-text>
      </v-card>
    </v-container>

    <!-- 专辑详情对话框 -->
    <v-dialog v-model="albumDialog" max-width="800" scrollable>
      <v-card v-if="selectedAlbum">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-album</v-icon>
          {{ selectedAlbum.title }}
          <v-spacer />
          <v-btn icon variant="text" @click="albumDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <div class="mb-4">
            <div class="text-body-2 text-medium-emphasis">艺术家：{{ selectedAlbum.artist_name }}</div>
            <div class="text-body-2 text-medium-emphasis">年份：{{ selectedAlbum.year || '未知' }}</div>
            <div class="text-body-2 text-medium-emphasis">曲目数：{{ selectedAlbum.track_count }}</div>
            <div class="text-body-2 text-medium-emphasis">
              总时长：{{ formatDuration(selectedAlbum.total_duration_seconds) }}
            </div>
          </div>

          <v-list density="compact">
            <v-list-item
              v-for="track in selectedAlbum.tracks"
              :key="track.id"
              @click="playTrack(track)"
              :disabled="!track.file_id"
            >
              <template v-slot:prepend>
                <span class="text-caption text-medium-emphasis mr-2" style="width: 24px;">
                  {{ track.track_number || '-' }}
                </span>
                <v-icon size="small" color="primary">mdi-play-circle-outline</v-icon>
              </template>
              <v-list-item-title>{{ track.title }}</v-list-item-title>
              <template v-slot:append>
                <span class="text-caption text-medium-emphasis">
                  {{ formatDuration(track.duration_seconds) }}
                </span>
              </template>
            </v-list-item>
          </v-list>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { musicLibraryApi, musicChartAdminApi, musicSubscriptionApi } from '@/services/api'
import { useToast } from '@/composables/useToast'
import type { 
  MusicAlbum, MusicArtist, MusicTrack, MusicAlbumDetail, MusicStats,
  MusicChart, MusicChartItem, UserMusicSubscription, MusicDownloadJob
} from '@/types/music'
import PageHeader from '@/components/common/PageHeader.vue'

const toast = useToast()

// 状态
const loading = ref(false)
const mainTab = ref('library')
const activeTab = ref('albums')
const keyword = ref('')

// 统计
const stats = ref<MusicStats>({
  total_artists: 0,
  total_albums: 0,
  total_tracks: 0,
  total_files: 0,
  total_size_mb: 0
})

// 专辑
const albums = ref<MusicAlbum[]>([])
const page = ref(1)
const totalPages = ref(0)

// 艺术家
const artists = ref<MusicArtist[]>([])
const artistPage = ref(1)
const artistTotalPages = ref(0)

// 曲目
const tracks = ref<MusicTrack[]>([])
const trackPage = ref(1)
const trackTotalPages = ref(0)

// 播放器
const currentTrack = ref<MusicTrack | null>(null)
const audioEl = ref<HTMLAudioElement | null>(null)

// 专辑详情
const albumDialog = ref(false)
const selectedAlbum = ref<MusicAlbumDetail | null>(null)

// MC2: 榜单相关
const charts = ref<MusicChart[]>([])
const chartsLoading = ref(false)
const selectedChartId = ref<number | null>(null)
const chartItems = ref<MusicChartItem[]>([])
const chartItemsLoading = ref(false)

// MC2: 订阅相关
const subscriptions = ref<UserMusicSubscription[]>([])
const runningSubscriptionId = ref<number | null>(null)

// MC2: 下载任务相关
const downloadJobs = ref<MusicDownloadJob[]>([])
const jobsLoading = ref(false)

// 表格列
const trackHeaders = [
  { title: '曲目', key: 'title', sortable: false },
  { title: '艺术家', key: 'artist_name', sortable: false },
  { title: '专辑', key: 'album_title', sortable: false },
  { title: '时长', key: 'duration_seconds', sortable: false },
  { title: '比特率', key: 'bitrate_kbps', sortable: false }
]

const chartItemHeaders = [
  { title: '排名', key: 'rank', sortable: false, width: 80 },
  { title: '曲目', key: 'title', sortable: false },
  { title: '艺术家', key: 'artist_name', sortable: false },
  { title: '专辑', key: 'album_name', sortable: false },
  { title: '时长', key: 'duration_seconds', sortable: false, width: 100 }
]

const jobHeaders = [
  { title: '曲目', key: 'search_query', sortable: false },
  { title: '状态', key: 'status', sortable: false, width: 120 },
  { title: '站点', key: 'matched_site', sortable: false, width: 120 },
  { title: '评分', key: 'quality_score', sortable: false, width: 80 },
  { title: '创建时间', key: 'created_at', sortable: false, width: 140 },
  { title: '操作', key: 'actions', sortable: false, width: 100 }
]

// MC3: 任务状态筛选
const jobStatusFilter = ref<string[]>([])

// 计算属性
const currentAudioSrc = computed(() => {
  if (!currentTrack.value?.file_id) return ''
  return musicLibraryApi.getStreamUrl(currentTrack.value.file_id)
})

// MC2: 是否已订阅当前榜单
const isChartSubscribed = computed(() => {
  if (!selectedChartId.value) return false
  return subscriptions.value.some(s => s.chart_id === selectedChartId.value)
})

// MC3: 筛选后的下载任务
const filteredDownloadJobs = computed(() => {
  if (jobStatusFilter.value.length === 0) {
    return downloadJobs.value
  }
  return downloadJobs.value.filter(job => jobStatusFilter.value.includes(job.status))
})

// 加载统计
const loadStats = async () => {
  try {
    stats.value = await musicLibraryApi.getStats()
  } catch (err: any) {
    console.error('加载统计失败:', err)
  }
}

// 加载专辑
const loadAlbums = async () => {
  loading.value = true
  try {
    const response = await musicLibraryApi.listAlbums({
      keyword: keyword.value || undefined,
      page: page.value,
      page_size: 24
    })
    albums.value = response.items
    totalPages.value = response.total_pages
  } catch (err: any) {
    console.error('加载专辑失败:', err)
    toast.error(err.response?.data?.detail || err.message || '加载失败')
  } finally {
    loading.value = false
  }
}

// 加载艺术家
const loadArtists = async () => {
  loading.value = true
  try {
    const response = await musicLibraryApi.listArtists({
      keyword: keyword.value || undefined,
      page: artistPage.value,
      page_size: 20
    })
    artists.value = response.items
    artistTotalPages.value = response.total_pages
  } catch (err: any) {
    console.error('加载艺术家失败:', err)
    toast.error(err.response?.data?.detail || err.message || '加载失败')
  } finally {
    loading.value = false
  }
}

// 加载曲目
const loadTracks = async () => {
  loading.value = true
  try {
    const response = await musicLibraryApi.listTracks({
      keyword: keyword.value || undefined,
      page: trackPage.value,
      page_size: 20
    })
    tracks.value = response.items
    trackTotalPages.value = response.total_pages
  } catch (err: any) {
    console.error('加载曲目失败:', err)
    toast.error(err.response?.data?.detail || err.message || '加载失败')
  } finally {
    loading.value = false
  }
}

// 打开专辑详情
const openAlbum = async (albumId: number) => {
  try {
    selectedAlbum.value = await musicLibraryApi.getAlbumDetail(albumId)
    albumDialog.value = true
  } catch (err: any) {
    console.error('加载专辑详情失败:', err)
    toast.error(err.response?.data?.detail || err.message || '加载失败')
  }
}

// 按艺术家筛选
const filterByArtist = (artistName: string) => {
  keyword.value = artistName
  activeTab.value = 'albums'
  page.value = 1
  loadAlbums()
}

// 播放曲目
const playTrack = (track: MusicTrack) => {
  if (!track.file_id) {
    toast.warning('该曲目没有可播放的文件')
    return
  }
  currentTrack.value = track
}

// 播放结束
const onEnded = () => {
  // 可以实现自动播放下一首
}

// 搜索
const handleSearch = () => {
  page.value = 1
  artistPage.value = 1
  trackPage.value = 1
  
  if (activeTab.value === 'albums') {
    loadAlbums()
  } else if (activeTab.value === 'artists') {
    loadArtists()
  } else {
    loadTracks()
  }
}

// 清除搜索
const handleClear = () => {
  keyword.value = ''
  handleSearch()
}

// 格式化时长
const formatDuration = (seconds?: number | null): string => {
  if (!seconds) return '--:--'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 格式化大小
const formatSize = (mb: number): string => {
  if (mb >= 1024) {
    return `${(mb / 1024).toFixed(1)} GB`
  }
  return `${mb.toFixed(1)} MB`
}

// 格式化日期
const formatDate = (dateStr?: string | null): string => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', { 
    month: '2-digit', 
    day: '2-digit', 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

// MC2: 加载榜单列表
const loadCharts = async () => {
  chartsLoading.value = true
  try {
    const response = await musicChartAdminApi.listCharts({ is_enabled: true })
    charts.value = response.items
  } catch (err: any) {
    console.error('加载榜单失败:', err)
  } finally {
    chartsLoading.value = false
  }
}

// MC2: 加载榜单条目
const loadChartItems = async () => {
  if (!selectedChartId.value) {
    chartItems.value = []
    return
  }
  chartItemsLoading.value = true
  try {
    const response = await musicChartAdminApi.getChartItems(selectedChartId.value, { page_size: 50 })
    chartItems.value = response.items
  } catch (err: any) {
    console.error('加载榜单条目失败:', err)
    toast.error('加载榜单条目失败')
  } finally {
    chartItemsLoading.value = false
  }
}

// MC2: 加载我的订阅
const loadSubscriptions = async () => {
  try {
    const response = await musicSubscriptionApi.listSubscriptions()
    subscriptions.value = response.items
  } catch (err: any) {
    console.error('加载订阅失败:', err)
  }
}

// MC2: 订阅榜单
const subscribeChart = async () => {
  if (!selectedChartId.value) return
  try {
    await musicSubscriptionApi.createSubscription({ chart_id: selectedChartId.value })
    toast.success('订阅成功')
    await loadSubscriptions()
  } catch (err: any) {
    toast.error(err.response?.data?.detail || '订阅失败')
  }
}

// MC2: 切换订阅状态
const toggleSubscription = async (sub: UserMusicSubscription) => {
  try {
    if (sub.status === 'active') {
      await musicSubscriptionApi.pauseSubscription(sub.id)
      toast.success('订阅已暂停')
    } else {
      await musicSubscriptionApi.resumeSubscription(sub.id)
      toast.success('订阅已恢复')
    }
    await loadSubscriptions()
  } catch (err: any) {
    toast.error(err.response?.data?.detail || '操作失败')
  }
}

// MC2: 手动运行订阅
const runSubscriptionOnce = async (subscriptionId: number) => {
  runningSubscriptionId.value = subscriptionId
  try {
    const result = await musicSubscriptionApi.runOnce(subscriptionId)
    toast.success(result.message || '运行完成')
    await loadSubscriptions()
  } catch (err: any) {
    toast.error(err.response?.data?.detail || '运行失败')
  } finally {
    runningSubscriptionId.value = null
  }
}

// MC2: 加载下载任务
const loadDownloadJobs = async () => {
  jobsLoading.value = true
  try {
    const response = await musicSubscriptionApi.listDownloadJobs()
    downloadJobs.value = response.items
  } catch (err: any) {
    console.error('加载下载任务失败:', err)
  } finally {
    jobsLoading.value = false
  }
}

// MC2: 任务状态颜色
const getJobStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    pending: 'grey',
    searching: 'info',
    found: 'success',
    downloading: 'primary',
    completed: 'success',
    failed: 'error',
    skipped: 'warning'
  }
  return colors[status] || 'grey'
}

// MC2: 任务状态文本
const getJobStatusText = (status: string): string => {
  const texts: Record<string, string> = {
    pending: '等待中',
    searching: '搜索中',
    found: '已找到',
    not_found: '未找到',
    submitted: '已提交',
    downloading: '下载中',
    importing: '导入中',
    completed: '已完成',
    failed: '失败',
    skipped_duplicate: '已跳过'
  }
  return texts[status] || status
}

// MC3: 重试任务
const retryJob = async (jobId: number) => {
  try {
    const result = await musicSubscriptionApi.retryJob(jobId)
    toast.success(result.message || '任务已重新排队')
    await loadDownloadJobs()
  } catch (err: any) {
    toast.error(err.response?.data?.detail || '重试失败')
  }
}

// MC3: 跳过任务
const skipJob = async (jobId: number) => {
  try {
    const result = await musicSubscriptionApi.skipJob(jobId)
    toast.success(result.message || '任务已跳过')
    await loadDownloadJobs()
  } catch (err: any) {
    toast.error(err.response?.data?.detail || '操作失败')
  }
}

// 监听标签页切换
watch(activeTab, (newTab) => {
  if (newTab === 'albums' && albums.value.length === 0) {
    loadAlbums()
  } else if (newTab === 'artists' && artists.value.length === 0) {
    loadArtists()
  } else if (newTab === 'tracks' && tracks.value.length === 0) {
    loadTracks()
  }
})

// MC2: 监听主标签页切换
watch(mainTab, (newTab) => {
  if (newTab === 'charts') {
    if (charts.value.length === 0) loadCharts()
    if (subscriptions.value.length === 0) loadSubscriptions()
  } else if (newTab === 'tasks') {
    loadDownloadJobs()
  }
})

// 初始化
onMounted(() => {
  loadStats()
  loadAlbums()
})
</script>

<style scoped>
.album-card {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.album-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.album-cover {
  border-radius: 4px 4px 0 0;
}

.mini-player {
  position: sticky;
  bottom: 16px;
}
</style>
