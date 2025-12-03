<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="800"
    scrollable
  >
    <v-card v-if="mediaDetails">
      <v-card-title class="d-flex align-center justify-space-between">
        <span>{{ mediaDetails.title || mediaId }}</span>
        <v-btn
          icon="mdi-close"
          variant="text"
          @click="$emit('update:modelValue', false)"
        />
      </v-card-title>

      <v-card-text>
        <v-row>
          <v-col cols="12" md="4">
            <v-img
              :src="mediaDetails.poster_url || '/default-poster.png'"
              :alt="mediaDetails.title"
              height="400"
              cover
            >
              <template v-slot:placeholder>
                <div class="d-flex align-center justify-center fill-height">
                  <v-icon size="64" color="grey-lighten-1">mdi-image-off</v-icon>
                </div>
              </template>
            </v-img>
          </v-col>
          <v-col cols="12" md="8">
            <div class="text-h5 mb-2">{{ mediaDetails.title }}</div>
            <div class="text-body-2 text-medium-emphasis mb-4">
              {{ mediaDetails.overview || '暂无描述' }}
            </div>
            
            <v-divider class="my-4" />
            
            <div class="mb-2">
              <strong>类型：</strong> {{ mediaDetails.type || '未知' }}
            </div>
            <div class="mb-2" v-if="mediaDetails.year">
              <strong>年份：</strong> {{ mediaDetails.year }}
            </div>
            <div class="mb-2" v-if="mediaDetails.rating">
              <strong>评分：</strong> {{ mediaDetails.rating }}
            </div>
            <div class="mb-2" v-if="mediaDetails.genres && mediaDetails.genres.length > 0">
              <strong>类型：</strong>
              <v-chip
                v-for="genre in mediaDetails.genres"
                :key="genre"
                size="small"
                class="mr-1"
              >
                {{ genre }}
              </v-chip>
            </div>
          </v-col>
        </v-row>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          variant="text"
          @click="$emit('update:modelValue', false)"
        >
          关闭
        </v-btn>
        <v-btn
          color="primary"
          @click="handleAddSubscription"
        >
          添加到订阅
        </v-btn>
      </v-card-actions>
    </v-card>

    <v-card v-else>
      <v-card-text class="text-center py-8">
        <v-progress-circular indeterminate color="primary" />
        <div class="mt-4 text-body-2 text-medium-emphasis">加载中...</div>
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

const mediaDetails = ref<any>(null)

const loadMediaDetails = async () => {
  if (!props.mediaId) return

  try {
    // TODO: 从媒体API获取详细信息
    // const response = await api.get(`/media/${props.mediaId}`)
    // mediaDetails.value = response.data
    
    // 临时使用模拟数据
    mediaDetails.value = {
      title: props.mediaId,
      type: 'movie',
      year: 2024,
      rating: 8.5,
      genres: ['动作', '科幻'],
      overview: '暂无描述'
    }
  } catch (error) {
    console.error('加载媒体详情失败:', error)
  }
}

const handleAddSubscription = () => {
  // TODO: 打开订阅创建对话框
  emit('update:modelValue', false)
}

watch(() => props.modelValue, (newValue) => {
  if (newValue && props.mediaId) {
    loadMediaDetails()
  }
})

watch(() => props.mediaId, () => {
  if (props.modelValue && props.mediaId) {
    loadMediaDetails()
  }
})
</script>

