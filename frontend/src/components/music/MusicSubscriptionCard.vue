<template>
  <v-card
    variant="outlined"
    class="music-subscription-card"
    :class="{ 'subscription-inactive': subscription.status !== 'active' }"
  >
    <v-img
      :src="getSubscriptionCover()"
      height="180"
      cover
      gradient="to bottom, rgba(0,0,0,.1), rgba(0,0,0,.5)"
    >
      <v-card-title class="text-white d-flex align-center justify-space-between">
        <div>
          <div class="text-h6 font-weight-bold">{{ getSubscriptionTitle() }}</div>
          <div class="text-caption">{{ getSubscriptionSubtitle() }}</div>
        </div>
        <v-chip
          :color="getSubscriptionTypeColor()"
          size="small"
          variant="flat"
        >
          {{ getSubscriptionTypeLabel() }}
        </v-chip>
      </v-card-title>
    </v-img>
    
    <v-card-text>
      <div class="d-flex align-center flex-wrap ga-2 mb-2">
        <v-chip
          size="x-small"
          variant="outlined"
        >
          {{ getSubscriptionTypeLabel() }}
        </v-chip>
        <v-chip
          v-if="subscription.quality_preference"
          size="x-small"
          variant="outlined"
          color="primary"
        >
          {{ subscription.quality_preference.toUpperCase() }}
        </v-chip>
        <v-chip
          :color="getStatusColor(subscription.status)"
          size="x-small"
          variant="flat"
        >
          {{ getStatusText(subscription.status) }}
        </v-chip>
        
        <!-- 安全策略标签 -->
        <v-chip
          v-if="subscription.allow_hr"
          size="x-small"
          variant="outlined"
          color="warning"
        >
          HR
        </v-chip>
        <v-chip
          v-if="subscription.allow_h3h5"
          size="x-small"
          variant="outlined"
          color="warning"
        >
          H3/H5
        </v-chip>
        <v-chip
          v-if="subscription.strict_free_only"
          size="x-small"
          variant="outlined"
          color="success"
        >
          仅免费
        </v-chip>
      </div>
      
      <!-- 运行统计 -->
      <div v-if="subscription.last_run_at" class="text-caption text-medium-emphasis mb-1">
        最后运行: {{ formatDate(subscription.last_run_at) }}
      </div>
      <div v-if="subscription.last_run_new_count !== null" class="text-caption text-medium-emphasis">
        上次找到: {{ subscription.last_run_new_count }} 个新项目
      </div>
    </v-card-text>
    
    <v-card-actions>
      <v-menu>
        <template v-slot:activator="{ props }">
          <v-btn
            icon="mdi-play-circle"
            size="small"
            variant="text"
            color="primary"
            :loading="downloading"
            v-bind="props"
            title="立即运行订阅"
          />
        </template>
        <v-list>
          <v-list-item @click="handleRunSubscription(false)" title="立即运行" />
          <v-list-item @click="handleRunSubscription(true)" title="试运行（仅统计）" />
        </v-list>
      </v-menu>
      <v-btn
        :icon="subscription.status === 'active' ? 'mdi-pause-circle' : 'mdi-play-circle'"
        size="small"
        variant="text"
        :color="subscription.status === 'active' ? 'warning' : 'success'"
        :loading="toggling"
        @click="handleToggleStatus"
        :title="subscription.status === 'active' ? '暂停订阅' : '恢复订阅'"
      />
      <v-spacer />
      <v-btn
        icon="mdi-delete"
        size="small"
        variant="text"
        color="error"
        @click="handleDelete"
        title="删除订阅"
      />
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useToast } from 'vue-toastification'
import { 
  runSubscriptionOnce,
  pauseMusicSubscription,
  resumeMusicSubscription,
  deleteMusicSubscription,
  type UserMusicSubscription,
  type MusicSubscriptionRunResult
} from '@/services/music'

interface Props {
  subscription: UserMusicSubscription
}

const props = defineProps<Props>()
const emit = defineEmits(['delete', 'updated', 'run'])
const toast = useToast()
const downloading = ref(false)
const toggling = ref(false)

// 获取订阅标题
const getSubscriptionTitle = () => {
  if (props.subscription.subscription_type === 'chart') {
    return props.subscription.chart_display_name || '榜单订阅'
  } else if (props.subscription.subscription_type === 'keyword') {
    return props.subscription.music_query || '关键字订阅'
  }
  return '音乐订阅'
}

// 获取订阅副标题
const getSubscriptionSubtitle = () => {
  if (props.subscription.subscription_type === 'chart') {
    return `榜单订阅 - ${props.subscription.source_platform || '未知平台'}`
  } else if (props.subscription.subscription_type === 'keyword') {
    const site = props.subscription.music_site || '所有站点'
    const quality = props.subscription.music_quality || '自动音质'
    return `关键字搜索 - ${site} - ${quality}`
  }
  return ''
}

// 获取订阅封面
const getSubscriptionCover = () => {
  if (props.subscription.subscription_type === 'chart') {
    return '/chart-music-cover.png'
  } else if (props.subscription.subscription_type === 'keyword') {
    return '/keyword-music-cover.png'
  }
  return '/default-music-cover.png'
}

// 获取订阅类型标签
const getSubscriptionTypeLabel = () => {
  if (props.subscription.subscription_type === 'chart') {
    return '榜单订阅'
  } else if (props.subscription.subscription_type === 'keyword') {
    return '关键字订阅'
  }
  return '未知类型'
}

// 获取订阅类型颜色
const getSubscriptionTypeColor = () => {
  if (props.subscription.subscription_type === 'chart') {
    return 'primary'
  } else if (props.subscription.subscription_type === 'keyword') {
    return 'secondary'
  }
  return 'grey'
}

const getStatusColor = (status: string) => {
  return status === 'active' ? 'success' : 'warning'
}

const getStatusText = (status: string) => {
  return status === 'active' ? '活跃' : '暂停'
}

// 格式化日期
const formatDate = (dateString: string) => {
  try {
    return new Date(dateString).toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateString
  }
}

// 事件处理函数
const handleRunSubscription = async (dryRun: boolean = false) => {
  downloading.value = true
  try {
    const result: MusicSubscriptionRunResult = await runSubscriptionOnce(props.subscription.id, dryRun)
    emit('run', props.subscription.id)
    
    // 构建详细的消息
    const modeText = dryRun ? '试运行' : '运行'
    let message = `${modeText}完成：找到 ${result.found_total} 条候选`
    
    if (result.filtered_out && Object.keys(result.filtered_out).length > 0) {
      const filteredTotal = Object.values(result.filtered_out).reduce((sum, count) => sum + count, 0)
      message += `，过滤 ${filteredTotal} 条`
    }
    
    if (result.skipped_existing > 0) {
      message += `，跳过重复 ${result.skipped_existing} 条`
    }
    
    if (!dryRun && result.created_tasks > 0) {
      message += `，创建任务 ${result.created_tasks} 个`
    } else if (dryRun && result.found_total > 0) {
      message += '（试运行模式，未创建实际任务）'
    }
    
    if (result.errors && result.errors.length > 0) {
      message += `，${result.errors.length} 个错误`
      toast.warning(message)
    } else {
      toast.success(message)
    }
    
    // 触发父组件更新以刷新统计数据
    emit('updated')
    
  } catch (error: any) {
    console.error('运行订阅失败:', error)
    const errorMessage = error.response?.data?.detail || '未知错误'
    toast.error('运行失败：' + errorMessage)
  } finally {
    downloading.value = false
  }
}

const handleToggleStatus = async () => {
  toggling.value = true
  try {
    if (props.subscription.status === 'active') {
      await pauseMusicSubscription(props.subscription.id)
      toast.success('订阅已暂停')
    } else {
      await resumeMusicSubscription(props.subscription.id)
      toast.success('订阅已恢复')
    }
    emit('updated')
  } catch (error: any) {
    console.error('切换订阅状态失败:', error)
    toast.error('操作失败：' + (error.response?.data?.detail || '未知错误'))
  } finally {
    toggling.value = false
  }
}

const handleDelete = async () => {
  if (!confirm('确定要删除这个音乐订阅吗？此操作不可撤销。')) {
    return
  }
  
  try {
    await deleteMusicSubscription(props.subscription.id)
    emit('delete')
    toast.success('订阅已删除')
  } catch (error: any) {
    console.error('删除订阅失败:', error)
    toast.error('删除失败：' + (error.response?.data?.detail || '未知错误'))
  }
}
</script>

<style scoped>
.music-subscription-card {
  transition: all 0.3s ease;
}

.music-subscription-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.subscription-inactive {
  opacity: 0.7;
}
</style>

