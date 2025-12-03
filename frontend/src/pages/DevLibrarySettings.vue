<template>
  <div class="library-settings-page">
    <v-container>
      <!-- 标题区 -->
      <v-card class="mb-6">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="primary">mdi-cog</v-icon>
          <span>媒体库与 Inbox 设置总览</span>
          <v-chip size="small" color="primary" class="ml-2">开发工具</v-chip>
        </v-card-title>
        <v-card-subtitle>
          这里是统一 Inbox 和各媒体库根目录的只读总览。
          配置来源于服务端环境变量 / 配置文件，当前页面不支持修改。
        </v-card-subtitle>
      </v-card>

      <!-- 加载状态 -->
      <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-4"></v-progress-linear>

      <!-- 错误提示 -->
      <v-alert v-if="errorMessage" type="error" class="mb-4">
        {{ errorMessage }}
      </v-alert>

      <!-- 内容区域 -->
      <v-row v-if="settings">
        <!-- Inbox 设置卡片 -->
        <v-col cols="12" md="6">
          <v-card>
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2" color="warning">mdi-inbox</v-icon>
              <span>收件箱（Inbox）配置</span>
            </v-card-title>
            <v-divider />
            <v-card-text>
              <v-list density="compact">
                <v-list-item>
                  <v-list-item-title>INBOX_ROOT</v-list-item-title>
                  <v-list-item-subtitle class="text-wrap">
                    {{ settings.inbox.inbox_root }}
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item>
                  <v-list-item-title>启用状态</v-list-item-title>
                  <template v-slot:append>
                    <v-chip
                      :color="settings.inbox.enabled ? 'success' : 'default'"
                      size="small"
                      variant="flat"
                    >
                      {{ settings.inbox.enabled ? '已启用' : '未启用' }}
                    </v-chip>
                  </template>
                </v-list-item>

                <v-list-item v-if="settings.inbox.enabled">
                  <v-list-item-title>启用的媒体类型</v-list-item-title>
                  <template v-slot:append>
                    <div class="d-flex flex-wrap gap-1">
                      <v-chip
                        v-for="type in settings.inbox.enabled_media_types"
                        :key="type"
                        size="small"
                        color="primary"
                        variant="flat"
                      >
                        {{ getMediaTypeLabel(type) }}
                      </v-chip>
                    </div>
                  </template>
                </v-list-item>

                <v-list-item>
                  <v-list-item-title>检测阈值</v-list-item-title>
                  <v-list-item-subtitle>
                    {{ settings.inbox.detection_min_score }}
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item>
                  <v-list-item-title>扫描最大项目数</v-list-item-title>
                  <v-list-item-subtitle>
                    {{ settings.inbox.scan_max_items }}
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item>
                  <v-list-item-title>最近运行状态</v-list-item-title>
                  <template v-slot:append>
                    <v-chip
                      :color="getStatusColor(settings.inbox.last_run_status)"
                      size="small"
                      variant="flat"
                    >
                      {{ getStatusLabel(settings.inbox.last_run_status) }}
                    </v-chip>
                  </template>
                </v-list-item>

                <v-list-item v-if="settings.inbox.last_run_at">
                  <v-list-item-title>最近运行时间</v-list-item-title>
                  <v-list-item-subtitle>
                    {{ formatRelativeTime(settings.inbox.last_run_at) }}
                    <span class="text-caption text-medium-emphasis ml-2">
                      ({{ formatDateTime(settings.inbox.last_run_at) }})
                    </span>
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item v-if="settings.inbox.last_run_summary">
                  <v-list-item-title>运行摘要</v-list-item-title>
                  <v-list-item-subtitle class="text-wrap">
                    {{ settings.inbox.last_run_summary }}
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item v-if="settings.inbox.pending_warning">
                  <v-list-item-title>警告</v-list-item-title>
                  <template v-slot:append>
                    <v-chip
                      color="warning"
                      size="small"
                      variant="flat"
                      prepend-icon="mdi-alert"
                    >
                      {{ getPendingWarningLabel(settings.inbox.pending_warning) }}
                    </v-chip>
                  </template>
                </v-list-item>
              </v-list>

              <!-- 快捷链接 -->
              <v-divider class="my-4" />
              <div class="d-flex gap-2">
                <v-btn
                  color="primary"
                  variant="outlined"
                  prepend-icon="mdi-inbox"
                  size="small"
                  @click="$router.push('/dev/inbox-preview')"
                >
                  查看收件箱预览
                </v-btn>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- 视频库根目录卡片 -->
        <v-col cols="12" md="6">
          <v-card>
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2" color="purple">mdi-movie</v-icon>
              <span>视频库根目录</span>
            </v-card-title>
            <v-divider />
            <v-card-text>
              <v-list density="compact">
                <v-list-item>
                  <v-list-item-title>MOVIE_LIBRARY_ROOT</v-list-item-title>
                  <v-list-item-subtitle class="text-wrap">
                    {{ settings.library_roots.movie }}
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item>
                  <v-list-item-title>TV_LIBRARY_ROOT</v-list-item-title>
                  <v-list-item-subtitle class="text-wrap">
                    {{ settings.library_roots.tv }}
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item>
                  <v-list-item-title>ANIME_LIBRARY_ROOT</v-list-item-title>
                  <v-list-item-subtitle class="text-wrap">
                    {{ settings.library_roots.anime }}
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item>
                  <v-list-item-title>SHORT_DRAMA_LIBRARY_ROOT</v-list-item-title>
                  <v-list-item-subtitle class="text-wrap">
                    <span v-if="settings.library_roots.short_drama">
                      {{ settings.library_roots.short_drama }}
                    </span>
                    <span v-else class="text-medium-emphasis">
                      未单独配置，默认继承电视剧库
                    </span>
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- 书籍/有声书/漫画/音乐库根卡片 -->
        <v-col cols="12" md="6">
          <v-card>
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2" color="green">mdi-book</v-icon>
              <span>书籍/有声书/漫画/音乐库根目录</span>
            </v-card-title>
            <v-divider />
            <v-card-text>
              <v-list density="compact">
                <v-list-item>
                  <v-list-item-title>EBOOK_LIBRARY_ROOT</v-list-item-title>
                  <v-list-item-subtitle class="text-wrap">
                    {{ settings.library_roots.ebook }}
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item>
                  <v-list-item-title>COMIC_LIBRARY_ROOT</v-list-item-title>
                  <v-list-item-subtitle class="text-wrap">
                    <span v-if="settings.library_roots.comic">
                      {{ settings.library_roots.comic }}
                    </span>
                    <span v-else class="text-medium-emphasis">未配置</span>
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item>
                  <v-list-item-title>MUSIC_LIBRARY_ROOT</v-list-item-title>
                  <v-list-item-subtitle class="text-wrap">
                    <span v-if="settings.library_roots.music">
                      {{ settings.library_roots.music }}
                    </span>
                    <span v-else class="text-medium-emphasis">未配置</span>
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminSettingsApi } from '@/services/api'
import type { LibrarySettingsResponse } from '@/types/settings'
import { formatDateTime, formatRelativeTime } from '@/utils/formatters'

// 状态
const loading = ref(false)
const errorMessage = ref<string | null>(null)
const settings = ref<LibrarySettingsResponse | null>(null)

// 加载设置
const loadSettings = async () => {
  loading.value = true
  errorMessage.value = null

  try {
    const response = await adminSettingsApi.getLibrarySettings()
    settings.value = response.data
  } catch (err: any) {
    console.error('加载设置失败:', err)
    errorMessage.value = err.response?.data?.error_message || 
                        err.response?.data?.message || 
                        err.message || 
                        '加载设置失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

// 获取媒体类型标签
const getMediaTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    video: '视频',
    ebook: '电子书',
    audiobook: '有声书',
    novel_txt: '小说',
    comic: '漫画',
    music: '音乐'
  }
  return labels[type] || type
}

// 获取状态颜色
const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    success: 'success',
    empty: 'info',
    partial: 'warning',
    failed: 'error',
    never: 'default'
  }
  return colors[status] || 'default'
}

// 获取状态标签
const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    success: '成功',
    empty: '空运行',
    partial: '部分成功',
    failed: '失败',
    never: '从未运行'
  }
  return labels[status] || status
}

// 获取待处理警告标签
const getPendingWarningLabel = (warning: string): string => {
  const labels: Record<string, string> = {
    never_run: '已启用但从未运行过 run-once',
    last_run_failed: '最近一次 Inbox 处理失败',
    too_long_without_run: '超过 24 小时未运行 run-once'
  }
  return labels[warning] || warning
}

// 组件挂载时加载
onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.library-settings-page {
  min-height: 100vh;
}
</style>

