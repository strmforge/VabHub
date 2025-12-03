<template>
  <v-dialog 
    v-model="dialogVisible" 
    max-width="900px" 
    persistent
    scrollable
  >
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="me-2">mdi-folder-move</v-icon>
        手动整理媒体文件
        <v-spacer />
        <v-btn icon variant="text" @click="closeDialog">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      
      <v-divider />
      
      <v-card-text class="pa-4">
        <v-form ref="formRef" v-model="formValid" @submit.prevent="handleSubmit">
          <!-- 原始信息显示 -->
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-h6">原始信息</v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="12" md="6">
                  <div class="text-caption text-medium-emphasis mb-1">源文件路径</div>
                  <div class="text-body-2 font-family-monospace">{{ config?.src }}</div>
                </v-col>
                <v-col cols="12" md="6">
                  <div class="text-caption text-medium-emphasis mb-1">原始标题</div>
                  <div class="text-body-2">{{ config?.title || '未知' }}</div>
                </v-col>
                <v-col cols="12" md="6">
                  <div class="text-caption text-medium-emphasis mb-1">媒体类型</div>
                  <div class="text-body-2">{{ config?.type || '-' }}</div>
                </v-col>
                <v-col cols="12" md="6">
                  <div class="text-caption text-medium-emphasis mb-1">年份</div>
                  <div class="text-body-2">{{ config?.year || '-' }}</div>
                </v-col>
                <v-col cols="12" v-if="config?.errmsg">
                  <div class="text-caption text-medium-emphasis mb-1">错误信息</div>
                  <div class="text-body-2 text-error">{{ config.errmsg }}</div>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- 目标配置 -->
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-h6">目标配置</v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="12" md="6">
                  <v-select
                    v-model="formData.dest_storage"
                    :items="storageOptions"
                    :loading="loadingStorages"
                    item-title="label"
                    item-value="key"
                    label="目标存储"
                    variant="outlined"
                    density="compact"
                    :rules="[(v: any) => !!v || '请选择目标存储']"
                    :disabled="loadingStorages"
                    required
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-select
                    v-model="formData.operation_mode"
                    :items="operationModeOptions"
                    label="整理方式"
                    variant="outlined"
                    density="compact"
                    :rules="[(v: any) => !!v || '请选择整理方式']"
                    required
                  />
                </v-col>
                <v-col cols="12">
                  <v-text-field
                    v-model="formData.dest_path"
                    label="目标路径（可选，留空则自动生成）"
                    variant="outlined"
                    density="compact"
                    placeholder="例如：/电影/动作片/复仇者联盟"
                    hint="如果不指定，系统将根据媒体信息自动生成路径"
                    persistent-hint
                  />
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- 媒体信息 -->
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-h6 d-flex align-center">
              媒体信息
              <v-spacer />
              <v-btn
                size="small"
                variant="outlined"
                prepend-icon="mdi-magnify"
                @click="showTmdbSearch = true"
              >
                TMDB 搜索
              </v-btn>
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="12" md="6">
                  <v-select
                    v-model="formData.media_type"
                    :items="mediaTypeOptions"
                    label="媒体类型"
                    variant="outlined"
                    density="compact"
                    :rules="[(v: any) => !!v || '请选择媒体类型']"
                    required
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="formData.year"
                    label="年份"
                    variant="outlined"
                    density="compact"
                    type="number"
                    :rules="[
                      (v: any) => !v || (v >= 1900 && v <= 2030) || '年份必须在1900-2030之间'
                    ]"
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="formData.title"
                    label="标题"
                    variant="outlined"
                    density="compact"
                    :rules="[(v: any) => !!v || '请输入标题']"
                    required
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="formData.tmdb_id"
                    label="TMDB ID（可选）"
                    variant="outlined"
                    density="compact"
                    type="number"
                    hint="如果指定了TMDB ID，将优先使用TMDB信息"
                    persistent-hint
                  />
                </v-col>
                <v-col cols="12" md="6" v-if="formData.media_type === 'tv'">
                  <v-text-field
                    v-model="formData.season"
                    label="季数"
                    variant="outlined"
                    density="compact"
                    placeholder="例如：S01 或 第1季"
                    hint="电视剧的季数信息"
                    persistent-hint
                  />
                </v-col>
                <v-col cols="12" md="6" v-if="formData.media_type === 'tv'">
                  <v-text-field
                    v-model="formData.episodes"
                    label="集数"
                    variant="outlined"
                    density="compact"
                    placeholder="例如：E01-E02 或 第1-2集"
                    hint="电视剧的集数信息"
                    persistent-hint
                  />
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- 高级选项 -->
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-h6">高级选项</v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="12" md="6">
                  <v-checkbox
                    v-model="formData.use_classification"
                    label="使用分类规则"
                    hint="根据媒体类型自动分类到子目录"
                    density="compact"
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-checkbox
                    v-model="formData.delete_source"
                    label="删除源文件"
                    hint="仅在整理方式为&quot;移动&quot;时有效"
                    density="compact"
                    :disabled="formData.operation_mode !== 'move'"
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-checkbox
                    v-model="formData.reuse_history_meta"
                    label="复用历史元数据"
                    hint="保留原始历史记录中的其他元数据"
                    density="compact"
                  />
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-form>
      </v-card-text>

      <v-divider />
      
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="closeDialog">取消</v-btn>
        <v-btn
          color="primary"
          :loading="submitting"
          :disabled="!formValid"
          @click="handleSubmit"
        >
          开始整理
        </v-btn>
      </v-card-actions>
    </v-card>

    <!-- TMDB 搜索对话框 -->
    <TmdbSearchDialog
      v-if="showTmdbSearch"
      :initial-query="formData.title"
      :media-type="formData.media_type"
      @close="showTmdbSearch = false"
      @select="onTmdbSelect"
    />
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import { useToast } from '@/composables/useToast'
import api from '@/services/api'
import TmdbSearchDialog from './TmdbSearchDialog.vue'

// 类型定义
interface ManualStorageOption {
  key: string
  label: string
  kind: string
}

interface ManualTransferConfig {
  id: number
  src: string
  dest: string
  src_storage: string
  dest_storage: string
  mode: string
  type?: string
  category?: string
  title?: string
  year?: string
  tmdbid?: number
  seasons?: string
  episodes?: string
  errmsg?: string
}

interface Props {
  config?: ManualTransferConfig | null
}

interface Emits {
  (e: 'close'): void
  (e: 'complete', success: boolean): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const toast = useToast()

// 对话框显示状态
const dialogVisible = computed({
  get: () => !!props.config,
  set: (value) => {
    if (!value) closeDialog()
  }
})

// 表单相关
const formRef = ref()
const formValid = ref(false)
const submitting = ref(false)

// TMDB 搜索对话框
const showTmdbSearch = ref(false)

// 表单数据
const formData = ref({
  history_id: 0,
  dest_storage: '',
  dest_path: '',
  operation_mode: 'copy',
  media_type: 'movie',
  title: '',
  year: null as number | null,
  tmdb_id: null as number | null,
  season: '',
  episodes: '',
  use_classification: true,
  delete_source: false,
  reuse_history_meta: true
})

// 存储选项状态
const storageOptions = ref<ManualStorageOption[]>([])
const loadingStorages = ref(false)

// 选项数据
const operationModeOptions = [
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
  { title: '其他', value: 'other' }
]

// 监听配置变化，初始化表单
watch(() => props.config, (newConfig) => {
  if (newConfig) {
    formData.value = {
      history_id: newConfig.id,
      dest_storage: newConfig.dest_storage || 'local',
      dest_path: '',
      operation_mode: newConfig.mode || 'copy',
      media_type: newConfig.type || 'movie',
      title: newConfig.title || '',
      year: newConfig.year ? parseInt(newConfig.year) : null,
      tmdb_id: newConfig.tmdbid || null,
      season: newConfig.seasons || '',
      episodes: newConfig.episodes || '',
      use_classification: true,
      delete_source: false,
      reuse_history_meta: true
    }
  }
}, { immediate: true })

// 获取存储选项
const fetchStorageOptions = async () => {
  loadingStorages.value = true
  try {
    const response = await api.get('/storage/manual-transfer-options')
    storageOptions.value = response.data
    
    // 设置默认值：如果原存储在列表中，使用原存储；否则优先选择local
    if (props.config?.dest_storage) {
      const hasOriginalStorage = storageOptions.value.some(option => option.key === props.config!.dest_storage)
      if (!hasOriginalStorage) {
        // 原存储不在列表中，优先选择local
        const hasLocal = storageOptions.value.some(option => option.key === 'local')
        formData.value.dest_storage = hasLocal ? 'local' : storageOptions.value[0]?.key || ''
      }
    } else {
      // 没有原配置，优先选择local
      const hasLocal = storageOptions.value.some(option => option.key === 'local')
      formData.value.dest_storage = hasLocal ? 'local' : storageOptions.value[0]?.key || ''
    }
  } catch (error: any) {
    console.error('获取存储选项失败:', error)
    toast.error('获取存储选项失败')
    // 降级到默认选项
    storageOptions.value = [{ key: 'local', label: '本地', kind: 'local' }]
    formData.value.dest_storage = 'local'
  } finally {
    loadingStorages.value = false
  }
}

// 组件挂载时获取存储选项
onMounted(() => {
  fetchStorageOptions()
})

// 关闭对话框
const closeDialog = () => {
  emit('close')
}

// TMDB 选择回调
const onTmdbSelect = (tmdbItem: any) => {
  formData.value.title = tmdbItem.title
  formData.value.year = tmdbItem.year
  formData.value.tmdb_id = tmdbItem.id
  formData.value.media_type = tmdbItem.media_type
  showTmdbSearch.value = false
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) {
    return
  }

  const { valid } = await formRef.value.validate()
  if (!valid) {
    return
  }

  submitting.value = true
  try {
    const response = await api.post('/transfer-history/manual-transfer', formData.value)
    
    // axios interceptor already unwrapped, response.data is the actual data
    if (response.data.success) {
      toast.success('手动整理完成')
      emit('complete', true)
    } else {
      toast.error(response.data.message || '手动整理失败')
      emit('complete', false)
    }
  } catch (error: any) {
    toast.error(error.message || '手动整理失败')
    emit('complete', false)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.v-card {
  overflow: hidden;
}

.font-family-monospace {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}
</style>
