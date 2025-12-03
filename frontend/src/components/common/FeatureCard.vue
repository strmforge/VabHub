<template>
  <v-card
    class="feature-card"
    :to="to"
    @click="$emit('click')"
  >
    <v-card-text class="text-center pa-6">
      <v-avatar
        :color="color"
        size="64"
        class="mb-4"
      >
        <v-icon size="32" color="white">{{ icon }}</v-icon>
      </v-avatar>
      
      <h3 class="text-h6 font-weight-bold mb-2">{{ title }}</h3>
      <p class="text-body-2 text-medium-emphasis mb-0">
        {{ description }}
      </p>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
interface Props {
  icon: string
  title: string
  description: string
  color?: string
  to?: any
}

withDefaults(defineProps<Props>(), {
  color: 'primary'
})
</script>

<style lang="scss" scoped>
.feature-card {
  transition: var(--vabhub-transition);
  height: 100%;
  cursor: pointer;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: var(--vabhub-shadow-lg);
  }
}
</style>

