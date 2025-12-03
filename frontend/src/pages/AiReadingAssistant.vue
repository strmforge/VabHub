<template>
  <v-container fluid class="pa-4">
    <!-- 顶部说明 -->
    <v-alert type="info" variant="tonal" class="mb-4" closable>
      <v-alert-title>
        <div class="d-flex align-center">
          AI 阅读助手 (Beta)
          <v-chip size="x-small" color="primary" variant="flat" class="ml-2">READING_ASSISTANT</v-chip>
          <v-chip size="x-small" color="success" variant="outlined" class="ml-2">只读建议</v-chip>
        </div>
      </v-alert-title>
      <div class="text-body-2 mt-2">
        <p>AI 驱动的阅读规划助手，帮助您制定阅读计划和发现值得阅读的内容。</p>
        <p class="mt-1">所有输出仅为<strong>规划建议</strong>，不会修改任何阅读进度。</p>
      </div>
    </v-alert>

    <!-- AI 状态提示 -->
    <AiStatusAlert />

    <!-- 计划控制区 -->
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-book-open-page-variant</v-icon>
        生成阅读计划
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
          <v-col cols="12" md="3">
            <v-select
              v-model="goalType"
              :items="goalOptions"
              item-title="label"
              item-value="value"
              label="目标周期"
              variant="outlined"
              density="comfortable"
              hide-details
              clearable
            />
          </v-col>
          <v-col cols="12" md="6">
            <v-text-field
              v-model="prompt"
              label="需求描述（可选）"
              placeholder="例如：帮我规划本周阅读计划..."
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
            生成阅读计划
          </v-btn>
        </div>
      </v-card-text>
    </v-card>

    <!-- 阅读计划结果 -->
    <template v-if="plan">
      <!-- 总览卡片 -->
      <v-card class="mb-4" color="primary" variant="tonal">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-clipboard-text</v-icon>
          阅读计划草案
        </v-card-title>
        <v-card-text>
          <div class="text-body-1">{{ plan.summary }}</div>
          <div class="d-flex align-center mt-3 flex-wrap">
            <v-chip
              v-if="plan.stats_context.ongoing_count"
              color="info"
              variant="flat"
              class="mr-2 mb-2"
            >
              <v-icon start size="small">mdi-book-open</v-icon>
              正在阅读 {{ plan.stats_context.ongoing_count }} 本
            </v-chip>
            <v-chip
              v-if="plan.stats_context.finished_count"
              color="success"
              variant="flat"
              class="mr-2 mb-2"
            >
              <v-icon start size="small">mdi-check-circle</v-icon>
              已完成 {{ plan.stats_context.finished_count }} 本
            </v-chip>
            <v-chip
              v-if="plan.stats_context.unread_count"
              variant="outlined"
              class="mr-2 mb-2"
            >
              待阅读 {{ plan.stats_context.unread_count }} 本
            </v-chip>
            <span class="text-caption text-grey ml-auto" v-if="plan.generated_at">
              生成于 {{ formatTime(plan.generated_at) }}
            </span>
          </div>
        </v-card-text>
      </v-card>

      <!-- 阅读目标 -->
      <template v-if="plan.goals.length">
        <div class="text-h6 mb-3">
          <v-icon class="mr-2">mdi-target</v-icon>
          阅读目标
        </div>
        <v-row class="mb-4">
          <v-col
            v-for="(goal, idx) in plan.goals"
            :key="idx"
            cols="12"
            md="4"
          >
            <v-card variant="outlined">
              <v-card-text>
                <div class="d-flex align-center mb-2">
                  <v-chip size="small" :color="getGoalColor(goal.goal_type)">
                    {{ getGoalLabel(goal.goal_type) }}
                  </v-chip>
                  <span class="ml-2 text-body-2">{{ goal.description }}</span>
                </div>
                <v-progress-linear
                  :model-value="goal.target_count > 0 ? (goal.current_count / goal.target_count) * 100 : 0"
                  :color="getGoalColor(goal.goal_type)"
                  height="8"
                  rounded
                  class="mb-2"
                />
                <div class="d-flex justify-space-between text-caption">
                  <span>{{ goal.current_count }} / {{ goal.target_count }} 本</span>
                  <span v-if="goal.deadline">截止：{{ goal.deadline }}</span>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </template>

      <!-- 阅读建议 -->
      <template v-if="plan.suggestions.length">
        <div class="text-h6 mb-3">
          <v-icon class="mr-2">mdi-lightbulb</v-icon>
          阅读建议（{{ plan.suggestions.length }} 项）
        </div>
        
        <v-card variant="outlined" class="mb-4">
          <v-list density="compact">
            <v-list-item
              v-for="(suggestion, idx) in plan.suggestions"
              :key="idx"
            >
              <template #prepend>
                <v-icon :color="getSuggestionColor(suggestion.suggestion_type)" size="small">
                  {{ getSuggestionIcon(suggestion.suggestion_type) }}
                </v-icon>
              </template>
              
              <v-list-item-title class="d-flex align-center flex-wrap">
                <span class="text-truncate" style="max-width: 250px;">{{ suggestion.title }}</span>
                <v-chip
                  size="x-small"
                  :color="getPriorityColor(suggestion.priority)"
                  variant="tonal"
                  class="ml-2"
                >
                  {{ getPriorityLabel(suggestion.priority) }}
                </v-chip>
                <v-chip
                  size="x-small"
                  variant="outlined"
                  class="ml-1"
                >
                  {{ getMediaTypeLabel(suggestion.media_type) }}
                </v-chip>
                <v-chip
                  v-if="suggestion.current_progress"
                  size="x-small"
                  color="info"
                  variant="tonal"
                  class="ml-1"
                >
                  {{ suggestion.current_progress }}
                </v-chip>
              </v-list-item-title>
              
              <v-list-item-subtitle>
                <span v-if="suggestion.author" class="text-grey-darken-1 mr-2">{{ suggestion.author }}</span>
                <span class="text-grey">{{ suggestion.reason }}</span>
              </v-list-item-subtitle>

              <template #append>
                <div class="d-flex align-center">
                  <span v-if="suggestion.estimated_time" class="text-caption text-grey mr-2">
                    {{ suggestion.estimated_time }}
                  </span>
                  <v-chip
                    size="small"
                    :color="getSuggestionColor(suggestion.suggestion_type)"
                    variant="outlined"
                  >
                    {{ getSuggestionLabel(suggestion.suggestion_type) }}
                  </v-chip>
                </div>
              </template>
            </v-list-item>
          </v-list>
        </v-card>
      </template>

      <!-- 阅读洞察 -->
      <template v-if="plan.insights.length">
        <div class="text-h6 mb-3">
          <v-icon class="mr-2">mdi-chart-line</v-icon>
          阅读洞察
        </div>
        <v-card variant="outlined" class="mb-4">
          <v-card-text>
            <ul class="pl-4">
              <li v-for="(insight, idx) in plan.insights" :key="idx" class="mb-1">
                {{ insight }}
              </li>
            </ul>
          </v-card-text>
        </v-card>
      </template>
    </template>

    <!-- 无结果 -->
    <v-alert v-else-if="!loading && hasRunOnce" type="info" variant="tonal">
      暂无阅读计划，请点击"生成阅读计划"按钮。
    </v-alert>

    <!-- 错误提示 -->
    <v-alert v-if="error" type="error" variant="tonal" closable class="mt-4">
      {{ error }}
    </v-alert>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { 
  aiReadingAssistantApi, 
  type ReadingPlanDraft, 
  type PresetReadingPrompt,
  type ReadingGoalType,
  type SuggestionType,
  type SuggestionPriority,
} from '@/api/aiReadingAssistant'
import AiStatusAlert from '@/components/ai/AiStatusAlert.vue'

// 状态
const loading = ref(false)
const error = ref('')
const hasRunOnce = ref(false)

// 表单
const focus = ref<string | null>(null)
const goalType = ref<string | null>(null)
const prompt = ref('')

// 结果
const plan = ref<ReadingPlanDraft | null>(null)

// 预设
const presetPrompts = ref<PresetReadingPrompt[]>([])

// 选项
const focusOptions = [
  { value: 'all', label: '全面分析' },
  { value: 'novel', label: '小说' },
  { value: 'manga', label: '漫画' },
  { value: 'audiobook', label: '有声书' },
]

const goalOptions = [
  { value: 'daily', label: '每日目标' },
  { value: 'weekly', label: '每周目标' },
  { value: 'monthly', label: '每月目标' },
]

// 选择预设
function selectPreset(preset: PresetReadingPrompt) {
  prompt.value = preset.prompt
  if (preset.focus) {
    focus.value = preset.focus
  }
}

// 生成阅读计划
async function generatePlan() {
  loading.value = true
  error.value = ''
  hasRunOnce.value = true
  
  try {
    const result = await aiReadingAssistantApi.generate({
      prompt: prompt.value || undefined,
      focus: focus.value || undefined,
      goal_type: goalType.value || undefined,
    })
    
    if (result.success && result.plan) {
      plan.value = result.plan
    } else {
      error.value = result.error || '生成阅读计划失败'
    }
  } catch (e: any) {
    console.error('生成阅读计划失败:', e)
    error.value = e.response?.data?.detail || e.message || '请求失败'
  } finally {
    loading.value = false
  }
}

// 辅助函数
function getGoalColor(type: ReadingGoalType): string {
  const colors: Record<ReadingGoalType, string> = {
    daily: 'orange',
    weekly: 'blue',
    monthly: 'purple',
    yearly: 'green',
  }
  return colors[type] || 'grey'
}

function getGoalLabel(type: ReadingGoalType): string {
  const labels: Record<ReadingGoalType, string> = {
    daily: '每日',
    weekly: '每周',
    monthly: '每月',
    yearly: '年度',
  }
  return labels[type] || type
}

function getSuggestionIcon(type: SuggestionType): string {
  const icons: Record<SuggestionType, string> = {
    continue: 'mdi-play-circle',
    start: 'mdi-plus-circle',
    finish: 'mdi-check-circle',
    pause: 'mdi-pause-circle',
  }
  return icons[type] || 'mdi-help'
}

function getSuggestionColor(type: SuggestionType): string {
  const colors: Record<SuggestionType, string> = {
    continue: 'blue',
    start: 'green',
    finish: 'orange',
    pause: 'grey',
  }
  return colors[type] || 'grey'
}

function getSuggestionLabel(type: SuggestionType): string {
  const labels: Record<SuggestionType, string> = {
    continue: '继续阅读',
    start: '开始新书',
    finish: '完成',
    pause: '暂停',
  }
  return labels[type] || type
}

function getPriorityColor(priority: SuggestionPriority): string {
  const colors: Record<SuggestionPriority, string> = {
    high: 'red',
    medium: 'orange',
    low: 'grey',
  }
  return colors[priority] || 'grey'
}

function getPriorityLabel(priority: SuggestionPriority): string {
  const labels: Record<SuggestionPriority, string> = {
    high: '高优先',
    medium: '中优先',
    low: '低优先',
  }
  return labels[priority] || priority
}

function getMediaTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    novel: '小说',
    manga: '漫画',
    audiobook: '有声书',
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
    const result = await aiReadingAssistantApi.getPresetPrompts()
    presetPrompts.value = result.prompts
  } catch (e) {
    console.error('加载预设提示词失败:', e)
  }
})
</script>
