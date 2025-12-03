<template>
  <div class="vabhub-logo" :class="{ 'with-text': showText, 'glow': glow }">
    <!-- Logo图标 -->
    <div class="logo-icon" :style="iconStyle">
      <svg
        viewBox="0 0 120 120"
        class="logo-svg"
        :width="size"
        :height="size"
      >
        <!-- 渐变定义 -->
        <defs>
          <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#00D4FF;stop-opacity:1" />
            <stop offset="50%" style="stop-color:#0099FF;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#0066CC;stop-opacity:1" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>
        
        <!-- 圆角方形背景 -->
        <rect
          x="10"
          y="10"
          width="100"
          height="100"
          rx="20"
          ry="20"
          fill="url(#logoGradient)"
          filter="url(#glow)"
          class="logo-square"
        />
        
        <!-- 播放按钮（三角形） -->
        <polygon
          points="45,35 45,85 80,60"
          fill="rgba(255,255,255,0.3)"
          class="play-button"
        />
      </svg>
    </div>
    
    <!-- Logo文字 -->
    <span v-if="showText" class="logo-text" :style="textStyle">
      VabHub
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  size?: number
  showText?: boolean
  glow?: boolean
  variant?: 'light' | 'dark'
}

const props = withDefaults(defineProps<Props>(), {
  size: 48,
  showText: false,
  glow: true,
  variant: 'dark'
})

const iconStyle = computed(() => ({
  width: `${props.size}px`,
  height: `${props.size}px`
}))

const textStyle = computed(() => ({
  fontSize: props.size >= 48 ? '1.5rem' : '1.25rem',
  color: props.variant === 'dark' ? '#0066CC' : 'rgba(255, 255, 255, 0.95)'
}))
</script>

<style lang="scss" scoped>
.vabhub-logo {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  
  &.with-text {
    flex-direction: column;
    gap: 8px;
  }
  
  &.glow .logo-square {
    filter: drop-shadow(0 0 8px rgba(0, 212, 255, 0.6));
  }
}

.logo-icon {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  
  .logo-svg {
    display: block;
  }
  
  .logo-square {
    transition: filter 0.3s ease;
  }
  
  .play-button {
    transition: opacity 0.3s ease;
  }
  
  &:hover .logo-square {
    filter: drop-shadow(0 0 12px rgba(0, 212, 255, 0.8));
  }
  
  &:hover .play-button {
    opacity: 0.5;
  }
}

.logo-text {
  font-family: 'Roboto', 'Noto Sans SC', sans-serif;
  font-weight: 600;
  letter-spacing: 0.5px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: color 0.3s ease;
}

// 响应式调整
@media (max-width: 600px) {
  .vabhub-logo.with-text {
    gap: 6px;
  }
  
  .logo-text {
    font-size: 1rem !important;
  }
}
</style>

