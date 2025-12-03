<template>
  <div class="music-recommendations">
    <!-- 推荐算法选择 -->
    <v-card class="mb-4">
      <v-card-text>
        <v-row align="center">
          <v-col cols="12" md="6">
            <v-select
              v-model="algorithm"
              :items="algorithms"
              label="推荐算法"
              variant="outlined"
              density="compact"
              @update:model-value="loadRecommendations"
            />
          </v-col>
          <v-col cols="12" md="6">
            <v-btn
              color="primary"
              prepend-icon="mdi-refresh"
              :loading="loading"
              @click="loadRecommendations"
            >
              刷新推荐
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
    
    <!-- 推荐列表 -->
    <v-card>
      <v-card-title>个性化推荐</v-card-title>
      <v-card-text>
        <div v-if="loading" class="text-center py-8">
          <v-progress-circular indeterminate color="primary" />
        </div>
        <div v-else-if="recommendations.length === 0" class="text-center py-12">
          <v-icon size="64" color="grey">mdi-lightbulb-off</v-icon>
          <div class="text-h6 mt-4">暂无推荐</div>
          <div class="text-body-2 text-medium-emphasis mt-2">
            系统需要更多数据来生成个性化推荐
          </div>
        </div>
        <v-list v-else>
          <v-list-item
            v-for="item in recommendations"
            :key="item.id"
            :prepend-avatar="item.cover_url"
            :title="item.title"
            :subtitle="item.artist"
          >
            <template v-slot:append>
              <v-btn icon variant="text" size="small" @click="playTrack(item)">
                <v-icon>mdi-play</v-icon>
              </v-btn>
            </template>
          </v-list-item>
        </v-list>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'vue-toastification'
import api from '@/services/api'

const toast = useToast()

const loading = ref(false)
const algorithm = ref('hybrid')
const recommendations = ref<any[]>([])

const algorithms = [
  { title: '混合推荐', value: 'hybrid' },
  { title: '协同过滤', value: 'collaborative' },
  { title: '内容推荐', value: 'content' }
]

const loadRecommendations = async () => {
  loading.value = true
  try {
    // TODO: 获取当前用户ID
    const userId = 'default'
    const response = await api.get(`/music/recommendations/${userId}`, {
      params: {
        count: 20,
        algorithm: algorithm.value
      }
    })
    recommendations.value = response.data?.recommendations || []
  } catch (error: any) {
    toast.error(error.message || '加载推荐失败')
    recommendations.value = []
  } finally {
    loading.value = false
  }
}

const playTrack = (track: any) => {
  // TODO: 实现播放功能
  toast.info(`播放: ${track.title}`)
}

onMounted(() => {
  loadRecommendations()
})
</script>

<style scoped>
.music-recommendations {
  padding: 0;
}
</style>

