<template>
  <v-dialog
    v-model="modelValue"
    max-width="800"
    scrollable
  >
    <v-card>
      <v-card-title>创建音乐订阅</v-card-title>
      
      <v-card-text>
        <v-form ref="formRef" v-model="formValid">
          <!-- 订阅类型选择 -->
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-h6">订阅类型</v-card-title>
            <v-card-text>
              <v-radio-group v-model="form.subscription_type" inline>
                <v-radio 
                  label="榜单订阅" 
                  value="chart"
                  color="primary"
                />
                <v-radio 
                  label="关键字订阅" 
                  value="keyword"
                  color="primary"
                />
              </v-radio-group>
              
              <div class="text-caption text-medium-emphasis mt-2">
                <div v-if="form.subscription_type === 'chart'">
                  选择音乐榜单进行订阅，系统会定期检查榜单更新并下载新音乐
                </div>
                <div v-else-if="form.subscription_type === 'keyword'">
                  使用关键字搜索音乐，支持自定义搜索条件和安全策略
                </div>
              </div>
            </v-card-text>
          </v-card>

          <!-- 榜单订阅配置 -->
          <v-card 
            v-if="form.subscription_type === 'chart'" 
            variant="outlined" 
            class="mb-4"
          >
            <v-card-title class="text-h6">榜单配置</v-card-title>
            <v-card-text>
              <v-select
                v-model="form.chart_id"
                :items="charts"
                item-title="display_name"
                item-value="id"
                label="选择榜单 *"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-chart-bar"
                :loading="chartsLoading"
                :rules="[(v) => !!v || '请选择榜单']"
                class="mb-4"
              >
                <template v-slot:item="{ props, item }">
                  <v-list-item v-bind="props">
                    <template v-slot:subtitle>
                      {{ item.raw.source?.name || '未知平台' }} - {{ item.raw.chart_type }} - {{ item.raw.region }}
                    </template>
                  </v-list-item>
                </template>
              </v-select>
            </v-card-text>
          </v-card>

          <!-- 关键字订阅配置 -->
          <v-card 
            v-if="form.subscription_type === 'keyword'" 
            variant="outlined" 
            class="mb-4"
          >
            <v-card-title class="text-h6">关键字配置</v-card-title>
            <v-card-text>
              <v-text-field
                v-model="form.music_query"
                label="搜索关键字 *"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-magnify"
                :rules="[(v) => !!v?.trim() || '请输入搜索关键字']"
                hint="输入音乐搜索关键字，如歌曲名、艺术家名等"
                persistent-hint
                class="mb-4"
              />
              
              <v-select
                v-model="form.music_site"
                :items="musicSites"
                label="搜索站点"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-web"
                hint="选择音乐搜索站点，留空则使用默认站点"
                persistent-hint
                class="mb-4"
              />
              
              <v-select
                v-model="form.music_quality"
                :items="musicQualities"
                label="音质偏好"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-quality-high"
                hint="选择音质偏好，留空则使用默认设置"
                persistent-hint
                class="mb-4"
              />
            </v-card-text>
          </v-card>

          <!-- 通用配置 -->
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-h6">通用配置</v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="12" sm="6">
                  <v-switch
                    v-model="form.auto_search"
                    label="自动搜索"
                    color="primary"
                    hint="定期自动搜索新音乐"
                    persistent-hint
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-switch
                    v-model="form.auto_download"
                    label="自动下载"
                    color="primary"
                    hint="找到匹配的音乐时自动下载"
                    persistent-hint
                  />
                </v-col>
              </v-row>
              
              <v-text-field
                v-model.number="form.max_new_tracks_per_run"
                type="number"
                label="每次运行最大处理数量"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-counter"
                :rules="[(v) => (v && v > 0) || '请输入大于0的数字']"
                class="mb-4"
              />
              
              <v-select
                v-model="form.quality_preference"
                :items="qualityPreferences"
                label="全局音质偏好"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-quality-high"
                hint="全局音质设置，会覆盖关键字订阅的音质偏好"
                persistent-hint
                class="mb-4"
                clearable
              />
              
              <v-text-field
                v-model="form.preferred_sites"
                label="偏好站点"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-web"
                hint="指定偏好的下载站点，多个站点用逗号分隔"
                persistent-hint
                class="mb-4"
              />
            </v-card-text>
          </v-card>

          <!-- 安全策略配置 -->
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-h6">安全策略</v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="12" sm="4">
                  <v-switch
                    v-model="form.allow_hr"
                    label="允许HR"
                    color="warning"
                    hint="允许下载HR（高分辨率）音频"
                    persistent-hint
                  />
                </v-col>
                <v-col cols="12" sm="4">
                  <v-switch
                    v-model="form.allow_h3h5"
                    label="允许H3/H5"
                    color="warning"
                    hint="允许下载H3/H5站点内容"
                    persistent-hint
                  />
                </v-col>
                <v-col cols="12" sm="4">
                  <v-switch
                    v-model="form.strict_free_only"
                    label="仅免费"
                    color="success"
                    hint="仅下载免费内容，跳过付费内容"
                    persistent-hint
                  />
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-form>
      </v-card-text>
      
      <v-card-actions>
        <v-spacer />
        <v-btn @click="modelValue = false" variant="text">取消</v-btn>
        <v-btn
          color="primary"
          @click="handleSave"
          :loading="saving"
          :disabled="!formValid"
        >
          创建订阅
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { 
  createMusicSubscription, 
  fetchMusicCharts,
  type UserMusicSubscriptionCreate,
  type MusicChart
} from '@/services/music'

interface Props {
  modelValue: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'saved': []
}>()

const formRef = ref()
const formValid = ref(false)
const saving = ref(false)
const chartsLoading = ref(false)
const charts = ref<MusicChart[]>([])

const form = ref<UserMusicSubscriptionCreate>({
  subscription_type: 'chart',
  chart_id: null,
  music_query: '',
  music_site: '',
  music_quality: '',
  auto_search: true,
  auto_download: true,
  max_new_tracks_per_run: 10,
  quality_preference: null,
  preferred_sites: '',
  allow_hr: false,
  allow_h3h5: false,
  strict_free_only: false
})

const modelValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const musicSites = [
  { title: '所有站点', value: '' },
  { title: 'QQ音乐', value: 'qq' },
  { title: '网易云音乐', value: 'netease' },
  { title: '酷狗音乐', value: 'kugou' },
  { title: '酷我音乐', value: 'kuwo' },
  { title: '咪咕音乐', value: 'migu' }
]

const musicQualities = [
  { title: '自动选择', value: '' },
  { title: 'FLAC 无损', value: 'flac' },
  { title: 'MP3 320kbps', value: 'mp3_320' },
  { title: 'MP3 128kbps', value: 'mp3_128' },
  { title: '高品质', value: 'high' },
  { title: '标准品质', value: 'standard' }
]

const qualityPreferences = [
  { title: 'FLAC 无损', value: 'flac' },
  { title: 'MP3 320kbps', value: 'mp3_320' },
  { title: 'MP3 128kbps', value: 'mp3_128' },
  { title: '高品质', value: 'high' },
  { title: '标准品质', value: 'standard' }
]

// 加载榜单列表
const loadCharts = async () => {
  chartsLoading.value = true
  try {
    charts.value = await fetchMusicCharts({ is_active: true })
  } catch (error: any) {
    console.error('加载榜单列表失败:', error)
  } finally {
    chartsLoading.value = false
  }
}

// 监听订阅类型变化，重置相关字段
watch(() => form.value.subscription_type, (newType) => {
  if (newType === 'chart') {
    form.value.music_query = ''
    form.value.music_site = ''
    form.value.music_quality = ''
  } else if (newType === 'keyword') {
    form.value.chart_id = null
  }
})

const handleSave = async () => {
  if (!formRef.value?.validate()) {
    return
  }

  saving.value = true
  try {
    // 根据订阅类型清理数据
    const submitData: UserMusicSubscriptionCreate = {
      ...form.value,
      subscription_type: form.value.subscription_type!
    }

    if (submitData.subscription_type === 'chart') {
      submitData.music_query = null
      submitData.music_site = null
      submitData.music_quality = null
    } else if (submitData.subscription_type === 'keyword') {
      submitData.chart_id = null
      submitData.music_query = submitData.music_query?.trim()
    }

    await createMusicSubscription(submitData)
    
    emit('saved')
    modelValue.value = false
    resetForm()
  } catch (error: any) {
    console.error('创建音乐订阅失败:', error)
    alert('创建失败：' + (error.response?.data?.detail || '未知错误'))
  } finally {
    saving.value = false
  }
}

const resetForm = () => {
  form.value = {
    subscription_type: 'chart',
    chart_id: null,
    music_query: '',
    music_site: '',
    music_quality: '',
    auto_search: true,
    auto_download: true,
    max_new_tracks_per_run: 10,
    quality_preference: null,
    preferred_sites: '',
    allow_hr: false,
    allow_h3h5: false,
    strict_free_only: false
  }
  formRef.value?.resetValidation()
}

// 组件挂载时加载榜单列表
onMounted(() => {
  loadCharts()
})
</script>
