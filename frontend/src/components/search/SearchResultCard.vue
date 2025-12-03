<template>
  <v-card class="search-result-card" @click="handleClick">
    <v-img
      :src="result.coverUrl || '/default-cover.png'"
      height="200"
      cover
      loading="lazy"
      :lazy-src="result.coverUrl || '/default-cover.png'"
    >
      <template v-slot:placeholder>
        <div class="d-flex align-center justify-center fill-height">
          <v-progress-circular
            indeterminate
            color="grey-lighten-1"
            size="32"
          />
        </div>
      </template>
      <template v-slot:error>
        <div class="d-flex align-center justify-center fill-height">
          <v-icon size="48" color="grey-lighten-1">mdi-image-off</v-icon>
        </div>
      </template>
    </v-img>
    
    <v-card-title class="text-body-1">
      {{ result.title }}
    </v-card-title>
    
    <v-card-subtitle>
      <div class="d-flex align-center flex-wrap gap-2">
        <div class="d-flex align-center">
          <v-icon size="small" class="mr-1">mdi-seed</v-icon>
          <span>{{ result.seeders || 0 }}</span>
        </div>
        <div class="d-flex align-center">
          <v-icon size="small" class="mr-1">mdi-download</v-icon>
          <span>{{ formatSize(result.size_gb || result.sizeGb || 0) }}</span>
        </div>
        <!-- Phase 9: Local Intel 状态标签 -->
        <v-chip
          v-if="result.intel_hr_status && result.intel_hr_status !== 'UNKNOWN'"
          size="x-small"
          :color="getHRStatusColor(result.intel_hr_status)"
          variant="flat"
        >
          <v-icon size="12" class="me-1">{{ getHRStatusIcon(result.intel_hr_status) }}</v-icon>
          {{ getHRStatusText(result.intel_hr_status) }}
        </v-chip>
        <v-chip
          v-if="result.intel_site_status && result.intel_site_status !== 'UNKNOWN'"
          size="x-small"
          :color="getSiteStatusColor(result.intel_site_status)"
          variant="flat"
        >
          <v-icon size="12" class="me-1">{{ getSiteStatusIcon(result.intel_site_status) }}</v-icon>
          {{ getSiteStatusText(result.intel_site_status) }}
        </v-chip>
        <!-- Free/HR 标记 -->
        <v-chip v-if="result.is_free" size="x-small" color="success" variant="flat">
          <v-icon size="12" class="me-1">mdi-gift</v-icon>
          免费
        </v-chip>
        <v-chip v-else-if="result.is_half_free" size="x-small" color="info" variant="flat">
          <v-icon size="12" class="me-1">mdi-gift-outline</v-icon>
          半免费
        </v-chip>
        <v-chip v-if="result.is_hr" size="x-small" color="warning" variant="flat">
          <v-icon size="12" class="me-1">mdi-alert</v-icon>
          HR
        </v-chip>
        <v-chip v-if="result.quality" size="x-small" color="primary" variant="flat">
          {{ result.quality }}
        </v-chip>
        <v-chip v-if="result.site || result.site_id" size="x-small" color="secondary" variant="flat">
          {{ result.site || result.site_id }}
        </v-chip>
        <!-- Phase EXT-4: 搜索结果来源标记 -->
        <ResultSourceChip :source="result.source" />
      </div>
    </v-card-subtitle>
    
    <v-card-actions>
      <v-btn
        color="primary"
        variant="text"
        size="small"
        @click.stop="handleDownload"
      >
        下载
      </v-btn>
      <v-spacer />
      <v-btn
        icon
        size="small"
        variant="text"
        @click.stop="showDetails = true"
      >
        <v-icon>mdi-information</v-icon>
      </v-btn>
    </v-card-actions>
    
    <!-- 详情对话框 -->
    <v-dialog v-model="showDetails" max-width="600">
      <v-card>
        <v-card-title>{{ result.title }}</v-card-title>
        <v-card-text>
          <div class="mb-2">
            <strong>站点:</strong> {{ result.site }}
          </div>
          <div class="mb-2">
            <strong>大小:</strong> {{ formatSize(result.size_gb || result.sizeGb || 0) }}
          </div>
          <div class="mb-2" v-if="result.quality">
            <strong>质量:</strong> {{ result.quality }}
          </div>
          <div class="mb-2" v-if="result.resolution">
            <strong>分辨率:</strong> {{ result.resolution }}
          </div>
          <div class="mb-2" v-if="result.leechers !== undefined">
            <strong>下载数:</strong> {{ result.leechers }}
          </div>
          <div class="mb-2" v-if="result.upload_date">
            <strong>上传时间:</strong> {{ formatDate(result.upload_date) }}
          </div>
          <div class="mb-2">
            <strong>种子数:</strong> {{ result.seeders || 0 }}
          </div>
          <!-- Phase 9: Local Intel 状态信息 -->
          <div class="mb-2" v-if="result.intel_hr_status && result.intel_hr_status !== 'UNKNOWN'">
            <strong>HR 状态:</strong> 
            <v-chip size="x-small" :color="getHRStatusColor(result.intel_hr_status)" variant="flat">
              {{ getHRStatusText(result.intel_hr_status) }}
            </v-chip>
          </div>
          <div class="mb-2" v-if="result.intel_site_status && result.intel_site_status !== 'UNKNOWN'">
            <strong>站点状态:</strong> 
            <v-chip size="x-small" :color="getSiteStatusColor(result.intel_site_status)" variant="flat">
              {{ getSiteStatusText(result.intel_site_status) }}
            </v-chip>
          </div>
          <div class="mb-2" v-if="result.is_free || result.is_half_free">
            <strong>免费状态:</strong> 
            <v-chip v-if="result.is_free" size="x-small" color="success" variant="flat">免费</v-chip>
            <v-chip v-else-if="result.is_half_free" size="x-small" color="info" variant="flat">半免费</v-chip>
          </div>
          <div class="mb-2" v-if="result.is_hr">
            <strong>HR 标记:</strong> 
            <v-chip size="x-small" color="warning" variant="flat">是</v-chip>
          </div>
          <!-- Phase EXT-4: 搜索结果来源信息 -->
          <div class="mb-2" v-if="result.source">
            <strong>来源:</strong> 
            <ResultSourceChip :source="result.source" size="small" />
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="showDetails = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import api from '@/services/api'
import ResultSourceChip from '@/components/common/ResultSourceChip.vue'

interface Props {
  result: any
}

const props = defineProps<Props>()
const showDetails = ref(false)

const formatSize = (gb: number) => {
  if (!gb || gb === 0) return '0 B'
  if (gb < 1) return `${(gb * 1024).toFixed(2)} MB`
  return `${gb.toFixed(2)} GB`
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN')
  } catch {
    return dateStr
  }
}

// Phase 9: Local Intel 状态相关函数
const getHRStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    SAFE: 'success',
    ACTIVE: 'warning',
    RISK: 'error',
    UNKNOWN: 'grey'
  }
  return colors[status] || 'grey'
}

const getHRStatusIcon = (status: string) => {
  const icons: Record<string, string> = {
    SAFE: 'mdi-shield-check',
    ACTIVE: 'mdi-shield-alert',
    RISK: 'mdi-shield-alert-outline',
    UNKNOWN: 'mdi-shield-question'
  }
  return icons[status] || 'mdi-shield-question'
}

const getHRStatusText = (status: string) => {
  const texts: Record<string, string> = {
    SAFE: 'HR安全',
    ACTIVE: 'HR中',
    RISK: 'HR风险',
    UNKNOWN: '未知'
  }
  return texts[status] || '未知'
}

const getSiteStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    OK: 'success',
    THROTTLED: 'warning',
    ERROR: 'error',
    UNKNOWN: 'grey'
  }
  return colors[status] || 'grey'
}

const getSiteStatusIcon = (status: string) => {
  const icons: Record<string, string> = {
    OK: 'mdi-check-circle',
    THROTTLED: 'mdi-speedometer',
    ERROR: 'mdi-alert-circle',
    UNKNOWN: 'mdi-help-circle'
  }
  return icons[status] || 'mdi-help-circle'
}

const getSiteStatusText = (status: string) => {
  const texts: Record<string, string> = {
    OK: '站点正常',
    THROTTLED: '站点限流',
    ERROR: '站点错误',
    UNKNOWN: '未知'
  }
  return texts[status] || '未知'
}

const handleClick = () => {
  showDetails.value = true
}

const handleDownload = async () => {
  try {
    // 获取磁力链接或种子URL
    const magnetLink = props.result.magnet_link || props.result.magnetLink
    const torrentUrl = props.result.torrent_url || props.result.torrentUrl
    
    if (!magnetLink && !torrentUrl) {
      alert('该资源没有可用的下载链接')
      return
    }
    
    // 调用下载API
    const response = await api.post('/downloads', {
      title: props.result.title,
      magnet_link: magnetLink,
      torrent_url: torrentUrl,
      size_gb: props.result.size_gb || props.result.sizeGb,
      downloader: 'qBittorrent' // TODO: 从设置中获取默认下载器
    })
    
    console.log('下载任务已创建:', response)
    alert('下载任务已添加')
  } catch (error: any) {
    console.error('创建下载任务失败:', error)
    alert('下载失败：' + (error.response?.data?.detail || '未知错误'))
  }
}
</script>

<style lang="scss" scoped>
.search-result-card {
  transition: var(--vabhub-transition);
  cursor: pointer;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: var(--vabhub-shadow-lg);
  }
}
</style>

