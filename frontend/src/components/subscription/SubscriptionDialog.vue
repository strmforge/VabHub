<template>
  <v-dialog
    v-model="modelValue"
    max-width="900"
    scrollable
    persistent
  >
    <v-card class="subscription-dialog">
      <v-card-item class="py-3">
        <template #prepend>
          <v-icon icon="mdi-clipboard-list-outline" class="me-2" />
        </template>
        <v-card-title class="text-h6">
          {{ editingSubscription ? '编辑订阅' : '创建订阅' }}
        </v-card-title>
        <v-card-subtitle v-if="editingSubscription">
          {{ form.title || '未命名订阅' }}
        </v-card-subtitle>
        <v-card-subtitle v-else>
          {{ form.media_type === 'movie' ? '电影' : '电视剧' }}
        </v-card-subtitle>
        <template #append>
          <v-btn
            icon="mdi-close"
            variant="text"
            size="small"
            @click="modelValue = false"
          />
        </template>
      </v-card-item>

      <v-card-text>
        <v-form ref="formRef">
          <!-- 媒体选择 -->
          <v-row class="mb-4">
            <v-col cols="12" md="4">
              <v-select
                v-model="form.media_type"
                :items="mediaTypes"
                label="媒体类型 *"
                variant="outlined"
                density="compact"
                required
                prepend-inner-icon="mdi-movie-open"
                :rules="[v => !!v || '请选择媒体类型']"
                :disabled="!!editingSubscription"
              />
            </v-col>
            <v-col cols="12" md="8">
              <v-card variant="outlined" class="pa-3">
                <div class="d-flex align-center justify-space-between">
                  <div class="flex-grow-1">
                    <div v-if="selectedMedia" class="d-flex align-center">
                      <v-avatar size="48" class="me-3" rounded>
                        <v-img
                          v-if="selectedMedia.poster_path"
                          :src="getPosterUrl(selectedMedia.poster_path)"
                          cover
                        />
                        <v-icon v-else>mdi-movie</v-icon>
                      </v-avatar>
                      <div>
                        <div class="text-body-1 font-weight-bold">
                          {{ selectedMedia.title || selectedMedia.name }}
                        </div>
                        <div class="text-caption text-medium-emphasis">
                          {{ selectedMedia.release_date || selectedMedia.first_air_date }}
                          <span v-if="selectedMedia.tmdb_id"> • TMDB: {{ selectedMedia.tmdb_id }}</span>
                        </div>
                      </div>
                    </div>
                    <div v-else class="text-body-2 text-medium-emphasis">
                      点击"搜索媒体"按钮选择电影或电视剧
                    </div>
                  </div>
                  <v-btn
                    color="primary"
                    prepend-icon="mdi-magnify"
                    @click="showMediaSearch = true"
                    :disabled="!form.media_type"
                  >
                    {{ selectedMedia ? '重新选择' : '搜索媒体' }}
                  </v-btn>
                </div>
              </v-card>
            </v-col>
          </v-row>

          <!-- 已选媒体信息（只读显示） -->
          <v-row v-if="selectedMedia" class="mb-4">
            <v-col cols="12">
              <v-card variant="outlined" class="pa-4 media-info-card">
                <div class="text-caption text-medium-emphasis mb-3 d-flex align-center">
                  <v-icon size="small" class="me-1">mdi-information-outline</v-icon>
                  媒体信息（自动填充）
                </div>
                <v-row dense class="align-center">
                  <v-col cols="12" md="3">
                    <div class="text-caption text-medium-emphasis mb-1">标题</div>
                    <div class="text-body-1 font-weight-medium">{{ form.title || '-' }}</div>
                  </v-col>
                  <v-col cols="12" md="3">
                    <div class="text-caption text-medium-emphasis mb-1">原始标题</div>
                    <div class="text-body-2">{{ form.original_title || '-' }}</div>
                  </v-col>
                  <v-col cols="12" md="2">
                    <div class="text-caption text-medium-emphasis mb-1">年份</div>
                    <div class="text-body-2">{{ form.year || '-' }}</div>
                  </v-col>
                  <v-col cols="12" md="2">
                    <div class="text-caption text-medium-emphasis mb-1">TMDB ID</div>
                    <div class="text-body-2">{{ form.tmdb_id || '-' }}</div>
                  </v-col>
                  <v-col cols="12" md="2">
                    <div class="text-caption text-medium-emphasis mb-1">海报/背景</div>
                    <div class="text-body-2">
                      <v-icon v-if="form.poster" size="small" color="success">mdi-check-circle</v-icon>
                      <v-icon v-else size="small" color="grey">mdi-close-circle</v-icon>
                    </div>
                  </v-col>
                </v-row>
                
                <!-- 电视剧季信息 -->
                <v-row v-if="form.media_type === 'tv' && form.season" dense class="mt-2 align-center">
                  <v-col cols="12" md="3">
                    <div class="text-caption text-medium-emphasis mb-1">订阅季</div>
                    <div class="text-body-2">
                      <v-chip size="small" color="primary" variant="flat">
                        第 {{ form.season }} 季
                      </v-chip>
                    </div>
                  </v-col>
                  <v-col v-if="form.total_episode" cols="12" md="3">
                    <div class="text-caption text-medium-emphasis mb-1">总集数</div>
                    <div class="text-body-2">{{ form.total_episode }} 集</div>
                  </v-col>
                  <v-col v-if="form.start_episode" cols="12" md="3">
                    <div class="text-caption text-medium-emphasis mb-1">起始集数</div>
                    <div class="text-body-2">第 {{ form.start_episode }} 集</div>
                  </v-col>
                </v-row>
              </v-card>
            </v-col>
          </v-row>

          <!-- 电视剧季选择（仅电视剧显示） -->
          <v-row v-if="form.media_type === 'tv' && selectedMedia" class="mb-4">
            <v-col cols="12">
              <v-card variant="outlined" class="pa-3">
                <div class="d-flex align-center justify-space-between mb-2">
                  <div>
                    <div class="text-body-2 font-weight-medium mb-1">订阅季设置</div>
                    <div class="text-caption text-medium-emphasis">
                      选择要订阅的电视剧季（可多选）
                    </div>
                  </div>
                  <v-btn
                    color="primary"
                    variant="outlined"
                    prepend-icon="mdi-playlist-check"
                    @click="showSeasonDialog = true"
                  >
                    {{ selectedSeasons.length > 0 ? `已选 ${selectedSeasons.length} 季` : '选择季' }}
                  </v-btn>
                </div>
                <div v-if="selectedSeasons.length > 0" class="d-flex flex-wrap ga-2 mt-2">
                  <v-chip
                    v-for="seasonNum in selectedSeasons"
                    :key="seasonNum"
                    size="small"
                    color="primary"
                    variant="flat"
                    closable
                    @click:close="removeSeason(seasonNum)"
                  >
                    第 {{ seasonNum }} 季
                  </v-chip>
                </div>
              </v-card>
            </v-col>
          </v-row>

          <!-- 标签页：基础/进阶 -->
          <v-tabs v-model="activeTab" class="mb-4" color="primary">
            <v-tab value="basic">
              <v-icon start>mdi-cog</v-icon>
              基础
            </v-tab>
            <v-tab value="advanced">
              <v-icon start>mdi-tune</v-icon>
              进阶
            </v-tab>
          </v-tabs>

          <v-window v-model="activeTab" class="disable-tab-transition">
            <!-- 基础标签页 -->
            <v-window-item value="basic">
              <div class="pa-2">
                <!-- 电视剧特有字段 -->
                <v-row v-if="form.media_type === 'tv'" class="mb-2">
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="form.total_episode"
                      label="总集数"
                      type="number"
                      variant="outlined"
                      density="compact"
                      prepend-inner-icon="mdi-playlist-play"
                      hint="该季的总集数（可选）"
                      persistent-hint
                    />
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="form.start_episode"
                      label="起始集数"
                      type="number"
                      variant="outlined"
                      density="compact"
                      prepend-inner-icon="mdi-play-circle-outline"
                      hint="从第几集开始订阅（可选）"
                      persistent-hint
                    />
                  </v-col>
                </v-row>
                
                <!-- 质量、分辨率、特效 -->
                <v-row>
                  <v-col cols="12" md="4">
                    <v-autocomplete
                      v-model="form.quality"
                      :items="qualityOptions"
                      label="质量"
                      variant="outlined"
                      density="compact"
                      prepend-inner-icon="mdi-quality-high"
                      hint="订阅资源质量"
                      persistent-hint
                      clearable
                    />
                  </v-col>
                  <v-col cols="12" md="4">
                    <v-autocomplete
                      v-model="form.resolution"
                      :items="resolutionOptions"
                      label="分辨率"
                      variant="outlined"
                      density="compact"
                      prepend-inner-icon="mdi-monitor"
                      hint="订阅资源分辨率"
                      persistent-hint
                      clearable
                    />
                  </v-col>
                  <v-col cols="12" md="4">
                    <v-autocomplete
                      v-model="form.effect"
                      :items="effectOptions"
                      label="特效"
                      variant="outlined"
                      density="compact"
                      prepend-inner-icon="mdi-auto-fix"
                      hint="订阅资源特效"
                      persistent-hint
                      clearable
                    />
                  </v-col>
                </v-row>

                <!-- 订阅站点 -->
                <v-row>
                  <v-col cols="12">
                    <v-autocomplete
                      v-model="form.sites"
                      :items="siteOptions"
                      label="订阅站点"
                      variant="outlined"
                      density="compact"
                      prepend-inner-icon="mdi-web"
                      hint="订阅的站点范围，不选使用系统设置"
                      persistent-hint
                      multiple
                      chips
                      clearable
                    />
                  </v-col>
                </v-row>

                <!-- 下载器和保存路径 -->
                <v-row>
                  <v-col cols="12" md="6">
                    <v-autocomplete
                      v-model="form.downloader"
                      :items="downloaderOptions"
                      label="下载器"
                      variant="outlined"
                      density="compact"
                      prepend-inner-icon="mdi-download"
                      hint="指定该订阅使用的下载器"
                      persistent-hint
                      clearable
                    />
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-combobox
                      v-model="form.save_path"
                      :items="savePathOptions"
                      label="保存路径"
                      variant="outlined"
                      density="compact"
                      prepend-inner-icon="mdi-folder"
                      hint="指定该订阅的下载保存路径，留空自动使用设定的下载目录"
                      persistent-hint
                      clearable
                    />
                  </v-col>
                </v-row>

                <!-- 规则组选择和默认配置 -->
                <v-row>
                  <v-col cols="12">
                    <v-card variant="outlined" class="pa-3">
                      <div class="d-flex align-center justify-space-between mb-3">
                        <div class="text-subtitle-2 d-flex align-center">
                          <v-icon class="mr-2">mdi-filter-variant</v-icon>
                          过滤规则组
                        </div>
                        <v-btn
                          size="small"
                          variant="outlined"
                          prepend-icon="mdi-cog-outline"
                          @click="showRuleCenter = true"
                        >
                          规则中心
                        </v-btn>
                      </div>
                      
                      <v-row class="align-center">
                        <v-col cols="12" md="8">
                          <v-autocomplete
                            v-model="form.filter_group_ids"
                            :items="availableRuleGroups"
                            item-title="name"
                            item-value="id"
                            label="选择过滤规则组"
                            variant="outlined"
                            density="compact"
                            prepend-inner-icon="mdi-filter-variant"
                            hint="选择的规则组将按优先级顺序应用过滤"
                            persistent-hint
                            multiple
                            chips
                            clearable
                            :loading="loadingRuleGroups"
                          />
                        </v-col>
                        <v-col cols="12" md="4">
                          <v-btn
                            variant="outlined"
                            prepend-icon="mdi-download"
                            @click="loadDefaultConfig"
                            :disabled="!form.media_type || loadingDefaultConfig"
                            :loading="loadingDefaultConfig"
                            block
                          >
                            加载默认配置
                          </v-btn>
                        </v-col>
                      </v-row>
                    </v-card>
                  </v-col>
                </v-row>

                <!-- 最小做种数 -->
                <v-row>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="form.min_seeders"
                      label="最小做种数"
                      type="number"
                      variant="outlined"
                      density="compact"
                      prepend-inner-icon="mdi-seed"
                      hint="最小种子数要求"
                      persistent-hint
                    />
                  </v-col>
                </v-row>

                <!-- 开关选项 -->
                <v-row>
                  <v-col cols="12" md="4">
                    <v-switch
                      v-model="form.best_version"
                      label="洗版"
                      color="primary"
                      hint="根据洗版优先级进行洗版订阅"
                      persistent-hint
                    />
                  </v-col>
                  <v-col cols="12" md="4">
                    <v-switch
                      v-model="form.search_imdbid"
                      label="使用 ImdbID 搜索"
                      color="primary"
                      hint="开启使用 ImdbID 精确搜索资源"
                      persistent-hint
                    />
                  </v-col>
                  <v-col cols="12" md="4">
                    <v-switch
                      v-model="form.auto_download"
                      label="自动下载"
                      color="primary"
                      hint="匹配到资源后自动下载"
                      persistent-hint
                    />
                  </v-col>
                </v-row>
              </div>
            </v-window-item>

            <!-- 进阶标签页 -->
            <v-window-item value="advanced">
              <div class="pa-2">
                <!-- 包含/排除规则 -->
                <v-row>
                  <v-col cols="12" md="6">
                    <v-textarea
                      v-model="form.include"
                      label="包含（关键字、正则式）"
                      variant="outlined"
                      density="compact"
                      prepend-inner-icon="mdi-plus-circle-outline"
                      hint="包含规则，支持正则表达式"
                      persistent-hint
                      rows="4"
                      auto-grow
                    />
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-textarea
                      v-model="form.exclude"
                      label="排除（关键字、正则式）"
                      variant="outlined"
                      density="compact"
                      prepend-inner-icon="mdi-minus-circle-outline"
                      hint="排除规则，支持正则表达式"
                      persistent-hint
                      rows="4"
                      auto-grow
                    />
                  </v-col>
                </v-row>

                <!-- 优先级规则组 -->
                <v-row>
                  <v-col cols="12">
                    <v-autocomplete
                      v-model="form.filter_groups"
                      :items="filterGroupOptions"
                      label="优先级规则组"
                      variant="outlined"
                      density="compact"
                      prepend-inner-icon="mdi-filter"
                      hint="按选定的过滤规则组对订阅进行过滤"
                      persistent-hint
                      multiple
                      chips
                      clearable
                    />
                  </v-col>
                </v-row>

                <!-- 安全策略（VIDEO-AUTOLOOP-1） -->
                <v-row>
                  <v-col cols="12">
                    <v-card variant="outlined" class="pa-3">
                      <template #title>
                        <div class="d-flex align-center">
                          <v-icon icon="mdi-shield-check" class="me-2" color="warning" />
                          安全策略
                          <v-spacer />
                          <v-tooltip text="控制下载资源的安全策略，避免HR/H&R等风险" location="top">
                            <template #activator="{ props }">
                              <v-icon
                                v-bind="props"
                                icon="mdi-help-circle"
                                size="small"
                                color="grey"
                              />
                            </template>
                          </v-tooltip>
                        </div>
                      </template>
                      
                      <v-row class="mt-2">
                        <v-col cols="12" md="4">
                          <v-checkbox
                            v-model="form.allow_hr"
                            label="允许 HR/H&R"
                            color="warning"
                            hint="允许下载HR（Hit and Run）或H&R资源"
                            persistent-hint
                          >
                            <template #append>
                              <v-tooltip text="HR资源需要保持上传比例，可能影响账号安全" location="top">
                                <template #activator="{ props }">
                                  <v-icon
                                    v-bind="props"
                                    icon="mdi-alert"
                                    size="small"
                                    color="warning"
                                  />
                                </template>
                              </v-tooltip>
                            </template>
                          </v-checkbox>
                        </v-col>
                        
                        <v-col cols="12" md="4">
                          <v-checkbox
                            v-model="form.allow_h3h5"
                            label="允许 H3/H5 扩展规则"
                            color="warning"
                            hint="允许下载H3/H5等特殊规则的资源"
                            persistent-hint
                          >
                            <template #append>
                              <v-tooltip text="H3/H5等扩展规则可能有特殊下载要求" location="top">
                                <template #activator="{ props }">
                                  <v-icon
                                    v-bind="props"
                                    icon="mdi-alert"
                                    size="small"
                                    color="warning"
                                  />
                                </template>
                              </v-tooltip>
                            </template>
                          </v-checkbox>
                        </v-col>
                        
                        <v-col cols="12" md="4">
                          <v-checkbox
                            v-model="form.strict_free_only"
                            label="只下 Free 种"
                            color="success"
                            hint="只下载免费或促销资源，最安全"
                            persistent-hint
                          >
                            <template #append>
                              <v-tooltip text="只下载免费资源，完全避免HR风险" location="top">
                                <template #activator="{ props }">
                                  <v-icon
                                    v-bind="props"
                                    icon="mdi-shield-check"
                                    size="small"
                                    color="success"
                                  />
                                </template>
                              </v-tooltip>
                            </template>
                          </v-checkbox>
                        </v-col>
                      </v-row>
                    </v-card>
                  </v-col>
                </v-row>
              </div>
            </v-window-item>
          </v-window>
        </v-form>
      </v-card-text>

      <v-divider />

      <v-card-actions class="pa-4">
        <v-spacer />
        <v-btn
          variant="text"
          @click="modelValue = false"
        >
          取消
        </v-btn>
        <v-btn
          color="primary"
          prepend-icon="mdi-content-save"
          @click="handleSave"
          :loading="saving"
        >
          保存
        </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- 媒体搜索对话框 -->
    <MediaSearchDialog
      v-model="showMediaSearch"
      :media-type="form.media_type"
      @select="handleMediaSelect"
    />
    
    <!-- 季选择对话框 -->
    <SeasonSelectDialog
      v-model="showSeasonDialog"
      :media="selectedMedia"
      @confirm="handleSeasonSelect"
    />
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { filterRuleGroupsApi, subscriptionDefaultsApi } from '@/api/index'
import MediaSearchDialog from '@/components/media/MediaSearchDialog.vue'
import SeasonSelectDialog from '@/components/subscription/SeasonSelectDialog.vue'

interface Props {
  modelValue: boolean
  subscription?: any
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'saved': []
}>()

const router = useRouter()
const formRef = ref()
const activeTab = ref('basic')
const saving = ref(false)
const editingSubscription = computed(() => props.subscription)
const showMediaSearch = ref(false)
const selectedMedia = ref<any>(null)
const showSeasonDialog = ref(false)
const selectedSeasons = ref<number[]>([])

// 规则组相关数据
const availableRuleGroups = ref<any[]>([])
const loadingRuleGroups = ref(false)
const loadingDefaultConfig = ref(false)
const showRuleCenter = ref(false)

// 表单数据
const form = ref({
  title: '',
  original_title: '',
  media_type: 'movie' as 'movie' | 'tv',
  year: null,
  tmdb_id: null,
  tvdb_id: null,
  imdb_id: '',
  poster: '',
  backdrop: '',
  // 电视剧相关
  season: null as number | null,
  total_episode: null as number | null,
  start_episode: null as number | null,
  episode_group: '',
  // 基础规则
  quality: '',
  resolution: '',
  effect: '',
  sites: [] as number[],
  downloader: '',
  save_path: '',
  min_seeders: 5,
  auto_download: true,
  best_version: false,
  search_imdbid: false,
  // 进阶规则
  include: '',
  exclude: '',
  filter_group_ids: [] as number[], // 规则组ID数组
  // 安全策略（VIDEO-AUTOLOOP-1）
  allow_hr: false,
  allow_h3h5: false,
  strict_free_only: false
})

// 选项数据
const mediaTypes = [
  { title: '电影', value: 'movie' },
  { title: '电视剧', value: 'tv' }
]

const qualityOptions = [
  { title: '全部', value: '' },
  { title: '蓝光原盘', value: 'Blu-?Ray.+VC-?1|Blu-?Ray.+AVC|UHD.+blu-?ray.+HEVC|MiniBD' },
  { title: 'Remux', value: 'Remux' },
  { title: '蓝光', value: 'Blu-?Ray' },
  { title: 'UHD', value: 'UHD|UltraHD' },
  { title: 'WEB-DL', value: 'WEB-?DL|WEB-?RIP' },
  { title: 'HDTV', value: 'HDTV' },
  { title: 'H.265', value: '[Hx].?265|HEVC' },
  { title: 'H.264', value: '[Hx].?264|AVC' }
]

const resolutionOptions = [
  { title: '全部', value: '' },
  { title: '4K', value: '4K|2160p|x2160' },
  { title: '1080p', value: '1080[pi]|x1080' },
  { title: '720p', value: '720[pi]|x720' }
]

const effectOptions = [
  { title: '全部', value: '' },
  { title: 'HDR', value: 'HDR' },
  { title: 'SDR', value: 'SDR' },
  { title: 'Dolby Vision', value: 'Dolby.?Vision|DoVi' },
  { title: 'Dolby Atmos', value: 'Dolby.?Atmos|Atmos' },
  { title: '3D', value: '3D' }
]

const siteOptions = ref<Array<{ title: string; value: number }>>([])
const downloaderOptions = ref<Array<{ title: string; value: string }>>([])
const savePathOptions = ref<string[]>([])
const filterGroupOptions = ref<Array<{ title: string; value: string }>>([])

// 加载选项数据
const loadOptions = async () => {
  try {
    // 加载站点列表
    try {
      const sitesResponse = await api.get('/sites?active_only=true')
      siteOptions.value = sitesResponse.data.map((s: any) => ({ 
        title: s.name, 
        value: s.id 
      }))
    } catch (error) {
      console.warn('加载站点列表失败:', error)
      siteOptions.value = []
    }
    
    // 下载器选项
    downloaderOptions.value = [
      { title: '默认', value: '' },
      { title: 'qBittorrent', value: 'qbittorrent' },
      { title: 'Transmission', value: 'transmission' }
    ]
    
    // 优先级规则组（暂时不实现）
    filterGroupOptions.value = []
  } catch (error) {
    console.error('加载选项数据失败:', error)
  }
}

// 监听订阅变化
watch(() => props.subscription, (newVal) => {
  if (newVal) {
    form.value = {
      title: newVal.title || '',
      original_title: newVal.original_title || '',
      media_type: (newVal.media_type || 'movie') as 'movie' | 'tv',
      year: newVal.year || null,
      tmdb_id: newVal.tmdb_id || null,
      tvdb_id: newVal.tvdb_id || null,
      imdb_id: newVal.imdb_id || '',
      poster: newVal.poster || '',
      backdrop: newVal.backdrop || '',
      season: newVal.season || null,
      total_episode: newVal.total_episode || null,
      start_episode: newVal.start_episode || null,
      episode_group: newVal.episode_group || '',
      quality: newVal.quality || '',
      resolution: newVal.resolution || '',
      effect: newVal.effect || '',
      sites: newVal.sites || [],
      downloader: newVal.downloader || '',
      save_path: newVal.save_path || '',
      min_seeders: newVal.min_seeders || 5,
      auto_download: newVal.auto_download !== undefined ? newVal.auto_download : true,
      best_version: newVal.best_version || false,
      search_imdbid: newVal.search_imdbid || false,
      include: newVal.include || '',
      exclude: newVal.exclude || '',
      filter_groups: newVal.filter_groups || [],
      // 安全策略（VIDEO-AUTOLOOP-1）
      allow_hr: newVal.allow_hr !== undefined ? newVal.allow_hr : false,
      allow_h3h5: newVal.allow_h3h5 !== undefined ? newVal.allow_h3h5 : false,
      strict_free_only: newVal.strict_free_only !== undefined ? newVal.strict_free_only : false
    }
  } else {
    form.value = {
      title: '',
      original_title: '',
      media_type: 'movie' as 'movie' | 'tv',
      year: null,
      tmdb_id: null,
      tvdb_id: null,
      imdb_id: '',
      poster: '',
      backdrop: '',
      season: null,
      total_episode: null,
      start_episode: null,
      episode_group: '',
      quality: '',
      resolution: '',
      effect: '',
      sites: [],
      downloader: '',
      save_path: '',
      min_seeders: 5,
      auto_download: true,
      best_version: false,
      search_imdbid: false,
      include: '',
      exclude: '',
      filter_groups: [],
      // 安全策略（VIDEO-AUTOLOOP-1）
      allow_hr: false,
      allow_h3h5: false,
      strict_free_only: false
    }
  }
}, { immediate: true })

const modelValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const handleSave = async () => {
  // 验证是否已选择媒体（新建时）
  if (!editingSubscription.value && !selectedMedia.value) {
    alert('请先搜索并选择媒体')
    return
  }
  
  // 电视剧必须选择至少一个季
  if (form.value.media_type === 'tv' && selectedSeasons.value.length === 0 && !editingSubscription.value) {
    alert('请至少选择一个要订阅的季')
    showSeasonDialog.value = true
    return
  }
  
  // 表单验证
  const { valid } = await formRef.value?.validate()
  if (!valid) return
  
  saving.value = true
  try {
    // 如果是电视剧且选择了多个季，需要创建多个订阅
    if (form.value.media_type === 'tv' && selectedSeasons.value.length > 0 && !editingSubscription.value) {
      // 为每个季创建订阅
      for (const seasonNum of selectedSeasons.value) {
        const data = {
          ...form.value,
          season: seasonNum
        }
        await api.post('/subscriptions', data)
      }
    } else {
      // 单个订阅（电影或编辑）
      const data = { ...form.value }
      
      if (editingSubscription.value?.id) {
        // 更新订阅
        await api.put(`/subscriptions/${editingSubscription.value.id}`, data)
      } else {
        // 创建订阅
        await api.post('/subscriptions', data)
      }
    }
    
    emit('saved')
    modelValue.value = false
    // 重置表单
    selectedMedia.value = null
    selectedSeasons.value = []
  } catch (error: any) {
    console.error('保存订阅失败:', error)
    alert('保存失败：' + (error.response?.data?.detail || '未知错误'))
  } finally {
    saving.value = false
  }
}

// 获取海报URL
const getPosterUrl = (posterPath: string | null) => {
  if (!posterPath) return '/placeholder-poster.jpg'
  if (posterPath.startsWith('http')) return posterPath
  return `https://image.tmdb.org/t/p/w500${posterPath}`
}

// 处理媒体选择
const handleMediaSelect = async (media: any) => {
  selectedMedia.value = media
  
  // 自动填充基本信息
  form.value.title = media.title || media.name || ''
  form.value.original_title = media.original_title || media.original_name || ''
  form.value.year = media.year || null
  form.value.tmdb_id = media.tmdb_id || null
  
  // 如果是电视剧，重置季选择
  if (form.value.media_type === 'tv') {
    selectedSeasons.value = []
    form.value.season = null
    form.value.total_episode = null
    form.value.start_episode = null
  }
  
  // 获取详细信息和海报
  if (media.tmdb_id) {
    try {
      const detailsResponse = await api.get(`/media/details/${media.tmdb_id}`, {
        params: { type: form.value.media_type }
      })
      const details = detailsResponse.data
      
      // 填充详细信息
      form.value.poster = details.poster || null
      form.value.backdrop = details.backdrop || null
      form.value.tvdb_id = details.tvdb_id || null
      form.value.imdb_id = details.imdb_id || null
      if (details.year && !form.value.year) {
        form.value.year = details.year
      }
    } catch (error: any) {
      console.warn('获取媒体详情失败，使用搜索结果信息:', error)
      // 如果获取详情失败，使用搜索结果中的基本信息
      if (media.poster_path) {
        form.value.poster = `https://image.tmdb.org/t/p/w500${media.poster_path}`
      }
      if (media.backdrop_path) {
        form.value.backdrop = `https://image.tmdb.org/t/p/original${media.backdrop_path}`
      }
    }
  }
}

// 处理季选择
const handleSeasonSelect = (seasons: number[]) => {
  selectedSeasons.value = seasons
  // 如果只选择了一个季，自动填充到表单
  if (seasons.length === 1) {
    form.value.season = seasons[0]
  }
}

// 移除季
const removeSeason = (seasonNum: number) => {
  const index = selectedSeasons.value.indexOf(seasonNum)
  if (index > -1) {
    selectedSeasons.value.splice(index, 1)
  }
  if (form.value.season === seasonNum) {
    form.value.season = null
  }
}

// 监听订阅变化，如果有TMDB ID，自动加载媒体信息
watch(() => props.subscription, async (newVal) => {
  if (newVal && newVal.tmdb_id && !selectedMedia.value) {
    try {
      const detailsResponse = await api.get(`/media/details/${newVal.tmdb_id}`, {
        params: { type: newVal.media_type }
      })
      const details = detailsResponse.data
      selectedMedia.value = {
        title: details.title,
        name: details.title,
        tmdb_id: details.tmdb_id,
        poster_path: details.poster_path,
        release_date: details.release_date,
        first_air_date: details.release_date
      }
    } catch (error) {
      console.warn('加载媒体信息失败:', error)
    }
  }
}, { immediate: true })

// 初始化
onMounted(() => {
  loadOptions()
  loadRuleGroups()
})

// 加载规则组列表
const loadRuleGroups = async () => {
  loadingRuleGroups.value = true
  try {
    const response = await filterRuleGroupsApi.getFilterRuleGroups({
      enabled: true,
      size: 100 // 获取所有启用的规则组
    })
    availableRuleGroups.value = response.data.items
  } catch (error) {
    console.error('加载规则组失败:', error)
  } finally {
    loadingRuleGroups.value = false
  }
}

// 加载默认配置
const loadDefaultConfig = async () => {
  if (!form.value.media_type) return
  
  loadingDefaultConfig.value = true
  try {
    const response = await subscriptionDefaultsApi.getDefaultConfig(form.value.media_type)
    const defaultConfig = response.data
    
    // 应用默认配置到表单
    form.value.quality = defaultConfig.quality
    form.value.resolution = defaultConfig.resolution
    form.value.effect = defaultConfig.effect
    form.value.min_seeders = defaultConfig.min_seeders
    form.value.auto_download = defaultConfig.auto_download
    form.value.best_version = defaultConfig.best_version
    form.value.include = defaultConfig.include
    form.value.exclude = defaultConfig.exclude
    form.value.filter_group_ids = defaultConfig.filter_group_ids
    form.value.allow_hr = defaultConfig.allow_hr
    form.value.allow_h3h5 = defaultConfig.allow_h3h5
    form.value.strict_free_only = defaultConfig.strict_free_only
    form.value.sites = defaultConfig.sites
    form.value.downloader = defaultConfig.downloader
    form.value.save_path = defaultConfig.save_path
  } catch (error) {
    console.error('加载默认配置失败:', error)
    alert('加载默认配置失败，请检查规则中心设置')
  } finally {
    loadingDefaultConfig.value = false
  }
}

// 跳转到规则中心
const handleRuleCenterClick = () => {
  router.push('/settings/rule-center')
}
</script>

<style scoped lang="scss">
.subscription-dialog {
  background: rgba(var(--v-theme-surface), 0.95);
  backdrop-filter: blur(10px);
}

.media-select-card {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border: 1px solid rgba(var(--v-border-color), 0.2);
}

.media-info-card {
  background: rgba(var(--v-theme-surface-variant), 0.4);
  border: 1px solid rgba(var(--v-border-color), 0.15);
}

.season-select-card {
  background: rgba(var(--v-theme-primary), 0.05);
  border: 1px solid rgba(var(--v-theme-primary), 0.2);
}

.disable-tab-transition {
  transition: none !important;
}
</style>
