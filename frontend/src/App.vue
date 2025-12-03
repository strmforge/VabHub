<template>
  <v-app :theme="theme">
    <!-- 根据路由决定是否使用布局 -->
    <template v-if="route.name === 'Login'">
      <!-- 登录页面：独立显示，不使用布局 -->
      <router-view />
    </template>
    <template v-else>
      <!-- 其他页面：使用布局 -->
      <AppLayout>
        <router-view />
      </AppLayout>
    </template>
    
    <!-- 全局加载遮罩 -->
    <LoadingOverlay v-if="loading" />
    
    <!-- 全局通知 -->
    <NotificationSystem />
  </v-app>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from './stores/app'
import AppLayout from './layouts/DefaultLayout.vue'
import LoadingOverlay from './components/common/LoadingOverlay.vue'
import NotificationSystem from './components/common/NotificationSystem.vue'

const route = useRoute()
const appStore = useAppStore()

const theme = computed(() => appStore.theme)
const loading = computed(() => appStore.loading)
</script>

<style lang="scss">
// 页面过渡动画
.page-enter-active,
.page-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

// 全局样式
* {
  box-sizing: border-box;
}

html {
  overflow-y: auto !important;
}

body {
  margin: 0;
  padding: 0;
  font-family: 'Roboto', 'Noto Sans SC', sans-serif;
}
</style>

