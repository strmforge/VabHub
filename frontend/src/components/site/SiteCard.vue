<template>
  <v-card
    variant="outlined"
    class="site-card"
    :class="{ 'site-inactive': !site.is_active }"
  >
    <v-card-item class="pb-2">
      <div class="d-flex align-center justify-space-between">
        <div class="d-flex align-center ga-2">
          <SiteAvatar
            :site-id="site.id"
            :site-name="site.name"
            :site-url="site.url"
            :size="40"
          />
          <div>
            <div class="text-h6 font-weight-bold">
              {{ site.name }}
            </div>
            <div class="text-caption text-medium-emphasis">
              {{ getDomain(site.url) }}
            </div>
          </div>
        </div>
        <v-chip
          :color="site.is_active ? 'success' : 'default'"
          size="small"
          variant="flat"
        >
          {{ site.is_active ? '启用' : '禁用' }}
        </v-chip>
      </div>
    </v-card-item>

    <v-card-text class="pt-0">
      <div class="text-body-2 text-medium-emphasis mb-2">
        <v-icon size="small" class="me-1">mdi-link</v-icon>
        <a :href="site.url" target="_blank" class="text-primary">
          {{ site.url }}
        </a>
      </div>

      <div v-if="site.cookiecloud_uuid" class="text-caption text-medium-emphasis mb-2">
        <v-icon size="small" class="me-1">mdi-cloud-sync</v-icon>
        CookieCloud已配置
      </div>

      <div v-if="site.last_checkin" class="text-caption text-medium-emphasis mb-2">
        <v-icon size="small" class="me-1">mdi-clock-outline</v-icon>
        最后签到：{{ formatDate(site.last_checkin) }}
      </div>

      <!-- Phase AI-3/AI-4: AI 适配状态显示 - 仅在开发者模式显示 -->
      <div v-if="isDevMode() && site.ai_adapter_enabled" class="text-caption text-medium-emphasis mb-2">
        <v-tooltip location="top">
          <template #activator="{ props: tooltipProps }">
            <div v-bind="tooltipProps" class="d-flex align-center">
              <!-- Phase AI-4: 如果禁用，显示不同的图标和颜色 -->
              <v-icon 
                size="small" 
                class="me-1"
                :color="site.ai_disabled ? 'error' : (site.ai_config_present ? 'success' : 'grey')"
              >
                mdi-{{ site.ai_disabled ? 'cancel' : (site.ai_config_present ? 'check-circle' : 'circle-outline') }}
              </v-icon>
              <span>AI适配（实验）</span>
              <v-chip
                v-if="site.ai_disabled"
                size="x-small"
                variant="flat"
                color="error"
                class="ms-1"
              >
                已禁用
              </v-chip>
              <v-chip
                v-else-if="site.ai_config_present"
                size="x-small"
                variant="flat"
                color="info"
                class="ms-1"
              >
                {{ getAIEffectiveModeLabel(site.ai_effective_mode) }}
              </v-chip>
            </div>
          </template>
          <div>
            <div>AI适配功能：{{ site.ai_disabled ? '已禁用（本站点）' : (site.ai_config_present ? '已配置' : '未配置') }}</div>
            <div v-if="site.ai_manual_profile_preferred" class="mt-1 text-caption text-warning">
              优先使用人工配置
            </div>
            <div v-if="site.ai_config_last_analyzed_at && !site.ai_disabled">
              上次分析：{{ formatDate(site.ai_config_last_analyzed_at) }}
            </div>
            <div v-else-if="!site.ai_disabled">尚未分析</div>
            <div v-if="!site.ai_disabled" class="mt-1 text-caption">生效模式：{{ getAIEffectiveModeLabel(site.ai_effective_mode) }}</div>
            <div v-if="site.ai_confidence_score !== null && site.ai_confidence_score !== undefined" class="mt-1 text-caption">
              可信度：{{ site.ai_confidence_score }}/100
            </div>
          </div>
        </v-tooltip>
      </div>
    </v-card-text>

    <v-card-actions class="pt-0">
      <v-spacer />
      <v-tooltip text="测试连接" location="top">
        <template #activator="{ props: tooltipProps }">
          <v-btn
            v-bind="tooltipProps"
            icon="mdi-network"
            size="small"
            variant="text"
            @click.stop="handleTest"
          />
        </template>
      </v-tooltip>

      <v-tooltip text="签到" location="top">
        <template #activator="{ props: tooltipProps }">
          <v-btn
            v-bind="tooltipProps"
            icon="mdi-check-circle"
            size="small"
            variant="text"
            @click.stop="handleCheckin"
            :loading="checkinLoading"
          />
        </template>
      </v-tooltip>

      <v-tooltip :text="site.is_active ? '禁用' : '启用'" location="top">
        <template #activator="{ props: tooltipProps }">
          <v-btn
            v-bind="tooltipProps"
            :icon="site.is_active ? 'mdi-pause' : 'mdi-play'"
            size="small"
            variant="text"
            @click.stop="handleToggleStatus"
          />
        </template>
      </v-tooltip>

      <v-tooltip text="域名管理" location="top">
        <template #activator="{ props: tooltipProps }">
          <v-btn
            v-bind="tooltipProps"
            icon="mdi-web"
            size="small"
            variant="text"
            @click.stop="handleDomainManage"
          />
        </template>
      </v-tooltip>

      <v-tooltip text="编辑" location="top">
        <template #activator="{ props: tooltipProps }">
          <v-btn
            v-bind="tooltipProps"
            icon="mdi-pencil"
            size="small"
            variant="text"
            @click.stop="handleEdit"
          />
        </template>
      </v-tooltip>

      <!-- Phase AI-3: AI 配置调试入口 - 仅在开发者模式显示 -->
      <v-tooltip text="AI配置诊断（实验）" location="top" v-if="isDevMode() && site.ai_adapter_enabled">
        <template #activator="{ props: tooltipProps }">
          <v-btn
            v-bind="tooltipProps"
            icon="mdi-bug"
            size="small"
            variant="text"
            color="info"
            @click.stop="handleAIDebug"
          />
        </template>
      </v-tooltip>

      <v-tooltip text="删除" location="top">
        <template #activator="{ props: tooltipProps }">
          <v-btn
            v-bind="tooltipProps"
            icon="mdi-delete"
            size="small"
            variant="text"
            color="error"
            @click.stop="handleDelete"
          />
        </template>
      </v-tooltip>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import SiteAvatar from './SiteAvatar.vue'
import { isDevMode } from '@/utils/devMode'

interface Props {
  site: any
}

const props = defineProps<Props>()
const emit = defineEmits(['edit', 'delete', 'test', 'checkin', 'toggle-status', 'domain-manage', 'ai-debug'])

const checkinLoading = ref(false)

const getDomain = (url: string): string => {
  try {
    const urlObj = new URL(url)
    return urlObj.hostname
  } catch {
    return url
  }
}

const formatDate = (dateStr: string): string => {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateStr
  }
}

const handleEdit = () => {
  emit('edit', props.site)
}

const handleDelete = () => {
  emit('delete', props.site)
}

const handleTest = () => {
  emit('test', props.site)
}

const handleCheckin = async () => {
  checkinLoading.value = true
  try {
    emit('checkin', props.site)
  } finally {
    setTimeout(() => {
      checkinLoading.value = false
    }, 1000)
  }
}

const handleToggleStatus = () => {
  emit('toggle-status', props.site)
}

const handleDomainManage = () => {
  emit('domain-manage', props.site)
}

const handleAIDebug = () => {
  emit('ai-debug', props.site)
}

const getAIEffectiveModeLabel = (mode: string): string => {
  const labels: Record<string, string> = {
    'manual_profile': '手工配置',
    'ai_profile': 'AI配置',
    'none': '无配置'
  }
  return labels[mode] || mode
}
</script>

<style scoped>
.site-card {
  height: 100%;
  background: rgba(30, 30, 30, 0.8);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.site-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
}

.site-inactive {
  opacity: 0.6;
}
</style>

