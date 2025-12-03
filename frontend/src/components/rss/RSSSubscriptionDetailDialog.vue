<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    max-width="1200"
    scrollable
    :fullscreen="$vuetify.display.smAndDown"
  >
    <v-card class="rss-subscription-detail-dialog">
      <v-card-item class="py-3">
        <template #prepend>
          <v-icon icon="mdi-rss" class="me-2" />
        </template>
        <v-card-title class="text-h6">
          {{ subscription?.name || 'RSS订阅详情' }}
        </v-card-title>
        <v-card-subtitle v-if="subscription">
          {{ subscription.url }}
        </v-card-subtitle>
        <template #append>
          <v-btn
            icon="mdi-close"
            variant="text"
            size="small"
            @click="handleClose"
          />
        </template>
      </v-card-item>

      <v-divider />

      <v-card-text class="pa-4">
        <v-tabs v-model="activeTab" color="primary">
          <v-tab value="info">
            <v-icon class="me-2">mdi-information</v-icon>
            订阅信息
          </v-tab>
          <v-tab value="items">
            <v-icon class="me-2">mdi-list</v-icon>
            RSS项
            <v-chip
              v-if="subscription"
              size="x-small"
              color="primary"
              class="ms-2"
            >
              {{ subscription.total_items || 0 }}
            </v-chip>
          </v-tab>
          <v-tab value="rules">
            <v-icon class="me-2">mdi-cog</v-icon>
            规则配置
          </v-tab>
        </v-tabs>

        <v-window v-model="activeTab" class="mt-4">
          <!-- 订阅信息 -->
          <v-window-item value="info">
            <v-card variant="outlined">
              <v-card-text>
                <v-row>
                  <v-col cols="12" md="6">
                    <div class="text-caption text-medium-emphasis mb-1">订阅名称</div>
                    <div class="text-body-1 font-weight-medium mb-4">
                      {{ subscription?.name || '-' }}
                    </div>
                  </v-col>
                  <v-col cols="12" md="6">
                    <div class="text-caption text-medium-emphasis mb-1">状态</div>
                    <div class="mb-4">
                      <v-chip
                        :color="subscription?.enabled ? 'success' : 'grey'"
                        size="small"
                        variant="flat"
                      >
                        {{ subscription?.enabled ? '启用' : '禁用' }}
                      </v-chip>
                    </div>
                  </v-col>
                  <v-col cols="12">
                    <div class="text-caption text-medium-emphasis mb-1">RSS URL</div>
                    <div class="text-body-2 mb-4">
                      <a :href="subscription?.url" target="_blank" class="text-primary">
                        {{ subscription?.url || '-' }}
                      </a>
                    </div>
                  </v-col>
                  <v-col cols="12" md="4">
                    <div class="text-caption text-medium-emphasis mb-1">刷新间隔</div>
                    <div class="text-body-1 mb-4">
                      {{ subscription?.interval || 30 }} 分钟
                    </div>
                  </v-col>
                  <v-col cols="12" md="4">
                    <div class="text-caption text-medium-emphasis mb-1">最后检查</div>
                    <div class="text-body-2 mb-4">
                      {{ formatDate(subscription?.last_check) }}
                    </div>
                  </v-col>
                  <v-col cols="12" md="4">
                    <div class="text-caption text-medium-emphasis mb-1">下次检查</div>
                    <div class="text-body-2 mb-4">
                      {{ formatDate(subscription?.next_check) }}
                    </div>
                  </v-col>
                  <v-col cols="12" md="3">
                    <div class="text-caption text-medium-emphasis mb-1">总项数</div>
                    <div class="text-h6 font-weight-bold">
                      {{ subscription?.total_items || 0 }}
                    </div>
                  </v-col>
                  <v-col cols="12" md="3">
                    <div class="text-caption text-medium-emphasis mb-1">已下载</div>
                    <div class="text-h6 font-weight-bold text-success">
                      {{ subscription?.downloaded_items || 0 }}
                    </div>
                  </v-col>
                  <v-col cols="12" md="3">
                    <div class="text-caption text-medium-emphasis mb-1">已跳过</div>
                    <div class="text-h6 font-weight-bold text-warning">
                      {{ subscription?.skipped_items || 0 }}
                    </div>
                  </v-col>
                  <v-col cols="12" md="3">
                    <div class="text-caption text-medium-emphasis mb-1">错误数</div>
                    <div class="text-h6 font-weight-bold" :class="(subscription?.error_count || 0) > 0 ? 'text-error' : ''">
                      {{ subscription?.error_count || 0 }}
                    </div>
                  </v-col>
                  <v-col cols="12" v-if="subscription?.description">
                    <div class="text-caption text-medium-emphasis mb-1">描述</div>
                    <div class="text-body-2">
                      {{ subscription.description }}
                    </div>
                  </v-col>
                </v-row>

                <!-- 操作按钮 -->
                <v-divider class="my-4" />
                <div class="d-flex gap-2">
                  <v-btn
                    color="primary"
                    prepend-icon="mdi-refresh"
                    :loading="checking"
                    @click="handleCheck"
                  >
                    检查更新
                  </v-btn>
                  <v-btn
                    variant="outlined"
                    prepend-icon="mdi-pencil"
                    @click="handleEdit"
                  >
                    编辑订阅
                  </v-btn>
                </div>
              </v-card-text>
            </v-card>
          </v-window-item>

          <!-- RSS项列表 -->
          <v-window-item value="items">
            <RSSItemList
              v-if="subscription?.id"
              :subscription-id="subscription.id"
              :auto-load="activeTab === 'items'"
            />
          </v-window-item>

          <!-- 规则配置 -->
          <v-window-item value="rules">
            <v-card variant="outlined">
              <v-card-text>
                <v-row>
                  <!-- 过滤规则 -->
                  <v-col cols="12">
                    <div class="text-h6 mb-3">过滤规则</div>
                    <v-textarea
                      :model-value="filterRulesText"
                      label="过滤规则（JSON格式）"
                      variant="outlined"
                      rows="8"
                      readonly
                      hint="这些规则用于过滤RSS项"
                    />
                  </v-col>

                  <!-- 下载规则 -->
                  <v-col cols="12">
                    <div class="text-h6 mb-3">下载规则</div>
                    <v-textarea
                      :model-value="downloadRulesText"
                      label="下载规则（JSON格式）"
                      variant="outlined"
                      rows="8"
                      readonly
                      hint="这些规则用于控制下载行为"
                    />
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
          </v-window-item>
        </v-window>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { rssApi } from '@/services/api'
import { useToast } from '@/composables/useToast'
import RSSItemList from './RSSItemList.vue'

interface RSSSubscription {
  id: number
  name: string
  url: string
  site_id?: number
  enabled: boolean
  interval: number
  last_check?: string
  next_check?: string
  last_item_hash?: string
  filter_rules?: any
  download_rules?: any
  total_items: number
  downloaded_items: number
  skipped_items: number
  error_count: number
  description?: string
  created_at: string
  updated_at: string
}

interface Props {
  modelValue: boolean
  subscription: RSSSubscription | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  edit: [subscription: RSSSubscription]
  checked: []
}>()

const { showSuccess, showError, showInfo } = useToast()

// 对话框显示状态由父组件控制
const activeTab = ref('info')
const checking = ref(false)

const filterRulesText = computed(() => {
  if (!props.subscription?.filter_rules) {
    return '暂无过滤规则'
  }
  try {
    return JSON.stringify(props.subscription.filter_rules, null, 2)
  } catch {
    return '过滤规则格式错误'
  }
})

const downloadRulesText = computed(() => {
  if (!props.subscription?.download_rules) {
    return '暂无下载规则'
  }
  try {
    return JSON.stringify(props.subscription.download_rules, null, 2)
  } catch {
    return '下载规则格式错误'
  }
})

const formatDate = (date?: string) => {
  if (!date) return '从未检查'
  try {
    return new Date(date).toLocaleString('zh-CN')
  } catch {
    return date
  }
}

const handleClose = () => {
  emit('update:modelValue', false)
}

const handleEdit = () => {
  if (props.subscription) {
    emit('edit', props.subscription)
    handleClose()
  }
}

const handleCheck = async () => {
  if (!props.subscription) return

  checking.value = true
  try {
    showInfo('正在检查更新...')
    const response = await rssApi.checkRSSUpdates(props.subscription.id)
    const data = response.data
    
    showSuccess(
      `检查完成：新项 ${data.new_items || 0}，处理 ${data.processed_items || 0}，下载 ${data.downloaded_items || 0}`
    )
    emit('checked')
  } catch (error: any) {
    showError(error.message || '检查更新失败')
    console.error('检查RSS更新失败:', error)
  } finally {
    checking.value = false
  }
}

// 监听dialog打开，重置tab
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    activeTab.value = 'info'
  }
})
</script>

<style scoped>
.rss-subscription-detail-dialog {
  max-height: 90vh;
}
</style>

