<!--
站点导出对话框 (SITE-MANAGER-1)
支持JSON格式的站点配置批量导出
-->

<template>
  <v-dialog
    v-model="dialog"
    :max-width="600"
    persistent
  >
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-upload</v-icon>
        导出站点配置
      </v-card-title>

      <v-card-text>
        <v-form ref="formRef" v-model="formValid">
          <v-row>
            <v-col cols="12">
              <v-subheader>导出范围</v-subheader>
            </v-col>

            <v-col cols="12">
              <v-radio-group v-model="exportScope" column>
                <v-radio
                  label="全部站点"
                  value="all"
                />
                <v-radio
                  label="选中的站点"
                  value="selected"
                  :disabled="!selectedSites.length"
                />
                <v-radio
                  label="按分类导出"
                  value="category"
                />
                <v-radio
                  label="按状态导出"
                  value="status"
                />
              </v-radio-group>
            </v-col>

            <!-- 选中的站点列表 -->
            <v-col v-if="exportScope === 'selected'" cols="12">
              <v-list density="compact" max-height="200" class="overflow-y-auto">
                <v-list-item
                  v-for="siteId in selectedSites"
                  :key="siteId"
                >
                  <v-list-item-title>
                    {{ getSiteName(siteId) }}
                  </v-list-item-title>
                </v-list-item>
              </v-list>
            </v-col>

            <!-- 分类选择 -->
            <v-col v-if="exportScope === 'category'" cols="12">
              <v-select
                v-model="selectedCategories"
                :items="categoryOptions"
                label="选择分类"
                multiple
                chips
                :rules="[requiredRule]"
              />
            </v-col>

            <!-- 状态选择 -->
            <v-col v-if="exportScope === 'status'" cols="12">
              <v-select
                v-model="selectedStatus"
                :items="statusOptions"
                label="选择状态"
                multiple
                chips
                :rules="[requiredRule]"
              />
            </v-col>

            <v-col cols="12">
              <v-subheader>导出选项</v-subheader>
            </v-col>

            <v-col cols="12" sm="6">
              <v-switch
                v-model="exportOptions.includeStats"
                label="包含统计数据"
                hint="导出流量、健康状态等统计信息"
                persistent-hint
              />
            </v-col>

            <v-col cols="12" sm="6">
              <v-switch
                v-model="exportOptions.includeAccessConfig"
                label="包含访问配置"
                hint="导出RSS URL、代理设置等访问配置"
                persistent-hint
              />
            </v-col>

            <v-col cols="12" sm="6">
              <v-switch
                v-model="exportOptions.includeDisabled"
                label="包含禁用站点"
                hint="同时导出标记为禁用的站点"
                persistent-hint
              />
            </v-col>

            <v-col cols="12" sm="6">
              <v-switch
                v-model="exportOptions.prettyFormat"
                label="格式化JSON"
                hint="生成格式化的JSON文件，便于阅读"
                persistent-hint
              />
            </v-col>

            <v-col cols="12">
              <v-text-field
                v-model="fileName"
                label="文件名"
                placeholder="sites-export"
                hint="导出文件的名称（不含扩展名）"
                persistent-hint
                :rules="[requiredRule]"
              />
            </v-col>
          </v-row>
        </v-form>

        <!-- 预览 -->
        <div v-if="previewData.length" class="mt-4">
          <v-alert type="info" class="mb-4">
            将导出 {{ previewData.length }} 个站点配置
          </v-alert>
          
          <v-card variant="outlined">
            <v-card-text class="pa-2">
              <pre class="text-caption">{{ previewJson }}</pre>
            </v-card-text>
          </v-card>
        </div>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          variant="text"
          @click="onCancel"
        >
          取消
        </v-btn>
        <v-btn
          color="primary"
          :loading="loading"
          :disabled="!formValid || !previewData.length"
          @click="onExport"
        >
          导出
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useSiteManagerStore } from '@/stores/siteManager'
import type { SiteExportItem } from '@/types/siteManager'

interface Props {
  modelValue: boolean
  sites?: number[]
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const siteManagerStore = useSiteManagerStore()

// 响应式状态
const dialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const formRef = ref()
const formValid = ref(false)
const loading = ref(false)

// 导出配置
const exportScope = ref<'all' | 'selected' | 'category' | 'status'>('all')
const selectedCategories = ref<string[]>([])
const selectedStatus = ref<string[]>([])
const fileName = ref('sites-export')

const exportOptions = ref({
  includeStats: true,
  includeAccessConfig: true,
  includeDisabled: false,
  prettyFormat: true
})

// 预览数据
const previewData = ref<SiteExportItem[]>([])

// 计算属性
const selectedSites = computed(() => props.sites || [])

const categoryOptions = computed(() => [
  { title: 'PT站点', value: 'pt' },
  { title: 'BT站点', value: 'bt' },
  { title: '小说站点', value: 'novel' },
  { title: '漫画站点', value: 'comic' },
  { title: '音乐站点', value: 'music' },
  { title: '影视站点', value: 'movie' },
  { title: '游戏站点', value: 'game' }
])

const statusOptions = computed(() => [
  { title: '启用', value: 'enabled' },
  { title: '禁用', value: 'disabled' },
  { title: '健康', value: 'healthy' },
  { title: '异常', value: 'unhealthy' }
])

const previewJson = computed(() => {
  if (!previewData.value.length) return ''
  
  const sample = previewData.value.slice(0, 2)
  return JSON.stringify(sample, null, exportOptions.value.prettyFormat ? 2 : 0)
})

// 验证规则
const requiredRule = (value: any) => {
  if (Array.isArray(value)) return value.length > 0 || '请至少选择一项'
  return !!value || '此字段为必填项'
}

// 方法
const getSiteName = (siteId: number): string => {
  const site = siteManagerStore.sites.find(s => s.id === siteId)
  return site?.name || `站点 ${siteId}`
}

const updatePreview = async () => {
  try {
    let siteIds: number[] | undefined

    switch (exportScope.value) {
      case 'all':
        siteIds = undefined
        break
      case 'selected':
        siteIds = selectedSites.value
        break
      case 'category':
        if (selectedCategories.value.length === 0) {
          previewData.value = []
          return
        }
        const categorySites = siteManagerStore.sites.filter(site =>
          selectedCategories.value.includes(site.category || '')
        )
        siteIds = categorySites.map(site => site.id)
        break
      case 'status':
        if (selectedStatus.value.length === 0) {
          previewData.value = []
          return
        }
        let statusSites = siteManagerStore.sites
        if (selectedStatus.value.includes('enabled')) {
          statusSites = statusSites.filter(site => site.enabled)
        }
        if (selectedStatus.value.includes('disabled')) {
          statusSites = statusSites.filter(site => !site.enabled)
        }
        if (selectedStatus.value.includes('healthy')) {
          statusSites = statusSites.filter(site => site.stats?.health_status === 'OK')
        }
        if (selectedStatus.value.includes('unhealthy')) {
          statusSites = statusSites.filter(site => 
            site.stats?.health_status && site.stats.health_status !== 'OK'
          )
        }
        siteIds = statusSites.map(site => site.id)
        break
    }

    if (siteIds && siteIds.length === 0) {
      previewData.value = []
      return
    }

    const data = await siteManagerStore.exportSites(siteIds)
    
    // 根据选项过滤数据
    let filteredData = data
    
    if (!exportOptions.value.includeDisabled) {
      filteredData = filteredData.filter(site => site.enabled)
    }

    previewData.value = filteredData
  } catch (error) {
    console.error('获取预览数据失败:', error)
    previewData.value = []
  }
}

const onExport = async () => {
  loading.value = true

  try {
    const data = await siteManagerStore.exportSites(
      exportScope.value === 'all' ? undefined : 
      exportScope.value === 'selected' ? selectedSites.value :
      previewData.value.map(site => 
        siteManagerStore.sites.find(s => s.name === site.name)?.id
      ).filter(Boolean) as number[]
    )

    // 根据选项过滤数据
    let filteredData = data
    
    if (!exportOptions.value.includeDisabled) {
      filteredData = filteredData.filter(site => site.enabled)
    }

    // 生成JSON内容
    const jsonContent = JSON.stringify(
      { sites: filteredData, exported_at: new Date().toISOString() },
      null,
      exportOptions.value.prettyFormat ? 2 : 0
    )

    // 下载文件
    const blob = new Blob([jsonContent], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${fileName.value}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    dialog.value = false
  } catch (error) {
    console.error('导出失败:', error)
  } finally {
    loading.value = false
  }
}

const onCancel = () => {
  dialog.value = false
}

// 监听导出选项变化，更新预览
watch(
  [exportScope, selectedCategories, selectedStatus, exportOptions],
  updatePreview,
  { deep: true }
)

// 监听对话框打开
watch(dialog, (isOpen) => {
  if (isOpen) {
    updatePreview()
  }
})
</script>

<style lang="scss" scoped>
pre {
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
}
</style>
