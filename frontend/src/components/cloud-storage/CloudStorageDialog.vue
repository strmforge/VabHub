<template>
  <v-dialog
    :model-value="modelValue"
    max-width="600"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <v-card>
      <v-card-title>
        {{ storage ? '编辑云存储' : '添加云存储' }}
      </v-card-title>
      
      <v-card-text>
        <v-form ref="formRef">
          <v-text-field
            v-model="form.name"
            label="存储名称"
            :rules="[rules.required]"
            required
          ></v-text-field>
          
          <v-select
            v-model="form.provider"
            label="提供商"
            :items="providers"
            item-title="label"
            item-value="value"
            :rules="[rules.required]"
            required
            @update:model-value="handleProviderChange"
          ></v-select>
          
          <!-- 115网盘配置 -->
          <div v-if="form.provider === '115'">
            <v-alert type="info" variant="tonal" class="mb-4">
              115网盘使用开发者密钥进行认证，密钥已加密存储。
            </v-alert>
          </div>
          
          <!-- RClone配置 -->
          <div v-if="form.provider === 'rclone'">
            <v-text-field
              v-model="form.rclone_remote_name"
              label="远程名称"
              hint="RClone远程配置名称"
              persistent-hint
            ></v-text-field>
            
            <v-text-field
              v-model="form.rclone_config_path"
              label="配置文件路径"
              hint="RClone配置文件路径（默认: ~/.config/rclone/rclone.conf）"
              persistent-hint
            ></v-text-field>
          </div>
          
          <!-- OpenList配置 -->
          <div v-if="form.provider === 'openlist'">
            <v-text-field
              v-model="form.openlist_server_url"
              label="服务器地址"
              hint="OpenList服务器地址"
              persistent-hint
            ></v-text-field>
          </div>
          
          <v-switch
            v-model="form.enabled"
            label="启用"
            color="primary"
          ></v-switch>
        </v-form>
      </v-card-text>
      
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn
          variant="text"
          @click="$emit('update:modelValue', false)"
        >
          取消
        </v-btn>
        <v-btn
          color="primary"
          :loading="loading"
          @click="handleSave"
        >
          保存
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import api from '@/services/api'

const props = defineProps<{
  modelValue: boolean
  storage?: any
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  saved: []
}>()
const formRef = ref()
const loading = ref(false)

const providers = [
  { label: '115网盘', value: '115' },
  { label: 'RClone', value: 'rclone' },
  { label: 'OpenList', value: 'openlist' }
]

const form = reactive({
  name: '',
  provider: '115',
  enabled: true,
  rclone_remote_name: 'VabHub',
  rclone_config_path: '',
  openlist_server_url: 'https://api.oplist.org.cn'
})

const rules = {
  required: (value: any) => !!value || '此字段为必填项'
}

// 监听storage变化
watch(() => props.storage, (newStorage) => {
  if (newStorage) {
    form.name = newStorage.name
    form.provider = newStorage.provider
    form.enabled = newStorage.enabled
    form.rclone_remote_name = newStorage.rclone_remote_name || 'VabHub'
    form.rclone_config_path = newStorage.rclone_config_path || ''
    form.openlist_server_url = newStorage.openlist_server_url || 'https://api.oplist.org.cn'
  } else {
    // 重置表单
    form.name = ''
    form.provider = '115'
    form.enabled = true
    form.rclone_remote_name = 'VabHub'
    form.rclone_config_path = ''
    form.openlist_server_url = 'https://api.oplist.org.cn'
  }
}, { immediate: true })

// 处理提供商变更
const handleProviderChange = () => {
  // 可以根据提供商类型设置默认值
}

// 处理保存
const handleSave = async () => {
  const { valid } = await formRef.value.validate()
  if (!valid) {
    return
  }
  
  try {
    loading.value = true
    
    const data: any = {
      name: form.name,
      provider: form.provider,
      enabled: form.enabled
    }
    
    if (form.provider === 'rclone') {
      data.rclone_remote_name = form.rclone_remote_name
      data.rclone_config_path = form.rclone_config_path
    } else if (form.provider === 'openlist') {
      data.openlist_server_url = form.openlist_server_url
    }
    
    if (props.storage) {
      await api.put(`/cloud-storage/${props.storage.id}`, data)
    } else {
      await api.post('/cloud-storage', data)
    }
    
    emit('saved')
    emit('update:modelValue', false)
  } catch (error) {
    console.error('保存云存储配置失败:', error)
    alert('保存失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
</style>

