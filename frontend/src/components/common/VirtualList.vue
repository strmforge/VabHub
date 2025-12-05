<template>
  <div ref="containerRef" class="virtual-list-container" :style="containerStyle">
    <div
      ref="scrollContainerRef"
      class="virtual-list-scroll"
      :style="scrollContainerStyle"
      @scroll="handleScroll"
    >
      <!-- 占位空间（上方） -->
      <div :style="{ height: `${offsetY}px` }" />
      
      <!-- 可见项 -->
      <div class="virtual-list-items">
        <slot
          v-for="(item, index) in visibleItems"
          :key="getItemKey(item, startIndex + index)"
          :item="item"
          :index="startIndex + index"
        />
      </div>
      
      <!-- 占位空间（下方） -->
      <div :style="{ height: `${remainingHeight}px` }" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

interface Props {
  items: any[]
  itemHeight: number
  containerHeight?: number
  overscan?: number
  getItemKey?: (item: any, index: number) => string | number
  containerStyle?: Record<string, any>
}

const props = withDefaults(defineProps<Props>(), {
  containerHeight: 400,
  overscan: 5,
  getItemKey: (item: any, index: number) => index,
  containerStyle: () => ({})
})

const containerRef = ref<HTMLElement | null>(null)
const scrollContainerRef = ref<HTMLElement | null>(null)
const scrollTop = ref(0)

const handleScroll = (event: Event) => {
  const target = event.target as HTMLElement
  scrollTop.value = target.scrollTop
}

// 计算可见范围
const startIndex = computed(() => {
  const index = Math.floor(scrollTop.value / props.itemHeight)
  return Math.max(0, index - props.overscan)
})

const endIndex = computed(() => {
  const visibleCount = Math.ceil(props.containerHeight / props.itemHeight)
  const index = startIndex.value + visibleCount + props.overscan * 2
  return Math.min(props.items.length, index)
})

// 可见项
const visibleItems = computed(() => {
  return props.items.slice(startIndex.value, endIndex.value)
})

// 上方占位高度
const offsetY = computed(() => {
  return startIndex.value * props.itemHeight
})

// 下方占位高度
const remainingHeight = computed(() => {
  const remaining = props.items.length - endIndex.value
  return remaining * props.itemHeight
})

// 滚动容器样式
const scrollContainerStyle = computed((): Record<string, string> => {
  return {
    height: `${props.containerHeight}px`,
    overflowY: 'auto',
    ...props.containerStyle
  }
})

// 监听items变化，重置滚动位置
watch(() => props.items.length, () => {
  if (scrollContainerRef.value) {
    scrollTop.value = 0
    scrollContainerRef.value.scrollTop = 0
  }
})

onMounted(() => {
  // 可以在这里添加其他初始化逻辑
})

onUnmounted(() => {
  // 清理工作
})
</script>

<style scoped lang="scss">
.virtual-list-container {
  width: 100%;
  height: 100%;
}

.virtual-list-scroll {
  width: 100%;
  position: relative;
}

.virtual-list-items {
  width: 100%;
}
</style>

