<template>
  <v-dialog
    v-model="dialog"
    max-width="800"
    scrollable
    persistent
  >
    <v-card>
      <v-card-title class="d-flex align-center justify-space-between">
        <div>
          <div class="text-h6">站点域名管理</div>
          <div class="text-caption text-medium-emphasis">{{ siteName }}</div>
        </div>
        <v-btn
          icon="mdi-close"
          variant="text"
          @click="close"
        />
      </v-card-title>

      <v-divider />

      <v-card-text class="pa-4">
        <v-alert
          type="info"
          variant="tonal"
          class="mb-4"
          density="compact"
        >
          <div class="text-body-2">
            <strong>功能说明：</strong>当PT站点更换域名时，您可以在这里添加新域名并切换，无需等待版本更新。
            <br />
            系统会自动检测域名可访问性，并支持自动切换。
          </div>
        </v-alert>

        <!-- 当前域名 -->
        <v-card variant="outlined" class="mb-4">
          <v-card-title class="text-subtitle-1 pa-3">
            <v-icon size="20" class="mr-2">mdi-web</v-icon>
            当前使用域名
          </v-card-title>
          <v-card-text class="pa-3">
            <div v-if="domainConfig.current_domain" class="d-flex align-center justify-space-between">
              <div>
                <div class="text-body-1 font-weight-medium">{{ domainConfig.current_domain }}</div>
                <div class="text-caption text-medium-emphasis mt-1">
                  最后检测: {{ formatTime(domainConfig.last_detect_time) }}
                </div>
              </div>
              <v-chip color="success" size="small" prepend-icon="mdi-check-circle">
                使用中
              </v-chip>
            </div>
            <div v-else class="text-body-2 text-medium-emphasis">
              未设置当前域名
            </div>
          </v-card-text>
        </v-card>

        <!-- 自动检测开关 -->
        <v-card variant="outlined" class="mb-4">
          <v-card-text class="pa-3">
            <div class="d-flex align-center justify-space-between">
              <div>
                <div class="text-body-1 font-weight-medium">自动检测和切换</div>
                <div class="text-caption text-medium-emphasis mt-1">
                  启用后，系统会自动检测域名可访问性，并在当前域名不可访问时自动切换到其他可用域名
                </div>
              </div>
              <v-switch
                v-model="domainConfig.auto_detect"
                color="primary"
                hide-details
                @update:model-value="updateAutoDetect"
              />
            </div>
          </v-card-text>
        </v-card>

        <!-- 活跃域名列表 -->
        <v-card variant="outlined" class="mb-4">
          <v-card-title class="text-subtitle-1 pa-3 d-flex align-center justify-space-between">
            <div>
              <v-icon size="20" class="mr-2">mdi-check-circle</v-icon>
              活跃域名
            </div>
            <v-btn
              size="small"
              color="primary"
              prepend-icon="mdi-plus"
              @click="showAddDomainDialog = true"
            >
              添加域名
            </v-btn>
          </v-card-title>
          <v-card-text class="pa-3">
            <div v-if="domainConfig.active_domains && domainConfig.active_domains.length > 0">
              <v-list density="compact">
                <v-list-item
                  v-for="(domain, index) in domainConfig.active_domains"
                  :key="index"
                  class="px-0"
                >
                  <template v-slot:prepend>
                    <v-icon
                      :color="domain === domainConfig.current_domain ? 'success' : 'grey'"
                      size="20"
                    >
                      {{ domain === domainConfig.current_domain ? 'mdi-check-circle' : 'mdi-circle-outline' }}
                    </v-icon>
                  </template>
                  <v-list-item-title>{{ domain }}</v-list-item-title>
                  <template v-slot:append>
                    <div class="d-flex align-center ga-2">
                      <v-btn
                        v-if="domain !== domainConfig.current_domain"
                        size="small"
                        variant="text"
                        color="primary"
                        @click="switchDomain(domain)"
                      >
                        切换
                      </v-btn>
                      <v-btn
                        size="small"
                        variant="text"
                        color="error"
                        icon="mdi-delete"
                        @click="removeDomain(domain)"
                      />
                    </div>
                  </template>
                </v-list-item>
              </v-list>
            </div>
            <div v-else class="text-body-2 text-medium-emphasis text-center py-4">
              暂无活跃域名，请添加域名
            </div>
          </v-card-text>
        </v-card>

        <!-- 废弃域名列表 -->
        <v-card variant="outlined" class="mb-4">
          <v-card-title class="text-subtitle-1 pa-3">
            <v-icon size="20" class="mr-2">mdi-archive</v-icon>
            废弃域名
          </v-card-title>
          <v-card-text class="pa-3">
            <div v-if="domainConfig.deprecated_domains && domainConfig.deprecated_domains.length > 0">
              <v-list density="compact">
                <v-list-item
                  v-for="(domain, index) in domainConfig.deprecated_domains"
                  :key="index"
                  class="px-0"
                >
                  <v-list-item-title class="text-medium-emphasis">{{ domain }}</v-list-item-title>
                  <template v-slot:append>
                    <v-btn
                      size="small"
                      variant="text"
                      color="primary"
                      @click="restoreDomain(domain)"
                    >
                      恢复
                    </v-btn>
                  </template>
                </v-list-item>
              </v-list>
            </div>
            <div v-else class="text-body-2 text-medium-emphasis text-center py-4">
              暂无废弃域名
            </div>
          </v-card-text>
        </v-card>

        <!-- 切换历史 -->
        <v-card variant="outlined" v-if="domainConfig.switch_history && domainConfig.switch_history.length > 0">
          <v-card-title class="text-subtitle-1 pa-3">
            <v-icon size="20" class="mr-2">mdi-history</v-icon>
            切换历史（最近10条）
          </v-card-title>
          <v-card-text class="pa-3">
            <v-timeline density="compact" side="end">
              <v-timeline-item
                v-for="(item, index) in domainConfig.switch_history"
                :key="index"
                size="small"
                dot-color="primary"
              >
                <div class="text-body-2">
                  <div class="font-weight-medium">{{ item.reason }}</div>
                  <div class="text-caption text-medium-emphasis mt-1">
                    {{ item.from }} → {{ item.to }}
                  </div>
                  <div class="text-caption text-medium-emphasis">
                    {{ formatTime(item.time) }}
                  </div>
                </div>
              </v-timeline-item>
            </v-timeline>
          </v-card-text>
        </v-card>
      </v-card-text>

      <v-divider />

      <v-card-actions class="pa-3">
        <v-spacer />
        <v-btn
          variant="text"
          @click="close"
        >
          关闭
        </v-btn>
        <v-btn
          color="primary"
          prepend-icon="mdi-refresh"
          @click="detectAndSwitch"
          :loading="detecting"
        >
          检测并切换
        </v-btn>
      </v-card-actions>
    </v-card>

    <!-- 添加域名对话框 -->
    <v-dialog
      v-model="showAddDomainDialog"
      max-width="500"
    >
      <v-card>
        <v-card-title>添加域名</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="newDomain"
            label="域名"
            placeholder="https://example.com"
            hint="请输入完整的域名（包含协议）"
            persistent-hint
            variant="outlined"
            density="compact"
            class="mb-2"
          />
          <v-checkbox
            v-model="newDomainIsActive"
            label="添加到活跃域名"
            density="compact"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showAddDomainDialog = false">取消</v-btn>
          <v-btn color="primary" @click="addDomain">添加</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import api from '@/services/api'
import { useToast } from '@/composables/useToast'

const { showSuccess, showError } = useToast()

interface Props {
  modelValue: boolean
  siteId: number
  siteName: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const dialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const domainConfig = ref<any>({
  active_domains: [],
  deprecated_domains: [],
  current_domain: null,
  auto_detect: true,
  last_detect_time: null,
  switch_history: []
})

const loading = ref(false)
const detecting = ref(false)
const showAddDomainDialog = ref(false)
const newDomain = ref('')
const newDomainIsActive = ref(true)

const loadDomainConfig = async () => {
  if (!props.siteId) return
  
  loading.value = true
  try {
    const response = await api.get(`/sites/${props.siteId}/domains/`)
    if (response.data?.success && response.data?.data) {
      domainConfig.value = response.data.data
    }
  } catch (error: any) {
    console.error('加载域名配置失败:', error)
    showError(error.response?.data?.detail?.error_message || '加载域名配置失败')
  } finally {
    loading.value = false
  }
}

const updateAutoDetect = async () => {
  try {
    await api.put(`/sites/${props.siteId}/domains/`, {
      auto_detect: domainConfig.value.auto_detect
    })
    showSuccess('自动检测设置已更新')
  } catch (error: any) {
    console.error('更新自动检测设置失败:', error)
    showError(error.response?.data?.detail?.error_message || '更新失败')
    // 恢复原值
    domainConfig.value.auto_detect = !domainConfig.value.auto_detect
  }
}

const addDomain = async () => {
  if (!newDomain.value.trim()) {
    showError('请输入域名')
    return
  }

  try {
    await api.post(`/sites/${props.siteId}/domains/add`, {
      domain: newDomain.value.trim(),
      is_active: newDomainIsActive.value
    })
    showSuccess('域名添加成功')
    newDomain.value = ''
    showAddDomainDialog.value = false
    await loadDomainConfig()
  } catch (error: any) {
    console.error('添加域名失败:', error)
    showError(error.response?.data?.detail?.error_message || '添加域名失败')
  }
}

const removeDomain = async (domain: string) => {
  if (domain === domainConfig.value.current_domain) {
    showError('不能移除当前使用的域名，请先切换到其他域名')
    return
  }

  try {
    await api.delete(`/sites/${props.siteId}/domains/remove`, {
      params: { domain }
    })
    showSuccess('域名已移除')
    await loadDomainConfig()
  } catch (error: any) {
    console.error('移除域名失败:', error)
    showError(error.response?.data?.detail?.error_message || '移除域名失败')
  }
}

const switchDomain = async (domain: string) => {
  try {
    await api.post(`/sites/${props.siteId}/domains/switch`, null, {
      params: { domain, reason: '手动切换' }
    })
    showSuccess('域名切换成功')
    await loadDomainConfig()
  } catch (error: any) {
    console.error('切换域名失败:', error)
    showError(error.response?.data?.detail?.error_message || '切换域名失败')
  }
}

const restoreDomain = async (domain: string) => {
  try {
    await api.post(`/sites/${props.siteId}/domains/add`, {
      domain,
      is_active: true
    })
    showSuccess('域名已恢复到活跃列表')
    await loadDomainConfig()
  } catch (error: any) {
    console.error('恢复域名失败:', error)
    showError(error.response?.data?.detail?.error_message || '恢复域名失败')
  }
}

const detectAndSwitch = async () => {
  detecting.value = true
  try {
    const response = await api.post(`/sites/${props.siteId}/domains/detect`)
    if (response.data?.success) {
      if (response.data?.data?.switched) {
        showSuccess(`域名已自动切换到: ${response.data.data.to}`)
      } else {
        showSuccess(response.data?.data?.reason || '检测完成')
      }
      await loadDomainConfig()
    }
  } catch (error: any) {
    console.error('自动检测失败:', error)
    showError(error.response?.data?.detail?.error_message || '自动检测失败')
  } finally {
    detecting.value = false
  }
}

const formatTime = (time: string | null) => {
  if (!time) return '从未'
  try {
    const date = new Date(time)
    return date.toLocaleString('zh-CN')
  } catch {
    return time
  }
}

const close = () => {
  dialog.value = false
}

watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    loadDomainConfig()
  }
})

watch(() => props.siteId, () => {
  if (props.modelValue) {
    loadDomainConfig()
  }
})
</script>

<style scoped>
.v-timeline-item {
  padding-bottom: 8px;
}
</style>

