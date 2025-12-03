<!--
站点导入对话框 (SITE-MANAGER-1)
支持JSON格式的站点配置批量导入
-->

<template>
  <v-dialog
    v-model="dialog"
    :max-width="800"
    persistent
  >
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-download</v-icon>
        导入站点配置
      </v-card-title>

      <v-card-text>
        <v-stepper v-model="step" alt-labels>
          <!-- 步骤1: 选择导入方式 -->
          <v-stepper-header>
            <v-stepper-item
              title="选择方式"
              value="1"
              :complete="step > 1"
            />
            <v-divider />
            <v-stepper-item
              title="配置数据"
              value="2"
              :complete="step > 2"
            />
            <v-divider />
            <v-stepper-item
              title="确认导入"
              value="3"
            />
          </v-stepper-header>

          <v-stepper-window>
            <!-- 步骤1: 选择导入方式 -->
            <v-stepper-window-item value="1">
              <v-card-text class="pa-4">
                <div class="text-h6 mb-4">选择导入方式</div>
                
                <v-radio-group v-model="importType" column>
                  <v-radio
                    label="JSON文件导入"
                    value="file"
                  />
                  <v-radio
                    label="JSON文本粘贴"
                    value="text"
                  />
                  <v-radio
                    label="从URL导入"
                    value="url"
                  />
                </v-radio-group>

                <!-- 文件上传 -->
                <div v-if="importType === 'file'" class="mt-4">
                  <v-file-input
                    v-model="selectedFile"
                    label="选择JSON文件"
                    accept=".json"
                    prepend-icon="mdi-file-upload"
                    show-size
                    @change="onFileChange"
                  />
                </div>

                <!-- 文本输入 -->
                <div v-if="importType === 'text'" class="mt-4">
                  <v-textarea
                    v-model="jsonText"
                    label="JSON数据"
                    placeholder="粘贴站点配置JSON数据..."
                    rows="8"
                    :rules="[jsonRule]"
                    @update:model-value="onTextChange"
                  />
                </div>

                <!-- URL输入 -->
                <div v-if="importType === 'url'" class="mt-4">
                  <v-text-field
                    v-model="importUrl"
                    label="JSON文件URL"
                    placeholder="https://example.com/sites.json"
                    :rules="[urlRule]"
                    @update:model-value="onUrlChange"
                  />
                </div>

                <!-- 预览区域 -->
                <div v-if="previewData.length > 0" class="mt-4">
                  <v-alert type="success" class="mb-4">
                    检测到 {{ previewData.length }} 个站点配置
                  </v-alert>
                  
                  <v-list density="compact" max-height="200" class="overflow-y-auto">
                    <v-list-item
                      v-for="(site, index) in previewData.slice(0, 10)"
                      :key="index"
                    >
                      <v-list-item-title>{{ site.name }}</v-list-item-title>
                      <v-list-item-subtitle>{{ site.url }}</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item v-if="previewData.length > 10">
                      <v-list-item-title class="text-medium-emphasis">
                        ... 还有 {{ previewData.length - 10 }} 个站点
                      </v-list-item-title>
                    </v-list-item>
                  </v-list>
                </div>
              </v-card-text>
            </v-stepper-window-item>

            <!-- 步骤2: 配置导入选项 -->
            <v-stepper-window-item value="2">
              <v-card-text class="pa-4">
                <div class="text-h6 mb-4">配置导入选项</div>
                
                <v-row>
                  <v-col cols="12">
                    <v-switch
                      v-model="importOptions.skipExisting"
                      label="跳过已存在的站点"
                      hint="如果站点标识或域名已存在，则跳过导入"
                      persistent-hint
                    />
                  </v-col>
                  
                  <v-col cols="12">
                    <v-switch
                      v-model="importOptions.updateExisting"
                      label="更新已存在的站点"
                      hint="如果站点标识或域名已存在，则更新其配置"
                      persistent-hint
                    />
                  </v-col>
                  
                  <v-col cols="12">
                    <v-switch
                      v-model="importOptions.importDisabled"
                      label="导入禁用的站点"
                      hint="同时导入标记为禁用的站点"
                      persistent-hint
                    />
                  </v-col>
                  
                  <v-col cols="12">
                    <v-switch
                      v-model="importOptions.importAccessConfig"
                      label="导入访问配置"
                      hint="同时导入RSS URL、代理设置等访问配置"
                      persistent-hint
                    />
                  </v-col>
                </v-row>

                <!-- 冲突处理 -->
                <v-divider class="my-4" />
                <div class="text-subtitle-1 mb-2">冲突处理</div>
                <v-radio-group v-model="importOptions.conflictStrategy" column>
                  <v-radio
                    label="跳过冲突项"
                    value="skip"
                  />
                  <v-radio
                    label="覆盖现有项"
                    value="overwrite"
                  />
                  <v-radio
                    label="创建副本"
                    value="duplicate"
                  />
                </v-radio-group>
              </v-card-text>
            </v-stepper-window-item>

            <!-- 步骤3: 确认导入 -->
            <v-stepper-window-item value="3">
              <v-card-text class="pa-4">
                <div class="text-h6 mb-4">确认导入</div>
                
                <v-alert
                  :type="importResult ? (importResult.failed_count > 0 ? 'warning' : 'success') : 'info'"
                  class="mb-4"
                >
                  <div v-if="importResult">
                    导入完成！
                    <br />
                    成功: {{ importResult.success_count }} 个
                    <br />
                    失败: {{ importResult.failed_count }} 个
                  </div>
                  <div v-else>
                    准备导入 {{ previewData.length }} 个站点
                  </div>
                </v-alert>

                <!-- 失败项列表 -->
                <div v-if="importResult?.failed_items?.length" class="mt-4">
                  <div class="text-subtitle-1 mb-2">导入失败的站点:</div>
                  <v-list density="compact" max-height="200" class="overflow-y-auto">
                    <v-list-item
                      v-for="(item, index) in importResult.failed_items"
                      :key="index"
                    >
                      <v-list-item-title>{{ item.site.name }}</v-list-item-title>
                      <v-list-item-subtitle class="text-error">
                        {{ item.error }}
                      </v-list-item-subtitle>
                    </v-list-item>
                  </v-list>
                </div>
              </v-card-text>
            </v-stepper-window-item>
          </v-stepper-window>
        </v-stepper>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          variant="text"
          @click="onCancel"
        >
          {{ step === 3 ? '关闭' : '取消' }}
        </v-btn>
        <v-btn
          v-if="step > 1"
          variant="text"
          @click="step--"
        >
          上一步
        </v-btn>
        <v-btn
          v-if="step < 3"
          color="primary"
          :disabled="!canProceed"
          @click="nextStep"
        >
          下一步
        </v-btn>
        <v-btn
          v-if="step === 2"
          color="primary"
          :loading="loading"
          @click="onImport"
        >
          开始导入
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useSiteManagerStore } from '@/stores/siteManager'
import type { SiteImportItem, ImportResult } from '@/types/siteManager'

interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'imported', result: ImportResult): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const siteManagerStore = useSiteManagerStore()

// 响应式状态
const dialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const step = ref(1)
const loading = ref(false)

// 导入方式
const importType = ref<'file' | 'text' | 'url'>('file')
const selectedFile = ref<File | null>(null)
const jsonText = ref('')
const importUrl = ref('')

// 导入数据
const previewData = ref<SiteImportItem[]>([])
const importResult = ref<ImportResult | null>(null)

// 导入选项
const importOptions = ref({
  skipExisting: true,
  updateExisting: false,
  importDisabled: true,
  importAccessConfig: true,
  conflictStrategy: 'skip' as 'skip' | 'overwrite' | 'duplicate'
})

// 计算属性
const canProceed = computed(() => {
  switch (step.value) {
    case 1:
      return previewData.value.length > 0
    case 2:
      return true
    default:
      return false
  }
})

// 验证规则
const jsonRule = (value: string) => {
  if (!value) return '请输入JSON数据'
  try {
    JSON.parse(value)
    return true
  } catch {
    return 'JSON格式无效'
  }
}

const urlRule = (value: string) => {
  if (!value) return '请输入URL'
  try {
    new URL(value)
    return true
  } catch {
    return 'URL格式无效'
  }
}

// 方法
const onFileChange = (file: File | null) => {
  if (!file) {
    previewData.value = []
    return
  }
  
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const content = e.target?.result as string
      const data = JSON.parse(content)
      parseImportData(data)
    } catch (error) {
      console.error('解析JSON文件失败:', error)
      previewData.value = []
    }
  }
  reader.readAsText(file)
}

const onTextChange = (text: string) => {
  if (!text) {
    previewData.value = []
    return
  }
  
  try {
    const data = JSON.parse(text)
    parseImportData(data)
  } catch (error) {
    console.error('解析JSON文本失败:', error)
    previewData.value = []
  }
}

const onUrlChange = async (url: string) => {
  if (!url) {
    previewData.value = []
    return
  }
  
  try {
    const response = await fetch(url)
    const text = await response.text()
    const data = JSON.parse(text)
    parseImportData(data)
  } catch (error) {
    console.error('从URL获取JSON失败:', error)
    previewData.value = []
  }
}

const parseImportData = (data: any) => {
  if (Array.isArray(data)) {
    previewData.value = data.filter(item => 
      item && typeof item === 'object' && item.name && item.url
    ) as SiteImportItem[]
  } else if (data.sites && Array.isArray(data.sites)) {
    previewData.value = data.sites.filter((item: any) => 
      item && typeof item === 'object' && item.name && item.url
    ) as SiteImportItem[]
  } else {
    previewData.value = []
  }
}

const nextStep = () => {
  if (step.value < 3) {
    step.value++
  }
}

const onImport = async () => {
  loading.value = true
  importResult.value = null
  
  try {
    const result = await siteManagerStore.importSites(previewData.value)
    importResult.value = result
    step.value = 3
    emit('imported', result)
  } catch (error) {
    console.error('导入失败:', error)
  } finally {
    loading.value = false
  }
}

const onCancel = () => {
  if (step.value === 3) {
    dialog.value = false
  } else {
    dialog.value = false
  }
}

// 监听对话框关闭，重置状态
watch(dialog, (isOpen) => {
  if (!isOpen) {
    step.value = 1
    selectedFile.value = null
    jsonText.value = ''
    importUrl.value = ''
    previewData.value = []
    importResult.value = null
    importType.value = 'file'
  }
})
</script>

<style lang="scss" scoped>
.v-stepper {
  .v-stepper-window-item {
    min-height: 400px;
  }
}
</style>
