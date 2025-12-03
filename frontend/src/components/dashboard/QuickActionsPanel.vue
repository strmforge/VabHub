<template>
  <v-card>
    <v-card-title>快速操作</v-card-title>
    <v-card-text>
      <v-row>
        <v-col
          v-for="action in quickActions"
          :key="action.id"
          cols="6"
          sm="4"
        >
          <v-btn
            :prepend-icon="action.icon"
            :color="action.color"
            variant="outlined"
            block
            @click="handleAction(action)"
          >
            {{ action.title }}
          </v-btn>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const quickActions = [
  { id: 1, title: '创建订阅', icon: 'mdi-plus', color: 'primary', route: 'Subscriptions' },
  { id: 2, title: '搜索资源', icon: 'mdi-magnify', color: 'primary', route: 'Search' },
  { id: 3, title: '音乐订阅', icon: 'mdi-music', color: 'purple', route: 'MusicSubscriptions' },
  { id: 4, title: 'AI推荐', icon: 'mdi-lightbulb-on', color: 'orange', route: 'Recommendations' },
  { id: 5, title: '站点管理', icon: 'mdi-web', color: 'info', route: 'Sites' },
  { id: 6, title: '插件市场', icon: 'mdi-puzzle', color: 'success', route: 'Plugins' }
]

const handleAction = (action: any) => {
  if (action.route) {
    router.push({ name: action.route })
  }
}
</script>

