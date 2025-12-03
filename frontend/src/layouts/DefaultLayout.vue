<template>
  <v-app>
    <!-- 顶部导航栏 -->
    <AppBar />
    
    <!-- 侧边栏导航 -->
    <AppDrawer />
    
    <!-- 主内容区 -->
    <v-main>
      <v-container fluid class="pa-4">
        <slot />
      </v-container>
    </v-main>
    
    <!-- 底部栏（可选） -->
    <AppFooter v-if="showFooter" />
    
    <!-- 全局搜索栏（快捷键触发） -->
    <GlobalSearchDialog v-model="searchDialog" />
    
    <!-- 音乐播放器（底部固定） -->
    <MusicPlayer v-if="showMusicPlayer" />
  </v-app>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAppStore } from '@/stores/app'
import AppBar from './components/AppBar.vue'
import AppDrawer from './components/AppDrawer.vue'
import AppFooter from './components/AppFooter.vue'
import GlobalSearchDialog from '@/components/common/GlobalSearchDialog.vue'
import MusicPlayer from '@/components/music/MusicPlayer.vue'

const appStore = useAppStore()
const searchDialog = ref(false)
const showFooter = computed(() => appStore.showFooter)
const showMusicPlayer = computed(() => appStore.showMusicPlayer)

// 快捷键：Ctrl+K 打开全局搜索
const handleKeyDown = (e: KeyboardEvent) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    searchDialog.value = true
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyDown)
})
</script>

<style lang="scss" scoped>
.v-main {
  min-height: 100vh;
  background: rgb(var(--v-theme-background));
}
</style>

