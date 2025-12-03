<template>
  <v-container fluid class="pa-4">
    <!-- 顶部说明 -->
    <v-alert type="info" variant="tonal" class="mb-4" closable>
      <v-alert-title>
        <div class="d-flex align-center">
          AI 整理顾问 (Beta)
          <v-chip size="x-small" color="primary" variant="flat" class="ml-2">CLEANUP_ADVISOR</v-chip>
          <v-chip size="x-small" color="success" variant="outlined" class="ml-2">只读建议</v-chip>
        </div>
      </v-alert-title>
      <div class="text-body-2 mt-2">
        <p>AI 驱动的媒体库清理建议助手，帮助您优化存储空间。</p>
        <p class="mt-1">所有输出仅为<strong>清理草案</strong>，不会自动执行任何删除或移动操作。</p>
      </div>
    </v-alert>

    <!-- AI 状态提示 -->
    <AiStatusAlert />

    <!-- 清理控制区 -->
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-broom</v-icon>
        生成清理计划
      </v-card-title>
      <v-card-text>
        <!-- 预设场景 -->
        <div class="mb-4">
          <span class="text-caption text-grey mr-2">快速选择：</span>
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
              v-model="focus"
              :items="focusOptions"
              item-title="label"
              item-value="value"
              label="聚焦类型"
              variant="outlined"
              density="comfortable"
              hide-details
              clearable
            />
          </v-col>
          <v-col cols="12" md="2">
            <v-text-field
              v-model.number="minSizeGb"
              label="最小大小 (GB)"
              type="number"
              variant="outlined"
              density="comfortable"
              hide-details
              clearable
            />
          </v-col>
          <v-col cols="12" md="2">
            <v-checkbox
              v-model="includeRisky"
              label="包含高风险"
              density="comfortable"
              hide-details
            />
          </v-col>
          <v-col cols="12" md="5">
            <v-text-field
              v-model="prompt"
              label="需求描述（可选）"
              placeholder="例如：释放 50GB 空间..."
              variant="outlined"
              density="comfortable"
              hide-details
              @keydown.enter="generatePlan"
            />
          </v-col>
        </v-row>

        <div class="d-flex justify-end mt-4">
          <v-btn
            color="primary"
            size="large"
            :loading="loading"
            @click="generatePlan"
          >
            <v-icon start>mdi-auto-fix</v-icon>
            生成清理计划
          </v-btn>
        </div>
      </v-card-text>
    </v-card>

    <!-- 清理计划结果 -->
    <template v-if="draft">
      <!-- 总览卡片 -->
      <v-card class="mb-4" color="primary" variant="tonal">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-package-variant</v-icon>
          清理计划草案
        </v-card-title>
        <v-card-text>
          <div class="text-body-1">{{ draft.summary }}</div>
          <div class="d-flex align-center mt-3">
            <v-chip color="success" variant="flat" class="mr-3">
              <v-icon start size="small">mdi-harddisk</v-icon>
              预计可释放 {{ draft.total_savable_gb.toFixed(1) }} GB
            </v-chip>
            <v-chip variant="outlined" class="mr-3">
              {{ draft.actions.length }} 项操作
            </v-chip>
            <span class="text-caption text-grey" v-if="draft.generated_at">
              生成于 {{ formatTime(draft.generated_at) }}
            </span>
          </div>
        </v-card-text>
      </v-card>

      <!-- 警告 -->
      <v-alert
        v-for="(warning, idx) in draft.warnings"
        :key="idx"
        type="warning"
        variant="tonal"
        class="mb-3"
        density="compact"
      >
        {{ warning }}
      </v-alert>

      <!-- 操作列表 -->
      <template v-if="draft.actions.length">
        <div class="text-h6 mb-3">
          <v-icon class="mr-2">mdi-format-list-checks</v-icon>
          建议操作（{{ draft.actions.length }} 项）
        </div>

        <!-- 按风险级别分组 -->
        <template v-for="riskGroup in groupedActions" :key="riskGroup.level">
          <div class="text-subtitle-2 mb-2 d-flex align-center">
            <v-chip :color="getRiskColor(riskGroup.level)" size="small" class="mr-2">
              {{ getRiskLabel(riskGroup.level) }}
            </v-chip>
            <span class="text-grey">{{ riskGroup.actions.length }} 项，共 {{ riskGroup.totalGb.toFixed(1) }} GB</span>
          </div>
          
          <v-card variant="outlined" class="mb-4">
            <v-list density="compact">
              <v-list-item
                v-for="action in riskGroup.actions"
                :key="action.id"
                :class="{ 'bg-red-lighten-5': action.risk_level === 'risky' }"
              >
                <template #prepend>
                  <v-icon :color="getActionColor(action.action_type)" size="small">
                    {{ getActionIcon(action.action_type) }}
                  </v-icon>
                </template>
                
                <v-list-item-title class="d-flex align-center">
                  <span class="text-truncate" style="max-width: 300px;">{{ action.target_title }}</span>
                  <v-chip size="x-small" variant="tonal" class="ml-2">
                    {{ action.size_gb.toFixed(1) }} GB
                  </v-chip>
                  <v-chip
                    v-if="action.hr_status === 'active'"
                    size="x-small"
                    color="error"
                    variant="tonal"
                    class="ml-1"
                  >
                    <v-icon size="x-small" start>mdi-seed</v-icon>
                    保种中
                  </v-chip>
                </v-list-item-title>
                
                <v-list-item-subtitle>
                  <span class="text-grey-darken-1">{{ action.reason }}</span>
                </v-list-item-subtitle>

                <!-- 风险提示 -->
                <div v-if="action.risk_notes.length" class="mt-1">
                  <v-chip
                    v-for="(note, nIdx) in action.risk_notes.slice(0, 2)"
                    :key="nIdx"
                    size="x-small"
                    color="warning"
                    variant="tonal"
                    class="mr-1"
                  >
                    {{ note }}
                  </v-chip>
                </div>

                <template #append>
                  <v-chip size="small" :color="getActionColor(action.action_type)" variant="outlined">
                    {{ getActionLabel(action.action_type) }}
                  </v-chip>
                </template>
              </v-list-item>
            </v-list>
          </v-card>
        </template>
      </template>

      <!-- 无操作 -->
      <v-alert v-else type="success" variant="tonal">
        未发现需要清理的内容，您的媒体库很整洁！
      </v-alert>
    </template>

    <!-- 无结果 -->
    <v-alert v-else-if="!loading && hasRunOnce" type="info" variant="tonal">
      暂无清理计划，请点击"生成清理计划"按钮。
    </v-alert>

    <!-- 错误提示 -->
    <v-alert v-if="error" type="error" variant="tonal" closable class="mt-4">
      {{ error }}
    </v-alert>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { 
  aiCleanupAdvisorApi, 
  type CleanupPlanDraft, 
  type PresetCleanupPrompt,
  type CleanupAction,
  type RiskLevel,
  type CleanupActionType 
} from '@/api/aiCleanupAdvisor'
import AiStatusAlert from '@/components/ai/AiStatusAlert.vue'

// 状态
const loading = ref(false)
const error = ref('')
const hasRunOnce = ref(false)

// 表单
const focus = ref<string | null>(null)
const minSizeGb = ref<number | null>(null)
const includeRisky = ref(false)
const prompt = ref('')

// 结果
const draft = ref<CleanupPlanDraft | null>(null)

// 预设
const presetPrompts = ref<PresetCleanupPrompt[]>([])

// 选项
const focusOptions = [
  { value: 'all', label: '全面分析' },
  { value: 'downloads', label: '已完成下载' },
  { value: 'duplicates', label: '重复媒体' },
  { value: 'low_quality', label: '低质量版本' },
  { value: 'seeding', label: '保种相关' },
]

// 按风险级别分组的操作
const groupedActions = computed(() => {
  if (!draft.value?.actions) return []
  
  const groups: Record<RiskLevel, { level: RiskLevel; actions: CleanupAction[]; totalGb: number }> = {
    safe: { level: 'safe', actions: [], totalGb: 0 },
    caution: { level: 'caution', actions: [], totalGb: 0 },
    risky: { level: 'risky', actions: [], totalGb: 0 },
  }
  
  for (const action of draft.value.actions) {
    const level = action.risk_level as RiskLevel
    if (groups[level]) {
      groups[level].actions.push(action)
      groups[level].totalGb += action.size_gb
    }
  }
  
  // 返回非空分组，按 safe -> caution -> risky 排序
  return ['safe', 'caution', 'risky']
    .map(level => groups[level as RiskLevel])
    .filter(g => g.actions.length > 0)
})

// 选择预设
function selectPreset(preset: PresetCleanupPrompt) {
  prompt.value = preset.prompt
  if (preset.focus) {
    focus.value = preset.focus
  }
}

// 生成清理计划
async function generatePlan() {
  loading.value = true
  error.value = ''
  hasRunOnce.value = true
  
  try {
    const result = await aiCleanupAdvisorApi.generate({
      prompt: prompt.value || undefined,
      focus: focus.value || undefined,
      min_size_gb: minSizeGb.value || undefined,
      include_risky: includeRisky.value,
    })
    
    if (result.success && result.draft) {
      draft.value = result.draft
    } else {
      error.value = result.error || '生成清理计划失败'
    }
  } catch (e: any) {
    console.error('生成清理计划失败:', e)
    error.value = e.response?.data?.detail || e.message || '请求失败'
  } finally {
    loading.value = false
  }
}

// 辅助函数
function getRiskColor(level: RiskLevel): string {
  const colors: Record<RiskLevel, string> = {
    safe: 'success',
    caution: 'warning',
    risky: 'error',
  }
  return colors[level] || 'grey'
}

function getRiskLabel(level: RiskLevel): string {
  const labels: Record<RiskLevel, string> = {
    safe: '安全',
    caution: '谨慎',
    risky: '高风险',
  }
  return labels[level] || level
}

function getActionIcon(type: CleanupActionType): string {
  const icons: Record<CleanupActionType, string> = {
    delete: 'mdi-delete',
    archive: 'mdi-archive',
    transcode: 'mdi-movie-filter',
    replace: 'mdi-swap-horizontal',
  }
  return icons[type] || 'mdi-help'
}

function getActionColor(type: CleanupActionType): string {
  const colors: Record<CleanupActionType, string> = {
    delete: 'red',
    archive: 'blue',
    transcode: 'purple',
    replace: 'orange',
  }
  return colors[type] || 'grey'
}

function getActionLabel(type: CleanupActionType): string {
  const labels: Record<CleanupActionType, string> = {
    delete: '删除',
    archive: '归档',
    transcode: '转码',
    replace: '替换',
  }
  return labels[type] || type
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
    const result = await aiCleanupAdvisorApi.getPresetPrompts()
    presetPrompts.value = result.prompts
  } catch (e) {
    console.error('加载预设提示词失败:', e)
  }
})
</script>
