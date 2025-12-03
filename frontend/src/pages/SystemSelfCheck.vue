<template>
  <div class="page-system-selfcheck">
    <PageHeader
      title="系统自检"
      subtitle="聚合可选依赖、数据库自愈与测试报告，快速判断当前部署是否健康"
    >
      <template #actions>
        <v-btn
          color="primary"
          variant="flat"
          prepend-icon="mdi-refresh"
          :loading="loading"
          @click="fetchData"
        >
          刷新
        </v-btn>
      </template>
    </PageHeader>

    <v-container fluid>
      <v-alert
        v-if="data?.generated_at"
        type="info"
        variant="tonal"
        class="mb-4"
        border="start"
      >
        上次自检时间：{{ formatDateTime(data.generated_at) }}
      </v-alert>

      <v-row class="mb-4" align="stretch">
        <v-col
          v-for="dep in optionalDependencies"
          :key="dep.name"
          cols="12"
          md="4"
        >
          <v-card :class="['h-100', 'dependency-card']" elevation="2">
            <div class="d-flex justify-space-between align-center">
              <div>
                <div class="text-subtitle-1 font-weight-medium">
                  {{ dep.name }}
                </div>
                <div class="text-body-2 text-medium-emphasis">
                  {{ dep.message || dependencyDescription(dep) }}
                </div>
              </div>
              <v-chip :color="statusColor(dep.status)" size="small" variant="flat">
                {{ dependencyLabel(dep) }}
              </v-chip>
            </div>
            <div
              v-if="dep.details"
              class="text-caption text-disabled mt-3"
            >
              {{ formatDetails(dep.details) }}
            </div>
          </v-card>
        </v-col>
      </v-row>

      <v-row>
        <v-col cols="12" lg="6">
          <v-card elevation="2">
            <v-card-title class="d-flex justify-space-between align-center">
              <div>
                <span class="text-subtitle-1 font-weight-medium">数据库与结构自愈</span>
                <span class="text-caption text-medium-emphasis d-block">短剧/音乐/RSSHub 关键列检测</span>
              </div>
              <v-chip
                :color="statusColor(data?.schema_checks?.status)"
                size="small"
                variant="flat"
              >
                {{ statusLabel(data?.schema_checks?.status) }}
              </v-chip>
            </v-card-title>
            <v-divider />
            <v-card-text>
              <div class="text-caption text-medium-emphasis mb-3">
                最近执行：{{ formatDateTime(data?.schema_checks?.checked_at) }}
              </div>
              <v-timeline
                density="compact"
                align="start"
              >
                <v-timeline-item
                  v-for="step in data?.schema_checks?.steps || []"
                  :key="step.id"
                  :color="statusColor(step.status)"
                  size="small"
                >
                  <div class="text-subtitle-2">{{ step.title }}</div>
                  <div class="text-caption text-medium-emphasis">
                    {{ formatDateTime(step.finished_at || step.started_at) }}
                  </div>
                  <div
                    v-if="step.error"
                    class="text-caption text-error mt-1"
                  >
                    {{ step.error }}
                  </div>
                </v-timeline-item>
              </v-timeline>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" lg="6">
          <v-card elevation="2">
            <v-card-title class="d-flex justify-space-between align-center">
              <div>
                <span class="text-subtitle-1 font-weight-medium">test_all 回归报告</span>
                <span class="text-caption text-medium-emphasis d-block">
                  从 <code>{{ data?.test_report?.path || defaultReportPath }}</code> 读取
                </span>
              </div>
              <v-chip
                :color="statusColor(data?.test_report?.status)"
                size="small"
                variant="flat"
              >
                {{ statusLabel(data?.test_report?.status) }}
              </v-chip>
            </v-card-title>
            <v-divider />
            <v-card-text>
              <template v-if="data?.test_report?.status === 'missing'">
                <v-alert type="warning" variant="tonal" border="start">
                  尚未生成报告。请在后端主机执行<br />
                  <code>python backend/scripts/test_all.py --skip-music-execute --report-path {{ defaultReportPath }}</code>
                </v-alert>
              </template>
              <template v-else-if="data?.test_report">
                <div class="text-caption text-medium-emphasis mb-3">
                  报告生成：{{ formatDateTime(data.test_report.generated_at) }} | 最近写入：{{ formatDateTime(data.test_report.updated_at) }}
                </div>
                <v-alert
                  v-if="(data.test_report.warnings?.length || 0) > 0"
                  type="warning"
                  variant="tonal"
                  border="start"
                  class="mb-3"
                >
                  <div class="font-weight-medium mb-1">非致命告警</div>
                  <ul class="text-body-2 pl-4">
                    <li v-for="(warn, index) in data.test_report.warnings" :key="index">
                      {{ warn }}
                    </li>
                  </ul>
                </v-alert>

                <v-table density="comfortable">
                  <thead>
                    <tr>
                      <th>脚本</th>
                      <th class="text-center">耗时</th>
                      <th>警告</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="result in data.test_report.results || []"
                      :key="result.script + result.args.join('-')"
                    >
                      <td>
                        <div class="font-weight-medium">{{ result.script }}</div>
                        <div class="text-caption text-medium-emphasis">
                          {{ result.args?.join(' ') || '默认参数' }}
                        </div>
                      </td>
                      <td class="text-center">
                        {{ result.duration_seconds.toFixed(1) }}s
                      </td>
                      <td>
                        <span v-if="!result.warnings?.length" class="text-disabled">—</span>
                        <ul v-else class="text-caption">
                          <li v-for="(warn, idx) in result.warnings" :key="idx">
                            {{ warn }}
                          </li>
                        </ul>
                      </td>
                    </tr>
                  </tbody>
                </v-table>

                <div
                  v-if="data.test_report.skipped?.length"
                  class="text-caption text-medium-emphasis mt-3"
                >
                  跳过脚本：
                  <span
                    v-for="(skip, idx) in data.test_report.skipped"
                    :key="skip.script + idx"
                  >
                    {{ skip.script }}（{{ skip.reason }}）<span v-if="idx < (data.test_report.skipped?.length || 0) - 1">，</span>
                  </span>
                </div>
              </template>
              <template v-else>
                <v-skeleton-loader type="list-item-two-line" />
              </template>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { systemApi } from '@/services/api'
import { useToast } from '@/composables/useToast'

interface OptionalDependency {
  name: string
  status: string
  enabled: boolean
  message?: string | null
  details?: Record<string, unknown> | null
}

interface SchemaStep {
  id: string
  title: string
  status: string
  started_at?: string
  finished_at?: string
  error?: string
}

interface SchemaChecks {
  status: string
  checked_at?: string
  steps: SchemaStep[]
}

interface TestResult {
  script: string
  args: string[]
  duration_seconds: number
  warnings: string[]
}

interface SkippedItem {
  script: string
  reason: string
}

interface TestReport {
  status: string
  path?: string
  generated_at?: string
  updated_at?: string
  warnings?: string[]
  skipped?: SkippedItem[]
  results?: TestResult[]
}

interface SelfCheckResponse {
  generated_at?: string
  optional_dependencies: OptionalDependency[]
  schema_checks: SchemaChecks
  test_report?: TestReport
}

const { showError } = useToast()
const loading = ref(false)
const data = ref<SelfCheckResponse | null>(null)

const optionalDependencies = computed<OptionalDependency[]>(() => data.value?.optional_dependencies || [])
const defaultReportPath = './reports/test_all-latest.json'

const formatDateTime = (value?: string | null) => {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString()
}

const statusLabel = (status?: string) => {
  if (!status) return '未知'
  const map: Record<string, string> = {
    ok: '正常',
    enabled: '已启用',
    disabled: '已禁用',
    simulation: '模拟模式',
    linked: '已连接',
    missing: '未生成',
    error: '异常',
  }
  return map[status] || status
}

const statusColor = (status?: string) => {
  switch (status) {
    case 'ok':
    case 'enabled':
    case 'linked':
      return 'success'
    case 'simulation':
      return 'warning'
    case 'disabled':
    case 'missing':
      return 'grey'
    case 'error':
      return 'error'
    default:
      return 'primary'
  }
}

const dependencyLabel = (dep: OptionalDependency) => {
  if (dep.status === 'simulation') return '模拟模式'
  if (!dep.enabled) return '已禁用'
  return dep.status === 'enabled' ? '已启用' : statusLabel(dep.status)
}

const dependencyDescription = (dep: OptionalDependency) => {
  if (dep.status === 'simulation') return '当前未连接真实下载器，回归测试将跳过执行模式'
  if (!dep.enabled) return '按配置已关闭，可通过环境变量重新启用'
  return '运行正常'
}

const formatDetails = (details: Record<string, unknown>) => {
  return Object.entries(details)
    .map(([key, value]) => `${key}: ${value}`)
    .join(' · ')
}

const fetchData = async () => {
  loading.value = true
  try {
    const response = await systemApi.getSelfCheck()
    data.value = response.data as SelfCheckResponse
  } catch (err: any) {
    showError(err?.message || '获取系统自检数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped lang="scss">
.page-system-selfcheck {
  .dependency-card {
    padding: 20px;
  }
}
</style>

