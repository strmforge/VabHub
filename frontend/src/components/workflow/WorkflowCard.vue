<template>
  <v-card
    variant="outlined"
    class="workflow-card"
    :class="{ 'workflow-inactive': !workflow.is_active }"
  >
    <v-card-item class="pb-2">
      <div class="d-flex align-center justify-space-between">
        <div class="d-flex align-center ga-2">
          <v-avatar
            size="40"
            color="primary"
            rounded
          >
            <v-icon>mdi-workflow</v-icon>
          </v-avatar>
          <div>
            <div class="text-h6 font-weight-bold">
              {{ workflow.name }}
            </div>
            <div class="text-caption text-medium-emphasis">
              {{ getTriggerEventLabel(workflow.trigger_event) }}
            </div>
          </div>
        </div>
        <v-chip
          :color="workflow.is_active ? 'success' : 'default'"
          size="small"
          variant="flat"
        >
          {{ workflow.is_active ? '启用' : '禁用' }}
        </v-chip>
      </div>
    </v-card-item>

    <v-card-text class="pt-0">
      <div v-if="workflow.description" class="text-body-2 text-medium-emphasis mb-2">
        {{ workflow.description }}
      </div>

      <div class="text-caption text-medium-emphasis">
        <v-icon size="small" class="me-1">mdi-playlist-play</v-icon>
        {{ workflow.actions?.length || 0 }} 个动作
      </div>

      <div v-if="workflow.conditions" class="text-caption text-medium-emphasis mt-1">
        <v-icon size="small" class="me-1">mdi-filter</v-icon>
        有条件限制
      </div>
    </v-card-text>

    <v-card-actions class="pt-0">
      <v-spacer />
      <v-tooltip text="执行工作流" location="top">
        <template #activator="{ props: tooltipProps }">
          <v-btn
            v-bind="tooltipProps"
            icon="mdi-play"
            size="small"
            variant="text"
            @click.stop="handleExecute"
            :loading="executing"
          />
        </template>
      </v-tooltip>

      <v-tooltip text="执行记录" location="top">
        <template #activator="{ props: tooltipProps }">
          <v-btn
            v-bind="tooltipProps"
            icon="mdi-history"
            size="small"
            variant="text"
            @click.stop="handleViewExecutions"
          />
        </template>
      </v-tooltip>

      <v-tooltip :text="workflow.is_active ? '禁用' : '启用'" location="top">
        <template #activator="{ props: tooltipProps }">
          <v-btn
            v-bind="tooltipProps"
            :icon="workflow.is_active ? 'mdi-pause' : 'mdi-play'"
            size="small"
            variant="text"
            @click.stop="handleToggleStatus"
          />
        </template>
      </v-tooltip>

      <v-tooltip text="编辑" location="top">
        <template #activator="{ props: tooltipProps }">
          <v-btn
            v-bind="tooltipProps"
            icon="mdi-pencil"
            size="small"
            variant="text"
            @click.stop="handleEdit"
          />
        </template>
      </v-tooltip>

      <v-tooltip text="删除" location="top">
        <template #activator="{ props: tooltipProps }">
          <v-btn
            v-bind="tooltipProps"
            icon="mdi-delete"
            size="small"
            variant="text"
            color="error"
            @click.stop="handleDelete"
          />
        </template>
      </v-tooltip>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  workflow: any
}

const props = defineProps<Props>()
const emit = defineEmits(['edit', 'delete', 'execute', 'toggle-status', 'view-executions'])

const executing = ref(false)

const getTriggerEventLabel = (event: string) => {
  const labels: Record<string, string> = {
    'download_completed': '下载完成',
    'download_failed': '下载失败',
    'subscription_created': '订阅创建',
    'subscription_updated': '订阅更新',
    'media_added': '媒体添加',
    'manual': '手动触发',
    'scheduled': '定时触发'
  }
  return labels[event] || event
}

const handleEdit = () => {
  emit('edit', props.workflow)
}

const handleDelete = () => {
  emit('delete', props.workflow)
}

const handleExecute = async () => {
  executing.value = true
  try {
    emit('execute', props.workflow)
  } finally {
    setTimeout(() => {
      executing.value = false
    }, 1000)
  }
}

const handleToggleStatus = () => {
  emit('toggle-status', props.workflow)
}

const handleViewExecutions = () => {
  emit('view-executions', props.workflow)
}
</script>

<style scoped>
.workflow-card {
  height: 100%;
  background: rgba(30, 30, 30, 0.8);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.workflow-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
}

.workflow-inactive {
  opacity: 0.6;
}
</style>

