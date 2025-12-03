<template>
  <v-row dense>
    <v-col
      v-for="(card, index) in cards"
      :key="index"
      :cols="12"
      :sm="6"
      :md="colsMd"
    >
      <v-card
        variant="outlined"
        class="pa-3 h-100"
      >
        <div class="d-flex align-center">
          <v-icon
            v-if="card.icon"
            :color="card.color || 'primary'"
            size="32"
            class="mr-3"
          >
            {{ card.icon }}
          </v-icon>
          <div class="flex-grow-1">
            <div class="text-caption text-medium-emphasis">{{ card.label }}</div>
            <div class="d-flex align-center">
              <span class="text-h5 font-weight-bold">{{ card.value }}</span>
              <span v-if="card.unit" class="text-body-2 text-medium-emphasis ml-1">{{ card.unit }}</span>
              <v-icon
                v-if="card.trend"
                :color="trendColor(card.trend)"
                size="small"
                class="ml-2"
              >
                {{ trendIcon(card.trend) }}
              </v-icon>
            </div>
          </div>
        </div>
      </v-card>
    </v-col>
  </v-row>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { MetricCard } from '@/types/pluginPanels'

const props = defineProps<{
  payload: { cards: MetricCard[] }
  config?: { cols?: number }
}>()

const cards = computed(() => props.payload?.cards || [])
const colsMd = computed(() => {
  const cols = props.config?.cols || 3
  return Math.floor(12 / cols)
})

function trendColor(trend: string): string {
  if (trend === 'up') return 'success'
  if (trend === 'down') return 'error'
  return 'grey'
}

function trendIcon(trend: string): string {
  if (trend === 'up') return 'mdi-arrow-up'
  if (trend === 'down') return 'mdi-arrow-down'
  return 'mdi-minus'
}
</script>
