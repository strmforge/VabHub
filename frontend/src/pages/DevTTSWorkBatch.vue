<template>
  <div class="tts-work-batch-page">
    <v-container>
      <PageHeader
        title="批量应用 TTS 声线预设"
        subtitle="按条件筛选作品并批量套用预设（Dev）"
      >
        <template #actions>
          <v-chip size="small" color="warning">Dev Only</v-chip>
        </template>
      </PageHeader>

      <!-- 筛选条件表单 -->
      <v-card class="mb-4">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="primary">mdi-filter</v-icon>
          <span>筛选条件</span>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-row>
            <!-- 预设选择 -->
            <v-col cols="12" md="6">
              <v-select
                v-model="selectedPresetId"
                :items="presets"
                item-title="name"
                item-value="id"
                label="选择 TTS 声线预设"
                placeholder="请选择一个预设"
                variant="outlined"
                density="comfortable"
                clearable
              >
                <template v-slot:item="{ props, item }">
                  <v-list-item v-bind="props">
                    <template v-slot:title>
                      <div class="d-flex align-center">
                        <span>{{ item.raw.name }}</span>
                        <v-chip
                          v-if="item.raw.is_default"
                          size="x-small"
                          color="success"
                          variant="flat"
                          class="ml-2"
                        >
                          默认
                        </v-chip>
                      </div>
                    </template>
                    <template v-slot:subtitle>
                      <span v-if="item.raw.provider || item.raw.language || item.raw.voice">
                        {{ [item.raw.provider, item.raw.language, item.raw.voice].filter(Boolean).join(' / ') }}
                      </span>
                    </template>
                  </v-list-item>
                </template>
              </v-select>
              
              <!-- 预设选择提醒 -->
              <v-alert
                v-if="selectedPresetHeatInfo"
                :type="getPresetAlertType(selectedPresetHeatInfo)"
                variant="tonal"
                density="compact"
                class="mt-2"
              >
                <template v-if="selectedPresetHeatInfo.is_sleeping">
                  ⚠ 当前声线预设最近几乎没有被使用（沉睡状态），请确认是否适合大规模套用。
                </template>
                <template v-else-if="selectedPresetHeatInfo.is_cold">
                  ⚠ 当前声线预设绑定作品较少、生成次数很低，可能是实验性声线，请谨慎在大量作品上使用。
                </template>
                <template v-else-if="selectedPresetHeatInfo.is_hot">
                  ✅ 当前声线预设为高频使用的热门预设。
                </template>
              </v-alert>
            </v-col>

            <!-- 语言 -->
            <v-col cols="12" md="6">
              <v-text-field
                v-model="filter.language"
                label="语言"
                placeholder="zh-CN / en-US"
                variant="outlined"
                density="comfortable"
                clearable
              />
            </v-col>

            <!-- 作者包含 -->
            <v-col cols="12" md="6">
              <v-text-field
                v-model="filter.author_substring"
                label="作者包含"
                placeholder="作者名关键字"
                variant="outlined"
                density="comfortable"
                clearable
              />
            </v-col>

            <!-- 系列包含 -->
            <v-col cols="12" md="6">
              <v-text-field
                v-model="filter.series_substring"
                label="系列包含"
                placeholder="系列名关键字"
                variant="outlined"
                density="comfortable"
                clearable
              />
            </v-col>

            <!-- 标签关键字 -->
            <v-col cols="12" md="6">
              <v-text-field
                v-model="filter.tag_keyword"
                label="标签关键字"
                placeholder="标签包含的关键字"
                variant="outlined"
                density="comfortable"
                clearable
              />
            </v-col>

            <!-- 是否已有 Profile -->
            <v-col cols="12" md="6">
              <v-select
                v-model="hasProfileFilter"
                :items="hasProfileOptions"
                item-title="label"
                item-value="value"
                label="是否已有 Profile"
                variant="outlined"
                density="comfortable"
                clearable
              />
            </v-col>

            <!-- 创建时间范围 -->
            <v-col cols="12" md="6">
              <v-text-field
                v-model="filter.created_from"
                label="创建时间（起始）"
                type="datetime-local"
                variant="outlined"
                density="comfortable"
                clearable
              />
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model="filter.created_to"
                label="创建时间（结束）"
                type="datetime-local"
                variant="outlined"
                density="comfortable"
                clearable
              />
            </v-col>
          </v-row>

          <v-btn
            color="primary"
            variant="elevated"
            prepend-icon="mdi-magnify"
            @click="handlePreview"
            :loading="previewLoading"
            class="mt-2"
          >
            预览匹配作品
          </v-btn>
        </v-card-text>
      </v-card>

      <!-- 预览结果统计 -->
      <v-card v-if="previewResult && previewResult.total > 0" class="mb-4">
        <v-card-text>
          <div class="d-flex flex-wrap gap-2 align-center">
            <v-chip size="small" color="primary">
              总数: {{ batchSummary.total }}
            </v-chip>
            <v-chip size="small" color="success">
              有 Profile: {{ batchSummary.withProfile }}
            </v-chip>
            <v-chip
              v-if="batchSummary.withProfileNoPreset > 0"
              size="small"
              color="warning"
            >
              有 Profile 但未绑定预设: {{ batchSummary.withProfileNoPreset }}
            </v-chip>
            <v-chip size="small" color="default">
              无 Profile: {{ batchSummary.withoutProfile }}
            </v-chip>
          </div>
        </v-card-text>
      </v-card>

      <!-- 预览结果表格 -->
      <v-card v-if="previewResult" class="mb-4">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="info">mdi-table</v-icon>
          <span>预览结果</span>
          <v-chip size="small" color="info" class="ml-2">
            共 {{ previewResult.total }} 本（限制 {{ previewResult.limit }}）
          </v-chip>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-data-table
            :headers="previewHeaders"
            :items="previewResult.items"
            :loading="previewLoading"
            density="compact"
            :items-per-page="20"
            no-data-text="暂无匹配的作品"
          >
            <template v-slot:item.title="{ item }">
              <div class="text-body-2 font-weight-medium">{{ item.title }}</div>
            </template>

            <template v-slot:item.profile_status="{ item }">
              <div class="d-flex flex-column gap-1">
                <v-chip
                  :color="item.has_profile ? (item.profile_enabled ? 'success' : 'warning') : 'default'"
                  size="small"
                  variant="flat"
                >
                  {{ item.has_profile ? (item.profile_enabled ? '已配置' : '已配置（禁用）') : '无 Profile' }}
                </v-chip>
                <span v-if="item.profile_preset_name" class="text-caption text-medium-emphasis">
                  预设: {{ item.profile_preset_name }}
                </span>
              </div>
            </template>

            <template v-slot:item.created_at="{ item }">
              {{ formatDateTime(item.created_at) }}
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>

      <!-- 批量应用操作 -->
      <v-card v-if="previewResult && previewResult.total > 0">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="success">mdi-play-circle</v-icon>
          <span>批量应用</span>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-row>
            <v-col cols="12">
              <v-checkbox
                v-model="applyOptions.override_existing"
                label="覆盖已有 Profile 的 preset"
                color="primary"
                density="compact"
              />
              <div class="text-caption text-medium-emphasis ml-8 mb-2">
                勾选后，已有 Profile 的作品也会更新 preset_id 和 enabled
              </div>
            </v-col>

            <v-col cols="12">
              <v-checkbox
                v-model="applyOptions.enable_profile"
                label="启用 Profile（enabled=true）"
                color="primary"
                density="compact"
              />
              <div class="text-caption text-medium-emphasis ml-8 mb-2">
                应用时是否将 Profile 设为启用状态
              </div>
            </v-col>
          </v-row>

          <v-divider class="my-3" />

          <div class="d-flex gap-2">
            <v-btn
              color="info"
              variant="outlined"
              prepend-icon="mdi-test-tube"
              @click="handleDryRun"
              :loading="applyLoading"
              :disabled="!selectedPresetId"
            >
              Dry-run 预演
            </v-btn>

            <v-btn
              color="success"
              variant="elevated"
              prepend-icon="mdi-check-circle"
              @click="handleApply"
              :loading="applyLoading"
              :disabled="!selectedPresetId"
            >
              应用预设到这些作品
            </v-btn>
          </div>

          <!-- 应用结果 -->
          <v-alert
            v-if="applyResult"
            :type="applyResult.matched_ebooks > 0 ? 'success' : 'info'"
            variant="tonal"
            class="mt-4"
          >
            <div class="text-body-2">
              <strong>处理结果：</strong>
            </div>
            <div class="text-body-2 mt-1">
              匹配作品: {{ applyResult.matched_ebooks }} 本
            </div>
            <div class="text-body-2">
              创建 Profile: {{ applyResult.created_profiles }} 个
            </div>
            <div class="text-body-2">
              更新 Profile: {{ applyResult.updated_profiles }} 个
            </div>
            <div class="text-body-2">
              跳过（已有 Profile）: {{ applyResult.skipped_existing_profile }} 个
            </div>
          </v-alert>
        </v-card-text>
      </v-card>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useToast } from 'vue-toastification'
import PageHeader from '@/components/common/PageHeader.vue'
import { devTTSVoicePresetsApi, devTTSWorkBatchApi, adminSettingsApi } from '@/services/api'
import type {
  TTSVoicePreset,
  TTSWorkBatchFilter,
  TTSWorkBatchPreviewResponse,
  ApplyTTSWorkPresetResult
} from '@/types/tts'
import type { TTSVoicePresetUsage } from '@/types/settings'
import { formatDateTime } from '@/utils/formatters'

const toast = useToast()

// 状态
const presets = ref<TTSVoicePreset[]>([])
const presetsLoading = ref(false)
const selectedPresetId = ref<number | null>(null)
const presetUsageMap = ref<Map<number, TTSVoicePresetUsage>>(new Map())
const filter = ref<TTSWorkBatchFilter>({
  language: undefined,
  author_substring: undefined,
  series_substring: undefined,
  tag_keyword: undefined,
  created_from: undefined,
  created_to: undefined,
  has_profile: undefined
})
const hasProfileFilter = ref<'all' | 'has' | 'none' | null>(null)
const previewResult = ref<TTSWorkBatchPreviewResponse | null>(null)
const previewLoading = ref(false)
const applyOptions = ref({
  override_existing: false,
  enable_profile: true
})
const applyLoading = ref(false)
const applyResult = ref<ApplyTTSWorkPresetResult | null>(null)

// 计算属性：批量预览统计
const batchSummary = computed(() => {
  const items = previewResult.value?.items ?? []
  let withProfile = 0
  let withProfileNoPreset = 0
  let withoutProfile = 0

  for (const item of items) {
    if (!item.has_profile) {
      withoutProfile++
    } else if (!item.profile_preset_id) {
      withProfileNoPreset++
      withProfile++
    } else {
      withProfile++
    }
  }

  return {
    total: items.length,
    withProfile,
    withProfileNoPreset,
    withoutProfile
  }
})

// 计算属性
const hasProfileOptions = [
  { label: '全部', value: 'all' },
  { label: '仅有 Profile', value: 'has' },
  { label: '仅无 Profile', value: 'none' }
]

const previewHeaders = [
  { title: 'EBook ID', key: 'ebook_id', sortable: true },
  { title: '标题', key: 'title', sortable: true },
  { title: '作者', key: 'author', sortable: false },
  { title: '系列', key: 'series', sortable: false },
  { title: '语言', key: 'language', sortable: false },
  { title: '创建时间', key: 'created_at', sortable: true },
  { title: 'TTS Profile 状态', key: 'profile_status', sortable: false }
]

// 加载预设列表
const loadPresets = async () => {
  presetsLoading.value = true
  try {
    presets.value = await devTTSVoicePresetsApi.list()
  } catch (err: any) {
    console.error('加载预设列表失败:', err)
    toast.error(err.response?.data?.message || err.message || '加载预设列表失败')
  } finally {
    presetsLoading.value = false
  }
}

// 加载预设使用统计（用于热度提醒）
const loadPresetUsage = async () => {
  try {
    const response = await adminSettingsApi.getTTSSettings()
    if (response.data && response.data.preset_usage) {
      const map = new Map<number, TTSVoicePresetUsage>()
      for (const usage of response.data.preset_usage) {
        map.set(usage.id, usage)
      }
      presetUsageMap.value = map
    }
  } catch (err: any) {
    // 静默失败，不影响基本功能
    console.warn('加载预设使用统计失败:', err)
  }
}

// 计算属性：当前选中预设的热度信息
const selectedPresetHeatInfo = computed(() => {
  if (!selectedPresetId.value) return null
  return presetUsageMap.value.get(selectedPresetId.value) || null
})

// 获取预设提醒类型
const getPresetAlertType = (info: TTSVoicePresetUsage): 'warning' | 'info' | 'success' => {
  if (info.is_sleeping || info.is_cold) return 'warning'
  if (info.is_hot) return 'success'
  return 'info'
}

// 预览匹配作品
const handlePreview = async () => {
  previewLoading.value = true
  previewResult.value = null
  applyResult.value = null

  try {
    // 转换 has_profile 筛选
    const filterPayload: TTSWorkBatchFilter = {
      ...filter.value,
      has_profile: hasProfileFilter.value === 'all' ? undefined : (hasProfileFilter.value === 'has' ? true : (hasProfileFilter.value === 'none' ? false : undefined))
    }

    // 转换日期时间格式（如果需要）
    if (filterPayload.created_from) {
      // 前端 datetime-local 返回的是本地时间字符串，需要转换为 ISO 格式
      const date = new Date(filterPayload.created_from)
      filterPayload.created_from = date.toISOString()
    }
    if (filterPayload.created_to) {
      const date = new Date(filterPayload.created_to)
      filterPayload.created_to = date.toISOString()
    }

    const result = await devTTSWorkBatchApi.preview(filterPayload)
    previewResult.value = result
    toast.success(`找到 ${result.total} 本匹配的作品`)
  } catch (err: any) {
    console.error('预览失败:', err)
    toast.error(err.response?.data?.message || err.message || '预览失败')
  } finally {
    previewLoading.value = false
  }
}

// Dry-run 预演
const handleDryRun = async () => {
  if (!selectedPresetId.value) {
    toast.warning('请先选择一个预设')
    return
  }

  applyLoading.value = true
  applyResult.value = null

  try {
    const filterPayload: TTSWorkBatchFilter = {
      ...filter.value,
      has_profile: hasProfileFilter.value === 'all' ? undefined : (hasProfileFilter.value === 'has' ? true : (hasProfileFilter.value === 'none' ? false : undefined))
    }

    // 转换日期时间格式
    if (filterPayload.created_from) {
      const date = new Date(filterPayload.created_from)
      filterPayload.created_from = date.toISOString()
    }
    if (filterPayload.created_to) {
      const date = new Date(filterPayload.created_to)
      filterPayload.created_to = date.toISOString()
    }

    const result = await devTTSWorkBatchApi.apply({
      preset_id: selectedPresetId.value,
      filter: filterPayload,
      override_existing: applyOptions.value.override_existing,
      enable_profile: applyOptions.value.enable_profile,
      dry_run: true
    })

    applyResult.value = result
    toast.info(`Dry-run 完成：将创建 ${result.created_profiles} 个，更新 ${result.updated_profiles} 个，跳过 ${result.skipped_existing_profile} 个`)
  } catch (err: any) {
    console.error('Dry-run 失败:', err)
    toast.error(err.response?.data?.message || err.message || 'Dry-run 失败')
  } finally {
    applyLoading.value = false
  }
}

// 应用预设
const handleApply = async () => {
  if (!selectedPresetId.value) {
    toast.warning('请先选择一个预设')
    return
  }

  if (!previewResult.value || previewResult.value.total === 0) {
    toast.warning('请先预览匹配的作品')
    return
  }

  // 二次确认
  const confirmMessage = `确定要将预设应用到 ${previewResult.value.total} 本作品吗？\n\n` +
    `将${applyOptions.value.override_existing ? '创建/更新' : '仅创建'} TTSWorkProfile，` +
    `preset_id=${selectedPresetId.value}，enabled=${applyOptions.value.enable_profile}`

  if (!confirm(confirmMessage)) {
    return
  }

  applyLoading.value = true
  applyResult.value = null

  try {
    const filterPayload: TTSWorkBatchFilter = {
      ...filter.value,
      has_profile: hasProfileFilter.value === 'all' ? undefined : (hasProfileFilter.value === 'has' ? true : (hasProfileFilter.value === 'none' ? false : undefined))
    }

    // 转换日期时间格式
    if (filterPayload.created_from) {
      const date = new Date(filterPayload.created_from)
      filterPayload.created_from = date.toISOString()
    }
    if (filterPayload.created_to) {
      const date = new Date(filterPayload.created_to)
      filterPayload.created_to = date.toISOString()
    }

    const result = await devTTSWorkBatchApi.apply({
      preset_id: selectedPresetId.value,
      filter: filterPayload,
      override_existing: applyOptions.value.override_existing,
      enable_profile: applyOptions.value.enable_profile,
      dry_run: false
    })

    applyResult.value = result
    toast.success(
      `批量应用完成：创建 ${result.created_profiles} 个 Profile，` +
      `更新 ${result.updated_profiles} 个，跳过 ${result.skipped_existing_profile} 个`
    )

    // 刷新预览列表
    await handlePreview()
  } catch (err: any) {
    console.error('批量应用失败:', err)
    toast.error(err.response?.data?.message || err.message || '批量应用失败')
  } finally {
    applyLoading.value = false
  }
}

// 组件挂载时加载预设列表和使用统计
onMounted(() => {
  loadPresets()
  loadPresetUsage()
})
</script>

<style scoped>
.tts-work-batch-page {
  min-height: 100vh;
  background-color: #f5f5f5;
}
</style>

