<template>
  <v-container fluid class="pa-4">
    <!-- 顶部说明区 -->
    <v-alert type="info" variant="tonal" class="mb-4" closable>
      <v-alert-title>
        <div class="d-flex align-center">
          AI 实验室 (Beta)
          <v-chip size="x-small" color="primary" variant="flat" class="ml-2">GENERIC</v-chip>
          <v-chip size="x-small" color="success" variant="outlined" class="ml-2">只读建议</v-chip>
        </div>
      </v-alert-title>
      <div class="text-body-2 mt-2">
        <p>当前 AI 总控处于 <strong>只读实验阶段</strong>，不会修改任何配置，只提供建议。</p>
        <p class="mt-1">
          需要配置外部 LLM Endpoint 才能发挥完全能力。
          未配置时将使用 Dummy 模式（仅支持预设场景）。
        </p>
      </div>
    </v-alert>

    <!-- 状态卡片 -->
    <v-row class="mb-4">
      <v-col cols="12" md="4">
        <v-card variant="outlined">
          <v-card-text class="d-flex align-center">
            <v-icon :color="status.enabled ? 'success' : 'grey'" class="mr-3">
              {{ status.enabled ? 'mdi-check-circle' : 'mdi-close-circle' }}
            </v-icon>
            <div>
              <div class="text-caption text-grey">总控状态</div>
              <div class="text-body-1">{{ status.enabled ? '已启用' : '未启用' }}</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="4">
        <v-card variant="outlined">
          <v-card-text class="d-flex align-center">
            <v-icon :color="status.llm_configured ? 'success' : 'warning'" class="mr-3">
              {{ status.llm_configured ? 'mdi-cloud-check' : 'mdi-cloud-off-outline' }}
            </v-icon>
            <div>
              <div class="text-caption text-grey">LLM 配置</div>
              <div class="text-body-1">{{ status.llm_configured ? '已配置' : '使用 Dummy' }}</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="4">
        <v-card variant="outlined">
          <v-card-text class="d-flex align-center">
            <v-icon color="primary" class="mr-3">mdi-tools</v-icon>
            <div>
              <div class="text-caption text-grey">可用工具</div>
              <div class="text-body-1">{{ status.available_tools?.length || 0 }} 个</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 控制区 -->
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-robot</v-icon>
        AI 助手
      </v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="4">
            <v-select
              v-model="selectedMode"
              :items="modeOptions"
              item-title="text"
              item-value="value"
              label="运行模式"
              variant="outlined"
              density="comfortable"
              hide-details
            />
          </v-col>
          <v-col cols="12" md="8">
            <v-switch
              v-model="forceDummy"
              label="使用 Dummy LLM（调试模式）"
              color="warning"
              hide-details
              density="comfortable"
            />
          </v-col>
        </v-row>
        
        <v-textarea
          v-model="prompt"
          label="输入您的请求"
          placeholder="例如：帮我分析一下当前站点和订阅情况"
          variant="outlined"
          rows="3"
          class="mt-4"
          :disabled="loading"
          @keydown.ctrl.enter="executeOrchestrator"
        />

        <div class="d-flex justify-end mt-2">
          <v-btn
            color="primary"
            :loading="loading"
            :disabled="!prompt.trim() || (!status.enabled && !forceDummy)"
            @click="executeOrchestrator"
          >
            <v-icon start>mdi-play</v-icon>
            执行
          </v-btn>
        </div>
      </v-card-text>
    </v-card>

    <!-- 结果展示 -->
    <template v-if="result">
      <!-- 执行计划 -->
      <v-card class="mb-4">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-format-list-checks</v-icon>
          执行计划
        </v-card-title>
        <v-card-text>
          <v-list density="compact" v-if="result.plan?.length">
            <v-list-item
              v-for="(call, index) in result.plan"
              :key="index"
              :prepend-icon="getStatusIcon(call.status)"
            >
              <v-list-item-title>
                {{ call.tool_name }}
              </v-list-item-title>
              <v-list-item-subtitle>
                {{ formatArguments(call.arguments) }}
              </v-list-item-subtitle>
              <template #append>
                <v-chip
                  :color="getStatusColor(call.status)"
                  size="small"
                  variant="tonal"
                >
                  {{ getStatusText(call.status) }}
                </v-chip>
              </template>
            </v-list-item>
          </v-list>
          <div v-else class="text-grey text-body-2">
            无工具调用
          </div>
        </v-card-text>
      </v-card>

      <!-- 工具输出摘要 -->
      <v-card class="mb-4" v-if="Object.keys(result.tool_results || {}).length">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-text-box-outline</v-icon>
          工具输出
        </v-card-title>
        <v-card-text>
          <v-expansion-panels variant="accordion">
            <v-expansion-panel
              v-for="(output, toolName) in result.tool_results"
              :key="toolName"
            >
              <v-expansion-panel-title>
                <v-icon class="mr-2" size="small">mdi-function</v-icon>
                {{ toolName }}
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <div v-if="output.summary_text" class="mb-2">
                  {{ output.summary_text }}
                </div>
                <pre class="text-caption bg-grey-lighten-4 pa-2 rounded overflow-auto" style="max-height: 200px;">{{ JSON.stringify(output, null, 2) }}</pre>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-card-text>
      </v-card>

      <!-- AI 总结 & 建议 -->
      <v-card class="mb-4">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-lightbulb-outline</v-icon>
          AI 总结 & 建议
        </v-card-title>
        <v-card-text>
          <div class="text-body-1 mb-4" style="white-space: pre-wrap;">
            {{ result.llm_summary || '无总结' }}
          </div>

          <template v-if="result.llm_suggested_changes">
            <v-divider class="my-3" />
            <v-alert type="warning" variant="tonal" density="compact" class="mb-2">
              <strong>以下为建议配置（草案），未实际应用</strong>
            </v-alert>
            <pre class="text-caption bg-amber-lighten-5 pa-3 rounded overflow-auto" style="max-height: 300px;">{{ JSON.stringify(result.llm_suggested_changes, null, 2) }}</pre>
          </template>
        </v-card-text>
      </v-card>
    </template>

    <!-- 错误提示 -->
    <v-alert v-if="error" type="error" variant="tonal" closable class="mt-4">
      {{ error }}
    </v-alert>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { aiOrchestratorApi } from '@/api/aiOrchestrator'

// 状态
const status = ref({
  enabled: false,
  llm_configured: false,
  available_tools: [] as string[],
  modes: [] as string[],
})

// 表单
const selectedMode = ref('generic')
const prompt = ref('')
const forceDummy = ref(false)
const loading = ref(false)

// 结果
const result = ref<any>(null)
const error = ref('')

// 模式选项
const modeOptions = [
  { value: 'generic', text: '通用模式 - 基础系统查询' },
  { value: 'subs_advisor', text: '订阅顾问 - 分析站点/订阅配置' },
  { value: 'diagnose', text: '系统诊断 - 排查故障和错误' },
  { value: 'cleanup_advisor', text: '整理顾问 - HR 风险和存储优化' },
]

// 加载状态
async function loadStatus() {
  try {
    const res = await aiOrchestratorApi.getStatus()
    status.value = res
  } catch (e: any) {
    console.error('获取状态失败:', e)
  }
}

// 执行 Orchestrator
async function executeOrchestrator() {
  if (!prompt.value.trim()) return
  
  loading.value = true
  error.value = ''
  result.value = null
  
  try {
    const res = await aiOrchestratorApi.execute({
      mode: selectedMode.value,
      prompt: prompt.value,
      debug: false,
      force_dummy: forceDummy.value,
    })
    
    if (res.success) {
      result.value = res.result
    } else {
      error.value = res.error || '执行失败'
    }
  } catch (e: any) {
    console.error('执行失败:', e)
    if (e.response?.status === 503) {
      error.value = 'AI Orchestrator 未启用，请在配置中设置 AI_ORCH_ENABLED=true'
    } else {
      error.value = e.response?.data?.detail || e.message || '执行失败'
    }
  } finally {
    loading.value = false
  }
}

// 辅助函数
function getStatusIcon(status: string) {
  switch (status) {
    case 'success': return 'mdi-check-circle'
    case 'failed': return 'mdi-close-circle'
    case 'skipped': return 'mdi-skip-next-circle'
    default: return 'mdi-clock-outline'
  }
}

function getStatusColor(status: string) {
  switch (status) {
    case 'success': return 'success'
    case 'failed': return 'error'
    case 'skipped': return 'warning'
    default: return 'grey'
  }
}

function getStatusText(status: string) {
  switch (status) {
    case 'success': return '成功'
    case 'failed': return '失败'
    case 'skipped': return '跳过'
    default: return '等待'
  }
}

function formatArguments(args: Record<string, any>) {
  if (!args || Object.keys(args).length === 0) return '无参数'
  return Object.entries(args)
    .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
    .join(', ')
}

// 初始化
onMounted(() => {
  loadStatus()
})
</script>

<style scoped>
pre {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 12px;
}
</style>
