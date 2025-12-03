<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-bell-cog</v-icon>
            告警渠道管理
            <v-spacer />
            <v-btn color="primary" @click="openCreateDialog">
              <v-icon left>mdi-plus</v-icon>
              添加渠道
            </v-btn>
          </v-card-title>

          <v-card-text>
            <v-data-table
              :headers="headers"
              :items="channels"
              :loading="loading"
              class="elevation-0"
            >
              <template #item.channel_type="{ item }">
                <v-chip size="small" :color="getTypeColor(item.channel_type)">
                  <v-icon start size="small">{{ getTypeIcon(item.channel_type) }}</v-icon>
                  {{ getTypeLabel(item.channel_type) }}
                </v-chip>
              </template>

              <template #item.is_enabled="{ item }">
                <v-switch
                  :model-value="item.is_enabled"
                  color="success"
                  hide-details
                  density="compact"
                  @update:model-value="toggleEnabled(item)"
                />
              </template>

              <template #item.min_severity="{ item }">
                <v-chip :color="getSeverityColor(item.min_severity)" size="small">
                  {{ getSeverityLabel(item.min_severity) }}
                </v-chip>
              </template>

              <template #item.actions="{ item }">
                <v-btn icon size="small" variant="text" @click="testChannel(item)" title="发送测试">
                  <v-icon>mdi-send</v-icon>
                </v-btn>
                <v-btn icon size="small" variant="text" @click="editChannel(item)" title="编辑">
                  <v-icon>mdi-pencil</v-icon>
                </v-btn>
                <v-btn icon size="small" variant="text" color="error" @click="confirmDelete(item)" title="删除">
                  <v-icon>mdi-delete</v-icon>
                </v-btn>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 创建/编辑对话框 -->
    <v-dialog v-model="dialogVisible" max-width="600" persistent>
      <v-card>
        <v-card-title>{{ editingChannel ? '编辑告警渠道' : '添加告警渠道' }}</v-card-title>
        <v-card-text>
          <v-form ref="formRef" v-model="formValid">
            <v-text-field
              v-model="formData.name"
              label="渠道名称"
              :rules="[v => !!v || '请输入名称']"
              required
            />

            <v-select
              v-model="formData.channel_type"
              :items="channelTypeOptions"
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
                </v-list-item>
              </template>
            </v-select>

            <v-select
              v-model="formData.min_severity"
              :items="severityOptions"
              item-title="title"
              item-value="value"
              label="最小告警级别"
            />

            <!-- 渠道配置字段 -->
            <v-divider class="my-4" />
            <div class="text-subtitle-2 mb-2">渠道配置</div>

            <template v-if="formData.channel_type === 'telegram'">
              <v-text-field
                v-model="formData.config.bot_token"
                label="Bot Token"
                type="password"
                :rules="[v => !!v || '请输入 Bot Token']"
              />
              <v-text-field
                v-model="formData.config.chat_id"
                label="Chat ID"
                :rules="[v => !!v || '请输入 Chat ID']"
              />
            </template>

            <template v-else-if="formData.channel_type === 'webhook'">
              <v-text-field
                v-model="formData.config.url"
                label="Webhook URL"
                type="url"
                :rules="[v => !!v || '请输入 URL']"
              />
              <v-select
                v-model="formData.config.method"
                :items="['POST', 'GET']"
                label="HTTP 方法"
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

            <!-- 过滤规则 -->
            <v-divider class="my-4" />
            <div class="text-subtitle-2 mb-2">过滤规则（可选）</div>

            <v-combobox
              v-model="formData.include_checks"
              label="只接收这些检查项（白名单）"
              multiple
              chips
              closable-chips
              hint="留空表示接收所有，支持 disk.* 通配符"
              persistent-hint
            />

            <v-combobox
              v-model="formData.exclude_checks"
              label="排除这些检查项（黑名单）"
              multiple
              chips
              closable-chips
              hint="支持 disk.* 通配符"
              persistent-hint
            />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="dialogVisible = false">取消</v-btn>
          <v-btn color="primary" :loading="saving" :disabled="!formValid" @click="saveChannel">
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
          确定要删除告警渠道「{{ deletingChannel?.name }}」吗？
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
import { ref, reactive, onMounted } from 'vue'
import { alertChannelApi } from '@/services/api'
import { useToast } from '@/composables/useToast'
import type { AlertChannel, AlertChannelType, AlertSeverity } from '@/types/alertChannel'
import { channelTypeOptions, severityOptions } from '@/types/alertChannel'

const toast = useToast()

const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)
const channels = ref<AlertChannel[]>([])
const dialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const formValid = ref(false)
const formRef = ref()

const editingChannel = ref<AlertChannel | null>(null)
const deletingChannel = ref<AlertChannel | null>(null)

const formData = reactive({
  name: '',
  channel_type: 'telegram' as AlertChannelType,
  min_severity: 'warning' as AlertSeverity,
  config: {} as Record<string, any>,
  include_checks: [] as string[],
  exclude_checks: [] as string[],
})

const headers = [
  { title: '名称', key: 'name' },
  { title: '类型', key: 'channel_type' },
  { title: '启用', key: 'is_enabled', width: 100 },
  { title: '最小级别', key: 'min_severity' },
  { title: '操作', key: 'actions', sortable: false, width: 150 },
]

const getTypeIcon = (type: AlertChannelType) => {
  const opt = channelTypeOptions.find(o => o.value === type)
  return opt?.icon || 'mdi-bell'
}

const getTypeLabel = (type: AlertChannelType) => {
  const opt = channelTypeOptions.find(o => o.value === type)
  return opt?.title || type
}

const getTypeColor = (type: AlertChannelType) => {
  const colors: Record<AlertChannelType, string> = {
    telegram: 'blue',
    webhook: 'purple',
    bark: 'orange',
  }
  return colors[type] || 'grey'
}

const getSeverityLabel = (severity: AlertSeverity) => {
  const opt = severityOptions.find(o => o.value === severity)
  return opt?.title || severity
}

const getSeverityColor = (severity: AlertSeverity) => {
  const opt = severityOptions.find(o => o.value === severity)
  return opt?.color || 'grey'
}

const loadChannels = async () => {
  try {
    loading.value = true
    channels.value = await alertChannelApi.list()
  } catch (error) {
    toast.error('加载告警渠道失败')
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  editingChannel.value = null
  Object.assign(formData, {
    name: '',
    channel_type: 'telegram',
    min_severity: 'warning',
    config: {},
    include_checks: [],
    exclude_checks: [],
  })
  dialogVisible.value = true
}

const editChannel = (channel: AlertChannel) => {
  editingChannel.value = channel
  Object.assign(formData, {
    name: channel.name,
    channel_type: channel.channel_type,
    min_severity: channel.min_severity,
    config: { ...channel.config },
    include_checks: channel.include_checks || [],
    exclude_checks: channel.exclude_checks || [],
  })
  dialogVisible.value = true
}

const saveChannel = async () => {
  try {
    saving.value = true
    const payload = {
      name: formData.name,
      channel_type: formData.channel_type,
      min_severity: formData.min_severity,
      config: formData.config,
      include_checks: formData.include_checks.length ? formData.include_checks : null,
      exclude_checks: formData.exclude_checks.length ? formData.exclude_checks : null,
    }

    if (editingChannel.value) {
      await alertChannelApi.update(editingChannel.value.id, payload)
      toast.success('更新成功')
    } else {
      await alertChannelApi.create(payload)
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

const toggleEnabled = async (channel: AlertChannel) => {
  try {
    await alertChannelApi.update(channel.id, { is_enabled: !channel.is_enabled })
    channel.is_enabled = !channel.is_enabled
  } catch (error) {
    toast.error('更新失败')
  }
}

const testChannel = async (channel: AlertChannel) => {
  try {
    await alertChannelApi.test(channel.id)
    toast.success('测试消息已发送')
  } catch (error) {
    toast.error('发送测试消息失败')
  }
}

const confirmDelete = (channel: AlertChannel) => {
  deletingChannel.value = channel
  deleteDialogVisible.value = true
}

const doDelete = async () => {
  if (!deletingChannel.value) return
  try {
    deleting.value = true
    await alertChannelApi.remove(deletingChannel.value.id)
    toast.success('删除成功')
    deleteDialogVisible.value = false
    await loadChannels()
  } catch (error) {
    toast.error('删除失败')
  } finally {
    deleting.value = false
  }
}

onMounted(() => {
  loadChannels()
})
</script>
