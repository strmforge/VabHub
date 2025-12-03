<template>
  <div class="library-preview-page">
    <PageHeader
      title="媒体库"
      subtitle="统一浏览所有媒体内容"
    >
      <template v-slot:actions>
        <v-btn
          color="primary"
          prepend-icon="mdi-refresh"
          @click="loadData"
          :loading="loading"
        >
          刷新
        </v-btn>
      </template>
    </PageHeader>

    <!-- 媒体类型过滤器 -->
    <v-card class="mb-4">
      <v-card-text>
        <div class="d-flex align-center flex-wrap gap-2">
          <span class="text-body-2 text-medium-emphasis mr-2">媒体类型：</span>
          <v-chip
            v-for="type in mediaTypes"
            :key="type.value"
            :color="selectedTypes.includes(type.value) ? 'primary' : 'default'"
            :variant="selectedTypes.includes(type.value) ? 'flat' : 'outlined'"
            @click="toggleMediaType(type.value)"
            class="cursor-pointer"
          >
            <v-icon start :icon="type.icon" />
            {{ type.label }}
          </v-chip>
        </div>
      </v-card-text>
    </v-card>

    <!-- 加载状态 -->
    <div v-if="loading" class="text-center py-12">
      <v-progress-circular indeterminate color="primary" size="64" />
      <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
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

    <!-- 内容列表 -->
    <div v-else-if="previewData && previewData.items.length > 0">
      <!-- 结果统计 -->
      <div class="mb-4 text-body-2 text-medium-emphasis">
        共找到 <strong>{{ previewData.total }}</strong> 项内容
      </div>

      <!-- 卡片网格 -->
      <v-row>
        <v-col
          v-for="item in previewData.items"
          :key="`${item.media_type}-${item.id}`"
          cols="12"
          sm="6"
          md="4"
          lg="3"
          xl="2"
        >
          <LibraryPreviewCard
            :item="item"
            @click="handleCardClick(item)"
          />
        </v-col>
      </v-row>

      <!-- 分页 -->
      <div class="mt-6 d-flex justify-center">
        <v-pagination
          v-model="currentPage"
          :length="totalPages"
          :total-visible="7"
          @update:model-value="handlePageChange"
        />
      </div>
    </div>

    <!-- 空状态 -->
    <v-card v-else class="text-center py-12">
      <v-card-text>
        <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-inbox-outline</v-icon>
        <div class="text-h6 text-medium-emphasis mb-2">暂无内容</div>
        <div class="text-body-2 text-medium-emphasis">尝试调整筛选条件或刷新页面</div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { libraryApi } from '@/services/api'
import type { LibraryPreviewResponse, LibraryPreviewItem, MediaType } from '@/types/library'
import PageHeader from '@/components/common/PageHeader.vue'
import LibraryPreviewCard from '@/components/library/LibraryPreviewCard.vue'

const router = useRouter()

// 媒体类型选项
const mediaTypes = [
  { value: 'movie' as MediaType, label: '电影', icon: 'mdi-movie' },
  { value: 'tv' as MediaType, label: '剧集', icon: 'mdi-television' },
  { value: 'anime' as MediaType, label: '动漫', icon: 'mdi-animation' },
  { value: 'ebook' as MediaType, label: '电子书', icon: 'mdi-book-open-variant' },
  { value: 'audiobook' as MediaType, label: '有声书', icon: 'mdi-headphones' },
  { value: 'comic' as MediaType, label: '漫画', icon: 'mdi-book-open-page-variant' },
  { value: 'music' as MediaType, label: '音乐', icon: 'mdi-music' }
]

// 状态
const loading = ref(false)
const error = ref<string | null>(null)
const previewData = ref<LibraryPreviewResponse | null>(null)
const selectedTypes = ref<MediaType[]>(['movie', 'tv', 'anime', 'ebook', 'audiobook', 'comic', 'music'])
const currentPage = ref(1)
const pageSize = ref(20)

// 计算属性
const totalPages = computed(() => {
  if (!previewData.value) return 0
  return Math.ceil(previewData.value.total / pageSize.value)
})

// 切换媒体类型
const toggleMediaType = (type: MediaType) => {
  const index = selectedTypes.value.indexOf(type)
  if (index > -1) {
    selectedTypes.value.splice(index, 1)
  } else {
    selectedTypes.value.push(type)
  }
  currentPage.value = 1
  loadData()
}

// 加载数据
const loadData = async () => {
  loading.value = true
  error.value = null
  
  try {
    const response = await libraryApi.getPreview({
      page: currentPage.value,
      page_size: pageSize.value,
      media_types: selectedTypes.value
    })
    
    previewData.value = response.data
  } catch (err: any) {
    error.value = err.message || '加载失败，请稍后重试'
    console.error('加载媒体库预览失败:', err)
  } finally {
    loading.value = false
  }
}

// 处理分页变化
const handlePageChange = (page: number) => {
  currentPage.value = page
  loadData()
  // 滚动到顶部
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// 处理卡片点击
const handleCardClick = (item: LibraryPreviewItem) => {
  if (item.media_type === 'ebook') {
    // 电子书：跳转到作品详情页
    router.push(`/works/${item.id}`)
  } else if (item.media_type === 'audiobook') {
    // 有声书：从 extra 中获取 ebook_id，跳转到作品详情页
    const ebookId = item.extra?.ebook_id
    if (ebookId) {
      router.push(`/works/${ebookId}`)
    } else {
      console.warn('有声书项缺少 ebook_id:', item)
    }
  } else {
    // Movie/TV/Anime：暂时不做处理，或跳转到现有详情页
    console.log('点击了媒体项:', item)
    // TODO: 可以后续实现跳转到媒体详情页
  }
}

// 初始化
onMounted(() => {
  loadData()
})
</script>

<style lang="scss" scoped>
.library-preview-page {
  padding: 16px;
}

.cursor-pointer {
  cursor: pointer;
}
</style>

