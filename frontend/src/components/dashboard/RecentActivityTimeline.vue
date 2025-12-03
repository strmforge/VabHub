<template>
  <v-card>
    <v-card-title>最近活动</v-card-title>
    <v-card-text>
      <v-timeline density="compact" side="end">
        <v-timeline-item
          v-for="(activity, index) in activities"
          :key="index"
          :icon="activity.icon"
          :color="activity.color"
          size="small"
        >
          <div class="text-caption text-medium-emphasis mb-1">
            {{ formatTime(activity.timestamp) }}
          </div>
          <div class="text-body-2">{{ activity.title }}</div>
          <div v-if="activity.description" class="text-caption text-medium-emphasis">
            {{ activity.description }}
          </div>
        </v-timeline-item>
      </v-timeline>
      
      <div v-if="activities.length === 0" class="text-center text-medium-emphasis py-4">
        暂无活动
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const activities = ref([
  {
    icon: 'mdi-download',
    color: 'success',
    title: '下载完成',
    description: '电影：The Matrix',
    timestamp: Date.now() - 1000 * 60 * 5
  },
  {
    icon: 'mdi-bookmark',
    color: 'primary',
    title: '创建订阅',
    description: '电视剧：Breaking Bad',
    timestamp: Date.now() - 1000 * 60 * 30
  },
  {
    icon: 'mdi-music',
    color: 'purple',
    title: '音乐订阅',
    description: '艺术家：Taylor Swift',
    timestamp: Date.now() - 1000 * 60 * 60
  }
])

const formatTime = (timestamp: number) => {
  return dayjs(timestamp).fromNow()
}

onMounted(() => {
  // TODO: 从API获取最近活动
})
</script>

