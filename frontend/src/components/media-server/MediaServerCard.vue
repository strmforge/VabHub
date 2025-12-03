<template>
  <v-card>
    <v-card-title class="d-flex align-center">
      <v-avatar
        :color="getServerTypeColor(server.server_type)"
        size="40"
        class="mr-3"
      >
        <v-icon color="white">{{ getServerTypeIcon(server.server_type) }}</v-icon>
      </v-avatar>
      <div class="flex-grow-1">
        <div class="text-h6">{{ server.name }}</div>
        <div class="text-caption text-medium-emphasis">{{ getServerTypeText(server.server_type) }}</div>
      </div>
      <v-chip
        :color="getStatusColor(server.status)"
        size="small"
        variant="flat"
      >
        {{ getStatusText(server.status) }}
      </v-chip>
    </v-card-title>

    <v-card-text>
      <div class="mb-2">
        <div class="text-caption text-medium-emphasis">服务器地址</div>
        <div class="text-body-2">{{ server.url }}</div>
      </div>

      <v-row class="mt-2">
        <v-col cols="6">
          <div class="text-caption text-medium-emphasis">电影</div>
          <div class="text-body-1 font-weight-bold">{{ server.total_movies || 0 }}</div>
        </v-col>
        <v-col cols="6">
          <div class="text-caption text-medium-emphasis">剧集</div>
          <div class="text-body-1 font-weight-bold">{{ server.total_tv_shows || 0 }}</div>
        </v-col>
      </v-row>

      <div v-if="server.last_sync" class="mt-2">
        <div class="text-caption text-medium-emphasis">最后同步</div>
        <div class="text-body-2">{{ formatDateTime(server.last_sync) }}</div>
      </div>
    </v-card-text>

    <v-card-actions>
      <v-btn
        variant="text"
        size="small"
        prepend-icon="mdi-eye"
        @click="$emit('view-details', server.id)"
      >
        详情
      </v-btn>
      <v-spacer></v-spacer>
      <v-btn
        variant="text"
        size="small"
        prepend-icon="mdi-pencil"
        @click="$emit('edit', server)"
      >
        编辑
      </v-btn>
      <v-btn
        variant="text"
        size="small"
        prepend-icon="mdi-delete"
        color="error"
        @click="$emit('delete', server.id)"
      >
        删除
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
defineProps<{
  server: any
}>()

defineEmits<{
  edit: [server: any]
  delete: [id: number]
  check: [id: number]
  sync: [id: number, type: 'libraries' | 'metadata']
  'view-details': [id: number]
  refresh: []
}>()

// 获取服务器类型颜色
const getServerTypeColor = (type: string): string => {
  switch (type.toLowerCase()) {
    case 'plex':
      return 'orange'
    case 'jellyfin':
      return 'purple'
    case 'emby':
      return 'blue'
    default:
      return 'grey'
  }
}

// 获取服务器类型图标
const getServerTypeIcon = (type: string): string => {
  switch (type.toLowerCase()) {
    case 'plex':
      return 'mdi-play-circle'
    case 'jellyfin':
      return 'mdi-movie-open'
    case 'emby':
      return 'mdi-television'
    default:
      return 'mdi-server'
  }
}

// 获取服务器类型文本
const getServerTypeText = (type: string): string => {
  switch (type.toLowerCase()) {
    case 'plex':
      return 'Plex'
    case 'jellyfin':
      return 'Jellyfin'
    case 'emby':
      return 'Emby'
    default:
      return type
  }
}

// 获取状态颜色
const getStatusColor = (status: string): string => {
  switch (status) {
    case 'online':
      return 'success'
    case 'offline':
      return 'error'
    case 'error':
      return 'error'
    default:
      return 'grey'
  }
}

// 获取状态文本
const getStatusText = (status: string): string => {
  switch (status) {
    case 'online':
      return '在线'
    case 'offline':
      return '离线'
    case 'error':
      return '错误'
    default:
      return '未知'
  }
}

// 格式化日期时间
const formatDateTime = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}
</script>

<style scoped>
.v-card {
  height: 100%;
}
</style>

