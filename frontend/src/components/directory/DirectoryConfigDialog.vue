<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="800"
    persistent
  >
    <v-card>
      <v-card-title>
        <span class="text-h5">{{ directory ? '编辑目录配置' : '创建目录配置' }}</span>
      </v-card-title>

      <v-card-text>
        <v-form ref="formRef" v-model="valid">
          <v-row>
            <!-- 下载目录 -->
            <v-col cols="12">
              <PathInput
                v-model="form.download_path"
                label="下载目录 *"
                :rules="[rules.required]"
                required
                hint="源文件下载目录路径"
                persistent-hint
                root="/"
                storage="local"
              />
            </v-col>

            <!-- 媒体库目录 -->
            <v-col cols="12">
              <PathInput
                v-model="form.library_path"
                label="媒体库目录 *"
                :rules="[rules.required]"
                required
                hint="目标媒体库目录路径"
                persistent-hint
                root="/"
                storage="local"
              />
            </v-col>

            <!-- 存储类型 -->
            <v-col cols="12" md="6">
              <v-select
                v-model="form.storage"
                :items="storageOptions"
                label="源存储类型 *"
                :rules="[rules.required]"
                required
                variant="outlined"
                density="compact"
              />
            </v-col>

            <v-col cols="12" md="6">
              <v-select
                v-model="form.library_storage"
                :items="storageOptions"
                label="目标存储类型 *"
                :rules="[rules.required]"
                required
                variant="outlined"
                density="compact"
              />
            </v-col>

            <!-- 监控类型 -->
            <v-col cols="12" md="6">
              <v-select
                v-model="form.monitor_type"
                :items="monitorTypeOptions"
                label="监控类型"
                variant="outlined"
                density="compact"
                hint="选择文件整理触发方式"
                persistent-hint
              />
            </v-col>

            <!-- 整理方式 -->
            <v-col cols="12" md="6">
              <v-select
                v-model="form.transfer_type"
                :items="transferTypeOptions"
                label="整理方式"
                variant="outlined"
                density="compact"
                hint="文件整理时的操作方式"
                persistent-hint
              />
            </v-col>

            <!-- 媒体类型和类别 -->
            <v-col cols="12" md="6">
              <v-select
                v-model="form.media_type"
                :items="mediaTypeOptions"
                label="媒体类型"
                variant="outlined"
                density="compact"
                clearable
              />
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model="form.media_category"
                label="媒体类别"
                variant="outlined"
                density="compact"
                hint="自定义分类（可选）"
                persistent-hint
              />
            </v-col>

            <!-- 优先级 -->
            <v-col cols="12" md="6">
              <v-slider
                v-model="form.priority"
                label="优先级"
                min="0"
                max="100"
                step="1"
                thumb-label
                hint="数字越小优先级越高"
                persistent-hint
              >
                <template v-slot:append>
                  <v-text-field
                    v-model.number="form.priority"
                    type="number"
                    style="width: 80px"
                    density="compact"
                    hide-details
                  />
                </template>
              </v-slider>
            </v-col>

            <!-- 启用状态 -->
            <v-col cols="12" md="6">
              <v-switch
                v-model="form.enabled"
                label="启用此配置"
                color="primary"
                hide-details
              />
            </v-col>

            <!-- STRM 开关（仅对支持的媒体类型显示） -->
            <v-col cols="12" v-if="supportsStrm">
              <v-switch
                v-model="form.enable_strm"
                label="启用 STRM 模式"
                color="primary"
                hint="生成 STRM 文件，指向云存储中的实际文件"
                persistent-hint
              />
            </v-col>

            <!-- 书籍类型提示 -->
            <v-col cols="12" v-if="form.media_type === 'book'">
              <v-alert
                type="info"
                variant="tonal"
                density="compact"
              >
                书籍类（电子书 / 有声书 / TXT）当前只支持本地真实文件，不支持 STRM。
              </v-alert>
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
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
          :disabled="!valid"
        >
          保存
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import api from '@/services/api'
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

const toast = useToast()
const formRef = ref()
const valid = ref(false)
const saving = ref(false)

// 表单数据
const form = ref({
  download_path: '',
  library_path: '',
  storage: 'local',
  library_storage: 'local',
  monitor_type: null as string | null,
  transfer_type: null as string | null,
  media_type: null as string | null,
  media_category: '',
  priority: 0,
  enabled: true,
  enable_strm: false
})

// 选项
const storageOptions = [
  { title: '本地存储', value: 'local' },
  { title: '115网盘', value: '115' },
  { title: '123网盘', value: '123' }
]

const monitorTypeOptions = [
  { title: '下载器监控', value: 'downloader' },
  { title: '目录监控', value: 'directory' },
  { title: '不监控', value: null }
]

const transferTypeOptions = [
  { title: '复制', value: 'copy' },
  { title: '移动', value: 'move' },
  { title: '硬链接', value: 'link' },
  { title: '软链接', value: 'softlink' }
]

const mediaTypeOptions = [
  { title: '电影', value: 'movie' },
  { title: '电视剧', value: 'tv' },
  { title: '短剧', value: 'short_drama' },
  { title: '音乐', value: 'music' },
  { title: '书籍', value: 'book' },
  { title: '动漫', value: 'anime' }
]

// STRM 支持的媒体类型
const STRM_SUPPORTED_MEDIA_TYPES = ['movie', 'tv', 'short_drama', 'music', 'anime'] as const

// 判断当前媒体类型是否支持 STRM
const supportsStrm = computed(() => {
  if (!form.value.media_type) return false
  return STRM_SUPPORTED_MEDIA_TYPES.includes(form.value.media_type as any)
})

// 验证规则
const rules = {
  required: (v: any) => !!v || '此字段为必填项'
}

// 监听目录变化
watch(() => props.directory, (newDir) => {
  if (newDir) {
    form.value = {
      download_path: newDir.download_path || '',
      library_path: newDir.library_path || '',
      storage: newDir.storage || 'local',
      library_storage: newDir.library_storage || 'local',
      monitor_type: newDir.monitor_type,
      transfer_type: newDir.transfer_type,
      media_type: newDir.media_type,
      media_category: newDir.media_category || '',
      priority: newDir.priority || 0,
      enabled: newDir.enabled !== undefined ? newDir.enabled : true,
      enable_strm: newDir.enable_strm !== undefined ? newDir.enable_strm : false
    }
  } else {
    // 重置表单
    form.value = {
      download_path: '',
      library_path: '',
      storage: 'local',
      library_storage: 'local',
      monitor_type: null,
      transfer_type: null,
      media_type: null,
      media_category: '',
      priority: 0,
      enabled: true,
      enable_strm: false
    }
  }
}, { immediate: true })

// 监听媒体类型变化，自动关闭 STRM（如果切换到不支持的类型）
watch(
  () => form.value.media_type,
  (type) => {
    if (type && !STRM_SUPPORTED_MEDIA_TYPES.includes(type as any)) {
      form.value.enable_strm = false
    }
  }
)

// 保存
const handleSave = async () => {
  if (!formRef.value?.validate()) {
    return
  }

  try {
    saving.value = true
    const data = { ...form.value }
    
    let response
    if (props.directory) {
      // 更新
      response = await api.put(`/directories/${props.directory.id}`, data)
    } else {
      // 创建
      response = await api.post('/directories', data)
    }

    if (response.data.success) {
      toast.success(props.directory ? '更新成功' : '创建成功')
      emit('saved')
      emit('update:modelValue', false)
    } else {
      toast.error(response.data.error_message || '操作失败')
    }
  } catch (error: any) {
    toast.error(error.response?.data?.error_message || '操作失败')
  } finally {
    saving.value = false
  }
}
</script>

