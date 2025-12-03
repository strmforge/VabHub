<template>
  <div class="not-found-page text-center">
    <v-container>
      <v-row justify="center" align="center" class="fill-height">
        <v-col cols="12" md="6">
          <div class="mb-8">
            <VabHubLogo :size="120" :show-text="true" :glow="true" variant="dark" />
          </div>
          <h1 class="text-h1 font-weight-bold mb-4">404</h1>
          <h2 class="text-h4 mb-4">页面未找到</h2>
          <p class="text-body-1 text-medium-emphasis mb-6">
            抱歉，您访问的页面不存在
          </p>
          <v-btn
            color="primary"
            size="large"
            prepend-icon="mdi-home"
            to="/dashboard"
          >
            返回首页
          </v-btn>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import VabHubLogo from '@/components/common/VabHubLogo.vue'
</script>

<style lang="scss" scoped>
.not-found-page {
  min-height: 100vh;
}
</style>

