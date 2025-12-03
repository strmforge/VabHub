<template>
  <div class="default-subscription-config">
    <!-- 媒体类型选择 -->
    <v-card variant="outlined" class="mb-4">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-play-box-multiple</v-icon>
        选择媒体类型
      </v-card-title>
      
      <v-card-text>
        <v-chip-group
          v-model="selectedMediaType"
          mandatory
          selected-class="text-primary"
        >
          <v-chip
            v-for="type in mediaTypes"
            :key="type.value"
            :value="type.value"
            :prepend-icon="type.icon"
            variant="outlined"
            size="large"
          >
            {{ type.label }}
          </v-chip>
        </v-chip-group>
      </v-card-text>
    </v-card>

    <!-- 配置表单 -->
    <v-card variant="outlined" class="mb-4">
      <v-card-title class="d-flex align-center justify-space-between">
        <span>
          <v-icon class="mr-2">mdi-cog</v-icon>
          {{ getMediaTypeLabel(selectedMediaType) }}默认配置
        </span>
        <div class="d-flex gap-2">
          <v-btn
            color="warning"
            variant="outlined"
            prepend-icon="mdi-restore"
            @click="resetToDefault"
            :loading="resetting"
          >
            重置为默认
          </v-btn>
          <v-btn
            color="primary"
            prepend-icon="mdi-content-save"
            @click="saveConfig"
            :loading="saving"
          >
            保存配置
          </v-btn>
        </div>
      </v-card-title>

      <v-card-text>
        <div v-if="loading" class="text-center py-12">
          <v-progress-circular indeterminate color="primary" size="64" />
          <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
        </div>

        <v-form v-else ref="formRef" v-model="formValid">
          <v-row>
            <!-- 基础配置 -->
            <v-col cols="12">
              <v-card variant="flat" color="grey-lighten-5">
                <v-card-title class="text-subtitle-1">
                  <v-icon class="mr-2">mdi-information</v-icon>
                  基础配置
                </v-card-title>
                <v-card-text>
                  <v-row>
                    <v-col cols="12" md="4">
                      <v-select
                        v-model="config.quality"
                        :items="qualityOptions"
                        label="质量要求"
                        placeholder="请选择质量要求"
                        clearable
                        hide-details
                      />
                    </v-col>
                    <v-col cols="12" md="4">
                      <v-text-field
                        v-model="config.resolution"
                        label="分辨率要求"
                        placeholder="如: 1080p, 4K"
                        clearable
                        hide-details
                      />
                    </v-col>
                    <v-col cols="12" md="4">
                      <v-text-field
                        v-model="config.effect"
                        label="特效要求"
                        placeholder="如: HDR, DV"
                        clearable
                        hide-details
                      />
                    </v-col>
                  </v-row>
                  <v-row>
                    <v-col cols="12" md="4">
                      <v-text-field
                        v-model.number="config.min_seeders"
                        type="number"
                        label="最小做种数"
                        min="0"
                        hide-details
                      />
                    </v-col>
                    <v-col cols="12" md="4">
                      <v-select
                        v-model="config.downloader"
                        :items="downloaderOptions"
                        label="下载器"
                        placeholder="选择下载器"
                        clearable
                        hide-details
                      />
                    </v-col>
                    <v-col cols="12" md="4">
                      <v-text-field
                        v-model="config.save_path"
                        label="保存路径"
                        placeholder="下载保存路径"
                        clearable
                        hide-details
                      />
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>
            </v-col>

            <!-- 下载行为 -->
            <v-col cols="12">
              <v-card variant="flat" color="grey-lighten-5">
                <v-card-title class="text-subtitle-1">
                  <v-icon class="mr-2">mdi-download</v-icon>
                  下载行为
                </v-card-title>
                <v-card-text>
                  <v-row>
                    <v-col cols="12" md="4">
                      <v-switch
                        v-model="config.auto_download"
                        label="自动下载"
                        color="primary"
                        hide-details
                      />
                    </v-col>
                    <v-col cols="12" md="4">
                      <v-switch
                        v-model="config.best_version"
                        label="洗版模式"
                        color="primary"
                        hide-details
                      />
                    </v-col>
                    <v-col cols="12" md="4">
                      <v-switch
                        v-model="config.allow_hr"
                        label="允许HR"
                        color="primary"
                        hide-details
                      />
                    </v-col>
                  </v-row>
                  <v-row>
                    <v-col cols="12" md="4">
                      <v-switch
                        v-model="config.allow_h3h5"
                        label="允许H3/H5"
                        color="primary"
                        hide-details
                      />
                    </v-col>
                    <v-col cols="12" md="4">
                      <v-switch
                        v-model="config.strict_free_only"
                        label="仅免费种"
                        color="primary"
                        hide-details
                      />
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>
            </v-col>

            <!-- 过滤规则 -->
            <v-col cols="12">
              <v-card variant="flat" color="grey-lighten-5">
                <v-card-title class="text-subtitle-1">
                  <v-icon class="mr-2">mdi-filter</v-icon>
                  过滤规则
                </v-card-title>
                <v-card-text>
                  <v-row>
                    <v-col cols="12" md="6">
                      <v-textarea
                        v-model="config.include"
                        label="包含规则"
                        placeholder="关键词，用逗号分隔"
                        rows="3"
                        hint="包含这些关键词的资源才会被下载"
                        persistent-hint
                      />
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-textarea
                        v-model="config.exclude"
                        label="排除规则"
                        placeholder="关键词，用逗号分隔"
                        rows="3"
                        hint="包含这些关键词的资源将被排除"
                        persistent-hint
                      />
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>
            </v-col>

            <!-- 过滤规则组 -->
            <v-col cols="12">
              <v-card variant="flat" color="grey-lighten-5">
                <v-card-title class="text-subtitle-1">
                  <v-icon class="mr-2">mdi-filter-variant</v-icon>
                  过滤规则组
                </v-card-title>
                <v-card-text>
                  <v-select
                    v-model="config.filter_group_ids"
                    :items="availableRuleGroups"
                    item-title="name"
                    item-value="id"
                    label="选择过滤规则组"
                    placeholder="选择要应用的过滤规则组"
                    multiple
                    chips
                    clearable
                    :loading="loadingRuleGroups"
                    hint="选择的规则组将按优先级顺序应用"
                    persistent-hint
                  />
                </v-card-text>
              </v-card>
            </v-col>

            <!-- 站点选择 -->
            <v-col cols="12">
              <v-card variant="flat" color="grey-lighten-5">
                <v-card-title class="text-subtitle-1">
                  <v-icon class="mr-2">mdi-server</v-icon>
                  订阅站点
                </v-card-title>
                <v-card-text>
                  <v-select
                    v-model="config.sites"
                    :items="availableSites"
                    item-title="name"
                    item-value="id"
                    label="选择订阅站点"
                    placeholder="选择要订阅的站点"
                    multiple
                    chips
                    clearable
                    :loading="loadingSites"
                    hint="留空表示使用所有可用站点"
                    persistent-hint
                  />
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>
    </v-card>

    <!-- 操作结果提示 -->
    <v-snackbar
      v-model="showSnackbar"
      :color="snackbarColor"
      :timeout="3000"
    >
      {{ snackbarMessage }}
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { subscriptionDefaultsApi, filterRuleGroupsApi } from '@/api'
import type { DefaultSubscriptionConfig, FilterRuleGroup } from '@/api'

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const resetting = ref(false)
const formValid = ref(false)
const formRef = ref()

const selectedMediaType = ref('movie')
const mediaTypes = ref([
  { value: 'movie', label: '电影', icon: 'mdi-movie' },
  { value: 'tv', label: '电视剧', icon: 'mdi-television' },
  { value: 'short_drama', label: '短剧', icon: 'mdi-video' },
  { value: 'anime', label: '动漫', icon: 'mdi-animation' },
  { value: 'music', label: '音乐', icon: 'mdi-music' }
])

const config = reactive<DefaultSubscriptionConfig>({
  quality: '',
  resolution: '',
  effect: '',
  min_seeders: 5,
  auto_download: true,
  best_version: false,
  include: '',
  exclude: '',
  filter_group_ids: [],
  allow_hr: false,
  allow_h3h5: false,
  strict_free_only: false,
  sites: [],
  downloader: '',
  save_path: ''
})

// 可选项数据
const availableRuleGroups = ref<FilterRuleGroup[]>([])
const availableSites = ref<any[]>([])
const loadingRuleGroups = ref(false)
const loadingSites = ref(false)

// 选项数据
const qualityOptions = [
  { title: '4K', value: '4K' },
  { title: '1080p', value: '1080p' },
  { title: '720p', value: '720p' },
  { title: '无限制', value: '' }
]

const downloaderOptions = [
  { title: 'qBittorrent', value: 'qbittorrent' },
  { title: 'Transmission', value: 'transmission' },
  { title: 'Aria2', value: 'aria2' }
]

// 提示消息
const showSnackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref('success')

// 方法
const getMediaTypeLabel = (value: string) => {
  const type = mediaTypes.value.find(t => t.value === value)
  return type?.label || value
}

const loadConfig = async () => {
  if (!selectedMediaType.value) return
  
  loading.value = true
  try {
    const response = await subscriptionDefaultsApi.getDefaultConfig(selectedMediaType.value)
    Object.assign(config, response.data)
  } catch (error) {
    console.error('加载配置失败:', error)
    showSnackbar.value = true
    snackbarMessage.value = '加载配置失败'
    snackbarColor.value = 'error'
  } finally {
    loading.value = false
  }
}

const saveConfig = async () => {
  if (!formRef.value?.validate()) return
  
  saving.value = true
  try {
    const response = await subscriptionDefaultsApi.saveDefaultConfig(
      selectedMediaType.value,
      config
    )
    Object.assign(config, response.data)
    
    showSnackbar.value = true
    snackbarMessage.value = '保存配置成功'
    snackbarColor.value = 'success'
  } catch (error) {
    console.error('保存配置失败:', error)
    showSnackbar.value = true
    snackbarMessage.value = '保存配置失败'
    snackbarColor.value = 'error'
  } finally {
    saving.value = false
  }
}

const resetToDefault = async () => {
  resetting.value = true
  try {
    const response = await subscriptionDefaultsApi.resetDefaultConfig(selectedMediaType.value)
    Object.assign(config, response.data)
    
    showSnackbar.value = true
    snackbarMessage.value = '重置配置成功'
    snackbarColor.value = 'success'
  } catch (error) {
    console.error('重置配置失败:', error)
    showSnackbar.value = true
    snackbarMessage.value = '重置配置失败'
    snackbarColor.value = 'error'
  } finally {
    resetting.value = false
  }
}

const loadRuleGroups = async () => {
  loadingRuleGroups.value = true
  try {
    const response = await filterRuleGroupsApi.getFilterRuleGroups({ enabled: true })
    availableRuleGroups.value = response.data.items
  } catch (error) {
    console.error('加载规则组失败:', error)
  } finally {
    loadingRuleGroups.value = false
  }
}

const loadSites = async () => {
  loadingSites.value = true
  try {
    // 这里应该调用站点API，暂时使用模拟数据
    availableSites.value = [
      { id: 1, name: '示例站点1' },
      { id: 2, name: '示例站点2' },
      { id: 3, name: '示例站点3' }
    ]
  } catch (error) {
    console.error('加载站点失败:', error)
  } finally {
    loadingSites.value = false
  }
}

// 监听媒体类型变化
watch(selectedMediaType, () => {
  loadConfig()
})

// 生命周期
onMounted(() => {
  loadConfig()
  loadRuleGroups()
  loadSites()
})
</script>

<style scoped>
.default-subscription-config {
  min-height: 600px;
}

.v-card {
  transition: all 0.3s ease;
}

.v-card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}
</style>
