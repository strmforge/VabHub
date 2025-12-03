<template>
  <div class="music-page">
    <PageHeader
      title="音乐管理"
      subtitle="多平台音乐搜索、订阅、榜单和库管理"
    />
    
    <!-- 标签页导航 -->
    <v-card class="mb-4">
      <v-tabs v-model="activeTab" bg-color="primary" slider-color="white">
        <v-tab value="library">
          <v-icon start>mdi-music-box-multiple</v-icon>
          音乐库
        </v-tab>
        <v-tab value="search">
          <v-icon start>mdi-magnify</v-icon>
          搜索
        </v-tab>
        <v-tab value="charts">
          <v-icon start>mdi-chart-line</v-icon>
          榜单
        </v-tab>
        <v-tab value="subscriptions">
          <v-icon start>mdi-bookmark-multiple</v-icon>
          订阅
        </v-tab>
        <v-tab value="recommendations">
          <v-icon start>mdi-lightbulb-on</v-icon>
          推荐
        </v-tab>
      </v-tabs>
    </v-card>
    
    <!-- 标签页内容 -->
    <v-window v-model="activeTab">
      <v-window-item value="library">
        <MusicLibrary />
      </v-window-item>

      <v-window-item value="search">
        <MusicSearch />
      </v-window-item>

      <v-window-item value="charts">
        <MusicCharts @subscription-created="handleSubscriptionCreated" />
      </v-window-item>

      <v-window-item value="subscriptions">
        <MusicSubscriptions ref="musicSubscriptionsRef" />
      </v-window-item>

      <v-window-item value="recommendations">
        <MusicRecommendations />
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import MusicLibrary from '@/components/music/MusicLibrary.vue'
import MusicSearch from '@/components/music/MusicSearch.vue'
import MusicCharts from '@/components/music/MusicCharts.vue'
import MusicSubscriptions from '@/components/music/MusicSubscriptions.vue'
import MusicRecommendations from '@/components/music/MusicRecommendations.vue'

const activeTab = ref('library')
const musicSubscriptionsRef = ref<InstanceType<typeof MusicSubscriptions> | null>(null)

const handleSubscriptionCreated = () => {
  musicSubscriptionsRef.value?.reload?.()
}
</script>

<style scoped>
.music-page {
  padding: 24px;
}
</style>

