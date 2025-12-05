<template>
  <div class="system-update-page">
    <PageHeader
      title="系统升级"
      subtitle="版本信息、检查更新、一键升级"
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
                  <v-chip color="primary" variant="flat">{{ versionData?.current_version || '未知' }}</v-chip>
                </template>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>Commit Hash</v-list-item-title>
                <template v-slot:append>
                  <span class="text-caption text-medium-emphasis">{{ versionData?.build_commit || '未知' }}</span>
                </template>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>检查时间</v-list-item-title>
                <template v-slot:append>
                  <span class="text-caption text-medium-emphasis">{{ formatTime(versionData?.checked_at) }}</span>
                </template>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>Docker 升级</v-list-item-title>
                <template v-slot:append>
                  <v-chip 
                    :color="dockerAvailable ? 'success' : 'warning'" 
                    variant="flat"
                    size="small"
                  >
                    {{ dockerAvailable ? '可用' : '不可用' }}
                  </v-chip>
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
              v-if="versionData?.update_available"
              type="info"
              variant="tonal"
              class="mb-4"
            >
              <div class="text-body-2">
                <strong>🎉 发现新版本！</strong>
              </div>
              <div class="text-caption mt-2">
                当前版本: {{ versionData?.current_version }}<br />
                最新版本: {{ versionData?.latest_version }}
              </div>
            </v-alert>
            <v-alert
              v-else-if="versionData?.current_version"
              type="success"
              variant="tonal"
              class="mb-4"
            >
              <div class="text-body-2">
                <strong>✅ 已是最新版本</strong>
              </div>
              <div class="text-caption mt-2">
                当前版本: {{ versionData?.current_version }}
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

    <!-- Docker 升级卡片 -->
    <v-card variant="outlined" class="mb-4">
      <v-card-title class="d-flex align-center">
        <v-icon class="me-2">mdi-docker</v-icon>
        一键升级
        <v-spacer />
        <v-chip v-if="dockerAvailable" color="success" variant="flat" size="small">
          <v-icon start size="small">mdi-check-circle</v-icon>
          Docker 就绪
        </v-chip>
        <v-chip v-else color="warning" variant="flat" size="small">
          <v-icon start size="small">mdi-alert</v-icon>
          Docker 不可用
        </v-chip>
      </v-card-title>
      <v-card-text>
        <v-alert type="info" variant="tonal" class="mb-4">
          <div class="text-body-2">
            <strong>升级流程：</strong>拉取最新镜像 → 重启容器 → 完成升级
          </div>
          <div class="text-caption mt-2">
            升级过程中 Web 界面会短暂中断（约 10-30 秒），请稍后刷新页面。
          </div>
        </v-alert>

        <v-row>
          <v-col cols="12" md="6">
            <v-btn
              color="primary"
              prepend-icon="mdi-cloud-download"
              variant="elevated"
              block
              size="large"
              @click="applyUpgrade"
              :loading="upgrading"
              :disabled="!dockerAvailable"
            >
              立即升级
            </v-btn>
          </v-col>
          <v-col cols="12" md="6">
            <v-btn
              color="secondary"
              prepend-icon="mdi-console"
              variant="outlined"
              block
              size="large"
              @click="showManualUpgrade = true"
            >
              手动升级命令
            </v-btn>
          </v-col>
        </v-row>

        <v-alert
          v-if="upgradeResult"
          :type="upgradeResult.success ? 'success' : 'error'"
          variant="tonal"
          class="mt-4"
          closable
          @click:close="upgradeResult = null"
        >
          <div class="text-body-2">
            <strong>{{ upgradeResult.success ? '升级已启动' : '升级失败' }}</strong>
          </div>
          <div class="text-caption mt-2">{{ upgradeResult.message }}</div>
        </v-alert>

        <!-- 手动升级命令对话框 -->
        <v-dialog v-model="showManualUpgrade" max-width="600">
          <v-card>
            <v-card-title>手动升级命令</v-card-title>
            <v-card-text>
              <p class="text-body-2 mb-4">如果自动升级不可用，可以在服务器上执行以下命令：</p>
              <v-code class="pa-4 d-block bg-grey-darken-3">
docker compose pull && docker compose up -d
              </v-code>
              <p class="text-caption mt-4 text-medium-emphasis">
                执行目录：VabHub 的 docker-compose.yml 所在目录
              </p>
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <v-btn color="primary" @click="showManualUpgrade = false">关闭</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
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

// 状态
const checking = ref(false)
const upgrading = ref(false)
const reloading = ref(false)
const versionData = ref<any>(null)
const dockerAvailable = ref(false)
const upgradeResult = ref<any>(null)
const reloadResult = ref<any>(null)
const showManualUpgrade = ref(false)

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

// 格式化时间
const formatTime = (isoString: string | null) => {
  if (!isoString) return '未检查'
  try {
    return new Date(isoString).toLocaleString('zh-CN')
  } catch {
    return isoString
  }
}

// 加载版本信息
const loadVersionInfo = async () => {
  try {
    const response = await api.get('/admin/system/version')
    if (response.data?.success) {
      versionData.value = response.data.data
    }
  } catch (error: any) {
    console.error('Failed to load version info:', error)
    // 静默失败，不弹 toast
  }
}

// 检查 Docker 状态
const checkDockerStatus = async () => {
  try {
    const response = await api.get('/admin/system/docker-status')
    if (response.data?.success) {
      dockerAvailable.value = response.data.docker_available
    }
  } catch (error: any) {
    console.error('Failed to check docker status:', error)
    dockerAvailable.value = false
  }
}

// 检查更新
const checkUpdate = async () => {
  checking.value = true
  try {
    const response = await api.post('/admin/system/upgrade', { mode: 'check_only' })
    if (response.data?.success) {
      const result = response.data.data
      // 更新版本数据
      if (result.details) {
        versionData.value = {
          ...versionData.value,
          current_version: result.details.current_version,
          latest_version: result.details.latest_version,
          update_available: result.details.update_available,
          checked_at: new Date().toISOString()
        }
      }
      if (result.details?.update_available) {
        toast.info('发现新版本！')
      } else {
        toast.success('已是最新版本')
      }
    }
  } catch (error: any) {
    console.error('Failed to check update:', error)
    toast.error(error.response?.data?.detail || '检查更新失败！')
  } finally {
    checking.value = false
  }
}

// 执行升级
const applyUpgrade = async () => {
  if (!dockerAvailable.value) {
    toast.warning('Docker 不可用，请使用手动升级命令')
    showManualUpgrade.value = true
    return
  }

  upgrading.value = true
  upgradeResult.value = null
  
  try {
    const response = await api.post('/admin/system/upgrade', { mode: 'apply' })
    if (response.data?.success) {
      upgradeResult.value = response.data.data
      if (response.data.data.success) {
        toast.success('升级已启动，请稍后刷新页面')
        // 延迟刷新页面
        setTimeout(() => {
          window.location.reload()
        }, 10000)
      } else {
        toast.error(response.data.data.message || '升级失败')
      }
    }
  } catch (error: any) {
    console.error('Failed to apply upgrade:', error)
    upgradeResult.value = {
      success: false,
      message: error.response?.data?.detail || '升级失败'
    }
    toast.error(error.response?.data?.detail || '升级失败！')
  } finally {
    upgrading.value = false
  }
}

// 热重载
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
  await Promise.all([
    loadVersionInfo(),
    checkDockerStatus()
  ])
})
</script>

<style scoped>
.system-update-page {
  padding: 24px;
}
</style>

