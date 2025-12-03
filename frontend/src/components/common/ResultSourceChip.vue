<template>
  <v-chip
    v-if="source"
    :size="size"
    :color="getSourceColor(source)"
    variant="flat"
    :prepend-icon="getSourceIcon(source)"
  >
    {{ getSourceText(source) }}
  </v-chip>
</template>

<script setup lang="ts">
interface Props {
  source: 'local' | 'external' | null | undefined
  size?: 'x-small' | 'small' | 'default' | 'large'
}

const props = withDefaults(defineProps<Props>(), {
  size: 'x-small'
})

const getSourceColor = (source: string): string => {
  const colors: Record<string, string> = {
    local: 'primary',
    external: 'info'
  }
  return colors[source] || 'grey'
}

const getSourceIcon = (source: string): string => {
  const icons: Record<string, string> = {
    local: 'mdi-database',
    external: 'mdi-bridge'
  }
  return icons[source] || 'mdi-help-circle'
}

const getSourceText = (source: string): string => {
  const texts: Record<string, string> = {
    local: '本地索引',
    external: '外部索引'
  }
  return texts[source] || '未知来源'
}
</script>
