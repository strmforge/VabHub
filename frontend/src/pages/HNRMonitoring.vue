<template>
  <div class="hnr-monitoring-page">
    <PageHeader
      title="HNR风险检测"
      subtitle="智能做种管理和风险预警"
    >
      <template v-slot:actions>
        <v-btn
          color="warning"
          prepend-icon="mdi-cog"
          @click="showSettings = true"
        >
          风险设置
        </v-btn>
      </template>
    </PageHeader>
    
    <!-- 风险概览卡片 -->
    <v-row class="mb-4">
      <v-col cols="12">
        <HNRStatusCard
          :risk-tasks="highRiskTasks"
          :overall-risk="riskStats.high > 0 ? 70 : riskStats.medium > 0 ? 40 : 10"
        />
      </v-col>
    </v-row>

    <!-- 风险统计 -->
    <v-row class="mb-4">
      <v-col cols="12" sm="6" md="3">
        <v-card variant="outlined" color="error">
          <v-card-text class="text-center">
            <div class="text-h4 font-weight-bold">{{ riskStats.high }}</div>
            <div class="text-body-2 text-medium-emphasis">高风险任务</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card variant="outlined" color="warning">
          <v-card-text class="text-center">
            <div class="text-h4 font-weight-bold">{{ riskStats.medium }}</div>
            <div class="text-body-2 text-medium-emphasis">中风险任务</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card variant="outlined" color="success">
          <v-card-text class="text-center">
            <div class="text-h4 font-weight-bold">{{ riskStats.low }}</div>
            <div class="text-body-2 text-medium-emphasis">低风险任务</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card variant="outlined">
          <v-card-text class="text-center">
            <div class="text-h4 font-weight-bold">{{ riskStats.total }}</div>
            <div class="text-body-2 text-medium-emphasis">总监控任务</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    
    <!-- 风险任务列表 -->
    <v-card variant="outlined">
      <v-card-title class="d-flex align-center justify-space-between">
        <span>风险任务列表</span>
        <v-btn
          icon="mdi-refresh"
          variant="text"
          size="small"
          @click="refreshData"
          :loading="loading"
        />
      </v-card-title>
      <v-card-text>
        <div v-if="loading" class="text-center py-12">
          <v-progress-circular indeterminate color="primary" size="64" />
          <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
        </div>
        <div v-else-if="riskTasks.length === 0" class="text-center py-12">
          <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-shield-check</v-icon>
          <div class="text-h6 text-medium-emphasis mb-2">暂无监控任务</div>
          <div class="text-body-2 text-medium-emphasis">当前没有需要监控的下载任务</div>
        </div>
        <HNRTaskList v-else :tasks="riskTasks" @refresh="refreshData" />
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import api from '@/services/api'
import PageHeader from '@/components/common/PageHeader.vue'
import HNRStatusCard from '@/components/hnr/HNRStatusCard.vue'
import HNRTaskList from '@/components/hnr/HNRTaskList.vue'

const loading = ref(false)
const showSettings = ref(false)
const riskStats = ref({
  total: 0,
  high: 0,
  medium: 0,
  low: 0
})
const riskTasks = ref<any[]>([])

const highRiskTasks = computed(() => {
  return riskTasks.value.filter(t => t.risk_score >= 0.7)
})

const mediumRiskTasks = computed(() => {
  return riskTasks.value.filter(t => t.risk_score >= 0.3 && t.risk_score < 0.7)
})

const lowRiskTasks = computed(() => {
  return riskTasks.value.filter(t => t.risk_score < 0.3)
})

const loadStats = async () => {
  try {
    const response = await api.get('/hnr/stats')
    riskStats.value = response.data
  } catch (error: any) {
    console.error('加载HNR统计失败:', error)
  }
}

const loadTasks = async () => {
  loading.value = true
  try {
    const response = await api.get('/hnr/tasks', {
      params: {
        status: 'monitoring'
      }
    })
    riskTasks.value = response.data
  } catch (error: any) {
    console.error('加载HNR任务失败:', error)
    riskTasks.value = []
  } finally {
    loading.value = false
  }
}

const refreshData = async () => {
  await Promise.all([loadStats(), loadTasks()])
}

onMounted(() => {
  refreshData()
})
</script>

