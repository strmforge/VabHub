<template>
  <v-dialog
    v-model="modelValue"
    max-width="600"
    scrollable
    persistent
  >
    <v-card>
      <v-card-item class="py-3">
        <template #prepend>
          <v-icon icon="mdi-cog" class="me-2" />
        </template>
        <v-card-title class="text-h6">
          配置动作
        </v-card-title>
        <template #append>
          <v-btn
            icon="mdi-close"
            variant="text"
            size="small"
            @click="modelValue = false"
          />
        </template>
      </v-card-item>

      <v-card-text>
        <v-form ref="formRef">
          <v-select
            v-model="action.type"
            :items="actionTypes"
            label="动作类型 *"
            variant="outlined"
            density="compact"
            :rules="[v => !!v || '请选择动作类型']"
            required
            @update:model-value="handleTypeChange"
          />

          <!-- 发送通知配置 -->
          <div v-if="action.type === 'send_notification'">
            <v-text-field
              v-model="action.config.title"
              label="通知标题"
              variant="outlined"
              density="compact"
              class="mt-4"
            />
            <v-textarea
              v-model="action.config.message"
              label="通知内容"
              variant="outlined"
              density="compact"
              rows="3"
              class="mt-4"
            />
            <v-select
              v-model="action.config.channel"
              :items="notificationChannels"
              label="通知渠道"
              variant="outlined"
              density="compact"
              class="mt-4"
            />
          </div>

          <!-- 创建下载配置 -->
          <div v-if="action.type === 'create_download'">
            <v-text-field
              v-model="action.config.title"
              label="下载标题"
              variant="outlined"
              density="compact"
              class="mt-4"
            />
            <v-text-field
              v-model="action.config.magnet_link"
              label="磁力链接"
              variant="outlined"
              density="compact"
              class="mt-4"
            />
            <v-select
              v-model="action.config.downloader"
              :items="downloaders"
              label="下载器"
              variant="outlined"
              density="compact"
              class="mt-4"
            />
          </div>

          <!-- Webhook配置 -->
          <div v-if="action.type === 'webhook'">
            <v-text-field
              v-model="action.config.url"
              label="URL *"
              variant="outlined"
              density="compact"
              class="mt-4"
              :rules="[v => !!v || '请输入URL']"
            />
            <v-select
              v-model="action.config.method"
              :items="httpMethods"
              label="HTTP方法"
              variant="outlined"
              density="compact"
              class="mt-4"
            />
            <v-textarea
              v-model="actionConfigJson"
              label="请求数据 (JSON)"
              variant="outlined"
              density="compact"
              rows="4"
              class="mt-4"
              hint="输入JSON格式的数据"
              persistent-hint
            />
          </div>

          <!-- 延迟配置 -->
          <div v-if="action.type === 'delay'">
            <v-text-field
              v-model.number="action.config.seconds"
              label="延迟秒数"
              variant="outlined"
              density="compact"
              type="number"
              class="mt-4"
            />
          </div>

          <!-- 条件判断配置 -->
          <div v-if="action.type === 'condition'">
            <v-select
              v-model="action.config.type"
              :items="conditionTypes"
              label="条件类型"
              variant="outlined"
              density="compact"
              class="mt-4"
            />
            <v-text-field
              v-model="action.config.field"
              label="字段名"
              variant="outlined"
              density="compact"
              class="mt-4"
            />
            <v-select
              v-model="action.config.operator"
              :items="operators"
              label="操作符"
              variant="outlined"
              density="compact"
              class="mt-4"
            />
            <v-text-field
              v-model="action.config.value"
              label="值"
              variant="outlined"
              density="compact"
              class="mt-4"
            />
          </div>

          <v-switch
            v-model="action.config.stop_on_failure"
            label="失败时停止"
            color="primary"
            hide-details
            class="mt-4"
          />
        </v-form>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          variant="text"
          @click="modelValue = false"
        >
          取消
        </v-btn>
        <v-btn
          color="primary"
          @click="handleSave"
        >
          保存
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface Props {
  modelValue: boolean
  action?: any
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'save': [action: any]
}>()

const formRef = ref()
const action = ref<any>({
  type: '',
  config: {}
})

const actionConfigJson = ref('')

const modelValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const actionTypes = [
  { title: '发送通知', value: 'send_notification' },
  { title: '创建下载', value: 'create_download' },
  { title: '更新订阅', value: 'update_subscription' },
  { title: '执行命令', value: 'execute_command' },
  { title: 'Webhook', value: 'webhook' },
  { title: '延迟', value: 'delay' },
  { title: '条件判断', value: 'condition' }
]

const notificationChannels = [
  { title: '系统通知', value: 'system' },
  { title: '微信', value: 'wechat' },
  { title: '邮件', value: 'email' },
  { title: 'Telegram', value: 'telegram' }
]

const downloaders = [
  { title: 'qBittorrent', value: 'qBittorrent' },
  { title: 'Transmission', value: 'transmission' }
]

const httpMethods = [
  { title: 'GET', value: 'GET' },
  { title: 'POST', value: 'POST' },
  { title: 'PUT', value: 'PUT' },
  { title: 'DELETE', value: 'DELETE' }
]

const conditionTypes = [
  { title: '比较', value: 'comparison' },
  { title: '表达式', value: 'expression' }
]

const operators = [
  { title: '等于', value: 'eq' },
  { title: '不等于', value: 'ne' },
  { title: '大于', value: 'gt' },
  { title: '小于', value: 'lt' },
  { title: '大于等于', value: 'gte' },
  { title: '小于等于', value: 'lte' }
]

const handleTypeChange = () => {
  // 重置配置
  action.value.config = {
    stop_on_failure: false
  }

  // 根据类型设置默认配置
  if (action.value.type === 'send_notification') {
    action.value.config.channel = 'system'
  } else if (action.value.type === 'create_download') {
    action.value.config.downloader = 'qBittorrent'
  } else if (action.value.type === 'webhook') {
    action.value.config.method = 'POST'
    action.value.config.data = {}
  } else if (action.value.type === 'delay') {
    action.value.config.seconds = 1
  } else if (action.value.type === 'condition') {
    action.value.config.type = 'comparison'
    action.value.config.operator = 'eq'
  }
}

const handleSave = () => {
  // 处理Webhook的JSON数据
  if (action.value.type === 'webhook' && actionConfigJson.value) {
    try {
      action.value.config.data = JSON.parse(actionConfigJson.value)
    } catch (e) {
      alert('JSON格式错误')
      return
    }
  }

  emit('save', { ...action.value })
  modelValue.value = false
}

watch(() => props.action, (newVal) => {
  if (newVal) {
    action.value = { ...newVal }
    if (newVal.config?.data) {
      actionConfigJson.value = JSON.stringify(newVal.config.data, null, 2)
    } else {
      actionConfigJson.value = ''
    }
  } else {
    action.value = {
      type: '',
      config: {}
    }
    actionConfigJson.value = ''
  }
}, { immediate: true })

watch(() => props.modelValue, (newVal) => {
  if (newVal && props.action) {
    action.value = { ...props.action }
    if (props.action.config?.data) {
      actionConfigJson.value = JSON.stringify(props.action.config.data, null, 2)
    }
  }
})
</script>

<style scoped>
</style>

