<!--
视图设置对话框 (SITE-MANAGER-1)
配置站点管理页面的显示选项和布局
-->

<template>
  <v-dialog
    v-model="dialog"
    :max-width="600"
    persistent
  >
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-cog</v-icon>
        显示设置
      </v-card-title>

      <v-card-text>
        <v-form ref="formRef" v-model="formValid">
          <v-row>
            <!-- 布局设置 -->
            <v-col cols="12">
              <v-subheader>布局设置</v-subheader>
            </v-col>

            <v-col cols="12" sm="6">
              <v-select
                v-model="localConfig.layout"
                :items="layoutOptions"
                label="视图布局"
                hint="选择站点显示的布局方式"
                persistent-hint
              />
            </v-col>

            <v-col cols="12" sm="6">
              <v-select
                v-model="localConfig.cardSize"
                :items="cardSizeOptions"
                label="卡片大小"
                hint="调整站点卡片的显示大小"
                persistent-hint
              />
            </v-col>

            <!-- 排序设置 -->
            <v-col cols="12">
              <v-subheader>排序设置</v-subheader>
            </v-col>

            <v-col cols="12" sm="6">
              <v-select
                v-model="localConfig.sortBy"
                :items="sortByOptions"
                label="排序方式"
                hint="选择站点的排序依据"
                persistent-hint
              />
            </v-col>

            <v-col cols="12" sm="6">
              <v-select
                v-model="localConfig.sortOrder"
                :items="sortOrderOptions"
                label="排序顺序"
                hint="选择升序或降序排列"
                persistent-hint
              />
            </v-col>

            <!-- 显示选项 -->
            <v-col cols="12">
              <v-subheader>显示选项</v-subheader>
            </v-col>

            <v-col cols="12" sm="6">
              <v-switch
                v-model="localConfig.showDisabled"
                label="显示禁用站点"
                hint="在列表中包含已禁用的站点"
                persistent-hint
              />
            </v-col>

            <v-col cols="12" sm="6">
              <v-switch
                v-model="localConfig.autoRefresh"
                label="自动刷新"
                hint="定期自动刷新站点数据"
                persistent-hint
              />
            </v-col>

            <v-col v-if="localConfig.autoRefresh" cols="12">
              <v-slider
                v-model="localConfig.refreshInterval"
                :min="30"
                :max="300"
                :step="30"
                :label="`刷新间隔: ${localConfig.refreshInterval}秒`"
                hint="设置自动刷新的时间间隔"
                persistent-hint
              />
            </v-col>

            <!-- 性能设置 -->
            <v-col cols="12">
              <v-subheader>性能设置</v-subheader>
            </v-col>

            <v-col cols="12" sm="6">
              <v-switch
                v-model="localConfig.virtualScroll"
                label="虚拟滚动"
                hint="大量站点时启用虚拟滚动提升性能"
                persistent-hint
              />
            </v-col>

            <v-col cols="12" sm="6">
              <v-switch
                v-model="localConfig.lazyLoadImages"
                label="懒加载图片"
                hint="延迟加载站点图标以提升页面加载速度"
                persistent-hint
              />
            </v-col>

            <v-col cols="12">
              <v-slider
                v-model="localConfig.pageSize"
                :min="20"
                :max="100"
                :step="10"
                :label="`每页显示: ${localConfig.pageSize}个站点`"
                hint="设置每页显示的站点数量"
                persistent-hint
              />
            </v-col>

            <!-- 预览 -->
            <v-col cols="12">
              <v-subheader>预览</v-subheader>
            </v-col>

            <v-col cols="12">
              <v-card variant="outlined" class="pa-4">
                <div class="d-flex align-center justify-space-between mb-3">
                  <span class="text-caption">当前配置预览</span>
                  <v-btn
                    size="x-small"
                    variant="text"
                    @click="resetToDefault"
                  >
                    重置默认
                  </v-btn>
                </div>

                <div class="text-caption mb-2">
                  布局: {{ getLayoutText(localConfig.layout) }} | 
                  大小: {{ getCardSizeText(localConfig.cardSize) }} | 
                  排序: {{ getSortByText(localConfig.sortBy) }} {{ getSortOrderText(localConfig.sortOrder) }}
                </div>

                <div class="text-caption">
                  自动刷新: {{ localConfig.autoRefresh ? `${localConfig.refreshInterval}秒` : '关闭' }} | 
                  虚拟滚动: {{ localConfig.virtualScroll ? '开启' : '关闭' }}
                </div>
              </v-card>
            </v-col>
          </v-row>
        </v-form>
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
          @click="onSave"
        >
          保存
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { SiteManagerViewConfig } from '@/types/siteManager'

interface Props {
  modelValue: boolean
  config: SiteManagerViewConfig
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'updated', config: SiteManagerViewConfig): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式状态
const dialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const formValid = ref(false)

// 本地配置副本
const localConfig = ref<SiteManagerViewConfig>({
  layout: 'grid',
  cardSize: 'medium',
  sortBy: 'priority',
  sortOrder: 'desc',
  showDisabled: true,
  autoRefresh: false,
  refreshInterval: 60,
  virtualScroll: false,
  lazyLoadImages: true,
  pageSize: 50
})

// 选项配置
const layoutOptions = [
  { title: '网格布局', value: 'grid' },
  { title: '列表布局', value: 'list' }
]

const cardSizeOptions = [
  { title: '小卡片', value: 'small' },
  { title: '中卡片', value: 'medium' },
  { title: '大卡片', value: 'large' }
]

const sortByOptions = [
  { title: '优先级', value: 'priority' },
  { title: '名称', value: 'name' },
  { title: '创建时间', value: 'created_at' },
  { title: '健康状态', value: 'health_status' }
]

const sortOrderOptions = [
  { title: '升序', value: 'asc' },
  { title: '降序', value: 'desc' }
]

// 默认配置
const defaultConfig: SiteManagerViewConfig = {
  layout: 'grid',
  cardSize: 'medium',
  sortBy: 'priority',
  sortOrder: 'desc',
  showDisabled: true,
  autoRefresh: false,
  refreshInterval: 60,
  virtualScroll: false,
  lazyLoadImages: true,
  pageSize: 50
}

// 方法
const getLayoutText = (layout: string): string => {
  const textMap: Record<string, string> = {
    grid: '网格',
    list: '列表'
  }
  return textMap[layout] || layout
}

const getCardSizeText = (size: string): string => {
  const textMap: Record<string, string> = {
    small: '小',
    medium: '中',
    large: '大'
  }
  return textMap[size] || size
}

const getSortByText = (sortBy: string): string => {
  const textMap: Record<string, string> = {
    priority: '优先级',
    name: '名称',
    created_at: '创建时间',
    health_status: '健康状态'
  }
  return textMap[sortBy] || sortBy
}

const getSortOrderText = (sortOrder: string): string => {
  const textMap: Record<string, string> = {
    asc: '升序',
    desc: '降序'
  }
  return textMap[sortOrder] || sortOrder
}

const resetToDefault = () => {
  localConfig.value = { ...defaultConfig }
}

const onSave = () => {
  emit('updated', { ...localConfig.value })
  dialog.value = false
}

const onCancel = () => {
  dialog.value = false
}

// 监听配置变化
watch(
  () => props.config,
  (newConfig) => {
    localConfig.value = { ...newConfig }
  },
  { immediate: true, deep: true }
)

// 监听对话框打开
watch(dialog, (isOpen) => {
  if (isOpen) {
    localConfig.value = { ...props.config }
  }
})
</script>

<style lang="scss" scoped>
.v-slider {
  margin-top: 8px;
}
</style>
