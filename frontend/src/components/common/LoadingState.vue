<template>
  <div class="loading-state" :class="{ 'fullscreen': fullscreen }">
    <v-overlay :model-value="loading" class="align-center justify-center">
      <div class="loading-content">
        <v-progress-circular
          v-if="type === 'circular'"
          indeterminate
          :size="size"
          :width="width"
          :color="color"
        />
        <v-skeleton-loader
          v-else-if="type === 'skeleton'"
          :type="skeletonType"
          class="skeleton-loader"
        />
        <div v-else-if="type === 'progress'" class="progress-container">
          <v-progress-linear
            :model-value="progress"
            :color="color"
            height="4"
            rounded
          />
          <div class="progress-text">{{ progress }}%</div>
        </div>
        <div v-if="message" class="loading-message">{{ message }}</div>
      </div>
    </v-overlay>
  </div>
</template>

<script setup lang="ts">
interface Props {
  loading: boolean
  type?: 'circular' | 'skeleton' | 'progress'
  message?: string
  fullscreen?: boolean
  size?: number
  width?: number
  color?: string
  progress?: number
  skeletonType?: string
}

withDefaults(defineProps<Props>(), {
  type: 'circular',
  fullscreen: false,
  size: 64,
  width: 4,
  color: 'primary',
  progress: 0,
  skeletonType: 'card'
})
</script>

<style scoped>
.loading-state {
  position: relative;
}

.loading-state.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.loading-message {
  color: white;
  font-size: 1rem;
  text-align: center;
}

.skeleton-loader {
  width: 100%;
  max-width: 600px;
}

.progress-container {
  width: 100%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.progress-text {
  color: white;
  font-size: 0.875rem;
  text-align: center;
}
</style>

