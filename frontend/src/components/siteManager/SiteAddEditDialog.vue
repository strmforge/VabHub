<!--
站点添加/编辑对话框 (SITE-MANAGER-1)
用于创建新站点或编辑现有站点信息
-->

<template>
  <v-dialog
    v-model="dialog"
    :max-width="600"
    persistent
  >
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">
          {{ isEdit ? 'mdi-pencil' : 'mdi-plus' }}
        </v-icon>
        {{ isEdit ? '编辑站点' : '添加站点' }}
      </v-card-title>

      <v-card-text>
        <v-form
          ref="formRef"
          v-model="formValid"
          @submit.prevent="onSubmit"
        >
          <v-row>
            <!-- 基本信息 -->
            <v-col cols="12">
              <v-subheader>基本信息</v-subheader>
            </v-col>

            <v-col cols="12" sm="6">
              <v-text-field
                v-model="formData.name"
                label="站点名称"
                placeholder="请输入站点名称"
                :rules="[requiredRule]"
                required
                autofocus
              />
            </v-col>

            <v-col cols="12" sm="6">
              <v-text-field
                v-model="formData.key"
                label="站点标识"
                placeholder="如: hdhome"
                hint="用于内部识别，建议使用英文"
                persistent-hint
              />
            </v-col>

            <v-col cols="12" sm="6">
              <v-text-field
                v-model="formData.url"
                label="站点URL"
                placeholder="https://example.com"
                :rules="[requiredRule, urlRule]"
                required
              />
            </v-col>

            <v-col cols="12" sm="6">
              <v-text-field
                v-model="formData.domain"
                label="主域名"
                placeholder="example.com"
                hint="自动从URL提取，可手动修改"
                persistent-hint
              />
            </v-col>

            <v-col cols="12" sm="6">
              <v-select
                v-model="formData.category"
                :items="categoryOptions"
                label="站点分类"
                clearable
              />
            </v-col>

            <v-col cols="12" sm="6">
              <v-text-field
                v-model.number="formData.priority"
                label="优先级"
                type="number"
                min="0"
                max="10"
                hint="数值越大优先级越高"
                persistent-hint
              />
            </v-col>

            <v-col cols="12">
              <v-text-field
                v-model="formData.icon_url"
                label="图标URL"
                placeholder="https://example.com/favicon.ico"
                hint="站点图标URL，留空将使用默认图标"
                persistent-hint
              />
            </v-col>

            <v-col cols="12">
              <v-text-field
                v-model="formData.tags"
                label="标签"
                placeholder="标签1, 标签2, 标签3"
                hint="多个标签用逗号分隔"
                persistent-hint
              />
            </v-col>

            <!-- 访问配置 -->
            <v-col cols="12">
              <v-subheader>访问配置</v-subheader>
            </v-col>

            <v-col cols="12">
              <v-text-field
                v-model="accessConfigData.rss_url"
                label="RSS URL"
                placeholder="https://example.com/rss.php"
                hint="RSS订阅地址，用于健康检查"
                persistent-hint
              />
            </v-col>

            <v-col cols="12" sm="6">
              <v-switch
                v-model="accessConfigData.use_proxy"
                label="使用代理"
                hint="通过代理访问此站点"
                persistent-hint
              />
            </v-col>

            <v-col cols="12" sm="6">
              <v-switch
                v-model="accessConfigData.use_browser_emulation"
                label="浏览器模拟"
                hint="使用浏览器模拟访问"
                persistent-hint
              />
            </v-col>

            <v-col cols="12" sm="6">
              <v-text-field
                v-model.number="accessConfigData.min_interval_seconds"
                label="最小间隔(秒)"
                type="number"
                min="1"
                max="3600"
              />
            </v-col>

            <v-col cols="12" sm="6">
              <v-text-field
                v-model.number="accessConfigData.max_concurrent_requests"
                label="最大并发数"
                type="number"
                min="1"
                max="10"
              />
            </v-col>

            <!-- 启用状态 -->
            <v-col cols="12">
              <v-switch
                v-model="formData.enabled"
                label="启用站点"
                color="success"
              />
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
          :loading="loading"
          :disabled="!formValid"
          @click="onSubmit"
        >
          {{ isEdit ? '保存' : '添加' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { useSiteManagerStore } from '@/stores/siteManager'
import type { SiteDetail, SiteUpdatePayload, SiteAccessConfigPayload } from '@/types/siteManager'

interface Props {
  modelValue: boolean
  site?: SiteDetail | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'saved'): void
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

// 表单数据
const formData = ref({
  name: '',
  key: '',
  url: '',
  domain: '',
  category: '',
  icon_url: '',
  enabled: true,
  priority: 0,
  tags: ''
})

const accessConfigData = ref({
  rss_url: '',
  use_proxy: false,
  use_browser_emulation: false,
  min_interval_seconds: 10,
  max_concurrent_requests: 1
})

// 计算属性
const isEdit = computed(() => !!props.site)

const categoryOptions = computed(() => [
  { title: 'PT站点', value: 'pt' },
  { title: 'BT站点', value: 'bt' },
  { title: '小说站点', value: 'novel' },
  { title: '漫画站点', value: 'comic' },
  { title: '音乐站点', value: 'music' },
  { title: '影视站点', value: 'movie' },
  { title: '游戏站点', value: 'game' }
])

// 表单验证规则
const requiredRule = (value: string) => !!value || '此字段为必填项'
const urlRule = (value: string) => {
  try {
    new URL(value)
    return true
  } catch {
    return '请输入有效的URL'
  }
}

// 监听URL变化，自动提取域名
watch(
  () => formData.value.url,
  (newUrl) => {
    if (newUrl && !formData.value.domain) {
      try {
        const url = new URL(newUrl)
        formData.value.domain = url.hostname
      } catch {
        // URL格式无效时不提取
      }
    }
  }
)

// 监听站点数据变化，填充表单
watch(
  () => props.site,
  (site) => {
    if (site) {
      // 编辑模式，填充现有数据
      formData.value = {
        name: site.name || '',
        key: site.key || '',
        url: site.url || '',
        domain: site.domain || '',
        category: site.category || '',
        icon_url: site.icon_url || '',
        enabled: site.enabled ?? true,
        priority: site.priority ?? 0,
        tags: Array.isArray(site.tags) ? site.tags.join(', ') : site.tags || ''
      }
      
      // 填充访问配置
      if (site.access_config) {
        accessConfigData.value = {
          rss_url: site.access_config.rss_url || '',
          use_proxy: site.access_config.use_proxy || false,
          use_browser_emulation: site.access_config.use_browser_emulation || false,
          min_interval_seconds: site.access_config.min_interval_seconds || 10,
          max_concurrent_requests: site.access_config.max_concurrent_requests || 1
        }
      }
    } else {
      // 新增模式，重置表单
      resetForm()
    }
  },
  { immediate: true }
)

// 方法
const resetForm = () => {
  formData.value = {
    name: '',
    key: '',
    url: '',
    domain: '',
    category: '',
    icon_url: '',
    enabled: true,
    priority: 0,
    tags: ''
  }
  
  accessConfigData.value = {
    rss_url: '',
    use_proxy: false,
    use_browser_emulation: false,
    min_interval_seconds: 10,
    max_concurrent_requests: 1
  }
  
  nextTick(() => {
    formRef.value?.resetValidation()
  })
}

const onSubmit = async () => {
  if (!formValid.value) return
  
  loading.value = true
  
  try {
    const siteData: SiteUpdatePayload = {
      name: formData.value.name,
      key: formData.value.key || undefined,
      url: formData.value.url,
      domain: formData.value.domain || undefined,
      category: formData.value.category || undefined,
      icon_url: formData.value.icon_url || undefined,
      enabled: formData.value.enabled,
      priority: formData.value.priority,
      tags: formData.value.tags || undefined
    }
    
    const accessConfigPayload: SiteAccessConfigPayload = {
      rss_url: accessConfigData.value.rss_url || undefined,
      use_proxy: accessConfigData.value.use_proxy,
      use_browser_emulation: accessConfigData.value.use_browser_emulation,
      min_interval_seconds: accessConfigData.value.min_interval_seconds,
      max_concurrent_requests: accessConfigData.value.max_concurrent_requests
    }
    
    if (isEdit.value && props.site) {
      // 更新现有站点
      await siteManagerStore.updateSite(props.site.id, siteData)
      await siteManagerStore.updateSiteAccessConfig(props.site.id, accessConfigPayload)
    } else {
      // 创建新站点（这里需要实现创建站点的API）
      // 暂时使用更新API作为占位
      console.log('创建新站点:', siteData, accessConfigData)
    }
    
    emit('saved')
    dialog.value = false
  } catch (error) {
    console.error('保存站点失败:', error)
  } finally {
    loading.value = false
  }
}

const onCancel = () => {
  dialog.value = false
}
</script>

<style lang="scss" scoped>
.v-card {
  .v-card-title {
    font-size: 1.25rem;
    font-weight: 600;
  }
  
  .v-subheader {
    font-size: 0.875rem;
    font-weight: 600;
    color: rgb(var(--v-theme-primary));
    padding-left: 0;
    height: 32px;
  }
}
</style>
