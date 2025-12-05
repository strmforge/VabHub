<!--
批量健康检查对话框 (SITE-MANAGER-1)
支持对多个站点进行批量健康检查
-->

<template>
  <v-dialog
    v-model="dialog"
    :max-width="700"
    persistent
  >
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-heart-pulse</v-icon>
        批量健康检查
      </v-card-title>

      <v-card-text>
        <v-form ref="formRef" v-model="formValid">
          <v-row>
            <v-col cols="12">
              <v-subheader>检查配置</v-subheader>
            </v-col>

            <v-col cols="12" sm="6">
              <v-select
                v-model="checkType"
                :items="checkTypeOptions"
                label="检查类型"
                hint="选择健康检查的类型"
                persistent-hint
              />
            </v-col>

            <v-col cols="12" sm="6">
              <v-text-field
                v-model.number="maxConcurrent"
                label="最大并发数"
                type="number"
                min="1"
                max="5"
                hint="同时检查的站点数量"
                persistent-hint
              />
            </v-col>

            <v-col cols="12">
              <v-switch
                v-model="checkOnlyEnabled"
                label="仅检查启用站点"
                hint="跳过已禁用的站点"
                persistent-hint
              />
            </v-col>

            <v-col cols="12">
              <v-switch
                v-model="stopOnError"
                label="遇到错误时停止"
                hint="第一个站点检查失败时停止批量检查"
                persistent-hint
              />
            </v-col>
          </v-row>
        </v-form>

        <!-- 站点选择 -->
        <v-divider class="my-4" />
        <div class="text-subtitle-1 mb-2">选择站点 ({{ selectedSites.length }}/{{ availableSites.length }})</div>
        
        <v-text-field
          v-model="searchKeyword"
          label="搜索站点"
          prepend-inner-icon="mdi-magnify"
          clearable
          class="mb-3"
        />

        <v-card variant="outlined" max-height="300" class="overflow-y-auto">
          <v-list density="compact">
            <v-list-item
              v-for="site in filteredSites"
              :key="site.id"
              :disabled="!site.enabled && checkOnlyEnabled"
            >
              <template #prepend>
                <v-checkbox
                  :model-value="selectedSites.includes(site.id)"
                  :disabled="!site.enabled && checkOnlyEnabled"
                  @update:model-value="toggleSiteSelection(site.id)"
                />
              </template>

              <v-list-item-title class="d-flex align-center">
                <span>{{ site.name }}</span>
                <v-chip
                  v-if="site.priority > 0"
                  :color="getPriorityColor(site.priority)"
                  size="x-small"
                  class="ml-2"
                >
                  P{{ site.priority }}
                </v-chip>
                <v-chip
                  v-if="!site.enabled"
                  size="x-small"
                  color="grey"
                  class="ml-2"
                >
                  已禁用
                </v-chip>
              </v-list-item-title>

              <v-list-item-subtitle>
                {{ site.domain || site.url }}
              </v-list-item-subtitle>

              <template #append>
                <v-chip
                  :color="getHealthColor(site.stats?.health_status)"
                  size="x-small"
                >
                  {{ getHealthText(site.stats?.health_status) }}
                </v-chip>
              </template>
            </v-list-item>
          </v-list>
        </v-card>

        <!-- 检查进度 -->
        <div v-if="isChecking" class="mt-4">
          <v-divider class="mb-4" />
          <div class="text-subtitle-1 mb-2">检查进度</div>
          
          <v-progress-linear
            :model-value="progress"
            height="6"
            striped
            color="primary"
          />
          
          <div class="d-flex justify-space-between mt-2 text-caption">
            <span>已完成: {{ completedCount }} / {{ totalCount }}</span>
            <span>{{ Math.round(progress) }}%</span>
          </div>

          <!-- 实时结果 -->
          <v-list v-if="checkResults.length" density="compact" max-height="200" class="overflow-y-auto mt-3">
            <v-list-item
              v-for="result in checkResults.slice(-10)"
              :key="result.site_id"
            >
              <v-list-item-title class="d-flex align-center">
                <span>{{ getSiteName(result.site_id) }}</span>
                <v-chip
                  :color="getHealthColor(result.status)"
                  size="x-small"
                  class="ml-2"
                >
                  {{ getHealthText(result.status) }}
                </v-chip>
              </v-list-item-title>
              <v-list-item-subtitle v-if="result.error_message" class="text-error">
                {{ result.error_message }}
              </v-list-item-subtitle>
              <v-list-item-subtitle v-else-if="result.response_time_ms">
                响应时间: {{ result.response_time_ms }}ms
              </v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </div>

        <!-- 检查结果摘要 -->
        <div v-if="checkResult" class="mt-4">
          <v-divider class="mb-4" />
          <v-alert
            :type="checkResult.failed_count > 0 ? 'warning' : 'success'"
            class="mb-4"
          >
            <div class="text-h6 mb-2">检查完成</div>
            <div>总计: {{ checkResult.total }} 个站点</div>
            <div>成功: {{ checkResult.success_count }} 个</div>
            <div>失败: {{ checkResult.failed_count }} 个</div>
          </v-alert>
        </div>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          variant="text"
          @click="onCancel"
        >
          {{ checkResult ? '关闭' : '取消' }}
        </v-btn>
        <v-btn
          v-if="!checkResult"
          color="primary"
          :loading="isChecking"
          :disabled="selectedSites.length === 0"
          @click="onStartCheck"
        >
          开始检查
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useSiteManagerStore } from '@/stores/siteManager'
import type { SiteBrief, BatchHealthCheckResult, SiteHealthResult, HealthStatus } from '@/types/siteManager'
import { CheckType } from '@/types/siteManager'

interface Props {
  modelValue: boolean
  sites: SiteBrief[]
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'checked', result: BatchHealthCheckResult): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const siteManagerStore = useSiteManagerStore()

// 响应式状态
const dialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const formValid = ref(false)
const isChecking = ref(false)

// 检查配置
const checkType = ref<CheckType>(CheckType.BASIC)
const maxConcurrent = ref(3)
const checkOnlyEnabled = ref(true)
const stopOnError = ref(false)

// 站点选择
const selectedSites = ref<number[]>([])
const searchKeyword = ref('')

// 检查状态
const checkResult = ref<BatchHealthCheckResult | null>(null)
const checkResults = ref<SiteHealthResult[]>([])
const completedCount = ref(0)
const totalCount = ref(0)

// 计算属性
const availableSites = computed(() => {
  return props.sites.filter(site => 
    checkOnlyEnabled.value ? site.enabled : true
  )
})

const filteredSites = computed(() => {
  if (!searchKeyword.value) return availableSites.value
  
  const keyword = searchKeyword.value.toLowerCase()
  return availableSites.value.filter(site =>
    site.name.toLowerCase().includes(keyword) ||
    site.domain?.toLowerCase().includes(keyword) ||
    site.key?.toLowerCase().includes(keyword)
  )
})

const progress = computed(() => {
  if (totalCount.value === 0) return 0
  return (completedCount.value / totalCount.value) * 100
})

const checkTypeOptions = [
  { title: '基础检查', value: CheckType.BASIC },
  { title: 'RSS检查', value: CheckType.RSS },
  { title: 'API检查', value: CheckType.API }
]

// 方法
const getSiteName = (siteId: number): string => {
  const site = props.sites.find(s => s.id === siteId)
  return site?.name || `站点 ${siteId}`
}

const getPriorityColor = (priority: number): string => {
  if (priority >= 5) return 'error'
  if (priority >= 3) return 'warning'
  return 'info'
}

const getHealthColor = (status?: HealthStatus): string => {
  const colorMap: Record<HealthStatus, string> = {
    OK: 'success',
    WARN: 'warning',
    ERROR: 'error',
    UNKNOWN: 'grey'
  }
  return colorMap[status || 'UNKNOWN']
}

const getHealthText = (status?: HealthStatus): string => {
  const textMap: Record<HealthStatus, string> = {
    OK: '正常',
    WARN: '警告',
    ERROR: '错误',
    UNKNOWN: '未知'
  }
  return textMap[status || 'UNKNOWN']
}

const toggleSiteSelection = (siteId: number) => {
  const index = selectedSites.value.indexOf(siteId)
  if (index === -1) {
    selectedSites.value.push(siteId)
  } else {
    selectedSites.value.splice(index, 1)
  }
}

const selectAllSites = () => {
  selectedSites.value = availableSites.value.map(site => site.id)
}

const clearSelection = () => {
  selectedSites.value = []
}

const onStartCheck = async () => {
  if (selectedSites.value.length === 0) return
  
  isChecking.value = true
  checkResult.value = null
  checkResults.value = []
  completedCount.value = 0
  totalCount.value = selectedSites.value.length
  
  try {
    const result = await siteManagerStore.batchHealthCheck(
      selectedSites.value,
      checkType.value
    )
    
    checkResult.value = result
    checkResults.value = result.results
    emit('checked', result)
  } catch (error) {
    console.error('批量健康检查失败:', error)
  } finally {
    isChecking.value = false
  }
}

const onCancel = () => {
  if (isChecking.value) {
    // 检查进行中，不允许关闭
    return
  }
  dialog.value = false
}

// 监听对话框打开
watch(dialog, (isOpen) => {
  if (isOpen) {
    // 默认选择所有可用站点
    selectedSites.value = availableSites.value.map(site => site.id)
    searchKeyword.value = ''
    checkResult.value = null
    checkResults.value = []
  }
})
</script>

<style lang="scss" scoped>
.v-list-item {
  &:hover {
    background-color: rgba(var(--v-theme-surface-variant), 0.1);
  }
}
</style>
