<template>
  <v-card
    variant="outlined"
    class="rsshub-source-card"
    :class="{ 'rsshub-source-enabled': enabled }"
  >
    <v-card-text class="pa-3">
      <!-- 标题和开关 -->
      <div class="d-flex align-center justify-space-between mb-2">
        <div class="text-subtitle-2 font-weight-medium flex-grow-1">
          {{ source.name }}
        </div>
        <v-switch
          :model-value="enabled"
          @update:model-value="handleToggle"
          color="primary"
          density="compact"
          hide-details
          class="ma-0"
        />
      </div>
      
      <!-- 类型标签 -->
      <div class="d-flex align-center ga-1 mb-2">
        <v-chip
          :color="getTypeColor(source.type)"
          size="x-small"
          variant="flat"
        >
          {{ getTypeText(source.type) }}
        </v-chip>
        <v-chip
          v-if="source.group === 'rank'"
          size="x-small"
          variant="outlined"
          color="primary"
        >
          榜单
        </v-chip>
        <v-chip
          v-else
          size="x-small"
          variant="outlined"
          color="success"
        >
          更新
        </v-chip>
      </div>
      
      <!-- 描述 -->
      <div
        v-if="source.description"
        class="text-caption text-medium-emphasis mb-2 line-clamp-2"
      >
        {{ source.description }}
      </div>
      
      <!-- 操作按钮 -->
      <div class="d-flex align-center ga-2">
        <v-btn
          size="small"
          variant="text"
          prepend-icon="mdi-eye"
          @click="handlePreview"
        >
          预览
        </v-btn>
        <v-spacer />
        <v-icon
          v-if="enabled"
          size="16"
          color="success"
        >
          mdi-check-circle
        </v-icon>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
interface Props {
  source: {
    id: string
    name: string
    type: string
    group: string
    description?: string
    enabled: boolean
  }
  enabled: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  toggle: [sourceId: string, enabled: boolean]
  preview: [sourceId: string, sourceName: string]
}>()

const handleToggle = (value: boolean) => {
  emit('toggle', props.source.id, value)
}

const handlePreview = () => {
  emit('preview', props.source.id, props.source.name)
}

const getTypeText = (type: string) => {
  const types: Record<string, string> = {
    video: '电影',
    tv: '电视剧',
    variety: '综艺',
    anime: '番剧',
    music: '音乐',
    mixed: '混合'
  }
  return types[type] || type
}

const getTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    video: 'primary',
    tv: 'info',
    variety: 'warning',
    anime: 'purple',
    music: 'pink',
    mixed: 'grey'
  }
  return colors[type] || 'grey'
}
</script>

<style scoped lang="scss">
.rsshub-source-card {
  transition: all 0.2s ease;
  height: 100%;
  
  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
  }
  
  &.rsshub-source-enabled {
    border-color: rgb(var(--v-theme-primary));
    background-color: rgba(var(--v-theme-primary), 0.05);
  }
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>

