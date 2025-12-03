<template>
  <div class="tts-settings-page">
    <v-container>
      <!-- 标题区 -->
      <v-card class="mb-6">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="primary">mdi-text-to-speech</v-icon>
          <span>TTS 子系统状态</span>
          <v-chip size="small" color="primary" class="ml-2">开发工具</v-chip>
        </v-card-title>
        <v-card-subtitle>
          配置 / 限流 / 使用情况（只读）
        </v-card-subtitle>
      </v-card>

      <!-- 加载状态 -->
      <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-4"></v-progress-linear>

      <!-- 错误提示 -->
      <v-alert v-if="errorMessage" type="error" class="mb-4">
        {{ errorMessage }}
      </v-alert>

      <!-- 内容区域 -->
      <v-row v-if="settings">
        <!-- 卡片 1: 基础健康状态 -->
        <v-col cols="12">
          <v-card class="mb-4">
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2" color="info">mdi-heart-pulse</v-icon>
              <span>基础健康状态</span>
            </v-card-title>
            <v-divider />
            <v-card-text>
              <v-list density="compact">
                <v-list-item>
                  <v-list-item-title>启用状态</v-list-item-title>
                  <template v-slot:append>
                    <v-chip
                      :color="settings.enabled ? 'success' : 'default'"
                      size="small"
                      variant="flat"
                    >
                      {{ settings.enabled ? '已启用' : '未启用' }}
                    </v-chip>
                  </template>
                </v-list-item>

                <v-list-item>
                  <v-list-item-title>Provider</v-list-item-title>
                  <v-list-item-subtitle>
                    {{ settings.provider }}
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item>
                  <v-list-item-title>Status</v-list-item-title>
                  <template v-slot:append>
                    <v-chip
                      :color="getStatusColor(settings.status)"
                      size="small"
                      variant="flat"
                    >
                      {{ getStatusLabel(settings.status) }}
                    </v-chip>
                  </template>
                </v-list-item>

                <v-list-item v-if="settings.output_root">
                  <v-list-item-title>输出目录</v-list-item-title>
                  <v-list-item-subtitle class="text-wrap">
                    {{ settings.output_root }}
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item v-if="settings.strategy">
                  <v-list-item-title>章节策略</v-list-item-title>
                  <v-list-item-subtitle>
                    {{ settings.strategy }}
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item v-if="settings.max_chapters">
                  <v-list-item-title>最大章节数</v-list-item-title>
                  <v-list-item-subtitle>
                    {{ settings.max_chapters }}
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item v-if="settings.last_used_at">
                  <v-list-item-title>最近使用时间</v-list-item-title>
                  <v-list-item-subtitle>
                    {{ formatDateTime(settings.last_used_at) }}
                    <span class="text-medium-emphasis ml-2">
                      ({{ formatRelativeTime(settings.last_used_at) }})
                    </span>
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item v-if="settings.last_error">
                  <v-list-item-title>最近错误</v-list-item-title>
                  <template v-slot:append>
                    <v-alert type="error" density="compact" class="mt-2">
                      {{ settings.last_error }}
                    </v-alert>
                  </template>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- 卡片 2: 限流配置 & 最近限流 -->
        <v-col cols="12" md="6">
          <v-card class="mb-4">
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2" color="warning">mdi-speedometer</v-icon>
              <span>限流配置 & 最近限流</span>
            </v-card-title>
            <v-divider />
            <v-card-text>
              <v-list density="compact">
                <v-list-item>
                  <v-list-item-title>限流启用状态</v-list-item-title>
                  <template v-slot:append>
                    <v-chip
                      :color="settings.rate_limit_enabled ? 'success' : 'default'"
                      size="small"
                      variant="flat"
                    >
                      {{ settings.rate_limit_enabled ? '已启用' : '未启用' }}
                    </v-chip>
                  </template>
                </v-list-item>

                <template v-if="settings.rate_limit_enabled && settings.rate_limit_info">
                  <v-list-item>
                    <v-list-item-title>每日最大请求数</v-list-item-title>
                    <v-list-item-subtitle>
                      {{ settings.rate_limit_info.max_daily_requests || '无限制' }}
                    </v-list-item-subtitle>
                  </v-list-item>

                  <v-list-item>
                    <v-list-item-title>每日最大字符数</v-list-item-title>
                    <v-list-item-subtitle>
                      {{ settings.rate_limit_info.max_daily_characters || '无限制' }}
                    </v-list-item-subtitle>
                  </v-list-item>

                  <v-list-item>
                    <v-list-item-title>单次运行最大请求数</v-list-item-title>
                    <v-list-item-subtitle>
                      {{ settings.rate_limit_info.max_requests_per_run || '无限制' }}
                    </v-list-item-subtitle>
                  </v-list-item>

                  <v-list-item v-if="settings.rate_limit_info.last_limited_at">
                    <v-list-item-title>最近限流时间</v-list-item-title>
                    <v-list-item-subtitle>
                      {{ formatDateTime(settings.rate_limit_info.last_limited_at) }}
                      <span class="text-medium-emphasis ml-2">
                        ({{ formatRelativeTime(settings.rate_limit_info.last_limited_at) }})
                      </span>
                    </v-list-item-subtitle>
                  </v-list-item>

                  <v-list-item v-if="settings.rate_limit_info.last_limited_reason">
                    <v-list-item-title>最近限流原因</v-list-item-title>
                    <v-list-item-subtitle>
                      {{ settings.rate_limit_info.last_limited_reason }}
                    </v-list-item-subtitle>
                  </v-list-item>
                </template>

                <v-list-item v-else>
                  <v-list-item-subtitle class="text-medium-emphasis">
                    当前未启用 TTS 限流
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- 卡片 3: 使用统计 -->
        <v-col cols="12" md="6">
          <v-card class="mb-4">
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2" color="success">mdi-chart-bar</v-icon>
              <span>使用统计（来自数据库）</span>
            </v-card-title>
            <v-divider />
            <v-card-text>
              <v-list density="compact">
                <v-list-item>
                  <v-list-item-title>TTS 生成的有声书总数</v-list-item-title>
                  <template v-slot:append>
                    <v-chip color="primary" size="small" variant="flat">
                      {{ settings.usage_stats.total_tts_audiobooks }}
                    </v-chip>
                  </template>
                </v-list-item>

                <v-list-item v-if="Object.keys(settings.usage_stats.by_provider).length > 0">
                  <v-list-item-title>按 Provider 分布</v-list-item-title>
                </v-list-item>
              </v-list>

              <!-- Provider 分布表格 -->
              <v-data-table
                v-if="Object.keys(settings.usage_stats.by_provider).length > 0"
                :headers="providerHeaders"
                :items="providerItems"
                density="compact"
                hide-default-footer
                class="mt-2"
              >
                <template v-slot:item.provider="{ item }">
                  <v-chip size="small" color="primary" variant="flat">
                    {{ item.provider }}
                  </v-chip>
                </template>
                <template v-slot:item.count="{ item }">
                  <strong>{{ item.count }}</strong>
                </template>
              </v-data-table>

              <v-alert
                v-else
                type="info"
                density="compact"
                class="mt-2"
              >
                暂无 TTS 生成的有声书记录
              </v-alert>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- 预设使用统计卡片 -->
      <v-card class="mb-4" v-if="settings && settings.preset_usage && settings.preset_usage.length > 0">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="purple">mdi-chart-pie</v-icon>
          <span>声线预设使用统计</span>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <!-- 排序和筛选控制 -->
          <div class="d-flex gap-4 mb-4">
            <v-select
              v-model="presetSortBy"
              :items="presetSortOptions"
              label="排序方式"
              density="compact"
              variant="outlined"
              style="max-width: 200px"
            />
            <v-select
              v-model="presetFilterBy"
              :items="presetFilterOptions"
              label="筛选"
              density="compact"
              variant="outlined"
              style="max-width: 150px"
            />
          </div>

          <v-data-table
            :headers="presetUsageHeaders"
            :items="filteredAndSortedPresets"
            density="compact"
            hide-default-footer
          >
            <template v-slot:item.name="{ item }">
              <div class="d-flex align-center">
                <strong>{{ item.name }}</strong>
                <v-chip
                  v-if="item.is_default"
                  size="x-small"
                  color="success"
                  variant="flat"
                  class="ml-2"
                >
                  默认
                </v-chip>
                <!-- 热度徽章 -->
                <v-tooltip v-if="item.is_hot || item.is_sleeping || item.is_cold" location="top">
                  <template v-slot:activator="{ props }">
                    <v-chip
                      v-bind="props"
                      :color="getHeatChipColor(item)"
                      size="x-small"
                      variant="flat"
                      class="ml-2"
                    >
                      <v-icon :icon="getHeatIcon(item)" size="x-small" class="mr-1" />
                      {{ getHeatLabel(item) }}
                    </v-chip>
                  </template>
                  <span>{{ getHeatTooltip(item) }}</span>
                </v-tooltip>
              </div>
            </template>
            <template v-slot:item.voice_language="{ item }">
              <div class="text-caption">
                <div v-if="item.voice">{{ item.voice }}</div>
                <div v-if="item.language" class="text-medium-emphasis">{{ item.language }}</div>
                <div v-if="!item.voice && !item.language" class="text-medium-emphasis">-</div>
              </div>
            </template>
            <template v-slot:item.bound_works_count="{ item }">
              <v-chip size="small" color="primary" variant="flat">
                {{ item.bound_works_count }}
              </v-chip>
            </template>
            <template v-slot:item.tts_generated_works_count="{ item }">
              <v-chip size="small" color="success" variant="flat">
                {{ item.tts_generated_works_count }}
              </v-chip>
            </template>
            <template v-slot:item.usage_ratio="{ item }">
              <div class="d-flex align-center gap-2">
                <span class="text-caption">
                  {{ item.bound_works_count > 0 
                    ? `${item.tts_generated_works_count} / ${item.bound_works_count} (${Math.round((item.usage_ratio || 0) * 100)}%)`
                    : '0 / 0 (0%)'
                  }}
                </span>
                <v-progress-linear
                  :model-value="(item.usage_ratio || 0) * 100"
                  color="success"
                  height="6"
                  style="max-width: 80px"
                />
              </div>
            </template>
            <template v-slot:item.last_used_at="{ item }">
              <span v-if="item.last_used_at">
                {{ formatDateTime(item.last_used_at) }}
                <span class="text-medium-emphasis ml-1">
                  ({{ formatRelativeTime(item.last_used_at) }})
                </span>
              </span>
              <span v-else class="text-medium-emphasis">从未使用</span>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>

      <!-- 作品 Profile 总览卡片 -->
      <!-- TTS 存储状态卡片 -->
      <v-card class="mb-4" v-if="settings && settings.storage_overview">
        <v-card-title class="d-flex align-center justify-space-between">
          <div class="d-flex align-center">
            <v-icon class="mr-2" color="warning">mdi-folder-information</v-icon>
            <span>TTS 存储状态</span>
          </div>
          <v-chip :color="storageStatusColor" size="small" variant="flat">
            {{ storageStatusLabel }}
          </v-chip>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <div class="text-body-2 mb-2">
            根目录：<code>{{ settings.storage_overview.root }}</code>
          </div>
          <div class="text-body-2 mb-2">
            总文件数：{{ settings.storage_overview.total_files.toLocaleString() }}
          </div>
          <div class="text-body-2 mb-3">
            总大小：{{ formatBytes(settings.storage_overview.total_size_bytes) }}
          </div>

          <v-alert
            class="mt-3"
            v-if="settings.storage_overview.warning === 'high_usage' || settings.storage_overview.warning === 'critical'"
            type="warning"
            variant="tonal"
            density="compact"
          >
            当前 TTS 缓存占用偏高，建议前往存储管理页按需清理。
          </v-alert>

          <v-btn
            class="mt-3"
            size="small"
            variant="text"
            color="primary"
            @click="$router.push('/dev/tts-storage')"
          >
            <v-icon start>mdi-open-in-new</v-icon>
            打开 TTS 存储管理
          </v-btn>
        </v-card-text>
      </v-card>

      <v-card class="mb-4" v-if="settings && settings.work_profile_summary">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="info">mdi-book-open-variant</v-icon>
          <span>作品 Profile 总览</span>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-row>
            <v-col cols="12" sm="6" md="3">
              <v-card variant="outlined">
                <v-card-text class="text-center">
                  <div class="text-h5 font-weight-bold">{{ settings.work_profile_summary.works_total }}</div>
                  <div class="text-body-2 text-medium-emphasis">总作品数</div>
                </v-card-text>
              </v-card>
            </v-col>
            <v-col cols="12" sm="6" md="3">
              <v-card variant="outlined" color="success">
                <v-card-text class="text-center">
                  <div class="text-h5 font-weight-bold text-success">
                    {{ settings.work_profile_summary.works_with_profile }}
                  </div>
                  <div class="text-body-2 text-medium-emphasis">有 Profile 的作品</div>
                </v-card-text>
              </v-card>
            </v-col>
            <v-col cols="12" sm="6" md="3">
              <v-card variant="outlined" color="warning">
                <v-card-text class="text-center">
                  <div class="text-h5 font-weight-bold text-warning">
                    {{ settings.work_profile_summary.works_without_profile }}
                  </div>
                  <div class="text-body-2 text-medium-emphasis">无 Profile 的作品</div>
                </v-card-text>
              </v-card>
            </v-col>
            <v-col cols="12" sm="6" md="3">
              <v-card variant="outlined" color="primary">
                <v-card-text class="text-center">
                  <div class="text-h5 font-weight-bold text-primary">
                    {{ settings.work_profile_summary.works_with_preset }}
                  </div>
                  <div class="text-body-2 text-medium-emphasis">使用预设的作品</div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
          <v-row class="mt-2">
            <v-col cols="12" sm="6">
              <v-card variant="outlined" color="info">
                <v-card-text class="text-center">
                  <div class="text-h5 font-weight-bold text-info">
                    {{ settings.work_profile_summary.works_without_preset }}
                  </div>
                  <div class="text-body-2 text-medium-emphasis">有 Profile 但未使用预设</div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- 声线预设管理卡片 -->
      <v-card class="mb-4">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="purple">mdi-voice</v-icon>
          <span>TTS 声线预设管理（Dev）</span>
          <v-chip size="small" color="warning" class="ml-2">Dev Only</v-chip>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <div class="d-flex justify-end mb-3">
            <v-btn
              color="primary"
              variant="elevated"
              prepend-icon="mdi-plus"
              @click="openPresetDialog()"
            >
              新增声线预设
            </v-btn>
          </div>

          <v-data-table
            :headers="presetHeaders"
            :items="presets"
            :loading="presetsLoading"
            density="compact"
            no-data-text="暂无预设"
          >
            <template v-slot:item.name="{ item }">
              <div class="d-flex align-center">
                <strong>{{ item.name }}</strong>
                <v-chip
                  v-if="item.is_default"
                  size="x-small"
                  color="success"
                  variant="flat"
                  class="ml-2"
                >
                  默认
                </v-chip>
              </div>
            </template>

            <template v-slot:item.provider="{ item }">
              <span v-if="item.provider">{{ item.provider }}</span>
              <span v-else class="text-medium-emphasis">-</span>
            </template>

            <template v-slot:item.language="{ item }">
              <span v-if="item.language">{{ item.language }}</span>
              <span v-else class="text-medium-emphasis">-</span>
            </template>

            <template v-slot:item.voice="{ item }">
              <span v-if="item.voice">{{ item.voice }}</span>
              <span v-else class="text-medium-emphasis">-</span>
            </template>

            <template v-slot:item.params="{ item }">
              <div class="text-caption">
                <span v-if="item.speed !== null">Speed: {{ item.speed }}</span>
                <span v-if="item.speed !== null && item.pitch !== null">, </span>
                <span v-if="item.pitch !== null">Pitch: {{ item.pitch }}</span>
                <span v-if="item.speed === null && item.pitch === null" class="text-medium-emphasis">-</span>
              </div>
            </template>

            <template v-slot:item.actions="{ item }">
              <v-btn
                size="small"
                variant="text"
                icon="mdi-pencil"
                @click="openPresetDialog(item)"
              />
              <v-btn
                size="small"
                variant="text"
                icon="mdi-delete"
                color="error"
                @click="handleDeletePreset(item.id)"
              />
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>

      <!-- 预设编辑对话框 -->
      <v-dialog v-model="presetDialog" max-width="600" persistent>
        <v-card>
          <v-card-title>
            {{ editingPreset ? '编辑声线预设' : '新增声线预设' }}
          </v-card-title>
          <v-divider />
          <v-card-text>
            <v-form ref="presetFormRef">
              <v-text-field
                v-model="presetForm.name"
                label="预设名称"
                placeholder="例如：中文女声科幻"
                variant="outlined"
                density="compact"
                :rules="[v => !!v || '预设名称不能为空']"
                class="mb-2"
              />
              <v-text-field
                v-model="presetForm.provider"
                label="Provider"
                placeholder="dummy / http"
                variant="outlined"
                density="compact"
                class="mb-2"
              />
              <v-text-field
                v-model="presetForm.language"
                label="Language"
                placeholder="zh-CN / en-US"
                variant="outlined"
                density="compact"
                class="mb-2"
              />
              <v-text-field
                v-model="presetForm.voice"
                label="Voice"
                placeholder="zh-CN-female-1"
                variant="outlined"
                density="compact"
                class="mb-2"
              />
              <v-text-field
                v-model.number="presetForm.speed"
                label="Speed"
                type="number"
                placeholder="1.0"
                min="0.5"
                max="2.0"
                step="0.1"
                variant="outlined"
                density="compact"
                class="mb-2"
              />
              <v-text-field
                v-model.number="presetForm.pitch"
                label="Pitch"
                type="number"
                placeholder="0.0"
                min="-10.0"
                max="10.0"
                step="0.1"
                variant="outlined"
                density="compact"
                class="mb-2"
              />
              <v-textarea
                v-model="presetForm.notes"
                label="Notes"
                placeholder="备注信息"
                variant="outlined"
                density="compact"
                rows="2"
                class="mb-2"
              />
              <v-switch
                v-model="presetForm.is_default"
                label="设为默认预设"
                color="primary"
                density="compact"
              />
            </v-form>
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn
              variant="text"
              @click="presetDialog = false"
            >
              取消
            </v-btn>
            <v-btn
              color="primary"
              variant="elevated"
              :loading="presetSaving"
              @click="handleSavePreset"
            >
              保存
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { adminSettingsApi, devTTSVoicePresetsApi } from '@/services/api'
import type { TTSSettings } from '@/types/settings'
import type { TTSVoicePreset } from '@/types/tts'
import { formatDateTime, formatRelativeTime } from '@/utils/formatters'
import { useToast } from 'vue-toastification'

const toast = useToast()

// 状态
const loading = ref(false)
const errorMessage = ref<string | null>(null)
const settings = ref<TTSSettings | null>(null)
const presets = ref<TTSVoicePreset[]>([])
const presetsLoading = ref(false)
const presetDialog = ref(false)
const editingPreset = ref<TTSVoicePreset | null>(null)
const presetSaving = ref(false)
const presetForm = ref({
  name: '',
  provider: '',
  language: '',
  voice: '',
  speed: null as number | null,
  pitch: null as number | null,
  is_default: false,
  notes: ''
})
const presetFormRef = ref()

// Provider 分布表格
const providerHeaders = [
  { title: 'Provider', key: 'provider', sortable: false },
  { title: '数量', key: 'count', sortable: false, align: 'end' }
]

// 预设表格
const presetUsageHeaders = [
  { title: '预设名', key: 'name', sortable: true },
  { title: '提供商', key: 'provider', sortable: false },
  { title: '声音 / 语言', key: 'voice_language', sortable: false },
  { title: '绑定作品数', key: 'bound_works_count', sortable: true },
  { title: '已生成 TTS 作品数', key: 'tts_generated_works_count', sortable: true },
  { title: '使用比例', key: 'usage_ratio', sortable: true },
  { title: '最近使用时间', key: 'last_used_at', sortable: true }
]

// 排序和筛选
const presetSortBy = ref('bound_works_count')
const presetFilterBy = ref('all')

const presetSortOptions = [
  { title: '按绑定作品数', value: 'bound_works_count' },
  { title: '按已生成作品数', value: 'tts_generated_works_count' },
  { title: '按最近使用时间', value: 'last_used_at' },
  { title: '按热度（热门优先）', value: 'heat' }
]

const presetFilterOptions = [
  { title: '全部', value: 'all' },
  { title: '只看热门', value: 'hot' },
  { title: '只看沉睡', value: 'sleeping' },
  { title: '只看冷门', value: 'cold' }
]

// 筛选和排序后的预设列表
const filteredAndSortedPresets = computed(() => {
  if (!settings.value || !settings.value.preset_usage) return []
  
  let result = [...settings.value.preset_usage]
  
  // 筛选
  if (presetFilterBy.value !== 'all') {
    result = result.filter(item => {
      if (presetFilterBy.value === 'hot') return item.is_hot === true
      if (presetFilterBy.value === 'sleeping') return item.is_sleeping === true
      if (presetFilterBy.value === 'cold') return item.is_cold === true
      return true
    })
  }
  
  // 排序
  result.sort((a, b) => {
    if (presetSortBy.value === 'bound_works_count') {
      return b.bound_works_count - a.bound_works_count
    } else if (presetSortBy.value === 'tts_generated_works_count') {
      return b.tts_generated_works_count - a.tts_generated_works_count
    } else if (presetSortBy.value === 'last_used_at') {
      if (!a.last_used_at && !b.last_used_at) return 0
      if (!a.last_used_at) return 1
      if (!b.last_used_at) return -1
      return new Date(b.last_used_at).getTime() - new Date(a.last_used_at).getTime()
    } else if (presetSortBy.value === 'heat') {
      // 热度排序：hot > normal > sleeping > cold
      const heatOrder = { hot: 4, normal: 3, sleeping: 2, cold: 1 }
      const aOrder = heatOrder[a.heat_level || 'normal'] || 0
      const bOrder = heatOrder[b.heat_level || 'normal'] || 0
      if (aOrder !== bOrder) return bOrder - aOrder
      // 同热度时按绑定数排序
      return b.bound_works_count - a.bound_works_count
    }
    return 0
  })
  
  return result
})

// 热度相关辅助函数
const getHeatChipColor = (item: any): string => {
  if (item.is_hot) return 'error'
  if (item.is_sleeping) return 'blue-grey'
  if (item.is_cold) return 'info'
  return 'default'
}

const getHeatIcon = (item: any): string => {
  if (item.is_hot) return 'mdi-fire'
  if (item.is_sleeping) return 'mdi-weather-night'
  if (item.is_cold) return 'mdi-snowflake'
  return ''
}

const getHeatLabel = (item: any): string => {
  if (item.is_hot) return '热门'
  if (item.is_sleeping) return '沉睡'
  if (item.is_cold) return '冷门'
  return ''
}

const getHeatTooltip = (item: any): string => {
  if (item.is_hot) return '热门：绑定较多、生成比例高、最近 30 天内有使用'
  if (item.is_sleeping) return '沉睡：绑定较多，但 30 天未使用'
  if (item.is_cold) return '冷门：绑定和生成都比较少，适合评估是否保留'
  return ''
}

const presetHeaders = [
  { title: '名称', key: 'name', sortable: true },
  { title: 'Provider', key: 'provider', sortable: false },
  { title: 'Language', key: 'language', sortable: false },
  { title: 'Voice', key: 'voice', sortable: false },
  { title: 'Speed / Pitch', key: 'params', sortable: false },
  { title: '操作', key: 'actions', sortable: false, align: 'end' }
]

const providerItems = computed(() => {
  if (!settings.value) return []
  return Object.entries(settings.value.usage_stats.by_provider).map(([provider, count]) => ({
    provider: provider === 'unknown' ? '未知' : provider,
    count
  }))
})

// 加载设置
const loadSettings = async () => {
  loading.value = true
  errorMessage.value = null

  try {
    const response = await adminSettingsApi.getTTSSettings()
    settings.value = response.data
  } catch (err: any) {
    console.error('加载 TTS 设置失败:', err)
    errorMessage.value = err.response?.data?.error_message || 
                        err.response?.data?.message || 
                        err.message || 
                        '加载设置失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

// 获取状态颜色
const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    ok: 'success',
    degraded: 'warning',
    disabled: 'default'
  }
  return colors[status] || 'default'
}

// 获取状态标签
const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    ok: '正常',
    degraded: '降级',
    disabled: '已禁用'
  }
  return labels[status] || status
}

// 存储状态相关
const storageOverview = computed(() => settings.value?.storage_overview ?? null)

const storageStatusColor = computed(() => {
  const w = storageOverview.value?.warning
  if (!w || w === 'ok') return 'success'
  if (w === 'high_usage') return 'warning'
  if (w === 'critical') return 'error'
  if (w === 'no_root') return 'grey'
  if (w === 'scan_error') return 'error'
  return 'default'
})

const storageStatusLabel = computed(() => {
  const w = storageOverview.value?.warning
  switch (w) {
    case 'ok':
      return '正常'
    case 'high_usage':
      return '占用偏高'
    case 'critical':
      return '占用危险'
    case 'no_root':
      return '目录不存在'
    case 'scan_error':
      return '扫描错误'
    default:
      return '未知'
  }
})

function formatBytes(bytes: number): string {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let v = bytes
  let i = 0
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024
    i++
  }
  return `${v.toFixed(1)} ${units[i]}`
}

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

// 打开预设对话框
const openPresetDialog = (preset?: TTSVoicePreset) => {
  if (preset) {
    editingPreset.value = preset
    presetForm.value = {
      name: preset.name,
      provider: preset.provider || '',
      language: preset.language || '',
      voice: preset.voice || '',
      speed: preset.speed ?? null,
      pitch: preset.pitch ?? null,
      is_default: preset.is_default,
      notes: preset.notes || ''
    }
  } else {
    editingPreset.value = null
    presetForm.value = {
      name: '',
      provider: '',
      language: '',
      voice: '',
      speed: null,
      pitch: null,
      is_default: false,
      notes: ''
    }
  }
  presetDialog.value = true
}

// 保存预设
const handleSavePreset = async () => {
  if (!presetFormRef.value) return
  
  const { valid } = await presetFormRef.value.validate()
  if (!valid) return
  
  presetSaving.value = true
  try {
    const payload: any = {
      name: presetForm.value.name,
      provider: presetForm.value.provider || null,
      language: presetForm.value.language || null,
      voice: presetForm.value.voice || null,
      speed: presetForm.value.speed ?? null,
      pitch: presetForm.value.pitch ?? null,
      is_default: presetForm.value.is_default,
      notes: presetForm.value.notes || null
    }
    
    if (editingPreset.value) {
      payload.id = editingPreset.value.id
    }
    
    await devTTSVoicePresetsApi.upsert(payload)
    toast.success(editingPreset.value ? '预设已更新' : '预设已创建')
    presetDialog.value = false
    await loadPresets()
  } catch (err: any) {
    console.error('保存预设失败:', err)
    toast.error(err.response?.data?.message || err.message || '保存预设失败')
  } finally {
    presetSaving.value = false
  }
}

// 删除预设
const handleDeletePreset = async (presetId: number) => {
  if (!confirm('确定要删除此预设吗？引用该预设的作品 Profile 将自动解除绑定。')) return
  
  try {
    await devTTSVoicePresetsApi.delete(presetId)
    toast.success('预设已删除')
    await loadPresets()
  } catch (err: any) {
    console.error('删除预设失败:', err)
    toast.error(err.response?.data?.message || err.message || '删除预设失败')
  }
}

// 组件挂载时加载
onMounted(() => {
  loadSettings()
  loadPresets()
})
</script>

<style scoped>
.tts-settings-page {
  min-height: 100vh;
  background-color: #f5f5f5;
}
</style>

