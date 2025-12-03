<template>
  <v-card
    :variant="recommendation.confidence > 0.7 ? 'elevated' : 'outlined'"
    class="recommendation-card"
    :class="{ 'high-confidence': recommendation.confidence > 0.7 }"
  >
    <!-- 媒体海报 -->
    <v-img
      :src="posterUrl"
      :alt="recommendation.media_id"
      height="200"
      cover
      class="recommendation-poster"
    >
      <template v-slot:placeholder>
        <div class="d-flex align-center justify-center fill-height">
          <v-icon size="64" color="grey-lighten-1">mdi-image-off</v-icon>
        </div>
      </template>
      
      <!-- 推荐分数 -->
      <div class="recommendation-score">
        <v-chip
          :color="getScoreColor(recommendation.score)"
          size="small"
          variant="flat"
        >
          {{ (recommendation.score * 100).toFixed(0) }}%
        </v-chip>
      </div>
    </v-img>

    <v-card-title class="text-body-1 font-weight-medium">
      {{ recommendation.media_id }}
    </v-card-title>

    <v-card-subtitle>
      <div class="d-flex align-center ga-2">
        <v-chip
          :color="getAlgorithmColor(recommendation.recommendation_type)"
          size="x-small"
          variant="flat"
        >
          {{ getAlgorithmLabel(recommendation.recommendation_type) }}
        </v-chip>
        <span class="text-caption text-medium-emphasis">
          置信度: {{ (recommendation.confidence * 100).toFixed(0) }}%
        </span>
      </div>
    </v-card-subtitle>

    <v-card-text>
      <!-- 推荐理由 -->
      <div class="recommendation-reason mb-3">
        <div class="text-caption text-medium-emphasis mb-1">推荐理由：</div>
        <div class="text-body-2">{{ recommendation.reason || '智能推荐' }}</div>
      </div>

      <!-- 操作按钮 -->
      <div class="d-flex ga-2">
        <v-btn
          size="small"
          variant="outlined"
          prepend-icon="mdi-information"
          @click="$emit('view-details', recommendation.media_id)"
        >
          详情
        </v-btn>
        <v-btn
          size="small"
          variant="outlined"
          prepend-icon="mdi-playlist-plus"
          @click="$emit('add-subscription', recommendation.media_id)"
        >
          订阅
        </v-btn>
        <v-btn
          size="small"
          variant="text"
          icon="mdi-shuffle"
          @click="$emit('view-similar', recommendation.media_id)"
        >
          <v-icon>mdi-shuffle</v-icon>
          <v-tooltip activator="parent" location="top">
            查看相似内容
          </v-tooltip>
        </v-btn>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  recommendation: {
    media_id: string
    score: number
    reason: string
    confidence: number
    recommendation_type: string
  }
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'view-details': [mediaId: string]
  'add-subscription': [mediaId: string]
  'view-similar': [mediaId: string]
}>()

const posterUrl = computed(() => {
  // TODO: 从媒体信息获取海报URL
  return `https://via.placeholder.com/300x450?text=${encodeURIComponent(props.recommendation.media_id)}`
})

const getScoreColor = (score: number) => {
  if (score >= 0.8) return 'success'
  if (score >= 0.6) return 'primary'
  if (score >= 0.4) return 'warning'
  return 'grey'
}

const getAlgorithmColor = (type: string) => {
  const colors: Record<string, string> = {
    'hybrid': 'primary',
    'collaborative': 'info',
    'content': 'success',
    'popularity': 'warning',
    'intelligent': 'purple'
  }
  return colors[type] || 'grey'
}

const getAlgorithmLabel = (type: string) => {
  const labels: Record<string, string> = {
    'hybrid': '混合',
    'collaborative': '协同',
    'content': '内容',
    'popularity': '热门',
    'intelligent': '智能'
  }
  return labels[type] || type
}
</script>

<style scoped>
.recommendation-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s, box-shadow 0.2s;
}

.recommendation-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
}

.recommendation-card.high-confidence {
  border: 2px solid rgb(var(--v-theme-primary));
}

.recommendation-poster {
  position: relative;
}

.recommendation-score {
  position: absolute;
  top: 8px;
  right: 8px;
}

.recommendation-reason {
  min-height: 40px;
}
</style>

