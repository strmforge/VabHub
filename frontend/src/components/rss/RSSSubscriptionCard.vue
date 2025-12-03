<template>
  <v-hover v-slot="{ isHovering, props: hoverProps }">
    <v-card
      v-bind="hoverProps"
      :class="{
        'rss-subscription-card': true,
        'rss-subscription-disabled': !subscription.enabled,
        'rss-subscription-card-hover': isHovering
      }"
      variant="outlined"
    >
      <v-card-text class="pa-4">
        <!-- 头部：标题和状态 -->
        <div class="d-flex align-start justify-space-between mb-3">
          <div class="flex-grow-1">
            <div class="d-flex align-center mb-1">
              <v-icon 
                :color="subscription.enabled ? 'primary' : 'grey'" 
                size="20" 
                class="me-2"
              >
                {{ subscription.enabled ? 'mdi-rss' : 'mdi-rss-off' }}
              </v-icon>
              <div 
                class="text-h6 font-weight-bold"
                :class="subscription.enabled ? '' : 'text-grey'"
              >
                {{ subscription.name }}
              </div>
            </div>
            <div class="text-caption text-medium-emphasis">
              <v-icon size="14" class="me-1">mdi-link</v-icon>
              <span class="text-truncate d-inline-block" style="max-width: 200px;">
                {{ subscription.url }}
              </span>
            </div>
          </div>
          <v-chip
            :color="subscription.enabled ? 'success' : 'grey'"
            size="small"
            variant="flat"
          >
            {{ subscription.enabled ? '启用' : '禁用' }}
          </v-chip>
        </div>

        <!-- 统计信息 -->
        <v-row dense class="mb-3">
          <v-col cols="6">
            <div class="text-caption text-medium-emphasis">总项数</div>
            <div class="text-body-1 font-weight-bold">{{ subscription.total_items || 0 }}</div>
          </v-col>
          <v-col cols="6">
            <div class="text-caption text-medium-emphasis">已下载</div>
            <div class="text-body-1 font-weight-bold text-success">
              {{ subscription.downloaded_items || 0 }}
            </div>
          </v-col>
          <v-col cols="6">
            <div class="text-caption text-medium-emphasis">已跳过</div>
            <div class="text-body-1 font-weight-bold text-warning">
              {{ subscription.skipped_items || 0 }}
            </div>
          </v-col>
          <v-col cols="6">
            <div class="text-caption text-medium-emphasis">错误数</div>
            <div class="text-body-1 font-weight-bold" :class="subscription.error_count > 0 ? 'text-error' : ''">
              {{ subscription.error_count || 0 }}
            </div>
          </v-col>
        </v-row>

        <!-- 最后检查时间 -->
        <div class="text-caption text-medium-emphasis mb-3">
          <v-icon size="14" class="me-1">mdi-clock-outline</v-icon>
          最后检查: {{ formatDate(subscription.last_check) }}
        </div>

        <!-- 下次检查时间 -->
        <div v-if="subscription.next_check" class="text-caption text-medium-emphasis mb-3">
          <v-icon size="14" class="me-1">mdi-clock-alert-outline</v-icon>
          下次检查: {{ formatDate(subscription.next_check) }}
        </div>

        <!-- 刷新间隔 -->
        <div class="text-caption text-medium-emphasis">
          <v-icon size="14" class="me-1">mdi-refresh</v-icon>
          刷新间隔: {{ subscription.interval }} 分钟
        </div>

        <!-- 描述 -->
        <div v-if="subscription.description" class="text-body-2 text-medium-emphasis mt-3 pt-3 border-t">
          {{ subscription.description }}
        </div>
      </v-card-text>

      <!-- 操作按钮 -->
      <v-card-actions class="pa-3 pt-0">
        <v-btn
          size="small"
          variant="text"
          prepend-icon="mdi-eye"
          @click.stop="$emit('view', subscription)"
        >
          查看详情
        </v-btn>
        <v-spacer />
        <v-btn
          size="small"
          variant="text"
          prepend-icon="mdi-refresh"
          :loading="checking"
          @click.stop="$emit('check', subscription)"
        >
          检查
        </v-btn>
        <v-btn
          size="small"
          variant="text"
          icon="mdi-pencil"
          @click.stop="$emit('edit', subscription)"
        />
        <v-btn
          size="small"
          variant="text"
          icon="mdi-delete"
          color="error"
          @click.stop="$emit('delete', subscription)"
        />
      </v-card-actions>
    </v-card>
  </v-hover>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface RSSSubscription {
  id: number
  name: string
  url: string
  site_id?: number
  enabled: boolean
  interval: number
  last_check?: string
  next_check?: string
  last_item_hash?: string
  filter_rules?: any
  download_rules?: any
  total_items: number
  downloaded_items: number
  skipped_items: number
  error_count: number
  description?: string
  created_at: string
  updated_at: string
}

interface Props {
  subscription: RSSSubscription
}

defineProps<Props>()

const emit = defineEmits<{
  view: [subscription: RSSSubscription]
  edit: [subscription: RSSSubscription]
  delete: [subscription: RSSSubscription]
  check: [subscription: RSSSubscription]
}>()

const checking = ref(false)

const formatDate = (date?: string) => {
  if (!date) return '从未检查'
  try {
    return new Date(date).toLocaleString('zh-CN')
  } catch {
    return date
  }
}
</script>

<style scoped>
.rss-subscription-card {
  transition: all 0.3s ease;
  height: 100%;
}

.rss-subscription-card-hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.rss-subscription-disabled {
  opacity: 0.7;
}

.border-t {
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}
</style>

