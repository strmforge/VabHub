<template>
  <div ref="containerRef" class="lazy-image-container" :style="containerStyle">
    <v-img
      v-if="loaded || error"
      :src="src"
      :aspect-ratio="aspectRatio"
      :cover="cover"
      :class="imageClass"
      @error="handleError"
    >
      <template #placeholder>
        <v-skeleton-loader type="image" />
      </template>
    </v-img>
    <v-skeleton-loader
      v-else
      type="image"
      :class="skeletonClass"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'

interface Props {
  src: string
  aspectRatio?: number | string
  cover?: boolean
  rootMargin?: string
  threshold?: number
  imageClass?: string
  skeletonClass?: string
  containerStyle?: Record<string, any>
}

const props = withDefaults(defineProps<Props>(), {
  aspectRatio: 1,
  cover: false,
  rootMargin: '50px',
  threshold: 0.1,
  imageClass: '',
  skeletonClass: '',
  containerStyle: () => ({})
})

const loaded = ref(false)
const error = ref(false)
const containerRef = ref<HTMLElement | null>(null)
let observer: IntersectionObserver | null = null

const handleError = () => {
  error.value = true
}

const loadImage = () => {
  if (loaded.value || error.value) return
  loaded.value = true
  if (observer && containerRef.value) {
    observer.unobserve(containerRef.value)
  }
}

onMounted(async () => {
  // 如果src为空，直接返回
  if (!props.src) {
    error.value = true
    return
  }

  // 检查浏览器是否支持IntersectionObserver
  if (!('IntersectionObserver' in window)) {
    // 不支持时直接加载
    loaded.value = true
    return
  }

  // 等待DOM更新
  await nextTick()

  // 创建IntersectionObserver
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          loadImage()
        }
      })
    },
    {
      rootMargin: props.rootMargin,
      threshold: props.threshold
    }
  )

  // 观察容器元素
  if (containerRef.value) {
    observer.observe(containerRef.value)
  }
})

onUnmounted(() => {
  if (observer && containerRef.value) {
    observer.unobserve(containerRef.value)
    observer.disconnect()
  }
})

// 监听src变化，重置状态
watch(() => props.src, async (newSrc) => {
  if (newSrc) {
    loaded.value = false
    error.value = false
    // 等待DOM更新后检查可见性
    await nextTick()
    if (containerRef.value) {
      const rect = containerRef.value.getBoundingClientRect()
      const margin = parseInt(props.rootMargin) || 50
      const isVisible = rect.top < window.innerHeight + margin &&
                       rect.bottom > -margin
      if (isVisible) {
        loadImage()
      } else if (observer && containerRef.value) {
        // 重新观察
        observer.observe(containerRef.value)
      }
    }
  } else {
    error.value = true
  }
})
</script>

<style scoped lang="scss">
.lazy-image-container {
  width: 100%;
  height: 100%;
}
</style>

