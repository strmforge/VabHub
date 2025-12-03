<template>
  <v-container fluid class="pa-4">
    <!-- 顶部说明 -->
    <v-alert type="info" variant="tonal" class="mb-4" closable>
      <v-alert-title>
        <div class="d-flex align-center">
          AI 故障医生 (Beta)
          <v-chip size="x-small" color="primary" variant="flat" class="ml-2">DIAGNOSE</v-chip>
          <v-chip size="x-small" color="success" variant="outlined" class="ml-2">只读建议</v-chip>
        </div>
      </v-alert-title>
      <div class="text-body-2 mt-2">
        <p>AI 驱动的系统健康诊断助手，帮助您快速定位和分析系统问题。</p>
        <p class="mt-1">所有输出仅为<strong>诊断建议</strong>，不会自动执行任何修复操作。</p>
      </div>
    </v-alert>

    <!-- AI 状态提示 -->
    <AiStatusAlert />

    <!-- 诊断控制区 -->
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-stethoscope</v-icon>
        系统诊断
      </v-card-title>
      <v-card-text>
        <!-- 预设场景 -->
        <div class="mb-4">
          <span class="text-caption text-grey mr-2">快速诊断：</span>
          <v-chip
            v-for="preset in presetPrompts"
            :key="preset.id"
            size="small"
            variant="outlined"
            class="mr-2 mb-2"
            @click="selectPreset(preset)"
          >
            {{ preset.title }}
          </v-chip>
        </div>

        <v-row>
          <v-col cols="12" md="3">
            <v-select
              v-model="timeWindow"
              :items="timeWindowOptions"
              item-title="label"
              item-value="value"
              label="时间范围"
              variant="outlined"
              density="comfortable"
              hide-details
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="focus"
              :items="focusOptions"
              item-title="label"
              item-value="value"
              label="聚焦模块"
              variant="outlined"
              density="comfortable"
              hide-details
              clearable
            />
          </v-col>
          <v-col cols="12" md="6">
            <v-text-field
              v-model="prompt"
              label="问题描述（可选）"
              placeholder="例如：最近下载经常失败..."
              variant="outlined"
              density="comfortable"
              hide-details
              @keydown.enter="runDiagnosis"
            />
          </v-col>
        </v-row>

        <div class="d-flex justify-end mt-4">
          <v-btn
            color="primary"
            size="large"
            :loading="loading"
            @click="runDiagnosis"
          >
            <v-icon start>mdi-magnify-scan</v-icon>
            开始诊断
          </v-btn>
        </div>
      </v-card-text>
    </v-card>

    <!-- 诊断结果 -->
    <template v-if="report">
      <!-- 总体状态 -->
      <v-card class="mb-4" :color="getStatusColor(report.overall_status)" variant="tonal">
        <v-card-title class="d-flex align-center">
          <v-icon :color="getStatusIconColor(report.overall_status)" class="mr-2">
            {{ getStatusIcon(report.overall_status) }}
          </v-icon>
          诊断结果：{{ getStatusLabel(report.overall_status) }}
        </v-card-title>
        <v-card-text>
          <div class="text-body-1">{{ report.summary }}</div>
          <div class="text-caption text-grey mt-2" v-if="report.generated_at">
            生成时间：{{ formatTime(report.generated_at) }}
          </div>
        </v-card-text>
      </v-card>

      <!-- 诊断项列表 -->
      <template v-if="report.items?.length">
        <div class="text-h6 mb-3">
          <v-icon class="mr-2">mdi-clipboard-list-outline</v-icon>
          诊断项（{{ report.items.length }} 个）
        </div>

        <v-row>
          <v-col
            v-for="item in report.items"
            :key="item.id"
            cols="12"
            md="6"
          >
            <v-card variant="outlined" class="h-100">
              <v-card-title class="d-flex align-center">
                <v-chip :color="getSeverityColor(item.severity)" size="small" class="mr-2">
                  {{ getSeverityLabel(item.severity) }}
                </v-chip>
                <span class="text-truncate">{{ item.title }}</span>
              </v-card-title>
              <v-card-text>
                <div class="text-body-2 mb-3">{{ item.description }}</div>

                <!-- 证据 -->
                <div v-if="item.evidence?.length" class="mb-3">
                  <div class="text-caption text-grey mb-1">证据</div>
                  <v-chip
                    v-for="(ev, idx) in item.evidence.slice(0, 3)"
                    :key="idx"
                    size="x-small"
                    variant="tonal"
                    class="mr-1 mb-1"
                  >
                    {{ ev.length > 50 ? ev.substring(0, 50) + '...' : ev }}
                  </v-chip>
                </div>

                <!-- 相关组件 -->
                <div v-if="item.related_components?.length">
                  <div class="text-caption text-grey mb-1">相关组件</div>
                  <v-chip
                    v-for="comp in item.related_components"
                    :key="comp"
                    size="x-small"
                    variant="outlined"
                    class="mr-1"
                  >
                    {{ comp }}
                  </v-chip>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </template>

      <!-- 建议步骤 -->
      <template v-if="report.suggested_steps?.length">
        <div class="text-h6 mb-3 mt-4">
          <v-icon class="mr-2">mdi-format-list-numbered</v-icon>
          建议操作步骤
        </div>

        <v-timeline side="end" density="compact">
          <v-timeline-item
            v-for="step in report.suggested_steps"
            :key="step.step"
            :dot-color="step.is_safe ? 'success' : 'warning'"
            size="small"
          >
            <template #opposite>
              <span class="text-caption">步骤 {{ step.step }}</span>
            </template>
            <v-card variant="tonal" class="pa-3">
              <div class="d-flex align-center mb-1">
                <span class="font-weight-bold">{{ step.title }}</span>
                <v-chip
                  v-if="step.is_safe"
                  size="x-small"
                  color="success"
                  variant="tonal"
                  class="ml-2"
                >
                  <v-icon size="x-small" start>mdi-check-circle</v-icon>
                  只读
                </v-chip>
                <v-chip
                  v-else
                  size="x-small"
                  color="warning"
                  variant="tonal"
                  class="ml-2"
                >
                  <v-icon size="x-small" start>mdi-alert</v-icon>
                  需修改
                </v-chip>
              </div>
              <div class="text-body-2 text-grey-darken-1">{{ step.detail }}</div>
            </v-card>
          </v-timeline-item>
        </v-timeline>
      </template>

      <!-- 调试信息 -->
      <v-expansion-panels v-if="report.raw_refs" class="mt-4">
        <v-expansion-panel title="调试信息（仅管理员可见）">
          <v-expansion-panel-text>
            <pre class="text-caption bg-grey-lighten-4 pa-3 rounded overflow-auto" style="max-height: 300px;">{{ JSON.stringify(report.raw_refs, null, 2) }}</pre>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </template>

    <!-- 无诊断结果 -->
    <v-alert v-else-if="!loading && hasRunOnce" type="info" variant="tonal">
      暂无诊断结果，请点击"开始诊断"按钮。
    </v-alert>

    <!-- 错误提示 -->
    <v-alert v-if="error" type="error" variant="tonal" closable class="mt-4">
      {{ error }}
    </v-alert>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { aiLogDoctorApi, type SystemDiagnosisReport, type PresetPrompt, type DiagnosisSeverity } from '@/api/aiLogDoctor'
import AiStatusAlert from '@/components/ai/AiStatusAlert.vue'

// 状态
const loading = ref(false)
const error = ref('')
const hasRunOnce = ref(false)

// 表单
const timeWindow = ref('24h')
const focus = ref<string | null>(null)
const prompt = ref('')

// 结果
const report = ref<SystemDiagnosisReport | null>(null)

// 预设
const presetPrompts = ref<PresetPrompt[]>([])

// 选项
const timeWindowOptions = [
  { value: '1h', label: '最近 1 小时' },
  { value: '24h', label: '最近 24 小时' },
  { value: '7d', label: '最近 7 天' },
]

const focusOptions = [
  { value: 'all', label: '全面检查' },
  { value: 'download', label: '下载相关' },
  { value: 'rsshub', label: 'RSSHub 订阅' },
  { value: 'site', label: '站点连通性' },
  { value: 'runner', label: '定时任务' },
  { value: 'telegram', label: 'Telegram Bot' },
  { value: 'storage', label: '存储空间' },
]

// 选择预设
function selectPreset(preset: PresetPrompt) {
  prompt.value = preset.prompt
  if (preset.focus) {
    focus.value = preset.focus
  }
}

// 执行诊断
async function runDiagnosis() {
  loading.value = true
  error.value = ''
  hasRunOnce.value = true
  
  try {
    const result = await aiLogDoctorApi.diagnose({
      prompt: prompt.value || undefined,
      time_window: timeWindow.value,
      focus: focus.value || undefined,
    })
    
    if (result.success && result.report) {
      report.value = result.report
    } else {
      error.value = result.error || '诊断失败'
    }
  } catch (e: any) {
    console.error('诊断失败:', e)
    error.value = e.response?.data?.detail || e.message || '诊断请求失败'
  } finally {
    loading.value = false
  }
}

// 辅助函数
function getStatusColor(status: DiagnosisSeverity): string {
  const colors: Record<DiagnosisSeverity, string> = {
    info: 'blue-lighten-5',
    warning: 'orange-lighten-5',
    error: 'red-lighten-5',
    critical: 'red-darken-1',
  }
  return colors[status] || 'grey-lighten-4'
}

function getStatusIconColor(status: DiagnosisSeverity): string {
  const colors: Record<DiagnosisSeverity, string> = {
    info: 'blue',
    warning: 'orange',
    error: 'red',
    critical: 'white',
  }
  return colors[status] || 'grey'
}

function getStatusIcon(status: DiagnosisSeverity): string {
  const icons: Record<DiagnosisSeverity, string> = {
    info: 'mdi-check-circle',
    warning: 'mdi-alert',
    error: 'mdi-alert-circle',
    critical: 'mdi-alert-octagon',
  }
  return icons[status] || 'mdi-help-circle'
}

function getStatusLabel(status: DiagnosisSeverity): string {
  const labels: Record<DiagnosisSeverity, string> = {
    info: '系统正常',
    warning: '存在隐患',
    error: '有问题需要关注',
    critical: '严重问题',
  }
  return labels[status] || '未知'
}

function getSeverityColor(severity: DiagnosisSeverity): string {
  const colors: Record<DiagnosisSeverity, string> = {
    info: 'blue',
    warning: 'orange',
    error: 'red',
    critical: 'red-darken-3',
  }
  return colors[severity] || 'grey'
}

function getSeverityLabel(severity: DiagnosisSeverity): string {
  const labels: Record<DiagnosisSeverity, string> = {
    info: '提示',
    warning: '警告',
    error: '错误',
    critical: '严重',
  }
  return labels[severity] || severity
}

function formatTime(isoString: string): string {
  try {
    return new Date(isoString).toLocaleString('zh-CN')
  } catch {
    return isoString
  }
}

// 初始化
onMounted(async () => {
  try {
    const result = await aiLogDoctorApi.getPresetPrompts()
    presetPrompts.value = result.prompts
  } catch (e) {
    console.error('加载预设提示词失败:', e)
  }
})
</script>

<style scoped>
pre {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 12px;
}
</style>
