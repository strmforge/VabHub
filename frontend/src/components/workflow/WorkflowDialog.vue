<template>
  <v-dialog
    v-model="modelValue"
    max-width="900"
    scrollable
    persistent
  >
    <v-card class="workflow-dialog">
      <v-card-item class="py-3">
        <template #prepend>
          <v-icon icon="mdi-workflow" class="me-2" />
        </template>
        <v-card-title class="text-h6">
          {{ editingWorkflow ? '编辑工作流' : '创建工作流' }}
        </v-card-title>
        <v-card-subtitle>
          {{ editingWorkflow ? '修改工作流配置' : '配置自动化工作流' }}
        </v-card-subtitle>
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
          <v-row>
            <v-col cols="12">
              <v-text-field
                v-model="form.name"
                label="工作流名称 *"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-tag"
                :rules="[v => !!v || '请输入工作流名称']"
                required
              />
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="12">
              <v-textarea
                v-model="form.description"
                label="描述"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-text"
                rows="2"
                auto-grow
              />
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="12" md="6">
              <v-select
                v-model="form.trigger_event"
                :items="triggerEvents"
                label="触发事件 *"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-lightning-bolt"
                :rules="[v => !!v || '请选择触发事件']"
                required
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-switch
                v-model="form.is_active"
                label="启用工作流"
                color="primary"
                hide-details
              />
            </v-col>
          </v-row>

          <v-divider class="my-4" />

          <div class="text-subtitle-1 font-weight-medium mb-3">
            动作列表
          </div>

          <div v-if="form.actions.length === 0" class="text-center py-8 text-medium-emphasis">
            <v-icon size="48" color="grey-lighten-1" class="mb-2">mdi-playlist-plus</v-icon>
            <div class="text-body-2">暂无动作，点击下方按钮添加</div>
          </div>

          <v-list v-else density="compact" class="mb-4">
            <v-list-item
              v-for="(action, index) in form.actions"
              :key="index"
              class="action-item"
            >
              <template #prepend>
                <v-avatar size="32" color="primary" rounded>
                  <v-icon size="small">{{ getActionIcon(action.type) }}</v-icon>
                </v-avatar>
              </template>

              <v-list-item-title>
                {{ getActionLabel(action.type) }}
              </v-list-item-title>
              <v-list-item-subtitle>
                {{ action.config?.title || action.config?.command || '未配置' }}
              </v-list-item-subtitle>

              <template #append>
                <v-btn
                  icon="mdi-pencil"
                  size="x-small"
                  variant="text"
                  @click="editAction(index)"
                />
                <v-btn
                  icon="mdi-delete"
                  size="x-small"
                  variant="text"
                  color="error"
                  @click="removeAction(index)"
                />
              </template>
            </v-list-item>
          </v-list>

          <v-btn
            color="primary"
            prepend-icon="mdi-plus"
            @click="showActionDialog = true"
            variant="outlined"
            block
          >
            添加动作
          </v-btn>
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
          :loading="saving"
          @click="handleSave"
        >
          保存
        </v-btn>
      </v-card-actions>
    </v-card>

    <!-- 动作配置对话框 -->
    <ActionConfigDialog
      v-model="showActionDialog"
      :action="editingAction"
      @save="handleActionSave"
    />
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import api from '@/services/api'
import ActionConfigDialog from './ActionConfigDialog.vue'

interface Props {
  modelValue: boolean
  workflow?: any
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'saved': []
}>()

const formRef = ref()
const saving = ref(false)
const editingWorkflow = computed(() => props.workflow)
const showActionDialog = ref(false)
const editingActionIndex = ref<number | null>(null)
const editingAction = ref<any>(null)

const form = ref({
  name: '',
  description: '',
  trigger_event: 'manual',
  conditions: null as any,
  actions: [] as any[],
  is_active: true
})

const modelValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const triggerEvents = [
  { title: '手动触发', value: 'manual' },
  { title: '下载完成', value: 'download_completed' },
  { title: '下载失败', value: 'download_failed' },
  { title: '订阅创建', value: 'subscription_created' },
  { title: '订阅更新', value: 'subscription_updated' },
  { title: '媒体添加', value: 'media_added' },
  { title: '定时触发', value: 'scheduled' }
]

const getActionIcon = (type: string) => {
  const icons: Record<string, string> = {
    'send_notification': 'mdi-bell',
    'create_download': 'mdi-download',
    'update_subscription': 'mdi-update',
    'execute_command': 'mdi-console',
    'webhook': 'mdi-webhook',
    'delay': 'mdi-timer',
    'condition': 'mdi-code-braces'
  }
  return icons[type] || 'mdi-cog'
}

const getActionLabel = (type: string) => {
  const labels: Record<string, string> = {
    'send_notification': '发送通知',
    'create_download': '创建下载',
    'update_subscription': '更新订阅',
    'execute_command': '执行命令',
    'webhook': 'Webhook',
    'delay': '延迟',
    'condition': '条件判断'
  }
  return labels[type] || type
}

const resetForm = () => {
  form.value = {
    name: '',
    description: '',
    trigger_event: 'manual',
    conditions: null,
    actions: [],
    is_active: true
  }
}

const loadWorkflowData = () => {
  if (editingWorkflow.value) {
    form.value = {
      name: editingWorkflow.value.name || '',
      description: editingWorkflow.value.description || '',
      trigger_event: editingWorkflow.value.trigger_event || 'manual',
      conditions: editingWorkflow.value.conditions || null,
      actions: editingWorkflow.value.actions || [],
      is_active: editingWorkflow.value.is_active !== false
    }
  } else {
    resetForm()
  }
}

const editAction = (index: number) => {
  editingActionIndex.value = index
  editingAction.value = { ...form.value.actions[index] }
  showActionDialog.value = true
}

const removeAction = (index: number) => {
  if (confirm('确定要删除这个动作吗？')) {
    form.value.actions.splice(index, 1)
  }
}

const handleActionSave = (action: any) => {
  if (editingActionIndex.value !== null) {
    // 更新现有动作
    form.value.actions[editingActionIndex.value] = action
    editingActionIndex.value = null
  } else {
    // 添加新动作
    form.value.actions.push(action)
  }
  editingAction.value = null
}

const handleSave = async () => {
  const { valid } = await formRef.value.validate()
  if (!valid) return

  if (form.value.actions.length === 0) {
    alert('请至少添加一个动作')
    return
  }

  saving.value = true
  try {
    if (editingWorkflow.value?.id) {
      await api.put(`/workflows/${editingWorkflow.value.id}`, form.value)
    } else {
      await api.post('/workflows', form.value)
    }
    emit('saved')
    modelValue.value = false
  } catch (error: any) {
    console.error('保存工作流失败:', error)
    alert('保存失败：' + (error.response?.data?.detail || '未知错误'))
  } finally {
    saving.value = false
  }
}

watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    loadWorkflowData()
  }
})

watch(() => props.workflow, () => {
  if (props.modelValue) {
    loadWorkflowData()
  }
})
</script>

<style scoped>
.workflow-dialog {
  background: rgba(30, 30, 30, 0.95);
  backdrop-filter: blur(10px);
}

.action-item {
  border-bottom: 1px solid rgba(var(--v-border-color), 0.12);
}
</style>

