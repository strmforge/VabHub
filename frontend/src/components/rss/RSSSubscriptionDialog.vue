<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    max-width="800"
    scrollable
    persistent
  >
    <v-card class="rss-subscription-dialog">
      <v-card-item class="py-3">
        <template #prepend>
          <v-icon icon="mdi-rss" class="me-2" />
        </template>
        <v-card-title class="text-h6">
          {{ editingSubscription ? '编辑RSS订阅' : '创建RSS订阅' }}
        </v-card-title>
        <v-card-subtitle>
          {{ editingSubscription ? '修改RSS订阅配置' : '添加新的RSS订阅源' }}
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

      <v-card-text>
        <v-form ref="formRef" v-model="valid">
          <!-- 基本信息 -->
          <v-row>
            <v-col cols="12">
              <v-text-field
                v-model="form.name"
                label="订阅名称 *"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-text"
                :rules="[v => !!v || '请输入订阅名称']"
                required
              />
            </v-col>
            <v-col cols="12">
              <v-text-field
                v-model="form.url"
                label="RSS URL *"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-link"
                :rules="[
                  v => !!v || '请输入RSS URL',
                  v => /^https?:\/\/.+/.test(v) || '请输入有效的URL'
                ]"
                required
                hint="请输入完整的RSS订阅地址"
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model.number="form.interval"
                label="刷新间隔（分钟） *"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-timer"
                type="number"
                :rules="[
                  v => !!v || '请输入刷新间隔',
                  v => v > 0 || '刷新间隔必须大于0'
                ]"
                required
                hint="建议设置为30分钟或更长"
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-switch
                v-model="form.enabled"
                label="启用订阅"
                color="primary"
                hide-details
              />
            </v-col>
            <v-col cols="12">
              <v-textarea
                v-model="form.description"
                label="描述"
                variant="outlined"
                density="compact"
                rows="2"
                hint="可选：添加订阅描述信息"
              />
            </v-col>
          </v-row>

          <!-- 规则组选择和默认配置 -->
          <v-row class="mt-4">
            <v-col cols="12">
              <v-card variant="outlined" class="pa-3">
                <div class="d-flex align-center justify-space-between mb-3">
                  <div class="text-subtitle-2 d-flex align-center">
                    <v-icon class="mr-2">mdi-filter-variant</v-icon>
                    过滤规则组
                  </div>
                  <v-btn
                    size="small"
                    variant="outlined"
                    prepend-icon="mdi-cog-outline"
                    @click="showRuleCenter = true"
                  >
                    规则中心
                  </v-btn>
                </div>
                
                <v-row class="align-center">
                  <v-col cols="12" md="8">
                    <v-autocomplete
                      v-model="form.filter_group_ids"
                      :items="availableRuleGroups"
                      item-title="name"
                      item-value="id"
                      label="选择过滤规则组"
                      variant="outlined"
                      density="compact"
                      prepend-inner-icon="mdi-filter-variant"
                      hint="选择的规则组将按优先级顺序应用过滤"
                      persistent-hint
                      multiple
                      chips
                      clearable
                      :loading="loadingRuleGroups"
                    />
                  </v-col>
                  <v-col cols="12" md="4">
                    <v-btn
                      variant="outlined"
                      prepend-icon="mdi-download"
                      @click="loadDefaultConfig"
                      :disabled="loadingDefaultConfig"
                      :loading="loadingDefaultConfig"
                      block
                    >
                      加载默认配置
                    </v-btn>
                  </v-col>
                </v-row>
              </v-card>
            </v-col>
          </v-row>

          <!-- 过滤规则 -->
          <v-expansion-panels class="mt-4">
            <v-expansion-panel>
              <v-expansion-panel-title>
                <v-icon class="me-2">mdi-filter</v-icon>
                过滤规则（高级）
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-row>
                  <v-col cols="12">
                    <v-textarea
                      v-model="filterRulesText"
                      label="过滤规则（JSON格式）"
                      variant="outlined"
                      density="compact"
                      rows="6"
                      hint="JSON格式的过滤规则，例如：{&quot;include_keywords&quot;: [&quot;1080p&quot;], &quot;exclude_keywords&quot;: [&quot;sample&quot;]}"
                      @update:model-value="parseFilterRules"
                    />
                  </v-col>
                </v-row>
              </v-expansion-panel-text>
            </v-expansion-panel>

            <!-- 下载规则 -->
            <v-expansion-panel>
              <v-expansion-panel-title>
                <v-icon class="me-2">mdi-download</v-icon>
                下载规则（高级）
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-row>
                  <v-col cols="12">
                    <v-switch
                      v-model="downloadRules.auto_download"
                      label="自动下载"
                      color="primary"
                      hide-details
                      class="mb-3"
                    />
                    <v-textarea
                      v-model="downloadRulesText"
                      label="下载规则（JSON格式）"
                      variant="outlined"
                      density="compact"
                      rows="6"
                      hint="JSON格式的下载规则，例如：{&quot;auto_download&quot;: true, &quot;download_target_path&quot;: &quot;/downloads&quot;}"
                      @update:model-value="parseDownloadRules"
                    />
                  </v-col>
                </v-row>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-form>
      </v-card-text>

      <v-card-actions class="pa-4">
        <v-spacer />
        <v-btn
          variant="text"
          @click="handleClose"
        >
          取消
        </v-btn>
        <v-btn
          color="primary"
          variant="flat"
          :loading="saving"
          :disabled="!valid"
          @click="handleSave"
        >
          保存
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import { useToast } from '@/composables/useToast'
import { filterRuleGroupsApi, subscriptionDefaultsApi } from '@/api/index'

const { showError } = useToast()

// Dialog 组件接收的订阅类型（可以是部分字段）
interface RSSSubscriptionInput {
  id?: number
  user_id?: number  // 用户ID（可选，新建时不需要）
  name: string
  url: string
  site_id?: number
  enabled: boolean
  interval: number
  filter_rules?: any
  download_rules?: any
  filter_group_ids?: number[]  // 过滤规则组ID列表（可选）
  description?: string
}

// 保存时发出的完整类型
interface RSSSubscription extends RSSSubscriptionInput {
  user_id: number
  filter_group_ids: number[]
}

interface Props {
  modelValue: boolean
  subscription?: RSSSubscriptionInput | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  saved: [subscription: RSSSubscription]
}>()

const formRef = ref()
const valid = ref(false)
const saving = ref(false)

// 规则组相关数据
const availableRuleGroups = ref<any[]>([])
const loadingRuleGroups = ref(false)
const loadingDefaultConfig = ref(false)
const showRuleCenter = ref(false)

const editingSubscription = computed(() => !!props.subscription)

const form = ref<RSSSubscription>({
  user_id: 1,  // 默认admin用户
  name: '',
  url: '',
  enabled: true,
  interval: 30,
  description: '',
  filter_rules: {},
  download_rules: { auto_download: false },
  filter_group_ids: []  // 默认空数组
})

const downloadRules = ref({
  auto_download: false
})

const filterRulesText = ref('')
const downloadRulesText = ref('')

// 监听props变化，初始化表单
watch(() => props.subscription, (newVal) => {
  if (newVal) {
    form.value = { user_id: 1, filter_group_ids: [], ...newVal }
    downloadRules.value = {
      auto_download: newVal.download_rules?.auto_download || false
    }
    filterRulesText.value = newVal.filter_rules 
      ? JSON.stringify(newVal.filter_rules, null, 2)
      : ''
    downloadRulesText.value = newVal.download_rules
      ? JSON.stringify(newVal.download_rules, null, 2)
      : JSON.stringify({ auto_download: false }, null, 2)
  } else {
    resetForm()
  }
}, { immediate: true })

// 监听dialog打开，重置表单
watch(() => props.modelValue, (newVal) => {
  if (!newVal) {
    resetForm()
  } else if (props.subscription) {
    form.value = { user_id: 1, filter_group_ids: [], ...props.subscription }
    downloadRules.value = {
      auto_download: props.subscription.download_rules?.auto_download || false
    }
    filterRulesText.value = props.subscription.filter_rules
      ? JSON.stringify(props.subscription.filter_rules, null, 2)
      : ''
    downloadRulesText.value = props.subscription.download_rules
      ? JSON.stringify(props.subscription.download_rules, null, 2)
      : JSON.stringify({ auto_download: false }, null, 2)
  }
})

const resetForm = () => {
  form.value = {
    user_id: 1,  // 默认admin用户
    name: '',
    url: '',
    enabled: true,
    interval: 30,
    description: '',
    filter_rules: {},
    download_rules: { auto_download: false },
    filter_group_ids: []  // 默认空数组
  }
  downloadRules.value = { auto_download: false }
  filterRulesText.value = ''
  downloadRulesText.value = JSON.stringify({ auto_download: false }, null, 2)
  formRef.value?.resetValidation()
}

const parseFilterRules = () => {
  try {
    if (filterRulesText.value.trim()) {
      form.value.filter_rules = JSON.parse(filterRulesText.value)
    } else {
      form.value.filter_rules = {}
    }
  } catch (e) {
    // 解析错误时保持原值
    console.error('过滤规则JSON解析失败:', e)
  }
}

const parseDownloadRules = () => {
  try {
    if (downloadRulesText.value.trim()) {
      const rules = JSON.parse(downloadRulesText.value)
      form.value.download_rules = rules
      downloadRules.value.auto_download = rules.auto_download || false
    } else {
      form.value.download_rules = { auto_download: false }
      downloadRules.value.auto_download = false
    }
  } catch (e) {
    // 解析错误时保持原值
    console.error('下载规则JSON解析失败:', e)
  }
}

const handleClose = () => {
  emit('update:modelValue', false)
}

const handleSave = async () => {
  const { valid: isValid } = await formRef.value.validate()
  if (!isValid) {
    showError('请填写所有必填项')
    return
  }

  saving.value = true
  try {
    // 解析规则
    parseFilterRules()
    parseDownloadRules()

    // 确保download_rules包含auto_download
    if (!form.value.download_rules) {
      form.value.download_rules = {}
    }
    form.value.download_rules.auto_download = downloadRules.value.auto_download

    emit('saved', { ...form.value })
    handleClose()
  } catch (error) {
    console.error('保存RSS订阅失败:', error)
    showError('保存失败')
  } finally {
    saving.value = false
  }
}

// 加载规则组列表
const loadRuleGroups = async () => {
  loadingRuleGroups.value = true
  try {
    const response = await filterRuleGroupsApi.getFilterRuleGroups({
      enabled: true,
      size: 100 // 获取所有启用的规则组
    })
    availableRuleGroups.value = response.data.items
  } catch (error) {
    console.error('加载规则组失败:', error)
  } finally {
    loadingRuleGroups.value = false
  }
}

// 加载默认配置
const loadDefaultConfig = async () => {
  loadingDefaultConfig.value = true
  try {
    const response = await subscriptionDefaultsApi.getDefaultConfig('movie') // RSS默认使用电影配置
    const defaultConfig = response.data
    
    // 应用默认配置到表单
    form.value.filter_group_ids = defaultConfig.filter_group_ids
    
    // 更新下载规则
    downloadRules.value.auto_download = defaultConfig.auto_download
    form.value.download_rules = {
      auto_download: defaultConfig.auto_download
    }
    downloadRulesText.value = JSON.stringify(form.value.download_rules, null, 2)
    
    // 使用showError代替showToast，因为useToast只返回showError
    console.log('默认配置加载成功')
  } catch (error) {
    console.error('加载默认配置失败:', error)
    showError('加载默认配置失败，请检查规则中心设置')
  } finally {
    loadingDefaultConfig.value = false
  }
}

// 初始化
onMounted(() => {
  loadRuleGroups()
})
</script>

<style scoped>
.rss-subscription-dialog {
  max-height: 90vh;
}
</style>

