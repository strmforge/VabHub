<template>
  <div>
    <!-- 使用情况列表 -->
    <v-row v-if="usageList.length > 0">
      <v-col
        v-for="usage in usageList"
        :key="usage.directory_id"
        cols="12"
        md="6"
        lg="4"
      >
        <v-card>
          <v-card-title>
            <v-icon color="primary" class="mr-2">mdi-folder</v-icon>
            {{ usage.name }}
          </v-card-title>

          <v-card-text>
            <div class="mb-4">
              <div class="text-caption text-medium-emphasis mb-1">使用率</div>
              <v-progress-linear
                :model-value="usage.usage_percent"
                :color="getUsageColor(usage.usage_percent)"
                height="24"
                rounded
              >
                <template v-slot:default>
                  <strong class="text-white">{{ usage.usage_percent.toFixed(1) }}%</strong>
                </template>
              </v-progress-linear>
            </div>

            <v-row>
              <v-col cols="6">
                <div class="text-caption text-medium-emphasis">总空间</div>
                <div class="text-body-1 font-weight-bold">{{ formatBytes(usage.total_bytes) }}</div>
              </v-col>
              <v-col cols="6">
                <div class="text-caption text-medium-emphasis">已用空间</div>
                <div class="text-body-1 font-weight-bold">{{ formatBytes(usage.used_bytes) }}</div>
              </v-col>
              <v-col cols="6">
                <div class="text-caption text-medium-emphasis">可用空间</div>
                <div class="text-body-1 font-weight-bold">{{ formatBytes(usage.free_bytes) }}</div>
              </v-col>
              <v-col cols="6">
                <div class="text-caption text-medium-emphasis">预警阈值</div>
                <div class="text-body-1 font-weight-bold">{{ usage.alert_threshold }}%</div>
              </v-col>
            </v-row>

            <v-alert
              v-if="usage.usage_percent >= usage.alert_threshold"
              type="warning"
              variant="tonal"
              density="compact"
              class="mt-2"
            >
              存储使用率超过预警阈值
            </v-alert>
          </v-card-text>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn
              variant="text"
              size="small"
              prepend-icon="mdi-refresh"
              @click="$emit('refresh')"
            >
              刷新
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- 空状态 -->
    <v-alert
      v-else-if="!loading"
      type="info"
      variant="tonal"
      class="mt-4"
    >
      没有可用的存储目录使用情况数据。
    </v-alert>

    <!-- 加载状态 -->
    <div v-if="loading" class="text-center py-8">
      <v-progress-circular indeterminate color="primary"></v-progress-circular>
      <div class="mt-4 text-body-2 text-medium-emphasis">加载中...</div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  usageList: any[]
  loading: boolean
}>()

defineEmits<{
  refresh: []
}>()

// 格式化字节数
const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 根据使用率获取颜色
const getUsageColor = (percent: number): string => {
  if (percent >= 90) return 'error'
  if (percent >= 80) return 'warning'
  if (percent >= 50) return 'info'
  return 'success'
}
</script>

<style scoped>
.v-card {
  height: 100%;
}
</style>

