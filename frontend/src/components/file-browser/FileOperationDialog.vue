<template>
  <v-dialog v-model="dialog" max-width="600" persistent>
    <v-card>
      <v-card-title>
        {{ getTitle() }}
      </v-card-title>
      
      <v-card-text>
        <!-- 重命名 -->
        <v-form v-if="operation === 'rename'" ref="renameFormRef">
          <v-text-field
            v-model="renameForm.newName"
            label="新名称"
            variant="outlined"
            :rules="[v => !!v || '请输入新名称']"
            autofocus
          />
        </v-form>
        
        <!-- 整理文件 -->
        <v-form v-else-if="operation === 'transfer'" ref="transferFormRef">
          <v-select
            v-model="transferForm.targetStorage"
            :items="storageOptions"
            label="目标存储"
            variant="outlined"
            class="mb-4"
          />
          
          <v-text-field
            v-model="transferForm.targetPath"
            label="目标路径"
            variant="outlined"
            prepend-inner-icon="mdi-folder"
            hint="请输入目标路径"
            class="mb-4"
          />
          
          <v-select
            v-model="transferForm.transferType"
            :items="transferTypeOptions"
            label="整理方式"
            variant="outlined"
            class="mb-4"
          />
          
          <v-select
            v-model="transferForm.overwriteMode"
            :items="overwriteModeOptions"
            label="覆盖模式"
            variant="outlined"
          />
        </v-form>
      </v-card-text>
      
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="close">取消</v-btn>
        <v-btn color="primary" :loading="loading" @click="handleSubmit">确定</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useToast } from '@/composables/useToast'
import api from '@/services/api'

interface Props {
  modelValue: boolean
  file: any | null
  operation: string | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: []
}>()

const toast = useToast()
const dialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const loading = ref(false)
const renameFormRef = ref()
const transferFormRef = ref()

const renameForm = ref({
  newName: ''
})

const transferForm = ref({
  targetStorage: 'local',
  targetPath: '',
  transferType: 'move',
  overwriteMode: 'never'
})

const storageOptions = [
  { title: '本地存储', value: 'local' },
  { title: '115网盘', value: '115' },
  { title: 'RClone', value: 'rclone' },
  { title: 'OpenList', value: 'openlist' }
]

const transferTypeOptions = [
  { title: '移动', value: 'move' },
  { title: '复制', value: 'copy' },
  { title: '硬链接', value: 'link' },
  { title: '软链接', value: 'softlink' }
]

const overwriteModeOptions = [
  { title: '从不覆盖', value: 'never' },
  { title: '总是覆盖', value: 'always' },
  { title: '按大小覆盖', value: 'size' },
  { title: '覆盖旧文件', value: 'latest' }
]

const getTitle = () => {
  switch (props.operation) {
    case 'rename':
      return '重命名'
    case 'transfer':
      return '整理文件'
    default:
      return '操作'
  }
}

// 监听文件变化，初始化表单
watch(() => props.file, (file) => {
  if (file) {
    if (props.operation === 'rename') {
      renameForm.value.newName = file.name
    } else if (props.operation === 'transfer') {
      // 可以设置默认目标路径
      transferForm.value.targetPath = ''
    }
  }
}, { immediate: true })

const handleSubmit = async () => {
  if (!props.file) return
  
  loading.value = true
  
  try {
    if (props.operation === 'rename') {
      const { valid } = await renameFormRef.value?.validate()
      if (!valid) return
      
      await api.post('/file-browser/rename', {
        storage: 'local', // TODO: 从上下文获取
        path: props.file.path,
        new_name: renameForm.value.newName
      })
      
      toast.success('重命名成功')
      emit('success')
      close()
    } else if (props.operation === 'transfer') {
      const { valid } = await transferFormRef.value?.validate()
      if (!valid) return
      
      await api.post('/file-browser/transfer', {
        source_storage: 'local', // TODO: 从上下文获取
        source_path: props.file.path,
        target_storage: transferForm.value.targetStorage,
        target_path: transferForm.value.targetPath,
        transfer_type: transferForm.value.transferType,
        overwrite_mode: transferForm.value.overwriteMode
      })
      
      toast.success('整理成功')
      emit('success')
      close()
    }
  } catch (error: any) {
    toast.error(error.message || '操作失败')
  } finally {
    loading.value = false
  }
}

const close = () => {
  dialog.value = false
  renameForm.value.newName = ''
  transferForm.value = {
    targetStorage: 'local',
    targetPath: '',
    transferType: 'move',
    overwriteMode: 'never'
  }
}
</script>

