<template>
  <v-dialog
    v-model="dialog"
    max-width="900"
    scrollable
  >
    <v-card v-if="animeDetail" class="bangumi-detail-dialog">
      <!-- 头部 -->
      <v-card-title class="d-flex align-center justify-space-between">
        <span class="text-h5">{{ animeDetail.name_cn || animeDetail.name }}</span>
        <v-btn
          icon="mdi-close"
          variant="text"
          @click="dialog = false"
        />
      </v-card-title>

      <v-divider />

      <v-card-text class="pa-0">
        <v-container fluid>
          <v-row>
            <!-- 左侧：封面和基本信息 -->
            <v-col cols="12" md="4">
              <v-img
                :src="getImage(animeDetail.images)"
                aspect-ratio="2/3"
                cover
                class="mb-4"
              >
                <template #placeholder>
                  <v-skeleton-loader type="image" />
                </template>
              </v-img>

              <!-- 基本信息 -->
              <v-card variant="outlined">
                <v-card-title class="text-subtitle-1">基本信息</v-card-title>
                <v-card-text>
                  <v-list density="compact">
                    <v-list-item v-if="animeDetail.date">
                      <v-list-item-title>放送日期</v-list-item-title>
                      <v-list-item-subtitle>{{ animeDetail.date }}</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item v-if="animeDetail.rating && animeDetail.rating.score">
                      <v-list-item-title>评分</v-list-item-title>
                      <v-list-item-subtitle>
                        <v-rating
                          :model-value="animeDetail.rating.score / 2"
                          readonly
                          half-increments
                          density="compact"
                          color="warning"
                        />
                        <span class="ms-2">{{ animeDetail.rating.score }}</span>
                        <span v-if="animeDetail.rating.total" class="text-caption text-medium-emphasis ms-2">
                          ({{ animeDetail.rating.total }}人评分)
                        </span>
                      </v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item v-if="animeDetail.eps">
                      <v-list-item-title>集数</v-list-item-title>
                      <v-list-item-subtitle>{{ animeDetail.eps }} 集</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item v-if="animeDetail.url">
                      <v-list-item-title>Bangumi链接</v-list-item-title>
                      <v-list-item-subtitle>
                        <a :href="animeDetail.url" target="_blank" class="text-primary">
                          查看详情
                          <v-icon size="small" class="ms-1">mdi-open-in-new</v-icon>
                        </a>
                      </v-list-item-subtitle>
                    </v-list-item>
                  </v-list>
                </v-card-text>
              </v-card>
            </v-col>

            <!-- 右侧：详细信息 -->
            <v-col cols="12" md="8">
              <!-- 简介 -->
              <v-card variant="outlined" class="mb-4">
                <v-card-title class="text-subtitle-1">简介</v-card-title>
                <v-card-text>
                  <p v-if="animeDetail.summary" class="text-body-2">
                    {{ animeDetail.summary }}
                  </p>
                  <p v-else class="text-body-2 text-medium-emphasis">
                    暂无简介
                  </p>
                </v-card-text>
              </v-card>

              <!-- 标签 -->
              <v-card v-if="animeDetail.tags && animeDetail.tags.length > 0" variant="outlined" class="mb-4">
                <v-card-title class="text-subtitle-1">标签</v-card-title>
                <v-card-text>
                  <div class="d-flex flex-wrap gap-2">
                    <v-chip
                      v-for="tag in animeDetail.tags"
                      :key="tag.name"
                      size="small"
                      variant="outlined"
                    >
                      {{ tag.name }}
                    </v-chip>
                  </div>
                </v-card-text>
              </v-card>

              <!-- 角色（如果有） -->
              <v-card v-if="animeDetail.characters && animeDetail.characters.length > 0" variant="outlined" class="mb-4">
                <v-card-title class="text-subtitle-1">主要角色</v-card-title>
                <v-card-text>
                  <v-row>
                    <v-col
                      v-for="character in animeDetail.characters.slice(0, 6)"
                      :key="character.id"
                      cols="6"
                      sm="4"
                    >
                      <v-card variant="outlined">
                        <v-card-text class="pa-2">
                          <div class="text-body-2 font-weight-medium">
                            {{ character.name }}
                          </div>
                          <div v-if="character.actors && character.actors.length > 0" class="text-caption text-medium-emphasis">
                            CV: {{ character.actors[0].name }}
                          </div>
                        </v-card-text>
                      </v-card>
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </v-container>
      </v-card-text>

      <v-divider />

      <v-card-actions>
        <v-spacer />
        <v-btn
          variant="text"
          @click="dialog = false"
        >
          关闭
        </v-btn>
        <v-btn
          v-if="animeDetail.url"
          color="primary"
          prepend-icon="mdi-open-in-new"
          :href="animeDetail.url"
          target="_blank"
        >
          在Bangumi查看
        </v-btn>
      </v-card-actions>
    </v-card>

    <!-- 加载状态 -->
    <v-card v-else>
      <v-card-text class="d-flex justify-center align-center" style="min-height: 400px">
        <v-progress-circular indeterminate color="primary" size="64" />
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { bangumiApi } from '@/services/api'
import { useToast } from 'vue-toastification'

const props = defineProps<{
  modelValue: boolean
  subjectId: number | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const toast = useToast()
const dialog = ref(props.modelValue)
const animeDetail = ref<any>(null)
const loading = ref(false)

// 监听dialog变化
watch(() => props.modelValue, (newVal) => {
  dialog.value = newVal
  if (newVal && props.subjectId) {
    loadAnimeDetail()
  }
})

// 监听dialog关闭
watch(dialog, (newVal) => {
  emit('update:modelValue', newVal)
  if (!newVal) {
    animeDetail.value = null
  }
})

// 监听subjectId变化
watch(() => props.subjectId, (newId) => {
  if (newId && dialog.value) {
    loadAnimeDetail()
  }
})

// 加载动漫详情
const loadAnimeDetail = async () => {
  if (!props.subjectId) return

  try {
    loading.value = true
    const response = await bangumiApi.getAnimeDetail(props.subjectId)
    animeDetail.value = response.data
  } catch (err: any) {
    console.error('加载Bangumi详情失败:', err)
    toast.error('加载详情失败: ' + (err.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 获取图片
const getImage = (images: any) => {
  if (!images) return '/placeholder-poster.jpg'
  if (images.large) return images.large
  if (images.medium) return images.medium
  if (images.small) return images.small
  return '/placeholder-poster.jpg'
}
</script>

<style scoped lang="scss">
.bangumi-detail-dialog {
  .v-card-text {
    max-height: 70vh;
    overflow-y: auto;
  }
}
</style>

