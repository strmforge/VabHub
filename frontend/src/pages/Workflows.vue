<template>
  <div class="workflows-page">
    <PageHeader
      title="工作流管理"
      subtitle="自动化任务和工作流配置"
    />

    <v-container fluid class="pa-4">
      <!-- 操作栏 -->
      <v-card variant="outlined" class="mb-4">
        <v-card-text class="pa-3">
          <div class="d-flex align-center justify-space-between flex-wrap ga-2">
            <div class="d-flex align-center ga-2">
              <v-btn
                color="primary"
                prepend-icon="mdi-plus"
                @click="showWorkflowDialog = true"
              >
                创建工作流
              </v-btn>
              <v-btn
                color="secondary"
                prepend-icon="mdi-content-copy"
                @click="showTemplateDialog = true"
              >
                从模板创建
              </v-btn>
            </div>
            <div class="d-flex align-center ga-2">
              <v-switch
                v-model="activeOnly"
                label="仅显示启用"
                hide-details
                density="compact"
                @update:model-value="loadWorkflows"
              />
              <v-btn
                icon="mdi-refresh"
                variant="text"
                @click="loadWorkflows"
                :loading="loading"
              />
            </div>
          </div>
        </v-card-text>
      </v-card>

      <!-- 工作流列表 -->
      <div v-if="loading" class="text-center py-12">
        <v-progress-circular indeterminate color="primary" size="64" />
        <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
      </div>

      <div v-else-if="filteredWorkflows.length === 0" class="text-center py-12">
        <v-icon size="80" color="grey-darken-1" class="mb-4">mdi-workflow</v-icon>
        <div class="text-h5 font-weight-medium mb-2">暂无工作流</div>
        <div class="text-body-2 text-medium-emphasis mb-4">
          使用"创建工作流"按钮添加您的第一个工作流
        </div>
      </div>

      <v-row v-else>
        <v-col
          v-for="workflow in filteredWorkflows"
          :key="workflow.id"
          cols="12"
          md="6"
          lg="4"
        >
          <WorkflowCard
            :workflow="workflow"
            @edit="editWorkflow"
            @delete="deleteWorkflow"
            @execute="executeWorkflow"
            @toggle-status="toggleWorkflowStatus"
            @view-executions="viewExecutions"
          />
        </v-col>
      </v-row>
    </v-container>

    <!-- 工作流对话框 -->
    <WorkflowDialog
      v-model="showWorkflowDialog"
      :workflow="editingWorkflow"
      @saved="handleWorkflowSaved"
    />

    <!-- 执行记录对话框 -->
    <WorkflowExecutionsDialog
      v-model="showExecutionsDialog"
      :workflow-id="selectedWorkflowId"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import PageHeader from '@/components/common/PageHeader.vue'
import WorkflowCard from '@/components/workflow/WorkflowCard.vue'
import WorkflowDialog from '@/components/workflow/WorkflowDialog.vue'
import WorkflowExecutionsDialog from '@/components/workflow/WorkflowExecutionsDialog.vue'

const loading = ref(false)
const activeOnly = ref(false)
const workflows = ref<any[]>([])
const showWorkflowDialog = ref(false)
const showTemplateDialog = ref(false)
const showExecutionsDialog = ref(false)
const editingWorkflow = ref<any>(null)
const selectedWorkflowId = ref<number | null>(null)

const filteredWorkflows = computed(() => {
  if (!activeOnly.value) {
    return workflows.value
  }
  return workflows.value.filter(w => w.is_active)
})

const loadWorkflows = async () => {
  loading.value = true
  try {
    const response = await api.get('/workflows', {
      params: {
        active_only: activeOnly.value
      }
    })
    workflows.value = response.data
  } catch (error: any) {
    console.error('加载工作流列表失败:', error)
    alert('加载失败：' + (error.response?.data?.detail || '未知错误'))
  } finally {
    loading.value = false
  }
}

const editWorkflow = (workflow: any) => {
  editingWorkflow.value = workflow
  showWorkflowDialog.value = true
}

const deleteWorkflow = async (workflow: any) => {
  if (!confirm(`确定要删除工作流"${workflow.name}"吗？`)) {
    return
  }

  try {
    await api.delete(`/workflows/${workflow.id}`)
    await loadWorkflows()
  } catch (error: any) {
    console.error('删除工作流失败:', error)
    alert('删除失败：' + (error.response?.data?.detail || '未知错误'))
  }
}

const executeWorkflow = async (workflow: any) => {
  try {
    const response = await api.post(`/workflows/${workflow.id}/execute`, {})
    alert(response.data.success ? '工作流执行成功' : '工作流执行失败：' + (response.data.error || '未知错误'))
    await loadWorkflows()
  } catch (error: any) {
    console.error('执行工作流失败:', error)
    alert('执行失败：' + (error.response?.data?.detail || '未知错误'))
  }
}

const toggleWorkflowStatus = async (workflow: any) => {
  try {
    await api.put(`/workflows/${workflow.id}`, {
      is_active: !workflow.is_active
    })
    await loadWorkflows()
  } catch (error: any) {
    console.error('更新工作流状态失败:', error)
    alert('更新失败：' + (error.response?.data?.detail || '未知错误'))
  }
}

const viewExecutions = (workflow: any) => {
  selectedWorkflowId.value = workflow.id
  showExecutionsDialog.value = true
}

const handleWorkflowSaved = () => {
  loadWorkflows()
  editingWorkflow.value = null
}

onMounted(() => {
  loadWorkflows()
})
</script>

<style scoped>
.workflows-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
}
</style>

