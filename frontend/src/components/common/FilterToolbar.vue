<template>
  <v-row class="filter-toolbar mb-4" align="center">
    <slot />
    <v-col v-if="showActions" cols="auto" class="d-flex gap-2">
      <v-btn
        v-if="showReset"
        variant="outlined"
        size="small"
        @click="$emit('reset')"
      >
        <v-icon start>mdi-refresh</v-icon>
        重置
      </v-btn>
      <v-btn
        v-if="showApply"
        color="primary"
        variant="flat"
        size="small"
        @click="$emit('apply')"
      >
        <v-icon start>mdi-check</v-icon>
        应用
      </v-btn>
    </v-col>
  </v-row>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  showActions?: boolean
  showReset?: boolean
  showApply?: boolean
}>(), {
  showActions: true,
  showReset: true,
  showApply: false
})

defineEmits<{
  reset: []
  apply: []
}>()
</script>

<style scoped>
.filter-toolbar {
  flex-wrap: wrap;
}
</style>
