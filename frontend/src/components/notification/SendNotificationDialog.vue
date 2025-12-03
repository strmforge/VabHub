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
          <v-icon icon="mdi-bell-plus" class="me-2" />
        </template>
        <v-card-title class="text-h6">
          发送通知
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
          <v-text-field
            v-model="form.title"
            label="通知标题 *"
            variant="outlined"
            density="compact"
            prepend-inner-icon="mdi-tag"
            :rules="[v => !!v || '请输入通知标题']"
            required
            class="mb-4"
          />

          <v-textarea
            v-model="form.message"
            label="通知内容 *"
            variant="outlined"
            density="compact"
            prepend-inner-icon="mdi-text"
            :rules="[v => !!v || '请输入通知内容']"
            required
            rows="4"
            auto-grow
            class="mb-4"
          />

          <v-select
            v-model="form.type"
            :items="notificationTypes"
            label="通知类型 *"
            variant="outlined"
            density="compact"
            prepend-inner-icon="mdi-information"
            required
            class="mb-4"
          />

          <v-select
            v-model="form.channels"
            :items="channelOptions"
            label="通知渠道 *"
            multiple
            chips
            variant="outlined"
            density="compact"
            prepend-inner-icon="mdi-broadcast"
            :rules="[v => v.length > 0 || '请至少选择一个通知渠道']"
            required
            class="mb-4"
          />

          <!-- 邮件配置 -->
          <v-expand-transition>
            <v-card
              v-if="form.channels.includes('email')"
              variant="outlined"
              class="mb-4"
            >
              <v-card-title class="text-subtitle-2">邮件配置</v-card-title>
              <v-card-text>
                <v-text-field
                  v-model="form.metadata.email_config.smtp_host"
                  label="SMTP服务器"
                  variant="outlined"
                  density="compact"
                  class="mb-2"
                />
                <v-text-field
                  v-model.number="form.metadata.email_config.smtp_port"
                  label="SMTP端口"
                  variant="outlined"
                  density="compact"
                  type="number"
                  class="mb-2"
                />
                <v-text-field
                  v-model="form.metadata.email_config.smtp_user"
                  label="用户名"
                  variant="outlined"
                  density="compact"
                  class="mb-2"
                />
                <v-text-field
                  v-model="form.metadata.email_config.smtp_password"
                  label="密码"
                  type="password"
                  variant="outlined"
                  density="compact"
                  class="mb-2"
                />
                <v-text-field
                  v-model="form.metadata.email_config.to_email"
                  label="收件人邮箱"
                  variant="outlined"
                  density="compact"
                />
              </v-card-text>
            </v-card>
          </v-expand-transition>

          <!-- Telegram配置 -->
          <v-expand-transition>
            <v-card
              v-if="form.channels.includes('telegram')"
              variant="outlined"
              class="mb-4"
            >
              <v-card-title class="text-subtitle-2">Telegram配置</v-card-title>
              <v-card-text>
                <v-text-field
                  v-model="form.metadata.telegram_config.bot_token"
                  label="Bot Token"
                  variant="outlined"
                  density="compact"
                  class="mb-2"
                />
                <v-text-field
                  v-model="form.metadata.telegram_config.chat_id"
                  label="Chat ID"
                  variant="outlined"
                  density="compact"
                />
              </v-card-text>
            </v-card>
          </v-expand-transition>

          <!-- 微信配置 -->
          <v-expand-transition>
            <v-card
              v-if="form.channels.includes('wechat')"
              variant="outlined"
              class="mb-4"
            >
              <v-card-title class="text-subtitle-2">微信配置</v-card-title>
              <v-card-text>
                <v-text-field
                  v-model="form.metadata.wechat_config.webhook_url"
                  label="Webhook URL"
                  variant="outlined"
                  density="compact"
                />
              </v-card-text>
            </v-card>
          </v-expand-transition>

          <!-- Webhook配置 -->
          <v-expand-transition>
            <v-card
              v-if="form.channels.includes('webhook')"
              variant="outlined"
              class="mb-4"
            >
              <v-card-title class="text-subtitle-2">Webhook配置</v-card-title>
              <v-card-text>
                <v-text-field
                  v-model="form.metadata.webhook_config.url"
                  label="Webhook URL"
                  variant="outlined"
                  density="compact"
                  class="mb-2"
                />
                <v-select
                  v-model="form.metadata.webhook_config.method"
                  :items="httpMethods"
                  label="HTTP方法"
                  variant="outlined"
                  density="compact"
                />
              </v-card-text>
            </v-card>
          </v-expand-transition>
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
          :loading="sending"
          @click="handleSend"
        >
          发送
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import api from '@/services/api'

interface Props {
  modelValue: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'sent': []
}>()

const formRef = ref()
const sending = ref(false)

const form = ref({
  title: '',
  message: '',
  type: 'info',
  channels: ['system'] as string[],
  metadata: {
    email_config: {
      smtp_host: '',
      smtp_port: 587,
      smtp_user: '',
      smtp_password: '',
      to_email: ''
    },
    telegram_config: {
      bot_token: '',
      chat_id: ''
    },
    wechat_config: {
      webhook_url: ''
    },
    webhook_config: {
      url: '',
      method: 'POST'
    }
  }
})

const modelValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const notificationTypes = [
  { title: '信息', value: 'info' },
  { title: '成功', value: 'success' },
  { title: '警告', value: 'warning' },
  { title: '错误', value: 'error' }
]

const channelOptions = [
  { title: '系统', value: 'system' },
  { title: '邮件', value: 'email' },
  { title: 'Telegram', value: 'telegram' },
  { title: '微信', value: 'wechat' },
  { title: 'Webhook', value: 'webhook' },
  { title: '推送', value: 'push' }
]

const httpMethods = [
  { title: 'GET', value: 'GET' },
  { title: 'POST', value: 'POST' },
  { title: 'PUT', value: 'PUT' },
  { title: 'DELETE', value: 'DELETE' }
]

const handleSend = async () => {
  const { valid } = await formRef.value.validate()
  if (!valid) return

  sending.value = true
  try {
    // 构建metadata，只包含选中的渠道配置
    const metadata: any = {}
    if (form.value.channels.includes('email')) {
      metadata.email_config = form.value.metadata.email_config
    }
    if (form.value.channels.includes('telegram')) {
      metadata.telegram_config = form.value.metadata.telegram_config
    }
    if (form.value.channels.includes('wechat')) {
      metadata.wechat_config = form.value.metadata.wechat_config
    }
    if (form.value.channels.includes('webhook')) {
      metadata.webhook_config = form.value.metadata.webhook_config
    }

    await api.post('/notifications', {
      title: form.value.title,
      message: form.value.message,
      type: form.value.type,
      channels: form.value.channels,
      metadata: Object.keys(metadata).length > 0 ? metadata : undefined
    })

    emit('sent')
    modelValue.value = false
    resetForm()
  } catch (error: any) {
    console.error('发送通知失败:', error)
    alert('发送失败：' + (error.response?.data?.detail || '未知错误'))
  } finally {
    sending.value = false
  }
}

const resetForm = () => {
  form.value = {
    title: '',
    message: '',
    type: 'info',
    channels: ['system'],
    metadata: {
      email_config: {
        smtp_host: '',
        smtp_port: 587,
        smtp_user: '',
        smtp_password: '',
        to_email: ''
      },
      telegram_config: {
        bot_token: '',
        chat_id: ''
      },
      wechat_config: {
        webhook_url: ''
      },
      webhook_config: {
        url: '',
        method: 'POST'
      }
    }
  }
}

watch(() => props.modelValue, (newVal) => {
  if (!newVal) {
    resetForm()
  }
})
</script>

<style scoped>
</style>

