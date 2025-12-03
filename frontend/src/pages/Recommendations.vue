<template>
  <div class="recommendations-page">
    <PageHeader
      title="智能推荐"
      subtitle="基于AI算法的个性化内容推荐"
    >
      <template v-slot:actions>
        <v-btn
          color="primary"
          prepend-icon="mdi-cog"
          @click="showSettings = true"
        >
          推荐设置
        </v-btn>
        <v-btn
          color="primary"
          prepend-icon="mdi-refresh"
          @click="refreshRecommendations"
          :loading="loading"
        >
          刷新推荐
        </v-btn>
      </template>
    </PageHeader>

    <!-- 推荐算法选择 -->
    <v-card variant="outlined" class="mb-4">
      <v-card-text>
        <div class="d-flex align-center flex-wrap ga-2">
          <span class="text-body-2 text-medium-emphasis">推荐算法：</span>
          <v-chip-group
            v-model="selectedAlgorithm"
            mandatory
            @update:model-value="handleAlgorithmChange"
          >
            <v-chip
              v-for="algorithm in algorithms"
              :key="algorithm.value"
              :value="algorithm.value"
              filter
              variant="outlined"
            >
              {{ algorithm.label }}
            </v-chip>
          </v-chip-group>
        </div>
      </v-card-text>
    </v-card>

    <!-- 推荐列表 -->
    <div v-if="loading && recommendations.length === 0" class="text-center py-12">
      <v-progress-circular indeterminate color="primary" size="64" />
      <div class="mt-4 text-body-1 text-medium-emphasis">加载推荐中...</div>
    </div>

    <div v-else-if="recommendations.length === 0" class="text-center py-12">
      <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-lightbulb-outline</v-icon>
      <div class="text-h6 text-medium-emphasis mb-2">暂无推荐</div>
      <div class="text-body-2 text-medium-emphasis mb-4">
        开始使用系统，我们会根据您的偏好为您推荐内容
      </div>
      <v-btn color="primary" @click="refreshRecommendations">
        获取热门推荐
      </v-btn>
    </div>

    <v-row v-else>
      <v-col
        v-for="recommendation in recommendations"
        :key="recommendation.media_id"
        cols="12"
        sm="6"
        md="4"
        lg="3"
      >
        <RecommendationCard
          :recommendation="recommendation"
          @view-details="handleViewDetails"
          @add-subscription="handleAddSubscription"
          @view-similar="handleViewSimilar"
        />
      </v-col>
    </v-row>

    <!-- 推荐设置对话框 -->
    <RecommendationSettingsDialog
      v-model="showSettings"
      @save="handleSettingsSave"
    />


    <!-- 相似内容对话框 -->
    <SimilarContentDialog
      v-model="showSimilarContent"
      :media-id="selectedMediaId"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import PageHeader from '@/components/common/PageHeader.vue'
import RecommendationCard from '@/components/recommendation/RecommendationCard.vue'
import RecommendationSettingsDialog from '@/components/recommendation/RecommendationSettingsDialog.vue'
import SimilarContentDialog from '@/components/recommendation/SimilarContentDialog.vue'

const authStore = useAuthStore()
const loading = ref(false)
const showSettings = ref(false)
const showSimilarContent = ref(false)
const selectedMediaId = ref<string | null>(null)
const recommendations = ref<any[]>([])
const selectedAlgorithm = ref('hybrid')

const algorithms = [
  { value: 'hybrid', label: '混合推荐' },
  { value: 'collaborative', label: '协同过滤' },
  { value: 'content', label: '内容推荐' },
  { value: 'popularity', label: '热门推荐' }
]

const userId = computed(() => authStore.user?.id || 1)

const loadRecommendations = async () => {
  if (!userId.value) {
    console.warn('用户未登录，无法加载推荐')
    return
  }

  loading.value = true
  try {
    const response = await api.get(`/recommendations/${userId.value}`, {
      params: {
        limit: 20,
        algorithm: selectedAlgorithm.value
      }
    })
    
    recommendations.value = response.data || []
  } catch (error: any) {
    console.error('加载推荐失败:', error)
    // 如果API失败，尝试获取热门推荐作为降级方案
    if (error.response?.status === 404 || error.response?.status === 500) {
      try {
        const popularResponse = await api.get('/recommendations/popular/recommendations', {
          params: { limit: 20 }
        })
        recommendations.value = popularResponse.data.recommendations || []
      } catch (popularError) {
        console.error('获取热门推荐也失败:', popularError)
      }
    }
  } finally {
    loading.value = false
  }
}

const refreshRecommendations = async () => {
  await loadRecommendations()
}

const handleAlgorithmChange = () => {
  loadRecommendations()
}

const handleViewDetails = (mediaId: string) => {
  selectedMediaId.value = mediaId
  // TODO: 打开媒体详情对话框或跳转到详情页
  console.log('查看详情:', mediaId)
}

const handleAddSubscription = async (mediaId: string) => {
  try {
    // TODO: 打开订阅创建对话框
    console.log('添加订阅:', mediaId)
  } catch (error: any) {
    console.error('添加订阅失败:', error)
  }
}

const handleViewSimilar = (mediaId: string) => {
  selectedMediaId.value = mediaId
  showSimilarContent.value = true
}

const handleSettingsSave = async () => {
  // 重新加载推荐
  await loadRecommendations()
}

onMounted(() => {
  loadRecommendations()
})
</script>

<style scoped>
.recommendations-page {
  padding: 24px;
}
</style>
