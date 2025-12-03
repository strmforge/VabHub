<template>
  <div class="plugins-page">
    <PageHeader
      title="插件管理"
      subtitle="启用/禁用并管理 VabHub 插件"
    >
      <template #actions>
        <v-switch
          v-model="hotReloadEnabled"
          inset
          color="primary"
          :label="`热更新 ${hotReloadEnabled ? '已开启' : '已关闭'}`"
          @change="handleHotReloadToggle"
        />
      </template>
    </PageHeader>

    <v-alert
      variant="tonal"
      type="info"
      class="mb-4"
      density="comfortable"
    >
      插件目录位于 <code>plugins/</code>。每次修改文件后，热更新会自动尝试重新加载；也可以手动点击卡片上的“重载”。
    </v-alert>

    <v-row dense>
      <v-col
        v-for="plugin in plugins"
        :key="plugin.name"
        cols="12"
        md="6"
        lg="4"
      >
        <v-card :variant="plugin.loaded ? 'flat' : 'outlined'">
          <v-card-title class="d-flex align-center justify-space-between">
            <div>
              <div class="text-subtitle-1">{{ plugin.metadata?.name ?? plugin.name }}</div>
              <div class="text-caption text-medium-emphasis">
                {{ plugin.metadata?.description || '暂无描述' }}
              </div>
            </div>
            <v-chip :color="statusColor(plugin)" size="small" variant="flat">
              {{ pluginStateLabel(plugin) }}
            </v-chip>
          </v-card-title>

          <v-card-text>
            <div class="d-flex flex-wrap ga-2 mb-2" v-if="plugin.metadata?.tags?.length">
              <v-chip
                v-for="tag in plugin.metadata?.tags"
                :key="tag"
                variant="outlined"
                size="x-small"
              >
                {{ tag }}
              </v-chip>
            </div>
            <div class="text-caption text-medium-emphasis">
              <div>版本：{{ plugin.metadata?.version ?? '未知' }}</div>
              <div>作者：{{ plugin.metadata?.author ?? '-' }}</div>
              <div>
                最近加载：
                {{ plugin.state?.loaded_at ? formatDate(plugin.state.loaded_at) : '-' }}
              </div>
              <div v-if="plugin.state?.last_error" class="text-error mt-1">
                最近错误：{{ plugin.state.last_error }}
              </div>
            </div>
          </v-card-text>

          <v-card-actions class="justify-end">
            <v-btn
              variant="text"
              prepend-icon="mdi-tune"
              @click="openConfig(plugin)"
              :disabled="!plugin.loaded"
            >
              配置
            </v-btn>
            <v-btn
              v-if="plugin.metadata?.tags?.includes('short_drama')"
              variant="text"
              prepend-icon="mdi-drama-masks"
              color="purple"
              @click="router.push({ name: 'ShortDrama' })"
            >
              短剧工作台
            </v-btn>
            <v-btn
              variant="text"
              prepend-icon="mdi-reload"
              @click="handleReload(plugin)"
            >
              重载
            </v-btn>
            <v-btn
              variant="text"
              prepend-icon="mdi-close-circle"
              color="warning"
              @click="handleUnload(plugin)"
              :disabled="!plugin.loaded"
            >
              卸载
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <v-dialog v-model="configDialog" max-width="600">
      <v-card>
        <v-card-title class="d-flex justify-space-between align-center">
          <span>配置：{{ activePlugin?.metadata?.name ?? activePlugin?.name }}</span>
          <v-btn icon="mdi-close" variant="text" @click="configDialog = false" />
        </v-card-title>
        <v-card-text>
          <v-alert
            v-if="configRows.length === 0"
            type="info"
            density="comfortable"
            variant="tonal"
          >
            当前插件未保存任何自定义配置。
          </v-alert>
          <v-row dense>
            <v-col
              v-for="(row, index) in configRows"
              :key="index"
              cols="12"
              class="d-flex ga-2"
            >
              <v-text-field
                v-model="row.key"
                label="键"
                density="compact"
                variant="outlined"
              />
              <v-text-field
                v-model="row.value"
                label="值"
                density="compact"
                variant="outlined"
                class="flex-grow-1"
              />
              <v-btn
                icon="mdi-delete"
                variant="text"
                color="error"
                @click="removeRow(index)"
              />
            </v-col>
          </v-row>
          <v-btn
            variant="text"
            prepend-icon="mdi-plus"
            @click="addRow"
          >
            新增配置项
          </v-btn>
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn variant="text" @click="configDialog = false">取消</v-btn>
          <v-btn color="primary" :loading="configSaving" @click="saveConfig">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-divider class="my-8" />

    <v-row dense>
      <v-col cols="12" md="6">
        <v-card variant="outlined">
          <v-card-title class="d-flex align-center justify-space-between">
            <span>官方插件</span>
            <v-progress-circular
              v-if="registryLoading"
              indeterminate
              size="20"
              color="primary"
            />
          </v-card-title>
          <v-card-subtitle class="text-medium-emphasis">
            来自 VabHub 官方维护的示例/套件，安装前建议查看源码。
          </v-card-subtitle>
          <v-card-text>
            <v-alert
              v-if="!registryLoading && officialRegistry.length === 0"
              type="info"
              variant="tonal"
              density="comfortable"
            >
              暂无官方插件条目。
            </v-alert>
            <v-list v-else density="compact">
              <v-list-item
                v-for="item in officialRegistry"
                :key="item.id"
              >
                <v-list-item-title class="d-flex align-center justify-space-between">
                  <span>{{ item.name || item.id }}</span>
                  <v-chip size="x-small" variant="outlined">
                    v{{ item.version || 'unknown' }}
                  </v-chip>
                </v-list-item-title>
                <v-list-item-subtitle class="text-wrap">
                  {{ item.description || '暂无描述' }}
                </v-list-item-subtitle>
                <template #append>
                  <v-btn
                    size="small"
                    variant="text"
                    prepend-icon="mdi-download"
                    @click="installPlugin(item.id)"
                  >
                    安装
                  </v-btn>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card variant="outlined">
          <v-card-title>本地/社区插件</v-card-title>
          <v-card-subtitle class="text-medium-emphasis">
            当前已放置在 <code>plugins/</code> 目录中的插件，来源可能是社区或自研。
          </v-card-subtitle>
          <v-card-text>
            <v-alert
              v-if="communityRegistry.length === 0"
              type="info"
              variant="tonal"
              density="comfortable"
            >
              暂未检测到本地插件。
            </v-alert>
            <v-list v-else density="compact">
              <v-list-item
                v-for="item in communityRegistry"
                :key="item.id"
              >
                <v-list-item-title class="d-flex align-center justify-space-between">
                  <span>{{ item.name || item.id }}</span>
                  <v-chip
                    size="x-small"
                    :color="item.installed ? 'success' : 'warning'"
                    variant="flat"
                  >
                    {{ item.installed ? '已安装' : '未安装' }}
                  </v-chip>
                </v-list-item-title>
                <v-list-item-subtitle class="text-wrap">
                  {{ item.description || '暂无描述' }}
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import PageHeader from '@/components/common/PageHeader.vue'
import {
  disableHotReload,
  enableHotReload,
  fetchPluginStatus,
  getPluginConfig,
  listPlugins,
  reloadPlugin,
  updatePluginConfig,
  unloadPlugin,
  type PluginItem
} from '@/services/plugins'
import api from '@/services/api'

const toast = useToast()
const router = useRouter()

const plugins = ref<PluginItem[]>([])
const loading = ref(false)
const hotReloadEnabled = ref(true)
const configDialog = ref(false)
const configRows = ref<{ key: string; value: string }[]>([])
const configSaving = ref(false)
const activePlugin = ref<PluginItem | null>(null)

const registryLoading = ref(false)
const officialRegistry = ref<any[]>([])
const communityRegistry = ref<any[]>([])

const fetchRegistry = async () => {
  registryLoading.value = true
  try {
    const resp = await api.get('/plugins/registry')
    const data = resp.data?.data || resp.data || {}
    officialRegistry.value = data.official || []
    communityRegistry.value = data.community || []
  } catch (error: any) {
    toast.error(error.message || '加载插件注册表失败')
  } finally {
    registryLoading.value = false
  }
}

const fetchPlugins = async () => {
  loading.value = true
  try {
    plugins.value = await listPlugins()
  } catch (error: any) {
    toast.error(error.message || '加载插件列表失败')
  } finally {
    loading.value = false
  }
}

const fetchStatus = async () => {
  try {
    const status = await fetchPluginStatus()
    if (typeof status?.hot_reload_enabled === 'boolean') {
      hotReloadEnabled.value = status.hot_reload_enabled
    }
  } catch (error: any) {
    toast.error(error.message || '获取插件状态失败')
  }
}

const handleHotReloadToggle = async () => {
  try {
    if (hotReloadEnabled.value) {
      await enableHotReload()
      toast.success('热更新已启用')
    } else {
      await disableHotReload()
      toast.success('热更新已禁用')
    }
  } catch (error: any) {
    toast.error(error.message || '切换热更新失败')
    hotReloadEnabled.value = !hotReloadEnabled.value
  }
}

const handleReload = async (plugin: PluginItem) => {
  try {
    await reloadPlugin(plugin.name)
    toast.success(`插件 ${plugin.name} 重载成功`)
    fetchPlugins()
  } catch (error: any) {
    toast.error(error.message || '重载插件失败')
  }
}

const handleUnload = async (plugin: PluginItem) => {
  try {
    await unloadPlugin(plugin.name)
    toast.success(`插件 ${plugin.name} 已卸载`)
    await fetchPlugins()
  } catch (error: any) {
    toast.error(error.message || '卸载插件失败')
  }
}

const openConfig = async (plugin: PluginItem) => {
  activePlugin.value = plugin
  configDialog.value = true
  configRows.value = []
  try {
    const config = await getPluginConfig(plugin.name)
    const rows = Object.entries(config).map(([key, value]) => ({
      key,
      value: typeof value === 'string' ? value : JSON.stringify(value)
    }))
    configRows.value = rows.length ? rows : [{ key: '', value: '' }]
  } catch (error: any) {
    toast.error(error.message || '读取插件配置失败')
    configDialog.value = false
  }
}

const addRow = () => {
  configRows.value.push({ key: '', value: '' })
}

const removeRow = (index: number) => {
  configRows.value.splice(index, 1)
  if (configRows.value.length === 0) {
    addRow()
  }
}

const saveConfig = async () => {
  if (!activePlugin.value) return
  configSaving.value = true
  try {
    const payload: Record<string, any> = {}
    configRows.value.forEach((row) => {
      if (!row.key) return
      try {
        payload[row.key] = JSON.parse(row.value)
      } catch {
        payload[row.key] = row.value
      }
    })
    await updatePluginConfig(activePlugin.value.name, payload)
    toast.success('配置已保存')
    configDialog.value = false
  } catch (error: any) {
    toast.error(error.message || '保存配置失败')
  } finally {
    configSaving.value = false
  }
}

const installPlugin = async (pluginId: string) => {
  try {
    await api.post(`/plugins/${pluginId}/install`)
    toast.success(`插件 ${pluginId} 安装请求已触发`)
    await Promise.all([fetchPlugins(), fetchRegistry()])
  } catch (error: any) {
    toast.error(error.message || '安装插件失败')
  }
}

const statusColor = (plugin: PluginItem) => {
  if (plugin.state?.status === 'error') return 'error'
  return plugin.loaded ? 'success' : 'warning'
}

const pluginStateLabel = (plugin: PluginItem) => {
  if (plugin.state?.status === 'error') return '错误'
  return plugin.loaded ? '已加载' : '未加载'
}

const formatDate = (value: string) => {
  return new Date(value).toLocaleString()
}

onMounted(() => {
  fetchStatus()
  fetchPlugins()
  fetchRegistry()
})
</script>

<style scoped>
.plugins-page {
  padding: 24px;
}
</style>

