<template>
  <v-container fluid class="pa-4">
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">
          <v-icon class="mr-2">mdi-bell-cog</v-icon>
          多渠道通知测试
        </h1>
        <p class="text-body-2 text-medium-emphasis mb-6">
          测试和预览通知在各渠道的表现，验证配置是否正确。
        </p>
      </v-col>
    </v-row>

    <v-row>
      <!-- 左侧：发送测试 -->
      <v-col cols="12" md="5">
        <v-card>
          <v-card-title>
            <v-icon class="mr-2">mdi-send</v-icon>
            发送测试通知
          </v-card-title>
          <v-card-text>
            <v-select
              v-model="selectedEventType"
              :items="eventTypes"
              item-title="label"
              item-value="value"
              label="事件类型"
              variant="outlined"
              density="comfortable"
              class="mb-4"
            />

            <v-text-field
              v-model="targetUserId"
              label="目标用户 ID（留空使用当前用户）"
              variant="outlined"
              density="comfortable"
              type="number"
              class="mb-4"
            />

            <v-btn
              color="primary"
              :loading="sending"
              @click="sendTestNotification"
              block
            >
              <v-icon class="mr-2">mdi-send</v-icon>
              发送测试通知
            </v-btn>

            <v-alert
              v-if="sendResult"
              :type="sendResult.success ? 'success' : 'error'"
              class="mt-4"
              density="compact"
            >
              {{ sendResult.message }}
            </v-alert>
          </v-card-text>
        </v-card>

        <!-- 我的渠道 -->
        <v-card class="mt-4">
          <v-card-title>
            <v-icon class="mr-2">mdi-lan-connect</v-icon>
            已配置渠道
          </v-card-title>
          <v-card-text>
            <v-list v-if="myChannels.length > 0" density="compact">
              <v-list-item
                v-for="channel in myChannels"
                :key="channel.id"
              >
                <template v-slot:prepend>
                  <v-icon :color="channel.enabled ? 'success' : 'grey'">
                    {{ getChannelIcon(channel.type) }}
                  </v-icon>
                </template>
                <v-list-item-title>{{ channel.name || channel.type }}</v-list-item-title>
                <v-list-item-subtitle>
                  {{ channel.enabled ? '已启用' : '已禁用' }}
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
            <div v-else class="text-center text-medium-emphasis pa-4">
              暂无配置渠道
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- 右侧：预览 -->
      <v-col cols="12" md="7">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-eye</v-icon>
            渠道预览
            <v-spacer />
            <v-btn
              variant="text"
              size="small"
              :loading="loadingPreview"
              @click="loadPreview"
            >
              <v-icon>mdi-refresh</v-icon>
            </v-btn>
          </v-card-title>
          <v-card-text>
            <v-tabs v-model="previewTab" density="compact">
              <v-tab value="base">基础数据</v-tab>
              <v-tab value="telegram">Telegram</v-tab>
              <v-tab value="webhook">Webhook</v-tab>
              <v-tab value="bark">Bark</v-tab>
            </v-tabs>

            <v-tabs-window v-model="previewTab" class="mt-4">
              <!-- 基础数据 -->
              <v-tabs-window-item value="base">
                <div v-if="preview" class="preview-content">
                  <div class="mb-3">
                    <strong>标题:</strong> {{ preview.base.title }}
                  </div>
                  <div class="mb-3">
                    <strong>消息:</strong>
                    <pre class="text-body-2 mt-1">{{ preview.base.message }}</pre>
                  </div>
                  <div class="mb-3">
                    <strong>事件类型:</strong> {{ preview.base.event_type }}
                  </div>
                  <div class="mb-3">
                    <strong>媒体类型:</strong> {{ preview.base.media_type || '-' }}
                  </div>
                  <div class="mb-3">
                    <strong>动作:</strong>
                    <v-chip
                      v-for="action in preview.base.actions"
                      :key="action.id"
                      size="small"
                      class="mr-1 mt-1"
                    >
                      {{ action.label }}
                    </v-chip>
                  </div>
                </div>
                <div v-else class="text-center text-medium-emphasis pa-8">
                  选择事件类型后加载预览
                </div>
              </v-tabs-window-item>

              <!-- Telegram -->
              <v-tabs-window-item value="telegram">
                <div v-if="preview?.per_channel?.telegram" class="preview-content">
                  <v-alert density="compact" type="info" class="mb-4">
                    支持 Markdown 格式，最多 {{ preview.per_channel.telegram.capabilities.max_button_count }} 个按钮
                  </v-alert>
                  <div class="telegram-preview pa-4 rounded">
                    <div class="telegram-message" v-html="formatTelegramText(preview.per_channel.telegram.rendered_text)"></div>
                    <div class="telegram-buttons mt-3">
                      <v-btn
                        v-for="btn in preview.per_channel.telegram.keyboard"
                        :key="btn.text"
                        size="small"
                        variant="outlined"
                        class="mr-2 mb-2"
                      >
                        {{ btn.text }}
                      </v-btn>
                    </div>
                  </div>
                </div>
              </v-tabs-window-item>

              <!-- Webhook -->
              <v-tabs-window-item value="webhook">
                <div v-if="preview?.per_channel?.webhook" class="preview-content">
                  <v-alert density="compact" type="info" class="mb-4">
                    JSON payload，包含 actions 数组供接收端处理
                  </v-alert>
                  <pre class="webhook-payload pa-4 rounded">{{ JSON.stringify(preview.per_channel.webhook.payload, null, 2) }}</pre>
                </div>
              </v-tabs-window-item>

              <!-- Bark -->
              <v-tabs-window-item value="bark">
                <div v-if="preview?.per_channel?.bark" class="preview-content">
                  <v-alert density="compact" type="info" class="mb-4">
                    纯文本，点击通知打开 URL
                  </v-alert>
                  <div class="bark-preview pa-4 rounded">
                    <div class="bark-title font-weight-bold mb-2">
                      {{ preview.per_channel.bark.title }}
                    </div>
                    <div class="bark-body text-body-2">
                      <pre>{{ preview.per_channel.bark.body }}</pre>
                    </div>
                    <div class="bark-url mt-3 text-caption text-primary">
                      点击跳转: {{ preview.per_channel.bark.url }}
                    </div>
                  </div>
                </div>
              </v-tabs-window-item>
            </v-tabs-window>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'
import { useToast } from 'vue-toastification'

const toast = useToast()

// 事件类型选项
const eventTypes = [
  { value: 'MANGA_UPDATED', label: '漫画更新' },
  { value: 'NOVEL_NEW_CHAPTER', label: '小说新章节' },
  { value: 'TTS_JOB_COMPLETED', label: 'TTS 任务完成' },
  { value: 'AUDIOBOOK_READY', label: '有声书就绪' },
  { value: 'SYSTEM_ALERT', label: '系统告警' },
]

// 状态
const selectedEventType = ref('MANGA_UPDATED')
const targetUserId = ref<number | null>(null)
const sending = ref(false)
const sendResult = ref<{ success: boolean; message: string } | null>(null)

const myChannels = ref<any[]>([])
const preview = ref<any>(null)
const previewTab = ref('base')
const loadingPreview = ref(false)

// 获取渠道图标
const getChannelIcon = (type: string): string => {
  const icons: Record<string, string> = {
    TELEGRAM_BOT: 'mdi-send',
    WEBHOOK: 'mdi-webhook',
    BARK: 'mdi-bell-ring',
  }
  return icons[type] || 'mdi-bell'
}

// 格式化 Telegram 文本（简单的 Markdown 转 HTML）
const formatTelegramText = (text: string): string => {
  return text
    .replace(/\*(.+?)\*/g, '<strong>$1</strong>')
    .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank">$1</a>')
    .replace(/\n/g, '<br>')
}

// 加载我的渠道
const loadMyChannels = async () => {
  try {
    const response = await axios.get('/api/notify/test/my_channels')
    myChannels.value = response.data.channels
  } catch (error: any) {
    console.error('加载渠道失败:', error)
  }
}

// 加载预览
const loadPreview = async () => {
  loadingPreview.value = true
  try {
    const response = await axios.get('/api/notify/test/preview', {
      params: { event_type: selectedEventType.value }
    })
    preview.value = response.data
  } catch (error: any) {
    console.error('加载预览失败:', error)
    toast.error('加载预览失败')
  } finally {
    loadingPreview.value = false
  }
}

// 发送测试通知
const sendTestNotification = async () => {
  sending.value = true
  sendResult.value = null
  
  try {
    const response = await axios.post('/api/notify/test/send_sample', {
      event_type: selectedEventType.value,
      user_id: targetUserId.value || undefined,
    })
    
    sendResult.value = {
      success: response.data.success,
      message: response.data.success ? '测试通知已发送' : '发送失败',
    }
    
    if (response.data.success) {
      toast.success('测试通知已发送')
    }
  } catch (error: any) {
    console.error('发送失败:', error)
    sendResult.value = {
      success: false,
      message: error.response?.data?.detail || '发送失败',
    }
    toast.error('发送失败')
  } finally {
    sending.value = false
  }
}

// 监听事件类型变化
watch(selectedEventType, () => {
  loadPreview()
})

// 初始化
onMounted(() => {
  loadMyChannels()
  loadPreview()
})
</script>

<style scoped>
.preview-content pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  background: rgba(0, 0, 0, 0.05);
  padding: 8px;
  border-radius: 4px;
  font-size: 13px;
}

.telegram-preview {
  background: #e3f2fd;
  border-left: 4px solid #2196f3;
}

.telegram-message {
  font-size: 14px;
  line-height: 1.5;
}

.webhook-payload {
  background: #263238;
  color: #80cbc4;
  font-family: monospace;
  font-size: 12px;
  overflow-x: auto;
}

.bark-preview {
  background: #fff3e0;
  border-left: 4px solid #ff9800;
}
</style>
