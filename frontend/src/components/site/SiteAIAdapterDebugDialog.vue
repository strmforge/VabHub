<template>
  <v-dialog
    v-model="dialog"
    max-width="800"
    scrollable
  >
    <v-card>
      <v-card-title class="d-flex align-center justify-space-between">
        <span>AI 适配配置诊断（实验性功能）</span>
        <v-btn
          icon="mdi-close"
          variant="text"
          @click="dialog = false"
        />
      </v-card-title>

      <v-divider />

      <v-card-text v-if="loading" class="text-center py-8">
        <v-progress-circular indeterminate color="primary" size="48" />
        <div class="mt-4 text-body-2 text-medium-emphasis">加载中...</div>
      </v-card-text>

      <v-card-text v-else-if="error" class="py-4">
        <v-alert type="error" variant="tonal">
          {{ error }}
        </v-alert>
      </v-card-text>

      <v-card-text v-else-if="configData" class="py-4">
        <!-- 站点基本信息 -->
        <v-card variant="outlined" class="mb-4">
          <v-card-title class="text-subtitle-1">站点信息</v-card-title>
          <v-card-text>
            <div class="d-flex flex-column ga-2">
              <div class="d-flex justify-space-between">
                <span class="text-medium-emphasis">站点名称：</span>
                <span>{{ configData.site_name }}</span>
              </div>
              <div class="d-flex justify-space-between">
                <span class="text-medium-emphasis">站点 ID：</span>
                <span>{{ configData.site_id }}</span>
              </div>
            </div>
          </v-card-text>
        </v-card>

        <!-- AI 配置状态 -->
        <v-card variant="outlined" class="mb-4">
          <v-card-title class="text-subtitle-1">AI 配置状态</v-card-title>
          <v-card-text>
            <div class="d-flex flex-column ga-2">
              <!-- Phase AI-4: 站点级别的控制状态 -->
              <div class="d-flex justify-space-between align-center">
                <span class="text-medium-emphasis">站点禁用状态：</span>
                <v-chip
                  :color="configData.ai_disabled ? 'error' : 'success'"
                  size="small"
                  variant="flat"
                >
                  {{ configData.ai_disabled ? '已禁用' : '未禁用' }}
                </v-chip>
              </div>
              <div class="d-flex justify-space-between align-center">
                <span class="text-medium-emphasis">优先人工配置：</span>
                <v-chip
                  :color="configData.ai_manual_profile_preferred ? 'warning' : 'default'"
                  size="small"
                  variant="flat"
                >
                  {{ configData.ai_manual_profile_preferred ? '是' : '否' }}
                </v-chip>
              </div>
              <div class="d-flex justify-space-between align-center">
                <span class="text-medium-emphasis">配置存在：</span>
                <v-chip
                  :color="configData.ai_config_exists ? 'success' : 'default'"
                  size="small"
                  variant="flat"
                >
                  {{ configData.ai_config_exists ? '是' : '否' }}
                </v-chip>
              </div>
              <!-- Phase AI-4: 可信度分数 -->
              <div class="d-flex justify-space-between align-center">
                <span class="text-medium-emphasis">AI 配置可信度：</span>
                <v-chip
                  v-if="configData.ai_confidence_score !== null && configData.ai_confidence_score !== undefined"
                  :color="getConfidenceColor(configData.ai_confidence_score)"
                  size="small"
                  variant="flat"
                >
                  {{ configData.ai_confidence_score }}/100
                </v-chip>
                <span v-else class="text-medium-emphasis">未知</span>
              </div>
              <!-- Phase AI-4: 错误信息预览 -->
              <div v-if="configData.last_error_preview" class="d-flex flex-column ga-2 mt-2">
                <div class="d-flex justify-space-between align-center">
                  <span class="text-medium-emphasis">最近错误：</span>
                  <v-chip
                    color="error"
                    size="small"
                    variant="flat"
                  >
                    有错误
                  </v-chip>
                </div>
                <v-alert
                  type="error"
                  variant="tonal"
                  density="compact"
                  class="mt-2"
                >
                  {{ configData.last_error_preview }}
                </v-alert>
              </div>
              <div v-if="configData.ai_config" class="d-flex flex-column ga-2 mt-2">
                <div class="d-flex justify-space-between">
                  <span class="text-medium-emphasis">引擎类型：</span>
                  <span>{{ configData.ai_config.engine || '未知' }}</span>
                </div>
                <div class="d-flex justify-space-between">
                  <span class="text-medium-emphasis">搜索 URL：</span>
                  <span class="text-caption">{{ configData.ai_config.search_url || '未配置' }}</span>
                </div>
                <div class="d-flex justify-space-between">
                  <span class="text-medium-emphasis">详情 URL：</span>
                  <span class="text-caption">{{ configData.ai_config.detail_url || '未配置' }}</span>
                </div>
                <div class="d-flex justify-space-between align-center">
                  <span class="text-medium-emphasis">HR 规则：</span>
                  <v-chip
                    :color="configData.ai_config.hr_enabled ? 'info' : 'default'"
                    size="small"
                    variant="flat"
                  >
                    {{ configData.ai_config.hr_enabled ? '已启用' : '未启用' }}
                  </v-chip>
                </div>
              </div>
            </div>
          </v-card-text>
        </v-card>

        <!-- Local Intel 配置 -->
        <v-card variant="outlined" class="mb-4">
          <v-card-title class="text-subtitle-1">Local Intel 配置</v-card-title>
          <v-card-text>
            <div class="d-flex flex-column ga-2">
              <div class="d-flex justify-space-between align-center">
                <span class="text-medium-emphasis">生效模式：</span>
                <v-chip
                  :color="getModeColor(configData.local_intel.mode)"
                  size="small"
                  variant="flat"
                >
                  {{ getModeLabel(configData.local_intel.mode) }}
                </v-chip>
              </div>
              <div v-if="configData.local_intel.profile" class="d-flex flex-column ga-2 mt-2">
                <div class="d-flex justify-space-between align-center">
                  <span class="text-medium-emphasis">HR 监控：</span>
                  <v-chip
                    :color="configData.local_intel.profile.hr_enabled ? 'success' : 'default'"
                    size="small"
                    variant="flat"
                  >
                    {{ configData.local_intel.profile.hr_enabled ? '已启用' : '未启用' }}
                  </v-chip>
                </div>
                <div v-if="configData.local_intel.profile.hr_page_path" class="d-flex justify-space-between">
                  <span class="text-medium-emphasis">HR 页面路径：</span>
                  <span class="text-caption">{{ configData.local_intel.profile.hr_page_path }}</span>
                </div>
                <div class="d-flex justify-space-between align-center">
                  <span class="text-medium-emphasis">站内信监控：</span>
                  <v-chip
                    :color="configData.local_intel.profile.inbox_enabled ? 'success' : 'default'"
                    size="small"
                    variant="flat"
                  >
                    {{ configData.local_intel.profile.inbox_enabled ? '已启用' : '未启用' }}
                  </v-chip>
                </div>
              </div>
            </div>
          </v-card-text>
        </v-card>

        <!-- External Indexer 配置 -->
        <v-card variant="outlined" class="mb-4">
          <v-card-title class="text-subtitle-1">External Indexer 配置</v-card-title>
          <v-card-text>
            <div class="d-flex flex-column ga-2">
              <div class="d-flex justify-space-between align-center">
                <span class="text-medium-emphasis">生效模式：</span>
                <v-chip
                  :color="getModeColor(configData.external_indexer.mode)"
                  size="small"
                  variant="flat"
                >
                  {{ getModeLabel(configData.external_indexer.mode) }}
                </v-chip>
              </div>
              <div v-if="configData.external_indexer && configData.external_indexer.config" class="d-flex flex-column ga-2 mt-2">
                <div class="d-flex justify-space-between">
                  <span class="text-medium-emphasis">站点名称：</span>
                  <span>{{ configData.external_indexer.config.name }}</span>
                </div>
                <div class="d-flex justify-space-between">
                  <span class="text-medium-emphasis">基础 URL：</span>
                  <span class="text-caption">{{ configData.external_indexer.config.base_url }}</span>
                </div>
                <div class="d-flex justify-space-between">
                  <span class="text-medium-emphasis">框架类型：</span>
                  <span>{{ configData.external_indexer.config.framework || '未知' }}</span>
                </div>
                <div v-if="configData.external_indexer.config.capabilities" class="d-flex justify-space-between">
                  <span class="text-medium-emphasis">支持能力：</span>
                  <v-chip-group>
                    <v-chip
                      v-for="cap in configData.external_indexer.config.capabilities"
                      :key="cap"
                      size="x-small"
                      variant="outlined"
                    >
                      {{ cap }}
                    </v-chip>
                  </v-chip-group>
                </div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-card-text>

      <v-divider />

      <v-card-actions>
        <v-spacer />
        <v-btn
          variant="text"
          @click="dialog = false"
        >
          关闭
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import api from '@/services/api'
import { useToast } from 'vue-toastification'

interface Props {
  modelValue: boolean
  site: any
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue'])

const toast = useToast()
const loading = ref(false)
const error = ref<string | null>(null)
const configData = ref<any>(null)

const dialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

watch(() => props.modelValue, (newVal) => {
  if (newVal && props.site) {
    loadConfig()
  } else {
    configData.value = null
    error.value = null
  }
})

const loadConfig = async () => {
  if (!props.site?.id) {
    error.value = '站点信息不完整'
    return
  }

  loading.value = true
  error.value = null

  try {
    const response = await api.get(`/admin/site-ai-adapter/effective-config/${props.site.id}`)
    const data = response.data?.data || response.data
    if (data) {
      configData.value = data
    } else {
      error.value = '获取配置数据失败'
    }
  } catch (err: any) {
    console.error('加载 AI 配置失败:', err)
    error.value = err.response?.data?.detail?.error_message || err.message || '加载失败'
    toast.error(error.value)
  } finally {
    loading.value = false
  }
}

const getModeLabel = (mode: string): string => {
  const labels: Record<string, string> = {
    'manual_profile': '手工配置',
    'manual_config': '手工配置',
    'ai_profile': 'AI 配置',
    'ai_config': 'AI 配置',
    'none': '无配置'
  }
  return labels[mode] || mode
}

const getModeColor = (mode: string): string => {
  if (mode.includes('manual')) return 'primary'
  if (mode.includes('ai')) return 'info'
  return 'default'
}

const getConfidenceColor = (score: number): string => {
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'error'
}
</script>


<style scoped>
.v-card-text {
  max-height: 60vh;
  overflow-y: auto;
}
</style>

