<template>
  <div class="manga-follow-center-page">
    <PageHeader title="漫画追更中心" subtitle="查看你正在追更的本地漫画更新情况">
      <template #actions>
        <v-switch
          v-model="onlyUnread"
          hide-details
          color="primary"
          inset
          :label="onlyUnread ? '只看有更新' : '显示全部'"
          class="mr-4"
        />
        <v-btn
          color="primary"
          variant="text"
          icon="mdi-refresh"
          :loading="loading"
          @click="loadFollowing"
        />
        <v-btn
          color="success"
          class="ml-2"
          prepend-icon="mdi-check-all"
          :disabled="filteredItems.length === 0"
          :loading="markingAllRead"
          @click="handleMarkAllRead"
        >
          全部标记已读
        </v-btn>
      </template>
    </PageHeader>

    <v-container fluid>
      <div v-if="loading" class="text-center py-12">
        <v-progress-circular indeterminate color="primary" size="64" />
        <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
      </div>

      <v-alert
        v-else-if="!error && filteredItems.length === 0"
        type="info"
        variant="tonal"
        class="mt-4"
      >
        当前没有正在追更的漫画。
      </v-alert>

      <v-alert
        v-else-if="error"
        type="error"
        variant="tonal"
        class="mt-4"
      >
        {{ error }}
      </v-alert>

      <v-row v-else dense class="mt-2">
        <v-col
          v-for="item in filteredItems"
          :key="item.follow_id"
          cols="12"
          sm="6"
          md="4"
          lg="3"
        >
          <v-card class="manga-follow-card" elevation="2">
            <v-img
              :src="item.cover_url || '/placeholder-manga.jpg'"
              aspect-ratio="2/3"
              cover
              class="manga-cover"
              @click="goToReader(item)"
            >
              <template #placeholder>
                <div class="d-flex align-center justify-center fill-height">
                  <v-icon size="64" color="grey-lighten-1">mdi-book-open-page-variant</v-icon>
                </div>
              </template>
            </v-img>

            <v-card-text class="pa-3">
              <div class="text-subtitle-2 font-weight-medium text-truncate" :title="item.series_title">
                {{ item.series_title }}
              </div>
              <div class="text-caption text-medium-emphasis mt-1">
                站点 ID：{{ item.source_id }}
              </div>

              <div class="d-flex align-center justify-space-between mt-3">
                <div class="d-flex flex-column">
                  <div class="text-body-2">
                    未读章节：
                    <span :class="{ 'text-error': (item.unread_chapter_count || 0) > 0 }">
                      {{ item.unread_chapter_count || 0 }} 话
                    </span>
                  </div>
                  <div class="text-caption text-medium-emphasis mt-1">
                    最近更新：{{ formatRelativeTime(item.updated_at) }}
                  </div>
                </div>

                <div class="d-flex flex-column align-end ga-2">
                  <v-btn
                    color="primary"
                    size="small"
                    variant="flat"
                    prepend-icon="mdi-book-open-page-variant"
                    @click="goToReader(item)"
                  >
                    去阅读
                  </v-btn>
                  <v-btn
                    size="small"
                    variant="text"
                    color="success"
                    prepend-icon="mdi-check-circle"
                    :disabled="(item.unread_chapter_count || 0) === 0"
                    :loading="markingIds.has(item.series_id)"
                    @click="handleMarkRead(item)"
                  >
                    标记已读
                  </v-btn>
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { mangaFollowApi } from '@/services/api'
import type { FollowedMangaItem } from '@/types/mangaFollow'
import PageHeader from '@/components/common/PageHeader.vue'

const router = useRouter()
const toast = useToast()

const loading = ref(false)
const error = ref<string | null>(null)
const items = ref<FollowedMangaItem[]>([])
const onlyUnread = ref(false)
const markingAllRead = ref(false)
const markingIds = ref<Set<number>>(new Set())

const loadFollowing = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await mangaFollowApi.listFollowing()
    const list = response.items || []
    // 简单排序：先按是否有未读，其次按更新时间倒序
    items.value = [...list].sort((a, b) => {
      const aUnread = a.unread_chapter_count || 0
      const bUnread = b.unread_chapter_count || 0
      if (aUnread === 0 && bUnread > 0) return 1
      if (aUnread > 0 && bUnread === 0) return -1
      const aTime = new Date(a.updated_at).getTime()
      const bTime = new Date(b.updated_at).getTime()
      return bTime - aTime
    })
  } catch (err: any) {
    console.error('加载追更列表失败:', err)
    const errMsg = err.response?.data?.detail || err.message || '加载追更列表失败'
    error.value = errMsg
    toast.error(errMsg)
  } finally {
    loading.value = false
  }
}

const filteredItems = computed(() => {
  if (!onlyUnread.value) return items.value
  return items.value.filter(item => (item.unread_chapter_count || 0) > 0)
})

const goToReader = (item: FollowedMangaItem) => {
  router.push({
    name: 'MangaReaderPage',
    params: { series_id: item.series_id }
  })
}

const handleMarkRead = async (item: FollowedMangaItem) => {
  try {
    markingIds.value.add(item.series_id)
    await mangaFollowApi.markSeriesRead(String(item.series_id))
    item.unread_chapter_count = 0
    toast.success('已标记为已读')
  } catch (err: any) {
    console.error('标记已读失败:', err)
    toast.error(err.response?.data?.detail || err.message || '标记已读失败')
  } finally {
    markingIds.value.delete(item.series_id)
  }
}

const handleMarkAllRead = async () => {
  const targets = filteredItems.value.filter(item => (item.unread_chapter_count || 0) > 0)
  if (targets.length === 0) return

  markingAllRead.value = true
  try {
    for (const item of targets) {
      markingIds.value.add(item.series_id)
      try {
        await mangaFollowApi.markSeriesRead(String(item.series_id))
        item.unread_chapter_count = 0
      } catch (err: any) {
        console.error('批量标记已读失败:', err)
      } finally {
        markingIds.value.delete(item.series_id)
      }
    }
    toast.success('已将可见项目全部标记为已读')
  } finally {
    markingAllRead.value = false
  }
}

const formatRelativeTime = (dateStr: string): string => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins} 分钟前`
  if (diffHours < 24) return `${diffHours} 小时前`
  if (diffDays === 1) return '昨天'
  if (diffDays < 7) return `${diffDays} 天前`
  return date.toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadFollowing()
})
</script>

<style scoped lang="scss">
.manga-follow-center-page {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.manga-follow-card {
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2) !important;
  }

  .manga-cover {
    border-radius: 4px 4px 0 0;
  }
}
</style>
