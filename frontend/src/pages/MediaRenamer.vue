<template>
  <div class="media-renamer-page">
    <!-- 页面标题 -->
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold">媒体文件管理</h1>
        <p class="text-body-1 text-medium-emphasis mt-2">识别、重命名和整理媒体文件</p>
      </div>
    </div>

    <!-- 功能标签页 -->
    <v-tabs v-model="activeTab" color="primary" class="mb-4">
      <v-tab value="identify">
        <v-icon class="me-2">mdi-magnify</v-icon>
        文件识别
      </v-tab>
      <v-tab value="organize">
        <v-icon class="me-2">mdi-folder-move</v-icon>
        文件整理
      </v-tab>
      <v-tab value="batch">
        <v-icon class="me-2">mdi-file-multiple</v-icon>
        批量处理
      </v-tab>
    </v-tabs>

    <v-window v-model="activeTab">
      <!-- 文件识别 -->
      <v-window-item value="identify">
        <v-card variant="outlined">
          <v-card-title>识别媒体文件</v-card-title>
          <v-card-text>
            <v-form ref="identifyFormRef">
              <v-text-field
                v-model="identifyForm.filePath"
                label="文件路径 *"
                variant="outlined"
                prepend-inner-icon="mdi-file"
                hint="请输入完整的文件路径，例如：/path/to/movie.mkv"
                :rules="[v => !!v || '请输入文件路径']"
                required
                class="mb-4"
              />

              <v-btn
                color="primary"
                prepend-icon="mdi-magnify"
                :loading="identifying"
                @click="handleIdentify"
              >
                识别文件
              </v-btn>
            </v-form>

            <!-- 识别结果 -->
            <v-card
              v-if="identifyResult"
              variant="outlined"
              class="mt-4"
              :color="identifyResult.success ? 'success' : 'error'"
            >
              <v-card-title>识别结果</v-card-title>
              <v-card-text>
                <v-row v-if="identifyResult.media_info">
                  <v-col cols="12" md="6">
                    <div class="text-caption text-medium-emphasis mb-1">标题</div>
                    <div class="text-body-1 font-weight-bold">{{ identifyResult.media_info.title }}</div>
                  </v-col>
                  <v-col cols="12" md="6">
                    <div class="text-caption text-medium-emphasis mb-1">媒体类型</div>
                    <div class="text-body-1">
                      <v-chip size="small" :color="identifyResult.media_info.media_type === 'movie' ? 'primary' : 'secondary'">
                        {{ identifyResult.media_info.media_type === 'movie' ? '电影' : '电视剧' }}
                      </v-chip>
                    </div>
                  </v-col>
                  <v-col cols="12" md="6" v-if="identifyResult.media_info.year">
                    <div class="text-caption text-medium-emphasis mb-1">年份</div>
                    <div class="text-body-1">{{ identifyResult.media_info.year }}</div>
                  </v-col>
                  <v-col cols="12" md="6" v-if="identifyResult.media_info.quality">
                    <div class="text-caption text-medium-emphasis mb-1">质量</div>
                    <div class="text-body-1">{{ identifyResult.media_info.quality }}</div>
                  </v-col>
                  <v-col cols="12" md="6" v-if="identifyResult.media_info.resolution">
                    <div class="text-caption text-medium-emphasis mb-1">分辨率</div>
                    <div class="text-body-1">{{ identifyResult.media_info.resolution }}</div>
                  </v-col>
                  <v-col cols="12" md="6" v-if="identifyResult.media_info.season">
                    <div class="text-caption text-medium-emphasis mb-1">季数</div>
                    <div class="text-body-1">S{{ identifyResult.media_info.season }}</div>
                  </v-col>
                  <v-col cols="12" md="6" v-if="identifyResult.media_info.episode">
                    <div class="text-caption text-medium-emphasis mb-1">集数</div>
                    <div class="text-body-1">E{{ identifyResult.media_info.episode }}</div>
                  </v-col>
                  <v-col cols="12" v-if="identifyResult.media_info.raw_title">
                    <div class="text-caption text-medium-emphasis mb-1">原始文件名</div>
                    <div class="text-body-2 text-medium-emphasis">{{ identifyResult.media_info.raw_title }}</div>
                  </v-col>
                </v-row>
                <v-alert
                  v-else
                  type="error"
                  variant="tonal"
                  class="mt-2"
                >
                  {{ identifyResult.error || '识别失败' }}
                </v-alert>
              </v-card-text>
            </v-card>
          </v-card-text>
        </v-card>
      </v-window-item>

      <!-- 文件整理 -->
      <v-window-item value="organize">
        <v-card variant="outlined" class="mb-4">
          <v-card-title>文件操作模式配置</v-card-title>
          <v-card-text>
            <!-- 文件操作卡片列表 -->
            <div v-if="fileOperationConfigs.length === 0" class="text-center py-8 text-medium-emphasis">
              <v-icon size="48" color="grey-lighten-1" class="mb-2">mdi-folder-move</v-icon>
              <div class="text-body-2">暂无文件操作配置，点击下方按钮添加</div>
            </div>

            <v-row v-else>
              <v-col
                v-for="(config, index) in fileOperationConfigs"
                :key="index"
                cols="12"
                md="6"
                lg="4"
              >
                <FileOperationCard
                  :config="config"
                  :storages="cloudStorages"
                  @close="removeFileOperationConfig(index)"
                  @changed="handleFileOperationConfigChange"
                />
              </v-col>
            </v-row>

            <v-btn
              color="primary"
              prepend-icon="mdi-plus"
              @click="addFileOperationConfig"
              variant="outlined"
              block
              class="mt-4"
            >
              添加文件操作配置
            </v-btn>
          </v-card-text>
        </v-card>

        <v-card variant="outlined">
          <v-card-title>整理媒体文件（传统模式）</v-card-title>
          <v-card-text>
            <v-form ref="organizeFormRef">
              <v-row>
                <v-col cols="12">
                  <v-text-field
                    v-model="organizeForm.sourcePath"
                    label="源文件路径 *"
                    variant="outlined"
                    prepend-inner-icon="mdi-file"
                    hint="要整理的媒体文件路径"
                    :rules="[v => !!v || '请输入源文件路径']"
                    required
                  />
                </v-col>
                <v-col cols="12">
                  <v-text-field
                    v-model="organizeForm.targetBaseDir"
                    label="目标目录 *"
                    variant="outlined"
                    prepend-inner-icon="mdi-folder"
                    hint="整理后文件的目标目录"
                    :rules="[v => !!v || '请输入目标目录']"
                    required
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="organizeForm.renameTemplate"
                    label="重命名模板（可选）"
                    variant="outlined"
                    prepend-inner-icon="mdi-format-text"
                    hint="例如：{title} ({year})"
                  />
                  <div class="d-flex flex-wrap ga-2 mt-2">
                    <v-chip
                      v-for="preset in renameTemplatePresets"
                      :key="preset.value"
                      size="small"
                      variant="outlined"
                      color="primary"
                      class="text-body-2"
                      @click="applyRenameTemplatePreset('organize', preset.value)"
                    >
                      {{ preset.title }}
                    </v-chip>
                  </div>
                  <v-alert
                    density="compact"
                    type="info"
                    variant="tonal"
                    class="mt-2"
                  >
                    可直接填入 <code>shortdrama_default</code> 使用短剧默认模板{{ ' ' }}
                    <span class="text-medium-emphasis">
                      （{{ renameTemplatePresets.at(-1)?.description }}）
                    </span>
                  </v-alert>
                </v-col>
                <v-col cols="12" md="6">
                  <v-select
                    v-model="organizeForm.subtitleLanguage"
                    :items="subtitleLanguageOptions"
                    label="字幕语言"
                    variant="outlined"
                    prepend-inner-icon="mdi-translate"
                  />
                </v-col>
                <v-col cols="12" md="4">
                  <v-switch
                    v-model="organizeForm.moveFile"
                    label="移动文件"
                    color="primary"
                    hide-details
                  />
                </v-col>
                <v-col cols="12" md="4">
                  <v-switch
                    v-model="organizeForm.downloadSubtitle"
                    label="下载字幕"
                    color="primary"
                    hide-details
                  />
                </v-col>
                <v-col cols="12" md="4">
                  <v-switch
                    v-model="organizeForm.useClassification"
                    label="使用分类规则"
                    color="primary"
                    hide-details
                  />
                </v-col>
              </v-row>

              <v-btn
                color="primary"
                prepend-icon="mdi-folder-move"
                :loading="organizing"
                @click="handleOrganize"
                class="mt-4"
              >
                整理文件
              </v-btn>
            </v-form>

            <!-- 整理结果 -->
            <v-card
              v-if="organizeResult"
              variant="outlined"
              class="mt-4"
              :color="organizeResult.success ? 'success' : 'error'"
            >
              <v-card-title>整理结果</v-card-title>
              <v-card-text>
                <div v-if="organizeResult.success">
                  <div class="text-body-1 mb-2">
                    <strong>原始路径：</strong>{{ organizeResult.original_path }}
                  </div>
                  <div class="text-body-1 mb-2">
                    <strong>新路径：</strong>{{ organizeResult.new_path }}
                  </div>
                  <v-alert type="success" variant="tonal" class="mt-2">
                    整理成功！
                  </v-alert>
                </div>
                <v-alert
                  v-else
                  type="error"
                  variant="tonal"
                  class="mt-2"
                >
                  {{ organizeResult.error || '整理失败' }}
                </v-alert>
              </v-card-text>
            </v-card>
          </v-card-text>
        </v-card>
      </v-window-item>

      <!-- 批量处理 -->
      <v-window-item value="batch">
        <v-card variant="outlined">
          <v-card-title>批量整理目录</v-card-title>
          <v-card-text>
            <v-form ref="batchFormRef">
              <v-row>
                <v-col cols="12">
                  <v-text-field
                    v-model="batchForm.sourcePath"
                    label="源目录路径 *"
                    variant="outlined"
                    prepend-inner-icon="mdi-folder"
                    hint="要整理的目录路径"
                    :rules="[v => !!v || '请输入源目录路径']"
                    required
                  />
                </v-col>
                <v-col cols="12">
                  <v-text-field
                    v-model="batchForm.targetBaseDir"
                    label="目标目录 *"
                    variant="outlined"
                    prepend-inner-icon="mdi-folder"
                    hint="整理后文件的目标目录"
                    :rules="[v => !!v || '请输入目标目录']"
                    required
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="batchForm.renameTemplate"
                    label="重命名模板（可选）"
                    variant="outlined"
                    prepend-inner-icon="mdi-format-text"
                  />
                  <div class="d-flex flex-wrap ga-2 mt-2">
                    <v-chip
                      v-for="preset in renameTemplatePresets"
                      :key="preset.value"
                      size="small"
                      variant="outlined"
                      color="primary"
                      class="text-body-2"
                      @click="applyRenameTemplatePreset('batch', preset.value)"
                    >
                      {{ preset.title }}
                    </v-chip>
                  </div>
                </v-col>
                <v-col cols="12" md="6">
                  <v-select
                    v-model="batchForm.subtitleLanguage"
                    :items="subtitleLanguageOptions"
                    label="字幕语言"
                    variant="outlined"
                  />
                </v-col>
                <v-col cols="12" md="4">
                  <v-switch
                    v-model="batchForm.moveFile"
                    label="移动文件"
                    color="primary"
                    hide-details
                  />
                </v-col>
                <v-col cols="12" md="4">
                  <v-switch
                    v-model="batchForm.downloadSubtitle"
                    label="下载字幕"
                    color="primary"
                    hide-details
                  />
                </v-col>
                <v-col cols="12" md="4">
                  <v-switch
                    v-model="batchForm.useClassification"
                    label="使用分类规则"
                    color="primary"
                    hide-details
                  />
                </v-col>
              </v-row>

              <v-btn
                color="primary"
                prepend-icon="mdi-file-multiple"
                :loading="batchProcessing"
                @click="handleBatchOrganize"
                class="mt-4"
              >
                批量整理
              </v-btn>
            </v-form>

            <!-- 批量处理结果 -->
            <v-card
              v-if="batchResult"
              variant="outlined"
              class="mt-4"
            >
              <v-card-title>批量整理结果</v-card-title>
              <v-card-text>
                <v-row class="mb-4">
                  <v-col cols="12" md="4">
                    <div class="text-caption text-medium-emphasis mb-1">总计</div>
                    <div class="text-h6">{{ batchResult.total || 0 }}</div>
                  </v-col>
                  <v-col cols="12" md="4">
                    <div class="text-caption text-medium-emphasis mb-1">成功</div>
                    <div class="text-h6 text-success">{{ batchResult.success || 0 }}</div>
                  </v-col>
                  <v-col cols="12" md="4">
                    <div class="text-caption text-medium-emphasis mb-1">失败</div>
                    <div class="text-h6 text-error">{{ batchResult.failed || 0 }}</div>
                  </v-col>
                </v-row>

                <!-- 结果列表 -->
                <v-expansion-panels v-if="batchResult.results && batchResult.results.length > 0">
                  <v-expansion-panel
                    v-for="(result, index) in batchResult.results"
                    :key="index"
                    :title="result.original_path"
                    :subtitle="result.success ? '成功' : '失败'"
                  >
                    <v-expansion-panel-text>
                      <div v-if="result.success">
                        <div class="text-body-2 mb-2">
                          <strong>新路径：</strong>{{ result.new_path }}
                        </div>
                        <div v-if="result.media_info" class="text-body-2">
                          <strong>识别信息：</strong>{{ result.media_info.title }}
                          <span v-if="result.media_info.year"> ({{ result.media_info.year }})</span>
                        </div>
                      </div>
                      <v-alert
                        v-else
                        type="error"
                        variant="tonal"
                        class="mt-2"
                      >
                        {{ result.error || '处理失败' }}
                      </v-alert>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>
              </v-card-text>
            </v-card>
          </v-card-text>
        </v-card>
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { mediaRenamerApi } from '@/services/api'
import api from '@/services/api'
import { useToast } from '@/composables/useToast'
import FileOperationCard from '@/components/file-operation/FileOperationCard.vue'

const { showSuccess, showError } = useToast()

const activeTab = ref('identify')

// 云存储列表
const cloudStorages = ref<any[]>([])

// 文件操作配置列表
const fileOperationConfigs = ref<any[]>([])

// 加载云存储列表
const loadCloudStorages = async () => {
  try {
    const response = await api.get('/cloud-storage')
    cloudStorages.value = response.data || []
  } catch (error) {
    console.error('加载云存储列表失败:', error)
  }
}

// 添加文件操作配置
const addFileOperationConfig = () => {
  fileOperationConfigs.value.push({
    name: `文件操作 ${fileOperationConfigs.value.length + 1}`,
    source_storage: 'local',
    target_storage: 'local',
    operation_mode: 'copy',
    source_path: '',
    target_path: '',
    overwrite_mode: 'never',
    delete_source: true,
    keep_seeding: true,
    strm_config: null
  })
}

// 删除文件操作配置
const removeFileOperationConfig = (index: number) => {
  if (confirm('确定要删除这个文件操作配置吗？')) {
    fileOperationConfigs.value.splice(index, 1)
  }
}

// 处理文件操作配置变化
const handleFileOperationConfigChange = () => {
  // 配置变化时的处理逻辑
  console.log('文件操作配置已更新')
}

// 文件识别
const identifyFormRef = ref()
const identifying = ref(false)
const identifyForm = ref({
  filePath: ''
})
const identifyResult = ref<any>(null)

// 文件整理
const organizeFormRef = ref()
const organizing = ref(false)
const organizeForm = ref({
  sourcePath: '',
  targetBaseDir: '',
  renameTemplate: '',
  moveFile: true,
  downloadSubtitle: false,
  subtitleLanguage: 'zh',
  useClassification: true
})
const organizeResult = ref<any>(null)

// 批量处理
const batchFormRef = ref()
const batchProcessing = ref(false)
const batchForm = ref({
  sourcePath: '',
  targetBaseDir: '',
  renameTemplate: '',
  moveFile: true,
  downloadSubtitle: false,
  subtitleLanguage: 'zh',
  useClassification: true
})
const batchResult = ref<any>(null)

const subtitleLanguageOptions = [
  { title: '中文', value: 'zh' },
  { title: '英文', value: 'en' },
  { title: '日文', value: 'ja' },
  { title: '韩文', value: 'ko' }
]

const renameTemplatePresets = [
  {
    title: '电影默认',
    value: '{title} ({year})/{title} ({year}) [{quality}]'
  },
  {
    title: '电视剧默认',
    value:
      '{title} ({year})/Season {season:02d}/{title} - S{season:02d}E{episode:02d} - {episode_name} [{quality}]'
  },
  {
    title: '动漫默认',
    value:
      '{title} ({year})/Season {season:02d}/{title} - S{season:02d}E{episode:02d} - {episode_name} [{resolution}]'
  },
  {
    title: '短剧默认（shortdrama_default）',
    value: 'shortdrama_default',
    description: '短剧/{title}/S{season:02d}/{title}.S{season:02d}E{episode:02d} {source} {quality}'
  }
]

const applyRenameTemplatePreset = (target: 'organize' | 'batch', value: string) => {
  if (target === 'organize') {
    organizeForm.value.renameTemplate = value
  } else {
    batchForm.value.renameTemplate = value
  }
}

const handleIdentify = async () => {
  const { valid } = await identifyFormRef.value.validate()
  if (!valid) {
    showError('请填写文件路径')
    return
  }

  identifying.value = true
  identifyResult.value = null
  try {
    const response = await mediaRenamerApi.identifyMediaFile(identifyForm.value.filePath)
    if (response.data) {
      identifyResult.value = {
        success: true,
        media_info: response.data
      }
      showSuccess('识别成功')
    } else {
      throw new Error('未获取到识别结果')
    }
  } catch (error: any) {
    identifyResult.value = {
      success: false,
      error: error.response?.data?.error_message || error.message || '识别失败'
    }
    showError(error.response?.data?.error_message || error.message || '识别失败')
  } finally {
    identifying.value = false
  }
}

const handleOrganize = async () => {
  const { valid } = await organizeFormRef.value.validate()
  if (!valid) {
    showError('请填写所有必填项')
    return
  }

  organizing.value = true
  organizeResult.value = null
  try {
    const response = await mediaRenamerApi.organizeFile({
      source_path: organizeForm.value.sourcePath,
      target_base_dir: organizeForm.value.targetBaseDir,
      rename_template: organizeForm.value.renameTemplate || undefined,
      move_file: organizeForm.value.moveFile,
      download_subtitle: organizeForm.value.downloadSubtitle,
      subtitle_language: organizeForm.value.subtitleLanguage,
      use_classification: organizeForm.value.useClassification
    })
    if (response.data) {
      organizeResult.value = response.data
      if (organizeResult.value.success) {
        showSuccess('整理成功')
      } else {
        showError(organizeResult.value.error || '整理失败')
      }
    } else {
      throw new Error('未获取到整理结果')
    }
  } catch (error: any) {
    organizeResult.value = {
      success: false,
      error: error.response?.data?.error_message || error.message || '整理失败'
    }
    showError(error.response?.data?.error_message || error.message || '整理失败')
  } finally {
    organizing.value = false
  }
}

const handleBatchOrganize = async () => {
  const { valid } = await batchFormRef.value.validate()
  if (!valid) {
    showError('请填写所有必填项')
    return
  }

  batchProcessing.value = true
  batchResult.value = null
  try {
    const response = await mediaRenamerApi.organizeDirectory({
      source_path: batchForm.value.sourcePath,
      target_base_dir: batchForm.value.targetBaseDir,
      rename_template: batchForm.value.renameTemplate || undefined,
      move_file: batchForm.value.moveFile,
      download_subtitle: batchForm.value.downloadSubtitle,
      subtitle_language: batchForm.value.subtitleLanguage,
      use_classification: batchForm.value.useClassification
    })
    if (response.data) {
      batchResult.value = response.data
      showSuccess(`批量整理完成：成功 ${batchResult.value.success || 0} 个，失败 ${batchResult.value.failed || 0} 个`)
    } else {
      throw new Error('未获取到批量整理结果')
    }
  } catch (error: any) {
    showError(error.response?.data?.error_message || error.message || '批量整理失败')
  } finally {
    batchProcessing.value = false
  }
}

onMounted(() => {
  // 加载云存储列表
  loadCloudStorages()
})
</script>

<style scoped>
.media-renamer-page {
  padding: 24px;
}
</style>

