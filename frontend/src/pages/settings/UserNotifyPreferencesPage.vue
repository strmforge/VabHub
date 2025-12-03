<template>
  <v-container fluid>
    <!-- 页面标题 -->
    <v-row>
      <v-col cols="12">
        <div class="d-flex align-center mb-4">
          <v-icon class="mr-2" size="28">mdi-bell-cog</v-icon>
          <div>
            <h1 class="text-h5 font-weight-bold">通知偏好</h1>
            <p class="text-body-2 text-medium-emphasis mb-0">
              控制哪些事件要推送、通过哪些渠道推送
            </p>
          </div>
          <v-spacer />
          <!-- 快捷操作 -->
          <v-btn
            v-if="!isSnoozing"
            color="warning"
            variant="tonal"
            class="mr-2"
            @click="quickSnooze(120)"
          >
            <v-icon left>mdi-bell-sleep</v-icon>
            静音 2 小时
          </v-btn>
          <v-btn
            v-else
            color="success"
            variant="tonal"
            @click="clearSnooze"
          >
            <v-icon left>mdi-bell-ring</v-icon>
            恢复通知
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- 全局静音/Snooze 卡片 -->
    <v-row>
      <v-col cols="12" md="6" lg="4">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2" :color="snoozeStatusColor">{{ snoozeStatusIcon }}</v-icon>
            通知状态
          </v-card-title>
          <v-card-text>
            <div class="d-flex align-center mb-3">
              <div class="flex-grow-1">
                <div class="text-body-1 font-weight-medium">{{ snoozeStatusText }}</div>
                <div v-if="snooze?.snooze_until" class="text-body-2 text-medium-emphasis">
                  静音到 {{ formatDateTime(snooze.snooze_until) }}
                </div>
              </div>
            </div>

            <v-divider class="my-3" />

            <!-- 全局静音开关 -->
            <div class="d-flex align-center mb-2">
              <div class="flex-grow-1">
                <div class="text-body-2">全局静音</div>
                <div class="text-caption text-medium-emphasis">暂停所有通知推送</div>
              </div>
              <v-switch
                v-model="globalMuted"
                hide-details
                density="compact"
                color="warning"
                @update:model-value="toggleGlobalMute"
              />
            </div>

            <!-- 仅重要通知 -->
            <div class="d-flex align-center">
              <div class="flex-grow-1">
                <div class="text-body-2">允许重要通知</div>
                <div class="text-caption text-medium-emphasis">静音时仍接收系统告警</div>
              </div>
              <v-switch
                v-model="allowCriticalOnly"
                hide-details
                density="compact"
                color="primary"
                :disabled="!globalMuted && !isSnoozing"
                @update:model-value="toggleAllowCritical"
              />
            </div>

            <v-divider class="my-3" />

            <!-- 快捷 Snooze -->
            <div class="text-body-2 mb-2">快捷静音</div>
            <div class="d-flex flex-wrap ga-2">
              <v-chip
                v-for="option in snoozeOptions"
                :key="option.minutes"
                :color="isSnoozing ? 'default' : 'primary'"
                :variant="isSnoozing ? 'outlined' : 'tonal'"
                size="small"
                @click="quickSnooze(option.minutes)"
              >
                {{ option.label }}
              </v-chip>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 事件类型矩阵 -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-view-grid</v-icon>
            通知类型设置
            <v-spacer />
            <v-btn variant="text" size="small" @click="resetAllPreferences">
              <v-icon left size="small">mdi-refresh</v-icon>
              恢复默认
            </v-btn>
          </v-card-title>

          <v-card-text>
            <v-skeleton-loader v-if="loading" type="table" />

            <v-table v-else density="comfortable">
              <thead>
                <tr>
                  <th class="text-left" style="min-width: 200px">通知类型</th>
                  <th class="text-center" style="width: 80px">
                    <v-tooltip text="站内通知（铃铛）">
                      <template #activator="{ props }">
                        <v-icon v-bind="props" size="20">mdi-bell</v-icon>
                      </template>
                    </v-tooltip>
                  </th>
                  <th class="text-center" style="width: 80px">
                    <v-tooltip text="Telegram Bot">
                      <template #activator="{ props }">
                        <v-icon v-bind="props" size="20">mdi-telegram</v-icon>
                      </template>
                    </v-tooltip>
                  </th>
                  <th class="text-center" style="width: 80px">
                    <v-tooltip text="Webhook">
                      <template #activator="{ props }">
                        <v-icon v-bind="props" size="20">mdi-webhook</v-icon>
                      </template>
                    </v-tooltip>
                  </th>
                  <th class="text-center" style="width: 80px">
                    <v-tooltip text="Bark 推送">
                      <template #activator="{ props }">
                        <v-icon v-bind="props" size="20">mdi-cellphone-message</v-icon>
                      </template>
                    </v-tooltip>
                  </th>
                  <th class="text-center" style="width: 80px">
                    <v-tooltip text="完全静音">
                      <template #activator="{ props }">
                        <v-icon v-bind="props" size="20">mdi-bell-off</v-icon>
                      </template>
                    </v-tooltip>
                  </th>
                </tr>
              </thead>
              <tbody>
                <template v-for="group in groupedNotificationTypes" :key="group.key">
                  <!-- 分组标题 -->
                  <tr class="bg-grey-lighten-4">
                    <td colspan="6">
                      <div class="d-flex align-center py-1">
                        <v-icon :color="group.config.color" size="18" class="mr-2">
                          {{ group.config.icon }}
                        </v-icon>
                        <span class="text-body-2 font-weight-medium">{{ group.config.label }}</span>
                      </div>
                    </td>
                  </tr>
                  <!-- 类型行 -->
                  <tr v-for="ntype in group.items" :key="ntype.type">
                    <td>
                      <div>
                        <div class="text-body-2">{{ ntype.name }}</div>
                        <div class="text-caption text-medium-emphasis">{{ ntype.description }}</div>
                      </div>
                    </td>
                    <td class="text-center">
                      <v-checkbox
                        :model-value="getPreferenceValue(ntype.type, 'enable_web')"
                        hide-details
                        density="compact"
                        :disabled="getPreferenceValue(ntype.type, 'muted')"
                        @update:model-value="updatePreference(ntype.type, 'enable_web', $event)"
                      />
                    </td>
                    <td class="text-center">
                      <v-checkbox
                        :model-value="getPreferenceValue(ntype.type, 'enable_telegram')"
                        hide-details
                        density="compact"
                        :disabled="getPreferenceValue(ntype.type, 'muted')"
                        @update:model-value="updatePreference(ntype.type, 'enable_telegram', $event)"
                      />
                    </td>
                    <td class="text-center">
                      <v-checkbox
                        :model-value="getPreferenceValue(ntype.type, 'enable_webhook')"
                        hide-details
                        density="compact"
                        :disabled="getPreferenceValue(ntype.type, 'muted')"
                        @update:model-value="updatePreference(ntype.type, 'enable_webhook', $event)"
                      />
                    </td>
                    <td class="text-center">
                      <v-checkbox
                        :model-value="getPreferenceValue(ntype.type, 'enable_bark')"
                        hide-details
                        density="compact"
                        :disabled="getPreferenceValue(ntype.type, 'muted')"
                        @update:model-value="updatePreference(ntype.type, 'enable_bark', $event)"
                      />
                    </td>
                    <td class="text-center">
                      <v-checkbox
                        :model-value="getPreferenceValue(ntype.type, 'muted')"
                        hide-details
                        density="compact"
                        color="error"
                        @update:model-value="updatePreference(ntype.type, 'muted', $event)"
                      />
                    </td>
                  </tr>
                </template>
              </tbody>
            </v-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 单作品静音（可选区域） -->
    <v-row v-if="mutedItems.length > 0" class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-volume-off</v-icon>
            已静音的作品
          </v-card-title>
          <v-card-text>
            <v-list density="compact">
              <v-list-item v-for="item in mutedItems" :key="item.id">
                <template #prepend>
                  <v-icon :color="getMediaTypeColor(item.media_type)" size="20">
                    {{ getMediaTypeIcon(item.media_type) }}
                  </v-icon>
                </template>
                <v-list-item-title>
                  {{ item.notification_type }} - {{ item.media_type }}:{{ item.target_id }}
                </v-list-item-title>
                <template #append>
                  <v-btn
                    icon
                    size="small"
                    variant="text"
                    color="error"
                    @click="deleteMutedItem(item.id)"
                  >
                    <v-icon>mdi-delete</v-icon>
                  </v-btn>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 提示信息 -->
    <v-snackbar v-model="snackbar" :color="snackbarColor" timeout="2000">
      {{ snackbarText }}
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { notifyPreferenceApi } from '@/services/api'
import type {
  UserNotifyPreferenceMatrix,
  UserNotifySnooze,
  UserNotifyPreference,
  NotificationTypeInfo,
  NotificationType,
} from '@/types/notifyPreferences'

// 分组配置
const GROUPS: Record<string, { label: string; icon: string; color: string }> = {
  manga: { label: '漫画', icon: 'mdi-book-open-page-variant', color: 'orange' },
  novel: { label: '小说/有声书', icon: 'mdi-book', color: 'blue' },
  music: { label: '音乐', icon: 'mdi-music', color: 'purple' },
  system: { label: '系统', icon: 'mdi-cog', color: 'grey' },
}

// 状态
const loading = ref(true)
const matrix = ref<UserNotifyPreferenceMatrix | null>(null)
const snooze = ref<UserNotifySnooze | null>(null)
const preferences = ref<UserNotifyPreference[]>([])
const availableTypes = ref<NotificationTypeInfo[]>([])

// Snackbar
const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

// Snooze 选项
const snoozeOptions = [
  { label: '30 分钟', minutes: 30 },
  { label: '1 小时', minutes: 60 },
  { label: '2 小时', minutes: 120 },
  { label: '4 小时', minutes: 240 },
  { label: '今晚', minutes: calculateTonightMinutes() },
]

function calculateTonightMinutes(): number {
  const now = new Date()
  const tonight = new Date(now)
  tonight.setHours(23, 59, 0, 0)
  return Math.max(30, Math.floor((tonight.getTime() - now.getTime()) / 60000))
}

// 计算属性
const globalMuted = computed({
  get: () => snooze.value?.muted || false,
  set: () => {},
})

const allowCriticalOnly = computed({
  get: () => snooze.value?.allow_critical_only || false,
  set: () => {},
})

const isSnoozing = computed(() => {
  if (!snooze.value) return false
  if (snooze.value.muted) return true
  if (snooze.value.snooze_until) {
    return new Date(snooze.value.snooze_until) > new Date()
  }
  return false
})

const snoozeStatusText = computed(() => {
  if (!snooze.value) return '正常'
  if (snooze.value.muted) return '全局静音中'
  if (snooze.value.snooze_until && new Date(snooze.value.snooze_until) > new Date()) {
    return '临时静音中'
  }
  return '正常'
})

const snoozeStatusIcon = computed(() => {
  if (isSnoozing.value) return 'mdi-bell-off'
  return 'mdi-bell-ring'
})

const snoozeStatusColor = computed(() => {
  if (isSnoozing.value) return 'warning'
  return 'success'
})

const groupedNotificationTypes = computed(() => {
  const groups: { key: string; config: typeof GROUPS[string]; items: NotificationTypeInfo[] }[] = []
  const groupMap: Record<string, NotificationTypeInfo[]> = {}

  for (const ntype of availableTypes.value) {
    const group = ntype.group || 'system'
    if (!groupMap[group]) {
      groupMap[group] = []
    }
    groupMap[group].push(ntype)
  }

  for (const key of Object.keys(GROUPS)) {
    if (groupMap[key] && groupMap[key].length > 0) {
      groups.push({
        key,
        config: GROUPS[key],
        items: groupMap[key],
      })
    }
  }

  return groups
})

const mutedItems = computed(() => {
  return preferences.value.filter(p => p.muted && p.target_id)
})

// 方法
async function loadMatrix() {
  loading.value = true
  try {
    matrix.value = await notifyPreferenceApi.getMatrix()
    preferences.value = matrix.value.preferences
    snooze.value = matrix.value.snooze || null
    availableTypes.value = matrix.value.available_notification_types
  } catch (e) {
    console.error('Failed to load preferences:', e)
    showSnackbar('加载失败', 'error')
  } finally {
    loading.value = false
  }
}

function getPreferenceValue(notificationType: NotificationType, field: keyof UserNotifyPreference): boolean {
  const pref = preferences.value.find(
    p => p.notification_type === notificationType && !p.media_type && !p.target_id
  )
  if (pref) {
    return pref[field] as boolean
  }
  // 默认值
  if (field === 'muted') return false
  return true
}

async function updatePreference(notificationType: NotificationType, field: string, value: boolean | null) {
  if (value === null) return
  try {
    const payload: any = { notification_type: notificationType }
    payload[field] = value

    // 如果静音，同时关闭所有渠道
    if (field === 'muted' && value) {
      payload.enable_web = false
      payload.enable_telegram = false
      payload.enable_webhook = false
      payload.enable_bark = false
    }

    const updated = await notifyPreferenceApi.upsertPreference(payload)

    // 更新本地状态
    const idx = preferences.value.findIndex(
      p => p.notification_type === notificationType && !p.media_type && !p.target_id
    )
    if (idx >= 0) {
      preferences.value[idx] = updated
    } else {
      preferences.value.push(updated)
    }

    showSnackbar('已保存', 'success')
  } catch (e) {
    console.error('Failed to update preference:', e)
    showSnackbar('保存失败', 'error')
  }
}

async function toggleGlobalMute(value: boolean | null) {
  if (value === null) return
  try {
    snooze.value = await notifyPreferenceApi.updateSnooze({ muted: value })
    showSnackbar(value ? '已开启全局静音' : '已关闭全局静音', 'success')
  } catch (e) {
    showSnackbar('操作失败', 'error')
  }
}

async function toggleAllowCritical(value: boolean | null) {
  if (value === null) return
  try {
    snooze.value = await notifyPreferenceApi.updateSnooze({ allow_critical_only: value })
    showSnackbar('已保存', 'success')
  } catch (e) {
    showSnackbar('操作失败', 'error')
  }
}

async function quickSnooze(minutes: number) {
  try {
    snooze.value = await notifyPreferenceApi.quickSnooze({ duration_minutes: minutes })
    showSnackbar(`已静音 ${minutes} 分钟`, 'success')
  } catch (e) {
    showSnackbar('操作失败', 'error')
  }
}

async function clearSnooze() {
  try {
    await notifyPreferenceApi.clearSnooze()
    snooze.value = null
    showSnackbar('已恢复通知', 'success')
  } catch (e) {
    showSnackbar('操作失败', 'error')
  }
}

async function resetAllPreferences() {
  if (!confirm('确定要恢复所有通知偏好为默认设置吗？')) return

  try {
    for (const pref of preferences.value) {
      if (!pref.target_id) {
        await notifyPreferenceApi.deletePreference(pref.id)
      }
    }
    await loadMatrix()
    showSnackbar('已恢复默认', 'success')
  } catch (e) {
    showSnackbar('操作失败', 'error')
  }
}

async function deleteMutedItem(id: number) {
  try {
    await notifyPreferenceApi.deletePreference(id)
    preferences.value = preferences.value.filter(p => p.id !== id)
    showSnackbar('已取消静音', 'success')
  } catch (e) {
    showSnackbar('操作失败', 'error')
  }
}

function formatDateTime(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function getMediaTypeIcon(mediaType?: string | null): string {
  switch (mediaType) {
    case 'MANGA': return 'mdi-book-open-page-variant'
    case 'NOVEL': return 'mdi-book'
    case 'AUDIOBOOK': return 'mdi-headphones'
    default: return 'mdi-file'
  }
}

function getMediaTypeColor(mediaType?: string | null): string {
  switch (mediaType) {
    case 'MANGA': return 'orange'
    case 'NOVEL': return 'blue'
    case 'AUDIOBOOK': return 'purple'
    default: return 'grey'
  }
}

function showSnackbar(text: string, color: string) {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

onMounted(() => {
  loadMatrix()
})
</script>

<style scoped>
.v-table {
  background: transparent;
}

.v-table tbody tr:hover {
  background: rgba(var(--v-theme-primary), 0.04);
}
</style>
