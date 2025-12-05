<template>
  <v-expansion-panels v-model="expanded" multiple class="search-filters">
    <v-expansion-panel title="高级筛选" value="filters">
      <v-expansion-panel-text>
        <v-row>
          <!-- 媒体类型 -->
          <v-col cols="12" md="6">
            <v-select
              v-model="filters.media_type"
              :items="mediaTypes"
              label="媒体类型"
              variant="outlined"
              density="compact"
              clearable
            />
          </v-col>

          <!-- 年份 -->
          <v-col cols="12" md="6">
            <v-text-field
              v-model.number="filters.year"
              label="年份"
              variant="outlined"
              density="compact"
              type="number"
              clearable
            />
          </v-col>

          <!-- 分辨率 -->
          <v-col cols="12" md="6">
            <v-select
              v-model="filters.resolution"
              :items="resolutions"
              label="分辨率"
              variant="outlined"
              density="compact"
              clearable
            />
          </v-col>

          <!-- 质量 -->
          <v-col cols="12" md="6">
            <v-select
              v-model="filters.quality"
              :items="qualities"
              label="质量"
              variant="outlined"
              density="compact"
              clearable
            />
          </v-col>

          <!-- 大小范围 -->
          <v-col cols="12" md="6">
            <v-text-field
              v-model.number="filters.min_size"
              label="最小大小 (GB)"
              variant="outlined"
              density="compact"
              type="number"
              clearable
            />
          </v-col>

          <v-col cols="12" md="6">
            <v-text-field
              v-model.number="filters.max_size"
              label="最大大小 (GB)"
              variant="outlined"
              density="compact"
              type="number"
              clearable
            />
          </v-col>

          <!-- 做种数范围 -->
          <v-col cols="12" md="6">
            <v-text-field
              v-model.number="filters.min_seeders"
              label="最小做种数"
              variant="outlined"
              density="compact"
              type="number"
              clearable
            />
          </v-col>

          <v-col cols="12" md="6">
            <v-text-field
              v-model.number="filters.max_seeders"
              label="最大做种数"
              variant="outlined"
              density="compact"
              type="number"
              clearable
            />
          </v-col>

          <!-- 包含关键词 -->
          <v-col cols="12" md="6">
            <v-text-field
              v-model="filters.include"
              label="必须包含"
              variant="outlined"
              density="compact"
              hint="标题必须包含的关键词"
              persistent-hint
              clearable
            />
          </v-col>

          <!-- 排除关键词 -->
          <v-col cols="12" md="6">
            <v-text-field
              v-model="filters.exclude"
              label="必须排除"
              variant="outlined"
              density="compact"
              hint="标题必须排除的关键词"
              persistent-hint
              clearable
            />
          </v-col>

          <!-- 语言 -->
          <v-col cols="12" md="6">
            <v-select
              v-model="filters.language"
              :items="languageOptions"
              label="语言"
              variant="outlined"
              density="compact"
              clearable
            />
          </v-col>

          <!-- 资源分类 -->
          <v-col cols="12" md="6">
            <v-select
              v-model="filters.category"
              :items="categoryOptions"
              label="资源分类"
              variant="outlined"
              density="compact"
              clearable
            />
          </v-col>

          <!-- 编码格式 -->
          <v-col cols="12" md="6">
            <v-select
              v-model="filters.encoding"
              :items="encodingOptions"
              label="编码格式"
              variant="outlined"
              density="compact"
              clearable
            />
          </v-col>

          <!-- 来源（资源来源，如 BluRay、WEB-DL 等） -->
          <v-col cols="12" md="6">
            <v-select
              v-model="filters.source"
              :items="sourceOptions"
              label="资源来源"
              variant="outlined"
              density="compact"
              clearable
            />
          </v-col>

          <!-- Phase EXT-4: 索引来源过滤（本地/外部） -->
          <v-col cols="12" md="6">
            <v-select
              v-model="filters.index_source"
              :items="indexSourceOptions"
              label="索引来源"
              variant="outlined"
              density="compact"
              clearable
              hint="过滤搜索结果的索引来源"
              persistent-hint
            />
          </v-col>

          <!-- 站点选择 -->
          <v-col cols="12">
            <v-autocomplete
              v-model="filters.sites"
              :items="siteOptions"
              label="搜索站点"
              variant="outlined"
              density="compact"
              multiple
              chips
              clearable
              hint="选择要搜索的站点，不选则搜索所有站点"
              persistent-hint
            />
          </v-col>

          <!-- Phase 9: HR 过滤 -->
          <v-col cols="12" md="6">
            <v-select
              v-model="filters.hr_filter"
              :items="hrFilterOptions"
              label="HR 过滤"
              variant="outlined"
              density="compact"
              clearable
              hint="过滤 HR 种子（来自本地索引）"
              persistent-hint
            />
          </v-col>
        </v-row>

        <v-row class="mt-2">
          <v-col cols="12" class="d-flex justify-end ga-2">
            <v-btn
              variant="text"
              @click="resetFilters"
            >
              重置
            </v-btn>
            <v-btn
              color="primary"
              @click="applyFilters"
            >
              应用筛选
            </v-btn>
          </v-col>
        </v-row>
      </v-expansion-panel-text>
    </v-expansion-panel>

    <v-expansion-panel title="排序选项" value="sort">
      <v-expansion-panel-text>
        <v-row>
          <v-col cols="12" md="6">
            <v-select
              v-model="sortBy"
              :items="sortOptions"
              label="排序方式"
              variant="outlined"
              density="compact"
            />
          </v-col>

          <v-col cols="12" md="6">
            <v-select
              v-model="sortOrder"
              :items="sortOrderOptions"
              label="排序顺序"
              variant="outlined"
              density="compact"
            />
          </v-col>
        </v-row>
      </v-expansion-panel-text>
    </v-expansion-panel>
  </v-expansion-panels>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import api from '@/services/api'

interface Filters {
  media_type: string | null
  year: number | null
  resolution: string | null
  quality: string | null
  min_size: number | null
  max_size: number | null
  min_seeders: number | null
  max_seeders: number | null
  include: string | null
  exclude: string | null
  language: string | null
  category: string | null
  encoding: string | null
  source: string | null
  sites: number[] | null
  hr_filter: string | null  // Phase 9: HR 过滤
  index_source: string | null  // Phase EXT-4: 索引来源
}

const props = defineProps<{
  modelValue: Filters
  sortBy?: string
  sortOrder?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [filters: Filters]
  'update:sortBy': [sortBy: string]
  'update:sortOrder': [sortOrder: string]
  'apply': []
}>()

const expanded = ref<string[]>([])

const filters = reactive<Filters>({
  media_type: null,
  year: null,
  resolution: null,
  quality: null,
  min_size: null,
  max_size: null,
  min_seeders: null,
  max_seeders: null,
  include: null,
  exclude: null,
  language: null,
  category: null,
  encoding: null,
  source: null,
  sites: null,
  hr_filter: null,  // Phase 9: HR 过滤
  index_source: null  // Phase EXT-4: 索引来源
})

const hrFilterOptions = [
  { title: '全部', value: null },
  { title: '排除 HR', value: 'exclude_hr' },
  { title: '仅 HR', value: 'hr_only' }
]

const sortBy = computed({
  get: () => props.sortBy || 'seeders',
  set: (value) => emit('update:sortBy', value)
})

const sortOrder = computed({
  get: () => props.sortOrder || 'desc',
  set: (value) => emit('update:sortOrder', value)
})

const mediaTypes = [
  { title: '全部', value: null },
  { title: '电影', value: 'movie' },
  { title: '电视剧', value: 'tv' },
  { title: '动漫', value: 'anime' }
]

const resolutions = [
  { title: '全部', value: null },
  { title: '4K (2160p)', value: '2160p' },
  { title: '1080p', value: '1080p' },
  { title: '720p', value: '720p' },
  { title: '480p', value: '480p' }
]

const qualities = [
  { title: '全部', value: null },
  { title: '4K', value: '4K' },
  { title: '1080p', value: '1080p' },
  { title: '720p', value: '720p' },
  { title: '480p', value: '480p' }
]

const sortOptions = [
  { title: '评分', value: 'score' },
  { title: '做种数', value: 'seeders' },
  { title: '大小', value: 'size' },
  { title: '上传时间', value: 'date' }
]

const sortOrderOptions = [
  { title: '降序', value: 'desc' },
  { title: '升序', value: 'asc' }
]

const siteOptions = ref<Array<{ title: string; value: number }>>([])

const languageOptions = [
  { title: '全部', value: null },
  { title: '中文', value: 'Chinese' },
  { title: '英语', value: 'English' },
  { title: '日语', value: 'Japanese' },
  { title: '韩语', value: 'Korean' },
  { title: '法语', value: 'French' },
  { title: '德语', value: 'German' },
  { title: '西班牙语', value: 'Spanish' }
]

const categoryOptions = [
  { title: '全部', value: null },
  { title: '电影', value: 'Movie' },
  { title: '电视剧', value: 'TV' },
  { title: '动漫', value: 'Anime' },
  { title: '音乐', value: 'Music' },
  { title: '软件', value: 'Software' },
  { title: '游戏', value: 'Game' }
]

const encodingOptions = [
  { title: '全部', value: null },
  { title: 'H.264', value: 'H.264' },
  { title: 'H.265', value: 'H.265' },
  { title: 'AV1', value: 'AV1' },
  { title: 'VP9', value: 'VP9' }
]

const sourceOptions = [
  { title: '全部', value: null },
  { title: 'BluRay', value: 'BluRay' },
  { title: 'WEB-DL', value: 'WEB-DL' },
  { title: 'WEBRip', value: 'WEBRip' },
  { title: 'HDTV', value: 'HDTV' },
  { title: 'DVD', value: 'DVD' },
  { title: 'Remux', value: 'Remux' }
]

// Phase EXT-4: 索引来源过滤选项
const indexSourceOptions = [
  { title: '全部', value: null },
  { title: '本地索引', value: 'local' },
  { title: '外部索引', value: 'external' }
]

const resetFilters = () => {
  Object.assign(filters, {
    media_type: null,
    year: null,
    resolution: null,
    quality: null,
    min_size: null,
    max_size: null,
    min_seeders: null,
    max_seeders: null,
    include: null,
    exclude: null,
    language: null,
    category: null,
    encoding: null,
    source: null,
    sites: null
  })
  emit('apply')
}

const applyFilters = () => {
  emit('update:modelValue', { ...filters })
  emit('apply')
}

const loadSites = async () => {
  try {
    const response = await api.get('/sites?active_only=true')
    siteOptions.value = response.data.map((s: any) => ({
      title: s.name,
      value: s.id
    }))
  } catch (error) {
    console.error('加载站点列表失败:', error)
  }
}

watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    Object.assign(filters, newVal)
  }
}, { deep: true, immediate: true })

onMounted(() => {
  loadSites()
})
</script>

<style scoped>
.search-filters {
  margin-bottom: 16px;
}
</style>

