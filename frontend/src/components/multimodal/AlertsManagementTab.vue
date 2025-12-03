<template>
  <div class="alerts-management-tab">
    <!-- 操作栏 -->
    <v-card variant="outlined" class="mb-4">
      <v-card-text>
        <v-row align="center">
          <v-col cols="12" md="6">
            <v-btn
              color="primary"
              prepend-icon="mdi-alert-circle"
              @click="handleCheck"
              :loading="checking || loading"
            >
              检查告警
            </v-btn>
            <v-btn
              color="secondary"
              prepend-icon="mdi-refresh"
              @click="$emit('refresh')"
              :loading="loading"
              class="ml-2"
            >
              刷新
            </v-btn>
          </v-col>
          <v-col cols="12" md="6" class="text-right">
            <v-chip
              :color="unresolvedCount > 0 ? 'error' : 'success'"
              class="mr-2"
            >
              未解决: {{ unresolvedCount }}
            </v-chip>
            <v-chip color="info">
              总数: {{ alerts.length }}
            </v-chip>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- 告警列表 -->
    <v-card variant="outlined">
      <v-card-title>告警列表</v-card-title>
      <v-card-text>
        <div v-if="loading" class="text-center py-12">
          <v-progress-circular indeterminate color="primary" size="64" />
          <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
        </div>
        <div v-else-if="alerts.length === 0" class="text-center py-12">
          <v-icon size="64" color="grey-lighten-1">mdi-check-circle</v-icon>
          <div class="mt-4 text-body-1 text-medium-emphasis">暂无告警</div>
        </div>
        <v-list v-else>
          <v-list-item
            v-for="alert in alerts"
            :key="alert.id"
            :class="getAlertClass(alert.severity)"
          >
            <template v-slot:prepend>
              <v-icon :color="getSeverityColor(alert.severity)">
                {{ getSeverityIcon(alert.severity) }}
              </v-icon>
            </template>
            <v-list-item-title>{{ alert.message }}</v-list-item-title>
            <v-list-item-subtitle>
              <div class="d-flex flex-wrap gap-2 mt-1">
                <v-chip size="small">{{ alert.operation }}</v-chip>
                <v-chip size="small">{{ alert.alert_type }}</v-chip>
                <v-chip size="small" :color="getSeverityColor(alert.severity)">
                  {{ alert.severity }}
                </v-chip>
                <v-chip size="small" variant="outlined">
                  {{ formatTime(alert.timestamp) }}
                </v-chip>
              </div>
            </v-list-item-subtitle>
            <template v-slot:append>
              <div class="d-flex align-center gap-2">
                <div v-if="alert.threshold !== null" class="text-caption text-medium-emphasis mr-2">
                  阈值: {{ alert.threshold }} | 实际: {{ alert.actual_value }}
                </div>
                <v-btn
                  v-if="!alert.resolved"
                  color="success"
                  size="small"
                  variant="text"
                  @click="$emit('resolve', alert.id)"
                >
                  解决
                </v-btn>
                <v-chip v-else size="small" color="success">
                  已解决
                </v-chip>
              </div>
            </template>
          </v-list-item>
        </v-list>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface Props {
  loading: boolean
  alerts: any[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'refresh'): void
  (e: 'resolve', alertId: number): void
  (e: 'check'): void
}>()

const checking = ref(false)

// 处理检查告警
const handleCheck = async () => {
  checking.value = true
  try {
    emit('check')
  } finally {
    // 延迟重置，让父组件处理
    setTimeout(() => {
      checking.value = false
    }, 1000)
  }
}

const unresolvedCount = computed(() => {
  return props.alerts.filter(a => !a.resolved).length
})

const getSeverityColor = (severity: string) => {
  const colors: Record<string, string> = {
    info: 'info',
    warning: 'warning',
    error: 'error',
    critical: 'error'
  }
  return colors[severity] || 'grey'
}

const getSeverityIcon = (severity: string) => {
  const icons: Record<string, string> = {
    info: 'mdi-information',
    warning: 'mdi-alert',
    error: 'mdi-alert-circle',
    critical: 'mdi-alert-octagon'
  }
  return icons[severity] || 'mdi-help-circle'
}

const getAlertClass = (severity: string) => {
  return `alert-${severity}`
}

const formatTime = (timestamp: string) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN')
}
</script>

<style scoped>
.alerts-management-tab {
  padding: 16px 0;
}

.alert-critical {
  border-left: 4px solid rgb(var(--v-theme-error));
}

.alert-error {
  border-left: 4px solid rgb(var(--v-theme-error));
}

.alert-warning {
  border-left: 4px solid rgb(var(--v-theme-warning));
}

.alert-info {
  border-left: 4px solid rgb(var(--v-theme-info));
}
</style>

