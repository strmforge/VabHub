<template>
  <div>
    <!-- 预警列表 -->
    <v-data-table
      :headers="headers"
      :items="alerts"
      :loading="loading"
      class="elevation-1"
    >
      <template v-slot:item.alert_type="{ item }">
        <v-chip
          :color="getAlertTypeColor(item.alert_type)"
          size="small"
          variant="flat"
        >
          {{ getAlertTypeText(item.alert_type) }}
        </v-chip>
      </template>

      <template v-slot:item.usage_percent="{ item }">
        <v-progress-linear
          :model-value="item.usage_percent"
          :color="getUsageColor(item.usage_percent)"
          height="20"
          rounded
        >
          <template v-slot:default>
            <strong class="text-white">{{ item.usage_percent.toFixed(1) }}%</strong>
          </template>
        </v-progress-linear>
      </template>

      <template v-slot:item.created_at="{ item }">
        {{ formatDate(item.created_at) }}
      </template>

      <template v-slot:item.actions="{ item }">
        <v-btn
          v-if="!item.resolved"
          variant="text"
          size="small"
          color="success"
          prepend-icon="mdi-check"
          @click="$emit('resolve', item.id)"
        >
          解决
        </v-btn>
        <v-chip
          v-else
          color="success"
          size="small"
          variant="flat"
        >
          已解决
        </v-chip>
      </template>

      <template v-slot:no-data>
        <div class="text-center py-8">
          <v-icon size="64" color="grey-lighten-1">mdi-alert-off</v-icon>
          <div class="text-h6 mt-4 text-medium-emphasis">暂无预警</div>
          <div class="text-body-2 text-medium-emphasis mt-2">所有存储目录使用正常</div>
        </div>
      </template>
    </v-data-table>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  alerts: any[]
  loading: boolean
}>()

const emit = defineEmits<{
  refresh: []
  resolve: [id: number]
}>()

// Vuetify DataTable headers - 使用 as const 满足 readonly 类型要求
const headers = [
  { title: '目录路径', key: 'path', sortable: true },
  { title: '预警类型', key: 'alert_type', sortable: true },
  { title: '使用率', key: 'usage_percent', sortable: true },
  { title: '预警阈值', key: 'threshold', sortable: true },
  { title: '消息', key: 'message', sortable: false },
  { title: '创建时间', key: 'created_at', sortable: true },
  { title: '操作', key: 'actions', sortable: false, align: 'end' as const }
] as const

// 获取预警类型颜色
const getAlertTypeColor = (type: string): string => {
  switch (type) {
    case 'critical':
      return 'error'
    case 'low_space':
      return 'warning'
    case 'threshold_exceeded':
      return 'info'
    default:
      return 'grey'
  }
}

// 获取预警类型文本
const getAlertTypeText = (type: string): string => {
  switch (type) {
    case 'critical':
      return '严重'
    case 'low_space':
      return '空间不足'
    case 'threshold_exceeded':
      return '超过阈值'
    default:
      return type
  }
}

// 根据使用率获取颜色
const getUsageColor = (percent: number): string => {
  if (percent >= 95) return 'error'
  if (percent >= 90) return 'warning'
  return 'info'
}

// 格式化日期
const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}
</script>

