<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="800"
  >
    <v-card>
      <v-card-title class="d-flex align-center justify-space-between">
        <span>相似内容推荐</span>
        <v-btn
          icon="mdi-close"
          variant="text"
          @click="$emit('update:modelValue', false)"
        />
      </v-card-title>

      <v-card-text>
        <div v-if="loading" class="text-center py-8">
          <v-progress-circular indeterminate color="primary" />
          <div class="mt-4 text-body-2 text-medium-emphasis">加载相似内容中...</div>
        </div>

        <div v-else-if="similarContent.length === 0" class="text-center py-8">
          <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-information-outline</v-icon>
          <div class="text-body-1 text-medium-emphasis">暂无相似内容</div>
        </div>

        <v-list v-else>
          <v-list-item
            v-for="item in similarContent"
            :key="item.media_id"
            :title="item.media_id"
            :subtitle="`相似度: ${(item.similarity * 100).toFixed(1)}%`"
          >
            <template v-slot:prepend>
              <v-avatar
                :color="getSimilarityColor(item.similarity)"
                size="40"
              >
                <span class="text-white">{{ (item.similarity * 100).toFixed(0) }}</span>
              </v-avatar>
            </template>

            <template v-slot:append>
              <v-btn
                size="small"
                variant="text"
                @click="handleViewDetails(item.media_id)"
              >
                查看
              </v-btn>
            </template>
          </v-list-item>
        </v-list>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import api from '@/services/api'

interface Props {
  modelValue: boolean
  mediaId: string | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const loading = ref(false)
const similarContent = ref<any[]>([])

const loadSimilarContent = async () => {
  if (!props.mediaId) return

  loading.value = true
  try {
    // 获取当前用户ID
    const { useAuthStore } = await import('@/stores/auth')
    const authStore = useAuthStore()
    const userId = authStore.user?.id || 1
    
    const response = await api.get(
      `/recommendations/${userId}/similar/${props.mediaId}`,
      { params: { limit: 10 } }
    )
    
    similarContent.value = response.data.similar_content || []
  } catch (error) {
    console.error('加载相似内容失败:', error)
    similarContent.value = []
  } finally {
    loading.value = false
  }
}

const getSimilarityColor = (similarity: number) => {
  if (similarity >= 0.8) return 'success'
  if (similarity >= 0.6) return 'primary'
  if (similarity >= 0.4) return 'warning'
  return 'grey'
}

const handleViewDetails = (mediaId: string) => {
  // TODO: 打开媒体详情
  console.log('查看详情:', mediaId)
}

watch(() => props.modelValue, (newValue) => {
  if (newValue && props.mediaId) {
    loadSimilarContent()
  }
})

watch(() => props.mediaId, () => {
  if (props.modelValue && props.mediaId) {
    loadSimilarContent()
  }
})
</script>

