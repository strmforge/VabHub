<template>
  <v-avatar
    :size="size"
    :color="fallbackColor"
    rounded
    class="site-avatar"
  >
    <!-- 本地资源Logo（优先） -->
    <img
      v-if="localLogoUrl && !localLogoError"
      :src="localLogoUrl"
      :alt="siteName"
      class="site-avatar-img"
      @error="handleLocalLogoError"
    />
    <!-- 缓存或预设图标（base64） -->
    <img
      v-else-if="iconData?.base64 && !imageError"
      :src="iconData.base64"
      :alt="siteName"
      class="site-avatar-img"
      @error="handleImageError"
    />
    <!-- URL图标 -->
    <img
      v-else-if="iconData?.url && !imageError"
      :src="iconData.url"
      :alt="siteName"
      class="site-avatar-img"
      @error="handleImageError"
    />
    <!-- SVG图标 -->
    <div
      v-else-if="iconData?.svg"
      v-html="iconData.svg"
      class="site-avatar-svg"
    />
    <!-- 默认图标 -->
    <v-icon v-else>mdi-web</v-icon>
  </v-avatar>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/services/api'

interface Props {
  siteId: number
  siteName: string
  siteUrl?: string
  size?: number
  fallbackColor?: string
}

const props = withDefaults(defineProps<Props>(), {
  size: 40,
  fallbackColor: 'primary'
})

const iconData = ref<{
  type?: string
  url?: string | null
  base64?: string | null
  svg?: string | null
} | null>(null)
const imageError = ref(false)
const localLogoError = ref(false)
const loading = ref(false)

// 本地Logo资源路径（参考包设计）
const localLogoUrl = computed(() => {
  if (localLogoError.value) return null
  return `/assets/site-logos/${props.siteId}.svg`
})

const loadIcon = async () => {
  if (loading.value) return
  
  loading.value = true
  imageError.value = false
  
  try {
    const response = await api.get(`/sites/${props.siteId}/icon`, {
      params: { size: props.size }
    })
    
    if (response.data) {
      iconData.value = response.data
    }
  } catch (error: any) {
    console.error('加载站点图标失败:', error)
    // 失败时使用默认图标
    iconData.value = null
  } finally {
    loading.value = false
  }
}

const handleImageError = () => {
  imageError.value = true
  // 如果URL图片加载失败，尝试使用SVG
  if (iconData.value?.url && !iconData.value.svg) {
    // 可以在这里触发生成SVG图标的请求
  }
}

const handleLocalLogoError = () => {
  localLogoError.value = true
  // 本地Logo加载失败，继续尝试后端API
  loadIcon()
}

const refreshIcon = async () => {
  try {
    const response = await api.post(`/sites/${props.siteId}/icon/refresh`)
    if (response.data) {
      iconData.value = response.data
      imageError.value = false
    }
  } catch (error: any) {
    console.error('刷新站点图标失败:', error)
  }
}

// 暴露刷新方法
defineExpose({
  refresh: refreshIcon
})

onMounted(() => {
  // 先尝试本地资源，如果失败再加载后端API
  // 本地资源通过img标签的@error自动处理
  if (!localLogoUrl.value) {
    loadIcon()
  }
})

// 监听siteId变化
watch(() => props.siteId, () => {
  loadIcon()
})
</script>

<style scoped lang="scss">
.site-avatar {
  flex-shrink: 0;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  .site-avatar-svg {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    
    :deep(svg) {
      width: 100%;
      height: 100%;
    }
  }
}
</style>

