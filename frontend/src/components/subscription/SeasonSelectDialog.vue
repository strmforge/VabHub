<template>
  <v-dialog
    v-model="modelValue"
    max-width="800"
    scrollable
    persistent
  >
    <v-card>
      <v-card-item class="py-3">
        <template #prepend>
          <v-icon icon="mdi-television" class="me-2" />
        </template>
        <v-card-title class="text-h6">
          选择订阅季
        </v-card-title>
        <v-card-subtitle>
          {{ media?.title || '电视剧' }}
        </v-card-subtitle>
        <template #append>
          <v-btn
            icon="mdi-close"
            variant="text"
            size="small"
            @click="modelValue = false"
          />
        </template>
      </v-card-item>

      <v-card-text class="pa-4">
        <!-- 加载中 -->
        <div v-if="loading" class="text-center py-12">
          <v-progress-circular indeterminate color="primary" size="64" />
          <div class="mt-4 text-body-1 text-medium-emphasis">加载季信息...</div>
        </div>

        <!-- 季列表 -->
        <div v-else-if="seasons.length > 0">
          <v-list class="season-list">
            <v-list-item
              v-for="season in seasons"
              :key="season.season_number"
              :value="season.season_number"
              @click="toggleSeason(season.season_number)"
              class="season-item"
              :class="{ 'season-selected': selectedSeasons.includes(season.season_number) }"
            >
              <template #prepend>
                <v-checkbox
                  :model-value="selectedSeasons.includes(season.season_number)"
                  @update:model-value="toggleSeason(season.season_number)"
                  @click.stop
                  class="me-2"
                />
                <v-avatar
                  size="72"
                  class="me-3"
                  rounded="lg"
                >
                  <v-img
                    v-if="season.poster_path"
                    :src="getSeasonPosterUrl(season.poster_path)"
                    cover
                  />
                  <v-icon v-else size="40">mdi-television</v-icon>
                </v-avatar>
              </template>

              <v-list-item-title class="font-weight-bold text-h6 mb-1">
                第 {{ season.season_number }} 季
                <span v-if="season.name" class="text-body-2 font-weight-normal text-medium-emphasis ms-2">
                  {{ season.name }}
                </span>
              </v-list-item-title>

              <v-list-item-subtitle class="mt-2">
                <div class="d-flex align-center flex-wrap ga-2 mb-2">
                  <v-chip
                    v-if="season.vote_average"
                    size="small"
                    color="primary"
                    variant="flat"
                  >
                    <v-icon start size="small">mdi-star</v-icon>
                    {{ season.vote_average.toFixed(1) }}
                  </v-chip>
                  <v-chip
                    v-if="season.episode_count"
                    size="small"
                    variant="outlined"
                  >
                    {{ season.episode_count }} 集
                  </v-chip>
                  <span v-if="season.air_date" class="text-body-2 text-medium-emphasis">
                    {{ formatDate(season.air_date) }}
                  </span>
                </div>
                <div v-if="season.overview" class="text-body-2 text-medium-emphasis line-clamp-2">
                  {{ season.overview }}
                </div>
              </v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </div>

        <!-- 无数据 -->
        <div v-else class="text-center py-12">
          <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-television-off</v-icon>
          <div class="text-h6 text-medium-emphasis mb-2">未找到季信息</div>
          <div class="text-body-2 text-medium-emphasis">请稍后重试</div>
        </div>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn @click="modelValue = false">取消</v-btn>
        <v-btn
          color="primary"
          :disabled="selectedSeasons.length === 0"
          @click="handleConfirm"
        >
          确认选择 ({{ selectedSeasons.length }})
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import api from '@/services/api'

interface Props {
  modelValue: boolean
  media: any
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'confirm': [seasons: number[]]
}>()

const loading = ref(false)
const seasons = ref<any[]>([])
const selectedSeasons = ref<number[]>([])

const modelValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 加载季信息
const loadSeasons = async () => {
  if (!props.media?.tmdb_id) return

  loading.value = true
  try {
    const response = await api.get(`/media/seasons/${props.media.tmdb_id}`)
    seasons.value = response.data || []
  } catch (error: any) {
    console.error('加载季信息失败:', error)
    seasons.value = []
  } finally {
    loading.value = false
  }
}

// 切换季选择
const toggleSeason = (seasonNumber: number) => {
  const index = selectedSeasons.value.indexOf(seasonNumber)
  if (index > -1) {
    selectedSeasons.value.splice(index, 1)
  } else {
    selectedSeasons.value.push(seasonNumber)
  }
}

// 确认选择
const handleConfirm = () => {
  if (selectedSeasons.value.length > 0) {
    emit('confirm', selectedSeasons.value)
    modelValue.value = false
  }
}

// 获取季海报URL
const getSeasonPosterUrl = (posterPath: string | null) => {
  if (!posterPath) return '/placeholder-poster.jpg'
  if (posterPath.startsWith('http')) return posterPath
  return `https://image.tmdb.org/t/p/w500${posterPath}`
}

// 格式化日期
const formatDate = (date: string) => {
  if (!date) return ''
  const d = new Date(date)
  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

// 监听对话框打开
watch(() => props.modelValue, (newVal) => {
  if (newVal && props.media) {
    selectedSeasons.value = []
    loadSeasons()
  }
})
</script>

<style scoped lang="scss">
.season-list {
  background: transparent;
}

.season-item {
  border-radius: 8px;
  margin-bottom: 8px;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(var(--v-theme-primary), 0.1);
  }
}

.season-selected {
  background: rgba(var(--v-theme-primary), 0.15);
  border: 1px solid rgba(var(--v-theme-primary), 0.3);
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>

