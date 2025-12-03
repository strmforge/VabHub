<template>
  <div class="skeleton-list">
    <v-row v-if="variant === 'grid'" dense>
      <v-col
        v-for="i in count"
        :key="i"
        :cols="cols"
        :sm="sm"
        :md="md"
        :lg="lg"
      >
        <v-skeleton-loader
          :type="type"
          :loading="true"
          class="skeleton-item"
        />
      </v-col>
    </v-row>
    
    <template v-else-if="variant === 'list'">
      <v-skeleton-loader
        v-for="i in count"
        :key="i"
        :type="type"
        :loading="true"
        class="skeleton-item mb-2"
      />
    </template>
    
    <template v-else>
      <v-skeleton-loader
        v-for="i in count"
        :key="i"
        :type="type"
        :loading="true"
        class="skeleton-item"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
/**
 * 骨架屏列表组件
 * UX-2 U4-1 实现
 */

withDefaults(defineProps<{
  count?: number
  type?: string
  variant?: 'grid' | 'list' | 'default'
  cols?: number | string
  sm?: number | string
  md?: number | string
  lg?: number | string
}>(), {
  count: 4,
  type: 'card',
  variant: 'grid',
  cols: 12,
  sm: 6,
  md: 4,
  lg: 3,
})
</script>

<style scoped>
.skeleton-list {
  width: 100%;
}

.skeleton-item {
  border-radius: 8px;
}
</style>
