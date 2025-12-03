<template>
  <v-footer
    app
    color="surface"
    class="app-footer"
  >
    <v-container>
      <div class="d-flex justify-space-between align-center">
        <div class="text-caption text-medium-emphasis">
          © 2025 VabHub. All rights reserved.
        </div>
        <div class="d-flex align-center">
          <span class="text-caption mr-2">v{{ version }}</span>
          <v-chip size="x-small" color="primary" variant="flat">Beta</v-chip>
        </div>
      </div>
    </v-container>
  </v-footer>
</template>

<script setup lang="ts">
const version = '1.0.0'
</script>

<style lang="scss" scoped>
.app-footer {
  border-top: 1px solid rgba(var(--v-border-color), 0.12);
}
</style>

