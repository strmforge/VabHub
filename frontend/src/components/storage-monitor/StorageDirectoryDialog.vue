<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="600"
  >
    <v-card>
      <v-card-title>
        <span class="text-h5">{{ directory ? '编辑存储目录' : '创建存储目录' }}</span>
      </v-card-title>

      <v-card-text>
        <v-form ref="formRef" v-model="valid">
          <v-text-field
            v-model="form.name"
            label="目录名称"
            :rules="[rules.required]"
            required
            class="mb-2"
          />

          <!-- 使用路径选择组件 -->
          <PathInput
            v-model="form.path"
            label="目录路径"
            :rules="[rules.required, rules.path]"
            required
            hint="点击选择或手动输入路径，例如: /data/media 或 C:\Media"
            persistent-hint
            root="/"
            storage="local"
            class="mb-2"
          />

          <v-switch
            v-model="form.enabled"
            label="启用监控"
            color="primary"
            class="mb-2"
          />

          <v-slider
            v-model="form.alert_threshold"
            label="预警阈值 (%)"
            min="0"
            max="100"
            step="1"
            thumb-label
            class="mb-2"
          >
            <template v-slot:append>
              <v-text-field
                v-model.number="form.alert_threshold"
                type="number"
                style="width: 80px"
                density="compact"
                hide-details
              />
            </template>
          </v-slider>

          <v-textarea
            v-model="form.description"
            label="描述（可选）"
            rows="3"
            class="mb-2"
          />
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
          :loading="saving"
          @click="handleSave"
        >
          保存
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { storageMonitorApi } from '@/services/api'
import { useToast } from '@/composables/useToast'
import PathInput from '@/components/common/PathInput.vue'

const props = defineProps<{
  modelValue: boolean
  directory?: any
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  saved: []
}>()

const { showToast } = useToast()

const formRef = ref()
const valid = ref(false)
const saving = ref(false)

const form = ref({
  name: '',
  path: '',
  enabled: true,
  alert_threshold: 80,
  description: ''
})

const rules = {
  required: (v: any) => !!v || '此字段为必填项',
  path: (v: string) => {
    if (!v) return true
    // 简单的路径验证
    if (v.length < 2) return '路径太短'
    return true
  }
}

// 监听directory变化，填充表单
watch(() => props.directory, (newDir) => {
  if (newDir) {
    form.value = {
      name: newDir.name || '',
      path: newDir.path || '',
      enabled: newDir.enabled !== undefined ? newDir.enabled : true,
      alert_threshold: newDir.alert_threshold || 80,
      description: newDir.description || ''
    }
  } else {
    // 重置表单
    form.value = {
      name: '',
      path: '',
      enabled: true,
      alert_threshold: 80,
      description: ''
    }
  }
}, { immediate: true })

// 保存
const handleSave = async () => {
  const { valid: isValid } = await formRef.value.validate()
  if (!isValid) {
    return
  }

  try {
    saving.value = true

    if (props.directory) {
      // 更新
      await storageMonitorApi.updateDirectory(props.directory.id, form.value)
      showToast('更新成功', 'success')
    } else {
      // 创建
      await storageMonitorApi.createDirectory(form.value)
      showToast('创建成功', 'success')
    }

    emit('saved')
    emit('update:modelValue', false)
  } catch (error: any) {
    showToast('保存失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    saving.value = false
  }
}
</script>

