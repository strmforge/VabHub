<template>
  <v-dialog v-model="dialog" max-width="800" scrollable>
    <v-card>
      <v-card-title>
        <v-icon class="me-2">mdi-information</v-icon>
        媒体信息
      </v-card-title>
      
      <v-card-text v-if="mediaInfo">
        <v-row>
          <v-col cols="12" md="6">
            <div class="text-caption text-medium-emphasis mb-1">标题</div>
            <div class="text-h6 font-weight-bold">{{ mediaInfo.title || '-' }}</div>
          </v-col>
          
          <v-col cols="12" md="6">
            <div class="text-caption text-medium-emphasis mb-1">媒体类型</div>
            <v-chip
              :color="mediaInfo.media_type === 'movie' ? 'primary' : 'secondary'"
              size="small"
            >
              {{ mediaInfo.media_type === 'movie' ? '电影' : '电视剧' }}
            </v-chip>
          </v-col>
          
          <v-col cols="12" md="6" v-if="mediaInfo.year">
            <div class="text-caption text-medium-emphasis mb-1">年份</div>
            <div class="text-body-1">{{ mediaInfo.year }}</div>
          </v-col>
          
          <v-col cols="12" md="6" v-if="mediaInfo.quality">
            <div class="text-caption text-medium-emphasis mb-1">质量</div>
            <div class="text-body-1">{{ mediaInfo.quality }}</div>
          </v-col>
          
          <v-col cols="12" md="6" v-if="mediaInfo.resolution">
            <div class="text-caption text-medium-emphasis mb-1">分辨率</div>
            <div class="text-body-1">{{ mediaInfo.resolution }}</div>
          </v-col>
          
          <v-col cols="12" md="6" v-if="mediaInfo.codec">
            <div class="text-caption text-medium-emphasis mb-1">编码</div>
            <div class="text-body-1">{{ mediaInfo.codec }}</div>
          </v-col>
          
          <v-col cols="12" md="6" v-if="mediaInfo.season">
            <div class="text-caption text-medium-emphasis mb-1">季数</div>
            <div class="text-body-1">S{{ mediaInfo.season }}</div>
          </v-col>
          
          <v-col cols="12" md="6" v-if="mediaInfo.episode">
            <div class="text-caption text-medium-emphasis mb-1">集数</div>
            <div class="text-body-1">E{{ mediaInfo.episode }}</div>
          </v-col>
          
          <v-col cols="12" md="6" v-if="mediaInfo.episode_name">
            <div class="text-caption text-medium-emphasis mb-1">集标题</div>
            <div class="text-body-1">{{ mediaInfo.episode_name }}</div>
          </v-col>
          
          <v-col cols="12" md="6" v-if="mediaInfo.source">
            <div class="text-caption text-medium-emphasis mb-1">来源</div>
            <div class="text-body-1">{{ mediaInfo.source }}</div>
          </v-col>
          
          <v-col cols="12" md="6" v-if="mediaInfo.group">
            <div class="text-caption text-medium-emphasis mb-1">发布组</div>
            <div class="text-body-1">{{ mediaInfo.group }}</div>
          </v-col>
          
          <v-col cols="12" v-if="mediaInfo.raw_title">
            <div class="text-caption text-medium-emphasis mb-1">原始文件名</div>
            <div class="text-body-2 text-medium-emphasis">{{ mediaInfo.raw_title }}</div>
          </v-col>
        </v-row>
      </v-card-text>
      
      <v-card-text v-else class="text-center py-8">
        <v-progress-circular indeterminate color="primary" />
      </v-card-text>
      
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="close">关闭</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  modelValue: boolean
  mediaInfo: any | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const dialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const close = () => {
  dialog.value = false
}
</script>

