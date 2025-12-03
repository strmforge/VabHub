<template>
  <v-card class="ai-recommendation-card">
    <v-img
      :src="recommendation.coverUrl || '/default-cover.png'"
      height="300"
      cover
      loading="lazy"
      :lazy-src="recommendation.coverUrl || '/default-cover.png'"
    >
      <template v-slot:placeholder>
        <div class="d-flex align-center justify-center fill-height">
          <v-progress-circular
            indeterminate
            color="grey-lighten-1"
            size="32"
          />
        </div>
      </template>
      <template v-slot:error>
        <div class="d-flex align-center justify-center fill-height">
          <v-icon size="48" color="grey-lighten-1">mdi-image-off</v-icon>
        </div>
      </template>
    </v-img>
    
    <v-card-title>{{ recommendation.title }}</v-card-title>
    <v-card-subtitle>
      <div class="d-flex align-center mb-2">
        <v-chip size="x-small" color="orange" variant="flat" class="mr-2">
          AI推荐
        </v-chip>
        <span class="text-caption">置信度: {{ (recommendation.confidence * 100).toFixed(0) }}%</span>
      </div>
    </v-card-subtitle>
    
    <v-card-text>
      <div class="text-caption text-medium-emphasis mb-2">推荐理由：</div>
      <div class="text-body-2">{{ recommendation.reason }}</div>
    </v-card-text>
    
    <v-card-actions>
      <v-btn
        color="primary"
        variant="text"
        size="small"
        @click="handleAction('view')"
      >
        查看
      </v-btn>
      <v-btn
        color="primary"
        variant="text"
        size="small"
        @click="handleAction('subscribe')"
      >
        订阅
      </v-btn>
      <v-spacer />
      <v-btn
        icon
        size="small"
        variant="text"
        @click="handleAction('like')"
      >
        <v-icon>{{ recommendation.liked ? 'mdi-heart' : 'mdi-heart-outline' }}</v-icon>
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
interface Props {
  recommendation: any
}

defineProps<Props>()

const handleAction = (action: string) => {
  // TODO: 实现操作
  console.log('Action:', action)
}
</script>

<style lang="scss" scoped>
.ai-recommendation-card {
  transition: var(--vabhub-transition);
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: var(--vabhub-shadow-lg);
  }
}
</style>

