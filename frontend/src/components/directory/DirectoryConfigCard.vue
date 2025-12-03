<template>
  <v-card variant="outlined" class="directory-config-card">
    <v-card-title class="d-flex align-center justify-space-between">
      <div class="d-flex align-center">
        <v-icon :color="getMonitorTypeColor(directory.monitor_type)" class="mr-2">
          {{ getMonitorTypeIcon(directory.monitor_type) }}
        </v-icon>
        <span class="text-subtitle-1">{{ getMonitorTypeName(directory.monitor_type) }}</span>
      </div>
      <v-chip
        :color="directory.enabled ? 'success' : 'default'"
        size="small"
        variant="flat"
      >
        {{ directory.enabled ? '启用' : '禁用' }}
      </v-chip>
    </v-card-title>

    <v-card-text>
      <div class="mb-2">
        <div class="text-caption text-medium-emphasis">下载目录</div>
        <div class="text-body-2 font-weight-medium">{{ directory.download_path || '-' }}</div>
      </div>

      <div class="mb-2">
        <div class="text-caption text-medium-emphasis">媒体库目录</div>
        <div class="text-body-2 font-weight-medium">{{ directory.library_path || '-' }}</div>
      </div>

      <v-row dense class="mt-2">
        <v-col cols="6">
          <div class="text-caption text-medium-emphasis">整理方式</div>
          <div class="text-body-2">{{ getTransferTypeName(directory.transfer_type) }}</div>
        </v-col>
        <v-col cols="6">
          <div class="text-caption text-medium-emphasis">优先级</div>
          <div class="text-body-2">{{ directory.priority }}</div>
        </v-col>
      </v-row>

      <v-row dense v-if="directory.media_type || directory.media_category">
        <v-col cols="6" v-if="directory.media_type">
          <div class="text-caption text-medium-emphasis">媒体类型</div>
          <div class="text-body-2">{{ directory.media_type }}</div>
        </v-col>
        <v-col cols="6" v-if="directory.media_category">
          <div class="text-caption text-medium-emphasis">媒体类别</div>
          <div class="text-body-2">{{ directory.media_category }}</div>
        </v-col>
      </v-row>
    </v-card-text>

    <v-card-actions>
      <v-spacer />
      <v-btn
        icon="mdi-pencil"
        size="small"
        variant="text"
        @click="$emit('edit', directory)"
      />
      <v-btn
        :icon="directory.enabled ? 'mdi-toggle-switch-off' : 'mdi-toggle-switch'"
        size="small"
        variant="text"
        @click="$emit('toggle-enabled', directory)"
      />
      <v-btn
        icon="mdi-delete"
        size="small"
        variant="text"
        color="error"
        @click="$emit('delete', directory)"
      />
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
const props = defineProps<{
  directory: any
}>()

defineEmits<{
  edit: [directory: any]
  delete: [directory: any]
  'toggle-enabled': [directory: any]
}>()

const getMonitorTypeName = (type: string | null) => {
  const map: Record<string, string> = {
    'downloader': '下载器监控',
    'directory': '目录监控',
    null: '不监控'
  }
  return map[type as string] || '未知'
}

const getMonitorTypeIcon = (type: string | null) => {
  const map: Record<string, string> = {
    'downloader': 'mdi-download',
    'directory': 'mdi-folder',
    null: 'mdi-close-circle'
  }
  return map[type as string] || 'mdi-help-circle'
}

const getMonitorTypeColor = (type: string | null) => {
  const map: Record<string, string> = {
    'downloader': 'primary',
    'directory': 'info',
    null: 'grey'
  }
  return map[type as string] || 'grey'
}

const getTransferTypeName = (type: string | null) => {
  const map: Record<string, string> = {
    'copy': '复制',
    'move': '移动',
    'link': '硬链接',
    'softlink': '软链接'
  }
  return map[type as string] || '-'
}
</script>

<style scoped>
.directory-config-card {
  height: 100%;
}
</style>

