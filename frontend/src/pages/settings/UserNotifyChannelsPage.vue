<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-bell-cog-outline</v-icon>
            通知渠道管理
            <v-spacer />
            <v-btn color="primary" @click="openCreateDialog">
              <v-icon left>mdi-plus</v-icon>
              添加渠道
            </v-btn>
          </v-card-title>

          <v-card-text>
            <v-alert v-if="!channels.length && !loading" type="info" variant="tonal" class="mb-4">
              还没有配置通知渠道。添加渠道后，追更通知、下载完成等消息会推送到你的外部设备。
            </v-alert>

            <v-list v-if="channels.length">
              <v-list-item
                v-for="channel in channels"
                :key="channel.id"
                class="mb-2"
                :class="{ 'bg-grey-lighten-4': !channel.is_enabled }"
              >
                <template #prepend>
                  <v-avatar :color="getTypeColor(channel.channel_type)" size="40">
                    <v-icon color="white">{{ getTypeIcon(channel.channel_type) }}</v-icon>
                  </v-avatar>
                </template>

                <v-list-item-title>
                  {{ channel.display_name || getTypeLabel(channel.channel_type) }}
                  <v-chip v-if="channel.is_verified" size="x-small" color="success" class="ml-2">已验证</v-chip>
                  <v-chip v-else size="x-small" color="warning" class="ml-2">未验证</v-chip>
                </v-list-item-title>

                <v-list-item-subtitle>
                  {{ getTypeLabel(channel.channel_type) }}
                  <span v-if="channel.last_test_at">
                    · 最近测试: {{ channel.last_test_ok ? '成功' : '失败' }}
                  </span>
                </v-list-item-subtitle>

                <template #append>
                  <v-switch
                    :model-value="channel.is_enabled"
                    color="success"
                    hide-details
                    density="compact"
                    class="mr-2"
                    @update:model-value="toggleEnabled(channel)"
                  />
                  <v-btn icon size="small" variant="text" @click="testChannel(channel)" title="测试">
                    <v-icon>mdi-send</v-icon>
                  </v-btn>
                  <v-btn icon size="small" variant="text" @click="editChannel(channel)" title="编辑">
                    <v-icon>mdi-pencil</v-icon>
                  </v-btn>
                  <v-btn icon size="small" variant="text" color="error" @click="confirmDelete(channel)" title="删除">
                    <v-icon>mdi-delete</v-icon>
                  </v-btn>
                </template>
              </v-list-item>
            </v-list>

            <v-skeleton-loader v-if="loading" type="list-item-avatar-two-line@3" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Telegram 绑定区块 -->
    <v-row class="mt-4">
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>
            <v-icon class="mr-2">mdi-telegram</v-icon>
            Telegram 绑定
          </v-card-title>
          <v-card-text>
            <div v-if="telegramChannel">
              <v-alert type="success" variant="tonal">
                已绑定 Telegram 账号
                <span v-if="telegramChannel.config?.username">(@{{ telegramChannel.config.username }})</span>
              </v-alert>
            </div>
            <div v-else>
              <p class="text-body-2 mb-4">
                通过 Telegram Bot 接收 VabHub 的通知推送。点击下方按钮获取绑定码，然后在 Telegram 中发送给机器人。
              </p>
              <v-btn color="primary" :loading="generatingCode" @click="generateBindingCode">
                <v-icon left>mdi-link</v-icon>
                获取绑定码
              </v-btn>
              
              <v-alert v-if="bindingCode" type="info" variant="tonal" class="mt-4">
                <p class="mb-2">请在 Telegram 中向 VabHub 机器人发送：</p>
                <code class="d-block pa-2 bg-grey-lighten-4 rounded">/start {{ bindingCode }}</code>
                <v-btn size="small" variant="text" class="mt-2" @click="copyBindingCode">
                  <v-icon left size="small">mdi-content-copy</v-icon>
                  复制命令
                </v-btn>
              </v-alert>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Telegram Bot 使用说明 -->
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>
            <v-icon class="mr-2">mdi-help-circle-outline</v-icon>
            Telegram Bot 使用说明
          </v-card-title>
          <v-card-text>
            <p class="text-body-2 mb-3">绑定成功后，你可以在 Telegram 中使用以下命令：</p>
            
            <v-table density="compact">
              <tbody>
                <tr>
                  <td class="font-weight-medium text-primary">/menu</td>
                  <td>打开主菜单</td>
                </tr>
                <tr>
                  <td class="font-weight-medium text-primary">/search 关键词</td>
                  <td>搜索影视/漫画/音乐</td>
                </tr>
                <tr>
                  <td class="font-weight-medium text-primary">/subscriptions</td>
                  <td>管理订阅</td>
                </tr>
                <tr>
                  <td class="font-weight-medium text-primary">/downloads</td>
                  <td>查看下载任务</td>
                </tr>
                <tr>
                  <td class="font-weight-medium text-primary">/reading</td>
                  <td>阅读进度</td>
                </tr>
                <tr>
                  <td class="font-weight-medium text-primary">/help</td>
                  <td>显示帮助信息</td>
                </tr>
              </tbody>
            </v-table>

            <v-alert type="info" variant="tonal" density="compact" class="mt-3">
              <strong>小技巧：</strong>直接发送媒体名称即可搜索，无需使用 /search 命令！
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 创建/编辑对话框 -->
    <v-dialog v-model="dialogVisible" max-width="500" persistent>
      <v-card>
        <v-card-title>{{ editingChannel ? '编辑通知渠道' : '添加通知渠道' }}</v-card-title>
        <v-card-text>
          <v-form ref="formRef" v-model="formValid">
            <v-select
              v-model="formData.channel_type"
              :items="availableChannelTypes"
              item-title="title"
              item-value="value"
              label="渠道类型"
              :disabled="!!editingChannel"
              :rules="[v => !!v || '请选择类型']"
            >
              <template #item="{ item, props }">
                <v-list-item v-bind="props">
                  <template #prepend>
                    <v-icon>{{ item.raw.icon }}</v-icon>
                  </template>
                  <template #subtitle>{{ item.raw.description }}</template>
                </v-list-item>
              </template>
            </v-select>

            <v-text-field
              v-model="formData.display_name"
              label="显示名称（可选）"
              placeholder="我的 Webhook"
            />

            <!-- 渠道配置字段 -->
            <template v-if="formData.channel_type === 'webhook'">
              <v-text-field
                v-model="formData.config.url"
                label="Webhook URL"
                type="url"
                :rules="[v => !!v || '请输入 URL']"
              />
              <v-text-field
                v-model="formData.config.secret"
                label="Secret（可选）"
                type="password"
              />
            </template>

            <template v-else-if="formData.channel_type === 'bark'">
              <v-text-field
                v-model="formData.config.server"
                label="服务器地址"
                placeholder="https://api.day.app/your-key"
                :rules="[v => !!v || '请输入服务器地址']"
              />
              <v-text-field
                v-model="formData.config.sound"
                label="提示音"
                placeholder="alarm"
              />
              <v-text-field
                v-model="formData.config.group"
                label="分组"
                placeholder="VabHub"
              />
            </template>

            <template v-else-if="formData.channel_type === 'telegram_bot'">
              <v-alert type="info" variant="tonal">
                Telegram 渠道请通过上方的"Telegram 绑定"功能添加。
              </v-alert>
            </template>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="dialogVisible = false">取消</v-btn>
          <v-btn 
            color="primary" 
            :loading="saving" 
            :disabled="!formValid || formData.channel_type === 'telegram_bot'" 
            @click="saveChannel"
          >
            保存
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 删除确认对话框 -->
    <v-dialog v-model="deleteDialogVisible" max-width="400">
      <v-card>
        <v-card-title>确认删除</v-card-title>
        <v-card-text>
          确定要删除通知渠道「{{ deletingChannel?.display_name || getTypeLabel(deletingChannel?.channel_type) }}」吗？
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="deleteDialogVisible = false">取消</v-btn>
          <v-btn color="error" :loading="deleting" @click="doDelete">删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { userNotifyChannelApi, telegramBindingApi } from '@/services/api'
import { useToast } from '@/composables/useToast'
import type { UserNotifyChannel, UserNotifyChannelType } from '@/types/userNotifyChannel'
import { channelTypeOptions } from '@/types/userNotifyChannel'

const toast = useToast()

const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)
const generatingCode = ref(false)
const channels = ref<UserNotifyChannel[]>([])
const dialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const formValid = ref(false)
const formRef = ref()
const bindingCode = ref('')

const editingChannel = ref<UserNotifyChannel | null>(null)
const deletingChannel = ref<UserNotifyChannel | null>(null)

const formData = reactive({
  channel_type: 'webhook' as UserNotifyChannelType,
  display_name: '',
  config: {} as Record<string, any>,
  is_enabled: true,
})

// 过滤掉 Telegram（需要通过绑定流程添加）
const availableChannelTypes = computed(() => 
  channelTypeOptions.filter(opt => opt.value !== 'telegram_bot')
)

// 获取已绑定的 Telegram 渠道
const telegramChannel = computed(() =>
  channels.value.find(c => c.channel_type === 'telegram_bot')
)

const getTypeIcon = (type: UserNotifyChannelType) => {
  const opt = channelTypeOptions.find(o => o.value === type)
  return opt?.icon || 'mdi-bell'
}

const getTypeLabel = (type?: UserNotifyChannelType) => {
  if (!type) return ''
  const opt = channelTypeOptions.find(o => o.value === type)
  return opt?.title || type
}

const getTypeColor = (type: UserNotifyChannelType) => {
  const colors: Record<UserNotifyChannelType, string> = {
    telegram_bot: 'blue',
    webhook: 'purple',
    bark: 'orange',
  }
  return colors[type] || 'grey'
}

const loadChannels = async () => {
  try {
    loading.value = true
    channels.value = await userNotifyChannelApi.list()
  } catch (error) {
    toast.error('加载通知渠道失败')
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  editingChannel.value = null
  Object.assign(formData, {
    channel_type: 'webhook',
    display_name: '',
    config: {},
    is_enabled: true,
  })
  dialogVisible.value = true
}

const editChannel = (channel: UserNotifyChannel) => {
  editingChannel.value = channel
  Object.assign(formData, {
    channel_type: channel.channel_type,
    display_name: channel.display_name || '',
    config: { ...channel.config },
    is_enabled: channel.is_enabled,
  })
  dialogVisible.value = true
}

const saveChannel = async () => {
  try {
    saving.value = true
    const payload = {
      channel_type: formData.channel_type,
      display_name: formData.display_name || null,
      config: formData.config,
      is_enabled: formData.is_enabled,
    }

    if (editingChannel.value) {
      await userNotifyChannelApi.update(editingChannel.value.id, payload)
      toast.success('更新成功')
    } else {
      await userNotifyChannelApi.create(payload)
      toast.success('创建成功')
    }

    dialogVisible.value = false
    await loadChannels()
  } catch (error) {
    toast.error('保存失败')
  } finally {
    saving.value = false
  }
}

const toggleEnabled = async (channel: UserNotifyChannel) => {
  try {
    await userNotifyChannelApi.update(channel.id, { is_enabled: !channel.is_enabled })
    channel.is_enabled = !channel.is_enabled
  } catch (error) {
    toast.error('更新失败')
  }
}

const testChannel = async (channel: UserNotifyChannel) => {
  try {
    const result = await userNotifyChannelApi.test(channel.id)
    if (result.success) {
      toast.success('测试消息已发送')
    } else {
      toast.error(result.message || '发送失败')
    }
    await loadChannels()
  } catch (error) {
    toast.error('发送测试消息失败')
  }
}

const confirmDelete = (channel: UserNotifyChannel) => {
  deletingChannel.value = channel
  deleteDialogVisible.value = true
}

const doDelete = async () => {
  if (!deletingChannel.value) return
  try {
    deleting.value = true
    await userNotifyChannelApi.remove(deletingChannel.value.id)
    toast.success('删除成功')
    deleteDialogVisible.value = false
    await loadChannels()
  } catch (error) {
    toast.error('删除失败')
  } finally {
    deleting.value = false
  }
}

const generateBindingCode = async () => {
  try {
    generatingCode.value = true
    const result = await telegramBindingApi.generateCode()
    bindingCode.value = result.code
    toast.info(`绑定码已生成，${Math.floor(result.expires_in / 60)} 分钟内有效`)
  } catch (error) {
    toast.error('生成绑定码失败')
  } finally {
    generatingCode.value = false
  }
}

const copyBindingCode = () => {
  navigator.clipboard.writeText(`/start ${bindingCode.value}`)
  toast.success('已复制到剪贴板')
}

onMounted(() => {
  loadChannels()
})
</script>
