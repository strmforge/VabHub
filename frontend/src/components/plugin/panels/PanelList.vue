<template>
  <v-data-table
    v-if="columns.length > 0"
    :headers="tableHeaders"
    :items="rows"
    :items-per-page="10"
    density="compact"
    class="elevation-0"
  >
    <template v-for="col in columns" :key="col.key" #[`item.${col.key}`]="{ item }">
      <span>{{ item[col.key] }}</span>
    </template>
  </v-data-table>
  <v-alert v-else type="info" variant="tonal">
    暂无数据
  </v-alert>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ListColumn } from '@/types/pluginPanels'

const props = defineProps<{
  payload: {
    columns: ListColumn[]
    rows: Record<string, any>[]
    total?: number
  }
  config?: Record<string, any>
}>()

const columns = computed(() => props.payload?.columns || [])
const rows = computed(() => props.payload?.rows || [])

const tableHeaders = computed(() => {
  return columns.value.map(col => ({
    title: col.title,
    key: col.key,
    width: col.width,
    align: (col.align || 'start') as 'start' | 'center' | 'end',
    sortable: true,
  }))
})
</script>
