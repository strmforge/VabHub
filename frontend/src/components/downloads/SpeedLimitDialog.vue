<template>
  <v-dialog v-model="dialog" max-width="500px" persistent>
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-speedometer</v-icon>
        <span>{{ props.taskIds && props.taskIds.length > 0 ? `批量速度限制设置 (${props.taskIds.length}个任务)` : '速度限制设置' }}</span>
        <v-spacer />
        <v-btn icon variant="text" @click="close">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      
      <v-divider />
      
      <v-card-text class="pt-4">
        <v-form ref="formRef">
          <v-text-field
            v-model.number="downloadLimit"
            label="下载速度限制 (MB/s)"
            type="number"
            min="0"
            step="0.1"
            prepend-inner-icon="mdi-download"
            variant="outlined"
            density="comfortable"
            hint="留空表示无限制"
            persistent-hint
            class="mb-4"
          />
          
          <v-text-field
            v-model.number="uploadLimit"
            label="上传速度限制 (MB/s)"
            type="number"
            min="0"
            step="0.1"
            prepend-inner-icon="mdi-upload"
            variant="outlined"
            density="comfortable"
            hint="留空表示无限制"
            persistent-hint
          />
        </v-form>
      </v-card-text>
      
      <v-divider />
      
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="close">取消</v-btn>
        <v-btn color="primary" variant="elevated" @click="save" :loading="saving">
          保存
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { downloadApi } from '@/services/api'
import { useToast } from '@/composables/useToast'

const props = defineProps<{
  modelValue: boolean
  taskId?: string | null
  taskIds?: string[]
  downloader?: string
  currentDownloadLimit?: number | null
  currentUploadLimit?: number | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'saved': []
}>()

const toast = useToast()
const dialog = ref(props.modelValue)
const downloadLimit = ref<number | null>(props.currentDownloadLimit ?? null)
const uploadLimit = ref<number | null>(props.currentUploadLimit ?? null)
const saving = ref(false)
const formRef = ref()

watch(() => props.modelValue, (val) => {
  dialog.value = val
  if (val) {
    downloadLimit.value = props.currentDownloadLimit ?? null
    uploadLimit.value = props.currentUploadLimit ?? null
  }
})

watch(dialog, (val) => {
  emit('update:modelValue', val)
})

const close = () => {
  dialog.value = false
}

const save = async () => {
  saving.value = true
  try {
    const data: { download_limit?: number; upload_limit?: number } = {}
    if (downloadLimit.value !== null && downloadLimit.value > 0) {
      data.download_limit = downloadLimit.value
    }
    if (uploadLimit.value !== null && uploadLimit.value > 0) {
      data.upload_limit = uploadLimit.value
    }
    
    if (props.taskIds && props.taskIds.length > 0) {
      // 批量设置任务速度限制
      await downloadApi.batchSetSpeedLimit(props.taskIds, data)
      toast.success(`已为 ${props.taskIds.length} 个任务设置速度限制`)
    } else if (props.taskId) {
      // 设置单个任务的速度限制
      await downloadApi.setTaskSpeedLimit(props.taskId, data)
      toast.success('任务速度限制设置成功')
    } else if (props.downloader) {
      // 设置全局速度限制
      await downloadApi.setGlobalSpeedLimit(props.downloader, data)
      toast.success('全局速度限制设置成功')
    } else {
      toast.error('缺少必要参数')
      return
    }
    
    emit('saved')
    close()
  } catch (error: any) {
    toast.error('设置速度限制失败：' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}
</script>

