<template>
  <v-bottom-sheet
    v-model="modelValue"
    persistent
    :height="80"
  >
    <v-card class="music-player">
      <v-card-text class="d-flex align-center pa-2">
        <!-- 当前播放信息 -->
        <div class="d-flex align-center flex-grow-1">
          <v-avatar size="56" class="mr-3">
            <v-img :src="currentTrack?.coverUrl || '/default-music-cover.png'" />
          </v-avatar>
          <div class="flex-grow-1">
            <div class="text-subtitle-1 font-weight-bold">{{ currentTrack?.title || '未播放' }}</div>
            <div class="text-caption text-medium-emphasis">{{ currentTrack?.artist || '选择音乐开始播放' }}</div>
          </div>
        </div>
        
        <!-- 播放控制 -->
        <div class="d-flex align-center mx-4">
          <v-btn icon variant="text" size="small">
            <v-icon>mdi-skip-previous</v-icon>
          </v-btn>
          <v-btn icon variant="text" size="large" color="primary">
            <v-icon>{{ isPlaying ? 'mdi-pause' : 'mdi-play' }}</v-icon>
          </v-btn>
          <v-btn icon variant="text" size="small">
            <v-icon>mdi-skip-next</v-icon>
          </v-btn>
        </div>
        
        <!-- 进度条 -->
        <div class="flex-grow-1 mx-4">
          <v-slider
            :model-value="progress"
            :max="100"
            hide-details
            density="compact"
            color="primary"
          />
          <div class="d-flex justify-space-between text-caption text-medium-emphasis">
            <span>{{ formatTime(currentTime) }}</span>
            <span>{{ formatTime(duration) }}</span>
          </div>
        </div>
        
        <!-- 音量和其他控制 -->
        <div class="d-flex align-center">
          <v-btn icon variant="text" size="small">
            <v-icon>mdi-volume-high</v-icon>
          </v-btn>
          <v-btn icon variant="text" size="small" @click="modelValue = false">
            <v-icon>mdi-chevron-down</v-icon>
          </v-btn>
        </div>
      </v-card-text>
    </v-card>
  </v-bottom-sheet>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

const modelValue = computed({
  get: () => appStore.showMusicPlayer,
  set: (value) => {
    appStore.showMusicPlayer = value
  }
})

const isPlaying = ref(false)
const progress = ref(0)
const currentTime = ref(0)
const duration = ref(0)
const currentTrack = ref<any>(null)

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style lang="scss" scoped>
.music-player {
  border-top: 1px solid rgba(var(--v-border-color), 0.12);
}
</style>

