<template>
  <v-card>
    <v-card-title class="d-flex align-center">
      <v-icon :color="directory.enabled ? 'success' : 'grey'" class="mr-2">
        {{ directory.enabled ? 'mdi-folder-check' : 'mdi-folder-cancel' }}
      </v-icon>
      <span class="text-h6">{{ directory.name }}</span>
      <v-spacer></v-spacer>
      <v-chip
        :color="directory.enabled ? 'success' : 'grey'"
        size="small"
        variant="flat"
      >
        {{ directory.enabled ? '启用' : '禁用' }}
      </v-chip>
    </v-card-title>

    <v-card-text>
      <div class="mb-2">
        <div class="text-caption text-medium-emphasis">路径</div>
        <div class="text-body-2">{{ directory.path }}</div>
      </div>

      <div class="mb-2" v-if="directory.description">
        <div class="text-caption text-medium-emphasis">描述</div>
        <div class="text-body-2">{{ directory.description }}</div>
      </div>

      <div>
        <div class="text-caption text-medium-emphasis">预警阈值</div>
        <div class="text-body-2">{{ directory.alert_threshold }}%</div>
      </div>
    </v-card-text>

    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn
        variant="text"
        size="small"
        prepend-icon="mdi-pencil"
        @click="$emit('edit', directory)"
      >
        编辑
      </v-btn>
      <v-btn
        variant="text"
        size="small"
        prepend-icon="mdi-delete"
        color="error"
        @click="$emit('delete', directory.id)"
      >
        删除
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
defineProps<{
  directory: any
}>()

defineEmits<{
  edit: [directory: any]
  delete: [id: number]
}>()
</script>

<style scoped>
.v-card {
  height: 100%;
}
</style>

