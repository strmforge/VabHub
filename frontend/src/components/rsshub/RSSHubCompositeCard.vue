<template>
  <v-card
    variant="outlined"
    class="rsshub-composite-card"
    :class="{ 'rsshub-composite-enabled': enabled }"
  >
    <v-card-text class="pa-3">
      <!-- 标题和开关 -->
      <div class="d-flex align-center justify-space-between mb-2">
        <div class="text-subtitle-2 font-weight-medium flex-grow-1">
          {{ composite.name }}
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
          :color="getTypeColor(composite.type)"
          size="x-small"
          variant="flat"
        >
          {{ getTypeText(composite.type) }}
        </v-chip>
        <v-chip
          size="x-small"
          variant="outlined"
          color="info"
        >
          组合
        </v-chip>
        <v-chip
          v-if="composite.sources && composite.sources.length > 0"
          size="x-small"
          variant="text"
          color="grey"
        >
          {{ composite.sources.length }} 个源
        </v-chip>
      </div>
      
      <!-- 描述 -->
      <div
        v-if="composite.description"
        class="text-caption text-medium-emphasis mb-2 line-clamp-2"
      >
        {{ composite.description }}
      </div>
      
      <!-- 包含的源列表（折叠） -->
      <v-expansion-panels v-if="composite.sources && composite.sources.length > 0" variant="accordion" class="mt-2">
        <v-expansion-panel>
          <v-expansion-panel-title class="text-caption">
            查看包含的源 ({{ composite.sources.length }})
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-chip
              v-for="sourceId in composite.sources"
              :key="sourceId"
              size="x-small"
              variant="outlined"
              class="ma-1"
            >
              {{ sourceId }}
            </v-chip>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
      
      <!-- 状态指示 -->
      <div class="d-flex align-center justify-end mt-2">
        <v-icon
          v-if="enabled"
          size="16"
          color="success"
        >
          mdi-check-circle
        </v-icon>
        <span v-else class="text-caption text-medium-emphasis">已禁用</span>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
interface Props {
  composite: {
    id: string
    name: string
    type: string
    description?: string
    sources?: string[]
    enabled: boolean
  }
  enabled: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  toggle: [compositeId: string, enabled: boolean]
}>()

const handleToggle = (value: boolean) => {
  emit('toggle', props.composite.id, value)
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
.rsshub-composite-card {
  transition: all 0.2s ease;
  height: 100%;
  
  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
  }
  
  &.rsshub-composite-enabled {
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

