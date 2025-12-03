<!--
系统设置页面（MoviePilot风格）
包含基础设置和高级设置对话框
-->
<template>
  <div class="system-settings-page">
    <PageHeader
      title="系统设置"
      subtitle="系统配置和偏好设置"
    />

    <v-container fluid class="pa-4">
      <v-row>
        <v-col cols="12">
          <!-- 基础设置卡片 -->
          <v-card variant="outlined">
            <v-card-item>
              <v-card-title>基础设置</v-card-title>
              <v-card-subtitle>设置服务器的全局功能</v-card-subtitle>
            </v-card-item>
            <v-card-text>
              <v-form @submit.prevent="saveBasicSettings">
                <v-row>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="basicSettings.APP_DOMAIN"
                      label="访问域名"
                      hint="用于发送通知时，添加快捷跳转地址"
                      persistent-hint
                      placeholder="http://localhost:3000"
                      variant="outlined"
                      density="compact"
                      prepend-inner-icon="mdi-web"
                    />
                  </v-col>

                  <v-col cols="12" md="6">
                    <v-select
                      v-model="basicSettings.RECOGNIZE_SOURCE"
                      label="识别数据源"
                      hint="设置默认媒体信息识别数据源"
                      persistent-hint
                      :items="recognizeSourceItems"
                      variant="outlined"
                      density="compact"
                      prepend-inner-icon="mdi-database"
                    />
                  </v-col>

                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="basicSettings.API_TOKEN"
                      label="API令牌"
                      hint="设置外部请求VabHub API时使用的token值（至少16个字符）"
                      persistent-hint
                      :placeholder="apiTokenPlaceholder"
                      variant="outlined"
                      density="compact"
                      prepend-inner-icon="mdi-key"
                      :append-inner-icon="basicSettings.API_TOKEN ? 'mdi-content-copy' : 'mdi-reload'"
                      @click:append-inner="handleApiTokenAction"
                      :rules="[
                        (v: string) => !!v || 'API令牌不能为空',
                        (v: string) => v.length >= 16 || 'API令牌长度至少16个字符'
                      ]"
                    />
                  </v-col>

                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="basicSettings.OCR_HOST"
                      label="验证码识别服务器"
                      hint="用于站点签到、更新站点Cookie等识别验证码"
                      persistent-hint
                      placeholder="https://movie-pilot.org"
                      variant="outlined"
                      density="compact"
                      prepend-inner-icon="mdi-text-recognition"
                    />
                  </v-col>

                  <v-col cols="12" md="6">
                    <v-row>
                      <v-col cols="12" :md="basicSettings.WALLPAPER === 'customize' ? 6 : 12">
                        <v-select
                          v-model="basicSettings.WALLPAPER"
                          label="背景壁纸"
                          hint="选择登录页面背景来源"
                          persistent-hint
                          :items="wallpaperItems"
                          variant="outlined"
                          density="compact"
                          prepend-inner-icon="mdi-image"
                        />
                      </v-col>

                      <v-col v-if="basicSettings.WALLPAPER === 'customize'" cols="12" md="6">
                        <v-text-field
                          v-model="basicSettings.CUSTOMIZE_WALLPAPER_API_URL"
                          label="自定义壁纸API"
                          hint="自定义壁纸API地址"
                          persistent-hint
                          variant="outlined"
                          density="compact"
                          prepend-inner-icon="mdi-api"
                          :rules="[v => !!v || '自定义壁纸API地址不能为空']"
                        />
                      </v-col>
                    </v-row>
                  </v-col>

                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model.number="basicSettings.MEDIASERVER_SYNC_INTERVAL"
                      label="媒体服务器同步间隔"
                      hint="媒体服务器同步间隔时间（小时）"
                      persistent-hint
                      type="number"
                      min="1"
                      suffix="小时"
                      variant="outlined"
                      density="compact"
                      prepend-inner-icon="mdi-sync"
                      :rules="[
                        (v: any) => !!v || '同步间隔不能为空',
                        (v: any) => !isNaN(v) || '请输入数字',
                        (v: any) => v >= 1 || '同步间隔至少1小时'
                      ]"
                    />
                  </v-col>

                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="basicSettings.GITHUB_TOKEN"
                      label="Github Token"
                      hint="用于访问Github API（可选）"
                      persistent-hint
                      placeholder="ghp_xxxxxxxxxxxx"
                      variant="outlined"
                      density="compact"
                      prepend-inner-icon="mdi-github"
                      type="password"
                    />
                  </v-col>
                </v-row>
              </v-form>
            </v-card-text>
            <v-card-actions>
              <v-btn
                color="primary"
                prepend-icon="mdi-content-save"
                @click="saveBasicSettings"
                :loading="savingBasic"
              >
                保存
              </v-btn>
              <v-spacer />
              <v-btn
                color="error"
                prepend-icon="mdi-cog"
                append-icon="mdi-dots-horizontal"
                @click="advancedDialog = true"
              >
                高级设置
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-col>
      </v-row>
    </v-container>

    <!-- 高级设置对话框 -->
    <v-dialog
      v-model="advancedDialog"
      scrollable
      max-width="60rem"
      :fullscreen="!$vuetify.display.mdAndUp"
    >
      <v-card>
        <v-card-item class="py-2">
          <template #prepend>
            <v-icon icon="mdi-cog" class="me-2" />
          </template>
          <v-card-title>高级设置</v-card-title>
          <v-card-subtitle>系统进阶设置，特殊情况下才需要调整</v-card-subtitle>
        </v-card-item>
        <v-dialog-close-btn @click="advancedDialog = false" />
        <v-card-text>
          <v-tabs v-model="activeTab" show-arrows>
            <v-tab value="system">
              <div>系统</div>
            </v-tab>
            <v-tab value="media">
              <div>媒体</div>
            </v-tab>
            <v-tab value="network">
              <div>网络</div>
            </v-tab>
            <v-tab value="log">
              <div>日志</div>
            </v-tab>
            <v-tab value="lab">
              <div>实验室</div>
            </v-tab>
          </v-tabs>

          <v-window v-model="activeTab" class="mt-5 disable-tab-transition" :touch="false">
            <!-- 系统标签 -->
            <v-window-item value="system">
              <SystemTab
                :model-value="advancedSettings"
                :db-type="dbType"
                @update:model-value="advancedSettings = $event"
              />
            </v-window-item>

            <!-- 媒体标签 -->
            <v-window-item value="media">
              <MediaTab
                :model-value="advancedSettings"
                :scraping-switches="scrapingSwitches"
                @update:model-value="advancedSettings = $event"
                @update:scraping-switches="scrapingSwitches = $event"
              />
            </v-window-item>

            <!-- 网络标签 -->
            <v-window-item value="network">
              <NetworkTab
                :model-value="advancedSettings"
                @update:model-value="advancedSettings = $event"
              />
            </v-window-item>

            <!-- 日志标签 -->
            <v-window-item value="log">
              <LogTab
                :model-value="advancedSettings"
                @update:model-value="advancedSettings = $event"
              />
            </v-window-item>

            <!-- 实验室标签 -->
            <v-window-item value="lab">
              <LabTab
                :model-value="advancedSettings"
                @update:model-value="advancedSettings = $event"
              />
            </v-window-item>
          </v-window>
        </v-card-text>
        <v-card-actions class="pt-3">
          <v-btn
            color="primary"
            prepend-icon="mdi-content-save"
            @click="saveAdvancedSettings"
            :loading="savingAdvanced"
            class="px-5"
          >
            保存
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useToast } from 'vue-toastification'
import api from '@/services/api'
import PageHeader from '@/components/common/PageHeader.vue'
import SystemTab from '@/components/settings/SystemTab.vue'
import MediaTab from '@/components/settings/MediaTab.vue'
import NetworkTab from '@/components/settings/NetworkTab.vue'
import LogTab from '@/components/settings/LogTab.vue'
import LabTab from '@/components/settings/LabTab.vue'

const $toast = useToast()

// 基础设置
const basicSettings = ref<any>({
  APP_DOMAIN: '',
  RECOGNIZE_SOURCE: 'themoviedb',
  API_TOKEN: '',
  OCR_HOST: '',
  WALLPAPER: 'tmdb',
  CUSTOMIZE_WALLPAPER_API_URL: '',
  MEDIASERVER_SYNC_INTERVAL: 6,
  GITHUB_TOKEN: ''
})

// 高级设置
const advancedSettings = ref<any>({})
const scrapingSwitches = ref<any>({})

// 对话框和标签
const advancedDialog = ref(false)
const activeTab = ref('system')
const dbType = ref('sqlite')

// 加载和保存状态
const savingBasic = ref(false)
const savingAdvanced = ref(false)

// 选项数据
const recognizeSourceItems = [
  { title: 'TheMovieDb', value: 'themoviedb' },
  { title: '豆瓣', value: 'douban' }
]

const wallpaperItems = [
  { title: 'TMDB电影海报', value: 'tmdb' },
  { title: 'Bing', value: 'bing' },
  { title: '媒体服务器', value: 'mediaserver' },
  { title: '自定义', value: 'customize' },
  { title: '无', value: '' }
]

const apiTokenPlaceholder = computed(() => {
  return basicSettings.value.API_TOKEN
    ? '点击复制图标复制令牌'
    : '点击刷新图标生成新令牌'
})

// 处理API令牌操作
const handleApiTokenAction = async () => {
  if (basicSettings.value.API_TOKEN) {
    // 复制到剪贴板
    try {
      await navigator.clipboard.writeText(basicSettings.value.API_TOKEN)
      $toast.success('API令牌已复制到剪贴板')
    } catch (error) {
      $toast.error('复制失败，请手动复制')
    }
  } else {
    // 生成新令牌
    generateApiToken()
  }
}

// 生成随机API令牌
const generateApiToken = () => {
  const charset = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_'
  const array = new Uint8Array(32)
  window.crypto.getRandomValues(array)
  basicSettings.value.API_TOKEN = Array.from(array, byte => charset[byte % charset.length]).join('')
  $toast.success('已生成新的API令牌')
}

// 加载系统设置
const loadSystemSettings = async () => {
  try {
    const response = await api.get('/system/env')
    if (response.data?.success && response.data?.data) {
      const data = response.data.data
      
      // 基础设置
      basicSettings.value = {
        APP_DOMAIN: data.APP_DOMAIN || '',
        RECOGNIZE_SOURCE: data.RECOGNIZE_SOURCE || 'themoviedb',
        API_TOKEN: data.API_TOKEN || '',
        OCR_HOST: data.OCR_HOST || '',
        WALLPAPER: data.WALLPAPER || 'tmdb',
        CUSTOMIZE_WALLPAPER_API_URL: data.CUSTOMIZE_WALLPAPER_API_URL || '',
        MEDIASERVER_SYNC_INTERVAL: data.MEDIASERVER_SYNC_INTERVAL || 6,
        GITHUB_TOKEN: data.GITHUB_TOKEN || ''
      }
      
      // 高级设置
      advancedSettings.value = {
        // 系统
        AUXILIARY_AUTH_ENABLE: data.AUXILIARY_AUTH_ENABLE ?? false,
        GLOBAL_IMAGE_CACHE: data.GLOBAL_IMAGE_CACHE ?? false,
        SUBSCRIBE_STATISTIC_SHARE: data.SUBSCRIBE_STATISTIC_SHARE ?? true,
        PLUGIN_STATISTIC_SHARE: data.PLUGIN_STATISTIC_SHARE ?? true,
        WORKFLOW_STATISTIC_SHARE: data.WORKFLOW_STATISTIC_SHARE ?? true,
        BIG_MEMORY_MODE: data.BIG_MEMORY_MODE ?? false,
        DB_WAL_ENABLE: data.DB_WAL_ENABLE ?? true,
        VABHUB_AUTO_UPDATE: data.VABHUB_AUTO_UPDATE || 'false',
        AUTO_UPDATE_RESOURCE: data.AUTO_UPDATE_RESOURCE ?? true,
        // 媒体
        TMDB_API_DOMAIN: data.TMDB_API_DOMAIN || 'api.themoviedb.org',
        TMDB_IMAGE_DOMAIN: data.TMDB_IMAGE_DOMAIN || 'image.tmdb.org',
        TMDB_LOCALE: data.TMDB_LOCALE || 'zh',
        META_CACHE_EXPIRE: data.META_CACHE_EXPIRE ?? 0,
        SCRAP_FOLLOW_TMDB: data.SCRAP_FOLLOW_TMDB ?? true,
        FANART_ENABLE: data.FANART_ENABLE ?? false,
        FANART_LANG: data.FANART_LANG || 'zh,en',
        TMDB_SCRAP_ORIGINAL_IMAGE: data.TMDB_SCRAP_ORIGINAL_IMAGE,
        // 网络
        PROXY_HOST: data.PROXY_HOST || '',
        GITHUB_PROXY: data.GITHUB_PROXY || '',
        PIP_PROXY: data.PIP_PROXY || '',
        DOH_ENABLE: data.DOH_ENABLE ?? false,
        DOH_RESOLVERS: data.DOH_RESOLVERS || '1.0.0.1,1.1.1.1,9.9.9.9,149.112.112.112',
        DOH_DOMAINS: data.DOH_DOMAINS || 'api.themoviedb.org,api.tmdb.org,webservice.fanart.tv,api.github.com,github.com',
        SECURITY_IMAGE_DOMAINS: data.SECURITY_IMAGE_DOMAINS || [],
        // 日志
        DEBUG: data.DEBUG ?? false,
        LOG_LEVEL: data.LOG_LEVEL || 'INFO',
        LOG_MAX_FILE_SIZE: data.LOG_MAX_FILE_SIZE || '5',
        LOG_BACKUP_COUNT: data.LOG_BACKUP_COUNT || '3',
        LOG_FILE_FORMAT: data.LOG_FILE_FORMAT || '【%(levelname)s】%(asctime)s - %(message)s',
        // 实验室
        PLUGIN_AUTO_RELOAD: data.PLUGIN_AUTO_RELOAD ?? false,
        ENCODING_DETECTION_PERFORMANCE_MODE: data.ENCODING_DETECTION_PERFORMANCE_MODE ?? true
      }
      
      // 加载刮削开关设置
      try {
        const scrapingResponse = await api.get('/system/setting/ScrapingSwitchs')
        if (scrapingResponse.data?.success && scrapingResponse.data?.data?.value) {
          scrapingSwitches.value = scrapingResponse.data.data.value
        }
      } catch (error) {
        console.warn('加载刮削开关设置失败:', error)
      }
    }
  } catch (error: any) {
    console.error('加载系统设置失败:', error)
    $toast.error('加载系统设置失败')
  }
}

// 保存基础设置
const saveBasicSettings = async () => {
  savingBasic.value = true
  try {
    // 清理空字符串，设置为null
    const cleanedSettings: any = {}
    for (const [key, value] of Object.entries(basicSettings.value)) {
      if (value === '' || value === null) {
        if (['APP_DOMAIN', 'CUSTOMIZE_WALLPAPER_API_URL', 'GITHUB_TOKEN', 'OCR_HOST'].includes(key)) {
          cleanedSettings[key] = null
        }
      } else {
        cleanedSettings[key] = value
      }
    }
    
    await api.post('/system/env', cleanedSettings)
    $toast.success('基础设置保存成功')
  } catch (error: any) {
    console.error('保存基础设置失败:', error)
    $toast.error('保存失败：' + (error.response?.data?.detail || '未知错误'))
  } finally {
    savingBasic.value = false
  }
}

// 保存高级设置
const saveAdvancedSettings = async () => {
  savingAdvanced.value = true
  try {
    // 清理空字符串
    const cleanedSettings: any = {}
    for (const [key, value] of Object.entries(advancedSettings.value)) {
      if (value === '' || value === null) {
        if (['PROXY_HOST', 'GITHUB_PROXY', 'PIP_PROXY', 'TMDB_SCRAP_ORIGINAL_IMAGE'].includes(key)) {
          cleanedSettings[key] = null
        }
      } else {
        cleanedSettings[key] = value
      }
    }
    
    // 保存高级设置
    await api.post('/system/env', cleanedSettings)
    
    // 保存刮削开关设置
    await api.post('/system/setting/ScrapingSwitchs', scrapingSwitches.value)
    
    $toast.success('高级设置保存成功')
    advancedDialog.value = false
  } catch (error: any) {
    console.error('保存高级设置失败:', error)
    $toast.error('保存失败：' + (error.response?.data?.detail || '未知错误'))
  } finally {
    savingAdvanced.value = false
  }
}

onMounted(() => {
  loadSystemSettings()
})
</script>

<style scoped>
.system-settings-page {
  min-height: 100vh;
}
</style>

