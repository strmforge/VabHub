<template>
  <div class="music-subscriptions">
    <v-card variant="outlined" class="mb-4">
      <v-card-text class="pa-3">
        <v-row align="center">
          <v-col cols="auto">
            <v-btn
              color="purple"
              prepend-icon="mdi-plus"
              @click="showCreateDialog = true"
            >
              创建音乐订阅
            </v-btn>
          </v-col>
          <v-col cols="auto">
            <v-menu>
              <template v-slot:activator="{ props }">
                <v-btn
                  color="primary"
                  prepend-icon="mdi-play-circle-multiple"
                  :loading="batchRunning"
                  v-bind="props"
                  :disabled="filteredSubscriptions.length === 0"
                >
                  批量检查
                </v-btn>
              </template>
              <v-list>
                <v-list-item @click="handleRunAllSubscriptions(false)" title="运行全部激活订阅" />
                <v-list-item @click="handleRunAllSubscriptions(true)" title="试运行（仅统计）" />
              </v-list>
            </v-menu>
          </v-col>
          <v-col>
            <v-tabs v-model="activeTab" @update:model-value="loadSubscriptions">
              <v-tab value="all">全部</v-tab>
              <v-tab value="chart">榜单订阅</v-tab>
              <v-tab value="keyword">关键字订阅</v-tab>
              <v-tab value="active">活跃</v-tab>
              <v-tab value="paused">暂停</v-tab>
            </v-tabs>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
    
    <!-- 音乐订阅列表 -->
    <div v-if="loading" class="text-center py-12">
      <v-progress-circular indeterminate color="primary" size="64" />
      <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
    </div>

    <div v-else-if="filteredSubscriptions.length === 0" class="text-center py-12">
      <v-icon size="80" color="grey-darken-1" class="mb-4">mdi-music-off</v-icon>
      <div class="text-h5 font-weight-medium mb-2">暂无音乐订阅</div>
      <div class="text-body-2 text-medium-emphasis">
        使用"创建音乐订阅"按钮添加您的第一个音乐订阅
      </div>
    </div>

    <v-row v-else>
      <v-col
        v-for="subscription in filteredSubscriptions"
        :key="subscription.id"
        cols="12"
        sm="6"
        md="4"
        lg="3"
      >
        <MusicSubscriptionCard
          :subscription="subscription"
          @delete="loadSubscriptions"
          @updated="loadSubscriptions"
          @run="handleRunSubscription"
        />
      </v-col>
    </v-row>
    
    <!-- 创建对话框 -->
    <MusicSubscriptionDialog
      v-model="showCreateDialog"
      @saved="handleSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useToast } from 'vue-toastification'
import MusicSubscriptionCard from '@/components/music/MusicSubscriptionCard.vue'
import MusicSubscriptionDialog from '@/components/music/MusicSubscriptionDialog.vue'
import { 
  fetchMusicSubscriptions, 
  runSubscriptionOnce,
  runAllSubscriptions,
  type UserMusicSubscription,
  type MusicSubscriptionBatchRunResult
} from '@/services/music'

const loading = ref(false)
const batchRunning = ref(false)
const activeTab = ref('all')
const showCreateDialog = ref(false)
const musicSubscriptions = ref<UserMusicSubscription[]>([])
const toast = useToast()

const filteredSubscriptions = computed(() => {
  if (activeTab.value === 'all') {
    return musicSubscriptions.value
  } else if (activeTab.value === 'chart') {
    return musicSubscriptions.value.filter(s => s.subscription_type === 'chart')
  } else if (activeTab.value === 'keyword') {
    return musicSubscriptions.value.filter(s => s.subscription_type === 'keyword')
  } else if (activeTab.value === 'active') {
    return musicSubscriptions.value.filter(s => s.status === 'active')
  } else if (activeTab.value === 'paused') {
    return musicSubscriptions.value.filter(s => s.status === 'paused')
  }
  return musicSubscriptions.value
})

const loadSubscriptions = async () => {
  loading.value = true
  try {
    let params: any = {
      page: 1,
      page_size: 100
    }
    
    // 根据当前tab设置过滤参数
    if (activeTab.value === 'chart') {
      params.subscription_type = 'chart'
    } else if (activeTab.value === 'keyword') {
      params.subscription_type = 'keyword'
    } else if (activeTab.value === 'active') {
      params.status = 'active'
    } else if (activeTab.value === 'paused') {
      params.status = 'paused'
    }
    
    const response = await fetchMusicSubscriptions(params)
    musicSubscriptions.value = response.items
  } catch (error: any) {
    console.error('加载音乐订阅列表失败:', error)
    musicSubscriptions.value = []
  } finally {
    loading.value = false
  }
}

const handleSaved = () => {
  showCreateDialog.value = false
  loadSubscriptions()
}

const handleRunSubscription = async (subscriptionId: number) => {
  try {
    const result = await runSubscriptionOnce(subscriptionId)
    console.log('订阅运行结果:', result)
    // 可以显示成功消息
  } catch (error: any) {
    console.error('运行订阅失败:', error)
    // 可以显示错误消息
  }
}

const handleRunAllSubscriptions = async (dryRun: boolean = false) => {
  batchRunning.value = true
  try {
    const result: MusicSubscriptionBatchRunResult = await runAllSubscriptions(
      true, // onlyActive
      20,   // limit
      dryRun
    )
    
    // 构建详细的消息
    const modeText = dryRun ? '批量试运行' : '批量运行'
    let message = `${modeText}完成：共检查 ${result.total_subscriptions} 个订阅`
    
    if (result.summary.found_total > 0) {
      message += `，找到 ${result.summary.found_total} 条候选`
    }
    
    if (result.summary.filtered_total && Object.keys(result.summary.filtered_total).length > 0) {
      const filteredTotal = Object.values(result.summary.filtered_total).reduce((sum, count) => sum + count, 0)
      message += `，过滤 ${filteredTotal} 条`
    }
    
    if (!dryRun && result.summary.created_tasks_total > 0) {
      message += `，创建任务 ${result.summary.created_tasks_total} 个`
    } else if (dryRun && result.summary.found_total > 0) {
      message += '（试运行模式，未创建实际任务）'
    }
    
    message += `，成功 ${result.summary.succeeded_checks} 个，失败 ${result.summary.failed_checks} 个`
    
    if (result.summary.failed_checks > 0) {
      toast.warning(message)
    } else {
      toast.success(message)
    }
    
    // 刷新订阅列表以更新运行统计
    await loadSubscriptions()
    
  } catch (error: any) {
    console.error('批量运行订阅失败:', error)
    const errorMessage = error.response?.data?.detail || '未知错误'
    toast.error('批量运行失败：' + errorMessage)
  } finally {
    batchRunning.value = false
  }
}

const openCreateDialog = () => {
  showCreateDialog.value = true
}

defineExpose({
  reload: loadSubscriptions,
  openCreateDialog
})

onMounted(() => {
  loadSubscriptions()
})
</script>

<style scoped>
.music-subscriptions {
  padding: 0;
}
</style>

