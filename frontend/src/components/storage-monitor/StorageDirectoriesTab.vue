<template>
  <div>
    <!-- 目录列表 -->
    <v-row v-if="directories.length > 0">
      <v-col
        v-for="directory in directories"
        :key="directory.id"
        cols="12"
        md="6"
        lg="4"
      >
        <StorageDirectoryCard
          :directory="directory"
          @edit="$emit('edit', directory)"
          @delete="$emit('delete', directory.id)"
        />
      </v-col>
    </v-row>

    <!-- 空状态 -->
    <v-alert
      v-else-if="!loading"
      type="info"
      variant="tonal"
      class="mt-4"
    >
      还没有配置存储目录，点击"添加存储目录"按钮开始配置。
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
  directories: any[]
  loading: boolean
}>()

defineEmits<{
  edit: [directory: any]
  delete: [id: number]
  refresh: []
}>()
</script>

