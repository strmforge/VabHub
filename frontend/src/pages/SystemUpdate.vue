<template>
  <div class="system-update-page">
    <PageHeader
      title="系统更新"
      subtitle="检查更新、自动更新和热更新管理"
    />

    <v-row>
      <!-- 版本信息卡片 -->
      <v-col cols="12" md="6">
        <v-card variant="outlined" class="mb-4">
          <v-card-title class="d-flex align-center">
            <v-icon class="me-2">mdi-information</v-icon>
            当前版本信息
          </v-card-title>
          <v-card-text>
            <v-list density="compact">
              <v-list-item>
                <v-list-item-title>版本号</v-list-item-title>
                <template v-slot:append>
                  <v-chip color="primary" variant="flat">{{ versionInfo.version || '未知' }}</v-chip>
                </template>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>Commit Hash</v-list-item-title>
                <template v-slot:append>
                  <span class="text-caption text-medium-emphasis">{{ versionInfo.commit || '未知' }}</span>
                </template>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>构建时间</v-list-item-title>
                <template v-slot:append>
                  <span class="text-caption text-medium-emphasis">{{ versionInfo.build_time || '未知' }}</span>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- 更新检查卡片 -->
      <v-col cols="12" md="6">
        <v-card variant="outlined" class="mb-4">
          <v-card-title class="d-flex align-center">
            <v-icon class="me-2">mdi-update</v-icon>
            更新检查
            <v-spacer />
            <v-btn
              color="primary"
              prepend-icon="mdi-refresh"
              variant="text"
              @click="checkUpdate"
              :loading="checking"
            >
              检查更新
            </v-btn>
          </v-card-title>
          <v-card-text>
            <v-alert
              v-if="updateInfo.has_update"
              type="info"
              variant="tonal"
              class="mb-4"
            >
              <div class="text-body-2">
                <strong>发现新版本！</strong>
              </div>
              <div class="text-caption mt-2">
                当前版本: {{ updateInfo.current_version }}<br />
                最新版本: {{ updateInfo.remote_info?.latest_release || updateInfo.remote_info?.latest_commit }}
              </div>
            </v-alert>
            <v-alert
              v-else-if="updateInfo.current_version"
              type="success"
              variant="tonal"
              class="mb-4"
            >
              <div class="text-body-2">
                <strong>已是最新版本</strong>
              </div>
              <div class="text-caption mt-2">
                当前版本: {{ updateInfo.current_version }}
              </div>
            </v-alert>
            <div v-else class="text-center py-4">
              <v-icon size="48" color="grey-lighten-1">mdi-information-outline</v-icon>
              <div class="text-body-2 mt-2 text-medium-emphasis">点击"检查更新"按钮检查版本</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 更新设置卡片 -->
    <v-card variant="outlined" class="mb-4">
      <v-card-title class="d-flex align-center">
        <v-icon class="me-2">mdi-cog</v-icon>
        更新设置
      </v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="6">
            <v-select
              v-model="updateMode"
              :items="updateModeOptions"
              label="自动更新模式"
              variant="outlined"
              hint="重启时自动更新系统"
              persistent-hint
              @update:model-value="saveUpdateMode"
            />
          </v-col>
          <v-col cols="12" md="6">
            <v-switch
              v-model="autoUpdateEnabled"
              label="启用自动更新"
              color="primary"
              hide-details
              @update:model-value="saveAutoUpdateEnabled"
            />
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- 更新操作卡片 -->
    <v-card variant="outlined" class="mb-4">
      <v-card-title class="d-flex align-center">
        <v-icon class="me-2">mdi-download</v-icon>
        更新操作
      </v-card-title>
      <v-card-text>
        <v-alert type="warning" variant="tonal" class="mb-4">
          <div class="text-body-2">
            <strong>注意：</strong>系统更新需要重启才能生效。更新前请确保已保存所有重要数据。
          </div>
        </v-alert>

        <v-row>
          <v-col cols="12" md="4">
            <v-btn
              color="primary"
              prepend-icon="mdi-download"
              variant="elevated"
              block
              @click="updateSystem('release')"
              :loading="updating"
              :disabled="!updateInfo.has_update"
            >
              更新到发行版
            </v-btn>
          </v-col>
          <v-col cols="12" md="4">
            <v-btn
              color="info"
              prepend-icon="mdi-code-branch"
              variant="elevated"
              block
              @click="updateSystem('dev')"
              :loading="updating"
            >
              更新到开发版
            </v-btn>
          </v-col>
          <v-col cols="12" md="4">
            <v-btn
              color="success"
              prepend-icon="mdi-reload"
              variant="elevated"
              block
              @click="hotReload"
              :loading="reloading"
            >
              热重载模块
            </v-btn>
          </v-col>
        </v-row>

        <v-alert
          v-if="updateResult"
          :type="updateResult.success ? 'success' : 'error'"
          variant="tonal"
          class="mt-4"
          closable
          @click:close="updateResult = null"
        >
          <div class="text-body-2">
            <strong>{{ updateResult.success ? '更新成功' : '更新失败' }}</strong>
          </div>
          <div class="text-caption mt-2">{{ updateResult.message }}</div>
          <div v-if="updateResult.requires_restart" class="text-caption mt-2">
            <strong>⚠️ 需要重启系统以应用更改</strong>
          </div>
        </v-alert>
      </v-card-text>
    </v-card>

    <!-- 热重载模块卡片 -->
    <v-card variant="outlined">
      <v-card-title class="d-flex align-center">
        <v-icon class="me-2">mdi-fire</v-icon>
        热重载模块
        <v-spacer />
        <v-chip size="small" color="success" variant="flat">无需重启</v-chip>
      </v-card-title>
      <v-card-text>
        <v-alert type="info" variant="tonal" class="mb-4">
          <div class="text-body-2">
            <strong>热重载功能：</strong>无需重启系统即可重新加载模块，适用于配置更新、插件更新等场景。
          </div>
        </v-alert>

        <v-row>
          <v-col cols="12" md="6">
            <v-select
              v-model="selectedModules"
              :items="reloadableModules"
              label="选择要重载的模块"
              variant="outlined"
              multiple
              chips
              hint="留空表示重载所有可重载模块"
              persistent-hint
            />
          </v-col>
          <v-col cols="12" md="6">
            <v-btn
              color="success"
              prepend-icon="mdi-reload"
              variant="elevated"
              block
              @click="hotReloadModules"
              :loading="reloading"
            >
              执行热重载
            </v-btn>
          </v-col>
        </v-row>

        <v-alert
          v-if="reloadResult"
          :type="reloadResult.success ? 'success' : 'warning'"
          variant="tonal"
          class="mt-4"
          closable
          @click:close="reloadResult = null"
        >
          <div class="text-body-2">
            <strong>{{ reloadResult.success ? '热重载成功' : '部分模块重载失败' }}</strong>
          </div>
          <div class="text-caption mt-2">
            <div v-if="reloadResult.reloaded_modules?.length">
              成功: {{ reloadResult.reloaded_modules.join(', ') }}
            </div>
            <div v-if="reloadResult.failed_modules?.length" class="mt-1">
              失败: {{ reloadResult.failed_modules.map((m: any) => m.module).join(', ') }}
            </div>
          </div>
        </v-alert>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'vue-toastification'
import api from '@/services/api'
import PageHeader from '@/components/common/PageHeader.vue'

const toast = useToast()

const checking = ref(false)
const updating = ref(false)
const reloading = ref(false)
const versionInfo = ref<any>({})
const updateInfo = ref<any>({})
const updateResult = ref<any>(null)
const reloadResult = ref<any>(null)

const updateMode = ref('never')
const autoUpdateEnabled = ref(false)
const selectedModules = ref<string[]>([])

const updateModeOptions = [
  { title: '从不更新', value: 'never' },
  { title: '仅更新到发行版', value: 'release' },
  { title: '更新到开发版', value: 'dev' }
]

const reloadableModules = [
  { title: '分类配置', value: 'category_helper' },
  { title: '系统设置', value: 'settings' },
  { title: '插件', value: 'plugins' }
]

const loadVersionInfo = async () => {
  try {
    const response = await api.get('/system/version')
    versionInfo.value = response.data
  } catch (error: any) {
    console.error('Failed to load version info:', error)
    toast.error(error.message || '获取版本信息失败！')
  }
}

const checkUpdate = async () => {
  checking.value = true
  try {
    const response = await api.get('/system/update/check')
    updateInfo.value = response.data
    if (updateInfo.value.has_update) {
      toast.info('发现新版本！')
    } else {
      toast.success('已是最新版本')
    }
  } catch (error: any) {
    console.error('Failed to check update:', error)
    toast.error(error.message || '检查更新失败！')
  } finally {
    checking.value = false
  }
}

const updateSystem = async (mode: string) => {
  updating.value = true
  try {
    const response = await api.post('/system/update', { mode })
    updateResult.value = response.data
    
    if (response.data.requires_restart) {
      toast.warning('系统已更新，需要重启以应用更改')
    } else {
      toast.success('更新成功')
    }
    
    // 重新检查更新
    await checkUpdate()
  } catch (error: any) {
    console.error('Failed to update system:', error)
    updateResult.value = {
      success: false,
      message: error.message || '更新失败'
    }
    toast.error(error.message || '系统更新失败！')
  } finally {
    updating.value = false
  }
}

const hotReload = async () => {
  reloading.value = true
  try {
    const response = await api.post('/system/hot-reload', {})
    reloadResult.value = response.data
    toast.success('热重载完成')
  } catch (error: any) {
    console.error('Failed to hot reload:', error)
    toast.error(error.message || '热重载失败！')
  } finally {
    reloading.value = false
  }
}

const hotReloadModules = async () => {
  reloading.value = true
  try {
    const response = await api.post('/system/hot-reload', {
      modules: selectedModules.value.length > 0 ? selectedModules.value : undefined
    })
    reloadResult.value = response.data
    toast.success('模块热重载完成')
  } catch (error: any) {
    console.error('Failed to hot reload modules:', error)
    toast.error(error.message || '模块热重载失败！')
  } finally {
    reloading.value = false
  }
}

const saveUpdateMode = async () => {
  try {
    // TODO: 保存到数据库
    toast.success('更新模式已保存')
  } catch (error: any) {
    console.error('Failed to save update mode:', error)
    toast.error('保存更新模式失败！')
  }
}

const saveAutoUpdateEnabled = async () => {
  try {
    // TODO: 保存到数据库
    toast.success('自动更新设置已保存')
  } catch (error: any) {
    console.error('Failed to save auto update setting:', error)
    toast.error('保存自动更新设置失败！')
  }
}

onMounted(async () => {
  await loadVersionInfo()
  await checkUpdate()
})
</script>

<style scoped>
.system-update-page {
  padding: 24px;
}
</style>

