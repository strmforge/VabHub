<template>
  <v-card
    class="stat-card"
    :class="{ 'stat-card--hover': hover }"
    @click="$emit('click')"
  >
    <v-card-text class="pa-4">
      <div class="d-flex justify-space-between align-center mb-2">
        <span class="text-caption text-medium-emphasis">{{ title }}</span>
        <v-icon :color="color" size="small">{{ icon }}</v-icon>
      </div>
      
      <div class="text-h4 font-weight-bold mb-2" :class="`text-${color}`">
        {{ formattedValue }}
      </div>
      
      <!-- 趋势指示 -->
      <div v-if="trend" class="d-flex align-center">
        <v-icon
          :color="trend.positive ? 'success' : 'error'"
          size="x-small"
          class="mr-1"
        >
          {{ trend.positive ? 'mdi-trending-up' : 'mdi-trending-down' }}
        </v-icon>
        <span
          class="text-caption"
          :class="trend.positive ? 'text-success' : 'text-error'"
        >
          {{ trend.positive ? '+' : '' }}{{ trend.value }}%
        </span>
      </div>
      
      <!-- 进度条 -->
      <v-progress-linear
        v-if="progress !== undefined"
        :model-value="progress"
        :color="color"
        height="4"
        rounded
        class="mt-2"
      />
      
      <!-- 副标题 -->
      <div v-if="subtitle" class="text-caption text-medium-emphasis mt-1">
        {{ subtitle }}
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  title: string
  value: string | number
  icon?: string
  color?: string
  trend?: {
    value: number
    positive: boolean
  }
  progress?: number
  subtitle?: string
  hover?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  icon: 'mdi-chart-line',
  color: 'primary',
  hover: true
})

const formattedValue = computed(() => {
  if (typeof props.value === 'number') {
    return props.value.toLocaleString()
  }
  return props.value
})
</script>

<style lang="scss" scoped>
.stat-card {
  transition: var(--vabhub-transition);
  height: 100%;
  
  &--hover:hover {
    transform: translateY(-4px);
    box-shadow: var(--vabhub-shadow-lg);
  }
}
</style>

