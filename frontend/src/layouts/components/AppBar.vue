<template>
  <v-app-bar
    :elevation="2"
    color="surface"
    class="app-bar"
  >
    <!-- 左侧：Logo和菜单按钮 -->
    <v-app-bar-nav-icon
      @click="toggleDrawer"
      class="d-lg-none"
    />
    
    <v-toolbar-title class="d-flex align-center">
      <router-link to="/dashboard" class="text-decoration-none d-flex align-center">
        <VabHubLogo :size="40" :show-text="false" class="mr-2" />
        <span class="text-h6 font-weight-bold d-none d-sm-flex">VabHub</span>
      </router-link>
    </v-toolbar-title>
    
    <!-- 中间：全局搜索栏 -->
    <v-spacer />
    <GlobalSearchBar class="mx-4" />
    <v-spacer />
    
    <!-- 右侧：快捷操作 -->
    <div class="d-flex align-center">
      <!-- 主题切换 -->
      <v-btn
        icon
        variant="text"
        @click="toggleTheme"
        :title="isDark ? '切换到浅色模式' : '切换到深色模式'"
      >
        <v-icon>{{ isDark ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon>
      </v-btn>
      
      <!-- 用户通知铃铛 -->
      <NotificationBell />
      
      <!-- 通知中心（保留原有功能，可选） -->
      <v-btn
        icon
        variant="text"
        @click="notificationDrawer = true"
        class="d-none"
      >
        <v-badge
          :content="unreadCount"
          :model-value="unreadCount > 0"
          color="error"
        >
          <v-icon>mdi-bell-outline</v-icon>
        </v-badge>
      </v-btn>
      
      <!-- 快速操作菜单 -->
      <v-menu>
        <template v-slot:activator="{ props }">
          <v-btn
            icon
            variant="text"
            v-bind="props"
          >
            <v-icon>mdi-dots-vertical</v-icon>
          </v-btn>
        </template>
        <v-list>
          <v-list-item prepend-icon="mdi-music" to="/music">
            <v-list-item-title>音乐库</v-list-item-title>
          </v-list-item>
          <v-list-item prepend-icon="mdi-lightbulb-on" to="/recommendations">
            <v-list-item-title>AI推荐</v-list-item-title>
          </v-list-item>
          <v-list-item prepend-icon="mdi-cog" to="/settings">
            <v-list-item-title>设置</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
      
      <!-- 用户菜单 -->
      <v-menu>
        <template v-slot:activator="{ props }">
          <v-btn
            icon
            variant="text"
            v-bind="props"
            class="position-relative"
          >
            <v-avatar size="32">
              <v-img :src="userAvatar" />
            </v-avatar>
            <!-- 更新提示徽章 -->
            <v-badge
              v-if="hasUpdate"
              color="error"
              dot
              location="top end"
              offset-x="2"
              offset-y="2"
            />
          </v-btn>
        </template>
        <v-list>
          <v-list-item prepend-icon="mdi-account" to="/profile">
            <v-list-item-title>个人资料</v-list-item-title>
          </v-list-item>
          <v-list-item prepend-icon="mdi-palette" @click="toggleTheme">
            <v-list-item-title>切换主题</v-list-item-title>
          </v-list-item>
          
          <!-- 更新状态 -->
          <v-divider />
          <v-list-item
            v-if="hasUpdate"
            prepend-icon="mdi-update"
            @click="showUpdateDialog = true"
            class="bg-warning"
          >
            <v-list-item-title>
              <span class="font-weight-bold">发现新版本</span>
            </v-list-item-title>
            <v-list-item-subtitle>
              {{ updateInfo.current_version }} → {{ updateInfo.new_version }}
            </v-list-item-subtitle>
          </v-list-item>
          
          <!-- 重启选项 -->
          <v-list-item
            prepend-icon="mdi-restart"
            @click="handleRestart"
            :disabled="restarting"
          >
            <v-list-item-title>
              {{ hasUpdate ? '重启并更新' : '重启系统' }}
            </v-list-item-title>
            <template v-slot:append v-if="hasUpdate">
              <v-chip size="x-small" color="warning" variant="flat">更新</v-chip>
            </template>
          </v-list-item>
          
          <v-divider />
          <v-list-item prepend-icon="mdi-logout" @click="logout">
            <v-list-item-title>退出登录</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
      
      <!-- 更新对话框 -->
      <v-dialog v-model="showUpdateDialog" max-width="600">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon color="primary" class="me-2">mdi-update</v-icon>
            系统更新
          </v-card-title>
          <v-card-text>
            <v-alert type="info" variant="tonal" class="mb-4">
              <div class="text-body-2">
                <strong>发现新版本！</strong>
              </div>
              <div class="text-caption mt-2">
                当前版本: {{ updateInfo.current_version }}<br />
                最新版本: {{ updateInfo.new_version }}
              </div>
            </v-alert>
            <div class="text-body-2 mb-2">更新方式：</div>
            <v-radio-group v-model="selectedUpdateMode" inline>
              <v-radio label="仅重启" value="restart" />
              <v-radio label="更新并重启" value="update" />
            </v-radio-group>
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn variant="text" @click="showUpdateDialog = false">取消</v-btn>
            <v-btn
              color="primary"
              @click="handleUpdateAndRestart"
              :loading="updating"
            >
              {{ selectedUpdateMode === 'update' ? '更新并重启' : '仅重启' }}
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </div>
    
    <!-- 通知抽屉 -->
    <NotificationDrawer v-model="notificationDrawer" />
  </v-app-bar>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import { useToast } from 'vue-toastification'
import api from '@/services/api'
import GlobalSearchBar from '@/components/common/GlobalSearchBar.vue'
import NotificationDrawer from '@/components/common/NotificationDrawer.vue'
import NotificationBell from '@/components/layout/NotificationBell.vue'
import VabHubLogo from '@/components/common/VabHubLogo.vue'

const appStore = useAppStore()
const authStore = useAuthStore()
const toast = useToast()

// 主题相关
const isDark = computed(() => appStore.isDark)

const notificationDrawer = ref(false)
const unreadCount = computed(() => appStore.unreadNotifications)
const userAvatar = computed(() => authStore.user?.avatar || '/default-avatar.png')

// 更新相关状态
const hasUpdate = ref(false)
const updateInfo = ref<any>({})
const showUpdateDialog = ref(false)
const selectedUpdateMode = ref<'restart' | 'update'>('update')
const updating = ref(false)
const restarting = ref(false)

// 定期检查更新的定时器
let updateCheckInterval: number | null = null

const toggleDrawer = () => {
  appStore.toggleDrawer()
}

const toggleTheme = () => {
  appStore.toggleTheme()
}

const logout = () => {
  authStore.logout()
}

// 检查更新
const checkUpdate = async () => {
  try {
    const response = await api.get('/system/update/check')
    const data = response.data
    
    if (data.has_update) {
      hasUpdate.value = true
      updateInfo.value = {
        current_version: data.current_version || data.current_image,
        new_version: data.remote_info?.latest_release || data.new_image_id?.substring(0, 8) || '最新版本',
        deployment_type: data.deployment_type
      }
    } else {
      hasUpdate.value = false
    }
  } catch (error: any) {
    console.error('检查更新失败:', error)
    // 静默失败，不影响用户体验
  }
}

// 处理重启
const handleRestart = async () => {
  if (!confirm('确定要重启系统吗？重启后您需要重新登录。')) {
    return
  }
  
  restarting.value = true
  try {
    const response = await api.post('/system/restart')
    toast.info('系统正在重启，请稍候...')
    
    // 等待一段时间后刷新页面
    setTimeout(() => {
      window.location.reload()
    }, 3000)
  } catch (error: any) {
    console.error('重启失败:', error)
    toast.error(error.message || '重启失败')
    restarting.value = false
  }
}

// 处理更新并重启
const handleUpdateAndRestart = async () => {
  updating.value = true
  try {
    if (selectedUpdateMode.value === 'update') {
      // 先更新
      const updateResponse = await api.post('/system/update', {
        mode: 'release'
      })
      
      if (!updateResponse.data.success) {
        toast.error(updateResponse.data.message || '更新失败')
        updating.value = false
        return
      }
      
      toast.success('更新成功，正在重启...')
    }
    
    // 重启
    await handleRestart()
  } catch (error: any) {
    console.error('更新并重启失败:', error)
    toast.error(error.message || '更新并重启失败')
    updating.value = false
  }
}

// 启动时检查更新，然后每30分钟检查一次
onMounted(() => {
  checkUpdate()
  updateCheckInterval = window.setInterval(checkUpdate, 30 * 60 * 1000) // 30分钟
})

onUnmounted(() => {
  if (updateCheckInterval) {
    clearInterval(updateCheckInterval)
  }
})
</script>

<style lang="scss" scoped>
.app-bar {
  backdrop-filter: blur(10px);
  background: rgba(var(--v-theme-surface), 0.8) !important;
  border-bottom: 1px solid rgba(var(--v-border-color), 0.12);
}
</style>

