<template>
  <div>
    <!-- LLM 未配置警告 -->
    <v-alert
      v-if="!status.llm_configured && !status.loading"
      type="warning"
      variant="tonal"
      class="mb-4"
      density="comfortable"
    >
      <template #title>
        <div class="d-flex align-center">
          <v-icon class="mr-2">mdi-cloud-off-outline</v-icon>
          AI 总控尚未配置 LLM 服务
        </div>
      </template>
      <div class="text-body-2 mt-1">
        当前处于演示模式（Dummy LLM），功能受限。请参考配置文档启用外部大模型。
      </div>
      <template #append>
        <v-btn
          variant="outlined"
          size="small"
          href="https://github.com/your-repo/vabhub#ai-configuration"
          target="_blank"
        >
          查看配置文档
        </v-btn>
      </template>
    </v-alert>

    <!-- Orchestrator 未启用 -->
    <v-alert
      v-else-if="!status.enabled && !status.loading"
      type="error"
      variant="tonal"
      class="mb-4"
      density="comfortable"
    >
      <template #title>
        <div class="d-flex align-center">
          <v-icon class="mr-2">mdi-robot-off</v-icon>
          AI 总控未启用
        </div>
      </template>
      <div class="text-body-2 mt-1">
        请在配置中设置 <code>AI_ORCH_ENABLED=true</code> 以启用 AI 功能。
      </div>
    </v-alert>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { aiOrchestratorApi } from '@/api/aiOrchestrator'

const status = ref({
  enabled: true,
  llm_configured: true,
  loading: true,
})

async function loadStatus() {
  try {
    const res = await aiOrchestratorApi.getStatus()
    status.value = {
      enabled: res.enabled,
      llm_configured: res.llm_configured,
      loading: false,
    }
  } catch (e: any) {
    console.error('获取 AI 状态失败:', e)
    // 如果获取失败，假设未配置
    status.value = {
      enabled: false,
      llm_configured: false,
      loading: false,
    }
  }
}

onMounted(() => {
  loadStatus()
})
</script>
