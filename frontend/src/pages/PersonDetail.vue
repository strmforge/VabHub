<template>
  <div class="person-detail-page">
    <!-- 加载状态 -->
    <div v-if="loading" class="d-flex justify-center align-center" style="min-height: 400px">
      <v-progress-circular indeterminate color="primary" size="64" />
    </div>

    <!-- 错误状态 -->
    <v-alert v-else-if="error" type="error" class="ma-4">
      {{ error }}
    </v-alert>

    <!-- 人物详情 -->
    <div v-else-if="personDetails">
      <v-container fluid>
        <v-row>
          <!-- 左侧：照片和基本信息 -->
          <v-col cols="12" md="4">
            <v-card class="person-photo-card" elevation="4">
              <v-img
                :src="personDetails.profile_path || '/placeholder-person.jpg'"
                aspect-ratio="2/3"
                cover
                class="person-photo"
              >
                <template #placeholder>
                  <v-skeleton-loader type="image" />
                </template>
              </v-img>
            </v-card>

            <!-- 基本信息 -->
            <v-card class="mt-4">
              <v-card-title>基本信息</v-card-title>
              <v-card-text>
                <v-list>
                  <v-list-item v-if="personDetails.birthday">
                    <v-list-item-title>生日</v-list-item-title>
                    <v-list-item-subtitle>{{ formatDate(personDetails.birthday) }}</v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item v-if="personDetails.place_of_birth">
                    <v-list-item-title>出生地</v-list-item-title>
                    <v-list-item-subtitle>{{ personDetails.place_of_birth }}</v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item v-if="personDetails.known_for_department">
                    <v-list-item-title>职业</v-list-item-title>
                    <v-list-item-subtitle>{{ personDetails.known_for_department }}</v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item v-if="personDetails.deathday">
                    <v-list-item-title>逝世日期</v-list-item-title>
                    <v-list-item-subtitle>{{ formatDate(personDetails.deathday) }}</v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-card-text>
            </v-card>
          </v-col>

          <!-- 右侧：详细信息 -->
          <v-col cols="12" md="8">
            <!-- 姓名和简介 -->
            <div class="person-header mb-6">
              <h1 class="text-h3 font-weight-bold mb-2">
                {{ personDetails.name }}
              </h1>
              <div v-if="personDetails.biography" class="text-body-1 mt-4">
                <p class="text-medium-emphasis">{{ personDetails.biography }}</p>
              </div>
            </div>

            <!-- 标签页 -->
            <v-tabs v-model="activeTab" class="mb-4">
              <v-tab value="movies">电影作品</v-tab>
              <v-tab value="tv">电视剧作品</v-tab>
            </v-tabs>

            <v-window v-model="activeTab">
              <!-- 电影作品 -->
              <v-window-item value="movies">
                <div v-if="personDetails.movies && personDetails.movies.length > 0">
                  <v-row>
                    <v-col
                      v-for="movie in personDetails.movies"
                      :key="movie.id"
                      cols="6"
                      sm="4"
                      md="3"
                      lg="2"
                    >
                      <v-card
                        class="work-card"
                        @click="goToMedia(movie.id, 'movie')"
                        style="cursor: pointer"
                      >
                        <v-img
                          :src="movie.poster_path || '/placeholder-poster.jpg'"
                          aspect-ratio="2/3"
                          cover
                        >
                          <template #placeholder>
                            <v-skeleton-loader type="image" />
                          </template>
                        </v-img>
                        <v-card-text class="pa-2">
                          <div class="text-body-2 font-weight-bold text-truncate">
                            {{ movie.title }}
                          </div>
                          <div v-if="movie.character" class="text-caption text-medium-emphasis text-truncate">
                            {{ movie.character }}
                          </div>
                          <div v-if="movie.release_date" class="text-caption text-medium-emphasis">
                            {{ getYear(movie.release_date) }}
                          </div>
                        </v-card-text>
                      </v-card>
                    </v-col>
                  </v-row>
                </div>
                <v-alert v-else type="info">暂无电影作品</v-alert>
              </v-window-item>

              <!-- 电视剧作品 -->
              <v-window-item value="tv">
                <div v-if="personDetails.tv_shows && personDetails.tv_shows.length > 0">
                  <v-row>
                    <v-col
                      v-for="tv in personDetails.tv_shows"
                      :key="tv.id"
                      cols="6"
                      sm="4"
                      md="3"
                      lg="2"
                    >
                      <v-card
                        class="work-card"
                        @click="goToMedia(tv.id, 'tv')"
                        style="cursor: pointer"
                      >
                        <v-img
                          :src="tv.poster_path || '/placeholder-poster.jpg'"
                          aspect-ratio="2/3"
                          cover
                        >
                          <template #placeholder>
                            <v-skeleton-loader type="image" />
                          </template>
                        </v-img>
                        <v-card-text class="pa-2">
                          <div class="text-body-2 font-weight-bold text-truncate">
                            {{ tv.name }}
                          </div>
                          <div v-if="tv.character" class="text-caption text-medium-emphasis text-truncate">
                            {{ tv.character }}
                          </div>
                          <div v-if="tv.first_air_date" class="text-caption text-medium-emphasis">
                            {{ getYear(tv.first_air_date) }}
                          </div>
                        </v-card-text>
                      </v-card>
                    </v-col>
                  </v-row>
                </div>
                <v-alert v-else type="info">暂无电视剧作品</v-alert>
              </v-window-item>
            </v-window>
          </v-col>
        </v-row>
      </v-container>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import { mediaApi } from '@/services/api'

const route = useRoute()
const router = useRouter()
const toast = useToast()

// 路由参数
const personId = computed(() => parseInt(route.params.personId as string))

// 状态
const loading = ref(true)
const error = ref<string | null>(null)
const personDetails = ref<any>(null)

// 标签页
const activeTab = ref('movies')

// 加载人物详情
const loadPersonDetails = async () => {
  try {
    loading.value = true
    error.value = null
    
    const response = await mediaApi.getPersonDetails(personId.value)
    personDetails.value = response.data
  } catch (err: any) {
    const errMsg = err.message || '加载人物详情失败'
    error.value = errMsg
    toast.error(errMsg)
  } finally {
    loading.value = false
  }
}

// 跳转到媒体详情
const goToMedia = (id: number, type: string) => {
  router.push(`/media/${type}/${id}`)
}

// 格式化日期
const formatDate = (date: string) => {
  if (!date) return ''
  return new Date(date).toLocaleDateString('zh-CN')
}

// 获取年份
const getYear = (date: string) => {
  if (!date) return ''
  return new Date(date).getFullYear().toString()
}

// 初始化
onMounted(() => {
  loadPersonDetails()
})
</script>

<style scoped lang="scss">
.person-detail-page {
  min-height: 100vh;
}

.person-photo-card {
  position: sticky;
  top: 20px;
}

.person-photo {
  border-radius: 8px;
}

.work-card {
  transition: transform 0.2s ease;
  
  &:hover {
    transform: translateY(-4px);
  }
}
</style>

