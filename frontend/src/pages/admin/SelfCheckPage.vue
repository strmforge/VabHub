<template>
  <v-container fluid class="pa-4">
    <v-row>
      <v-col cols="12">
        <div class="d-flex align-center mb-4">
          <v-icon size="32" class="mr-3" color="primary">mdi-stethoscope</v-icon>
          <div>
            <h1 class="text-h4">系统自检</h1>
            <p class="text-body-2 text-medium-emphasis mb-0">
              一键检查 VabHub 核心功能链路是否正常
            </p>
          </div>
          <v-spacer />
          <v-btn
            color="primary"
            size="large"
            :loading="running"
            @click="runSelfCheck"
          >
            <v-icon class="mr-2">mdi-play</v-icon>
            立即自检
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- 结果概览 -->
    <v-row v-if="result">
      <v-col cols="12">
        <v-card :color="getOverallCardColor()">
          <v-card-text class="d-flex align-center">
            <v-icon :color="getStatusColor(result.overall_status)" size="48" class="mr-4">
              {{ getStatusIcon(result.overall_status) }}
            </v-icon>
            <div>
              <div class="text-h5 font-weight-bold">
                整体状态: {{ getStatusLabel(result.overall_status).toUpperCase() }}
              </div>
              <div class="text-body-2 mt-1">
                耗时: {{ getDuration() }}ms |
                通过: {{ getSummary().pass }} |
                警告: {{ getSummary().warn }} |
                失败: {{ getSummary().fail }} |
                跳过: {{ getSummary().skipped }}
              </div>
            </div>
            <v-spacer />
            <v-btn
              variant="text"
              @click="showJson = !showJson"
            >
              <v-icon class="mr-1">mdi-code-json</v-icon>
              {{ showJson ? '隐藏 JSON' : '查看 JSON' }}
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- JSON 预览 -->
    <v-row v-if="showJson && result">
      <v-col cols="12">
        <v-card>
          <v-card-title>原始 JSON</v-card-title>
          <v-card-text>
            <pre class="json-preview">{{ JSON.stringify(result, null, 2) }}</pre>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 各组结果 -->
    <v-row v-if="result">
      <v-col
        v-for="group in result.groups"
        :key="group.code"
        cols="12"
        md="6"
      >
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon :color="getStatusColor(group.status)" class="mr-2">
              {{ getGroupIcon(group.code) }}
            </v-icon>
            {{ group.name }}
            <v-spacer />
            <v-chip
              :color="getStatusColor(group.status)"
              size="small"
              variant="flat"
            >
              {{ getStatusLabel(group.status) }}
              ({{ getPassCount(group) }}/{{ group.items.length }})
            </v-chip>
          </v-card-title>
          
          <v-divider />
          
          <v-card-text class="pa-0">
            <v-list density="compact">
              <v-list-item
                v-for="item in group.items"
                :key="item.code"
                :class="getItemClass(item.status)"
              >
                <template v-slot:prepend>
                  <v-icon :color="getStatusColor(item.status)" size="small">
                    {{ getStatusIcon(item.status) }}
                  </v-icon>
                </template>
                
                <v-list-item-title class="text-body-2">
                  {{ item.name }}
                  <span v-if="item.duration_ms" class="text-caption text-medium-emphasis ml-2">
                    ({{ item.duration_ms }}ms)
                  </span>
                </v-list-item-title>
                
                <v-list-item-subtitle v-if="item.message && item.status !== 'pass'" class="text-caption">
                  {{ item.message }}
                </v-list-item-subtitle>
                
                <template v-slot:append>
                  <v-tooltip v-if="item.details" location="left">
                    <template #activator="{ props }">
                      <v-icon v-bind="props" size="small" color="grey">mdi-information</v-icon>
                    </template>
                    <pre class="text-caption">{{ JSON.stringify(item.details, null, 2) }}</pre>
                  </v-tooltip>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 空状态 -->
    <v-row v-if="!result && !running">
      <v-col cols="12">
        <v-card class="pa-8 text-center">
          <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-clipboard-check-outline</v-icon>
          <div class="text-h6 text-medium-emphasis mb-2">点击「立即自检」开始检查</div>
          <div class="text-body-2 text-medium-emphasis">
            自检将检查数据库、Redis、下载器、各内容中心、通知渠道、Bot 和 Runner 状态
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- 加载状态 -->
    <v-row v-if="running">
      <v-col cols="12">
        <v-card class="pa-8 text-center">
          <v-progress-circular indeterminate color="primary" size="64" class="mb-4" />
          <div class="text-h6 mb-2">正在运行自检...</div>
          <div class="text-body-2 text-medium-emphasis">
            这可能需要几秒钟，请稍候
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- 使用说明 -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-expansion-panels variant="accordion">
          <v-expansion-panel title="使用说明">
            <v-expansion-panel-text>
              <div class="text-body-2">
                <p class="mb-2"><strong>什么是自检？</strong></p>
                <p class="mb-3">
                  自检是一个功能级检查工具，用于验证 VabHub 各核心功能链路是否正常工作。
                  它与 OPS 健康检查不同：OPS 健康检查侧重于基础设施（数据库、磁盘等），
                  而自检侧重于业务功能（API 可用性、Runner 运行状态等）。
                </p>
                
                <p class="mb-2"><strong>检查范围</strong></p>
                <ul class="mb-3">
                  <li><strong>核心检查</strong>：数据库迁移、查询、Redis、下载器、磁盘可写性</li>
                  <li><strong>小说/TTS</strong>：小说中心、TTS 存储、阅读中心聚合</li>
                  <li><strong>漫画</strong>：本地系列、追更列表、追更 Runner</li>
                  <li><strong>音乐</strong>：音乐库、榜单源、订阅 Runner</li>
                  <li><strong>通知</strong>：通知写入、用户渠道、告警渠道</li>
                  <li><strong>Bot</strong>：Telegram 配置和连通性</li>
                  <li><strong>Runner</strong>：各 Runner 的心跳状态</li>
                </ul>
                
                <p class="mb-2"><strong>结果解读</strong></p>
                <ul class="mb-3">
                  <li><v-icon size="small" color="success">mdi-check-circle</v-icon> <strong>PASS</strong>：检查通过，功能正常</li>
                  <li><v-icon size="small" color="warning">mdi-alert</v-icon> <strong>WARN</strong>：需要关注，但不阻止运行</li>
                  <li><v-icon size="small" color="error">mdi-close-circle</v-icon> <strong>FAIL</strong>：关键功能异常，建议修复</li>
                  <li><v-icon size="small" color="grey">mdi-minus-circle</v-icon> <strong>SKIPPED</strong>：已跳过（功能未启用或未配置）</li>
                </ul>
                
                <p class="mb-2"><strong>CLI 使用</strong></p>
                <pre class="pa-2 bg-grey-lighten-4 rounded">python -m app.runners.qa_self_check
python -m app.runners.qa_self_check --json
python -m app.runners.qa_self_check --fail-on-warn</pre>
              </div>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { selfCheckApi } from '@/services/api'
import { useToast } from 'vue-toastification'
import type {
  SelfCheckRunResult,
  SelfCheckStatus,
  SelfCheckGroupResult,
} from '@/types/selfCheck'
import {
  getStatusColor,
  getStatusIcon,
  getStatusLabel,
  getGroupIcon,
} from '@/types/selfCheck'

const toast = useToast()

const running = ref(false)
const result = ref<SelfCheckRunResult | null>(null)
const showJson = ref(false)

// 运行自检
const runSelfCheck = async () => {
  running.value = true
  result.value = null
  showJson.value = false
  
  try {
    result.value = await selfCheckApi.run()
    
    if (result.value.overall_status === 'pass') {
      toast.success('自检完成：所有检查通过')
    } else if (result.value.overall_status === 'warn') {
      toast.warning('自检完成：存在警告项')
    } else if (result.value.overall_status === 'fail') {
      toast.error('自检完成：存在失败项')
    }
  } catch (error: any) {
    console.error('自检失败:', error)
    toast.error(error.response?.data?.detail || '自检运行失败')
  } finally {
    running.value = false
  }
}

// 获取总体卡片颜色
const getOverallCardColor = () => {
  if (!result.value) return undefined
  const colors: Record<SelfCheckStatus, string> = {
    pass: 'green-lighten-5',
    warn: 'amber-lighten-5',
    fail: 'red-lighten-5',
    skipped: 'grey-lighten-4',
  }
  return colors[result.value.overall_status]
}

// 获取耗时
const getDuration = () => {
  if (!result.value) return 0
  const start = new Date(result.value.started_at).getTime()
  const end = new Date(result.value.finished_at).getTime()
  return end - start
}

// 获取统计
const getSummary = () => {
  if (!result.value) return { pass: 0, warn: 0, fail: 0, skipped: 0 }
  
  const counts = { pass: 0, warn: 0, fail: 0, skipped: 0 }
  for (const group of result.value.groups) {
    for (const item of group.items) {
      counts[item.status]++
    }
  }
  return counts
}

// 获取组内通过数
const getPassCount = (group: SelfCheckGroupResult) => {
  return group.items.filter(i => i.status === 'pass').length
}

// 获取项目样式类
const getItemClass = (status: SelfCheckStatus) => {
  if (status === 'fail') return 'item-fail'
  if (status === 'warn') return 'item-warn'
  return ''
}
</script>

<style scoped>
.json-preview {
  background: #263238;
  color: #80cbc4;
  padding: 16px;
  border-radius: 8px;
  font-size: 12px;
  overflow-x: auto;
  max-height: 400px;
}

.item-fail {
  background-color: rgba(var(--v-theme-error), 0.05);
  border-left: 3px solid rgb(var(--v-theme-error));
}

.item-warn {
  background-color: rgba(var(--v-theme-warning), 0.05);
  border-left: 3px solid rgb(var(--v-theme-warning));
}
</style>
