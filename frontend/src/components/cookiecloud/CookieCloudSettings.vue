<template>
  <div class="cookiecloud-settings">
    <!-- 基础配置 -->
    <v-form ref="formRef" v-model="formValid">
      <v-row>
        <v-col cols="12">
          <v-switch
            v-model="editingSettings.enabled"
            label="启用CookieCloud同步"
            color="primary"
            hint="启用后将自动从CookieCloud服务器同步Cookie到VabHub"
            persistent-hint
          />
        </v-col>
      </v-row>

      <v-expand-transition>
        <div v-show="editingSettings.enabled">
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="editingSettings.host"
                label="CookieCloud服务器地址"
                placeholder="https://cookiecloud.example.com"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-server"
                :rules="hostRules"
                hint="CookieCloud服务器的完整地址"
                persistent-hint
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="editingSettings.uuid"
                label="UUID"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-fingerprint"
                :rules="uuidRules"
                hint="CookieCloud账户的唯一标识符"
                persistent-hint
              />
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="editingSettings.password"
                label="密码"
                :type="showPassword ? 'text' : 'password'"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-lock"
                :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                @click:append-inner="showPassword = !showPassword"
                :rules="passwordRules"
                hint="CookieCloud账户密码"
                persistent-hint
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model.number="editingSettings.sync_interval_minutes"
                label="同步间隔（分钟）"
                type="number"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-clock-outline"
                :rules="syncIntervalRules"
                hint="自动同步的时间间隔，5-1440分钟"
                persistent-hint
              />
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="12">
              <v-textarea
                v-model="whitelistText"
                label="安全域名白名单"
                placeholder="example.com&#10;tracker.example.org&#10;*.example.net"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-shield-check"
                rows="3"
                hint="只同步这些域名的Cookie，每行一个域名，支持通配符"
                persistent-hint
                @update:model-value="updateWhitelist"
              />
            </v-col>
          </v-row>
        </div>
      </v-expand-transition>
    </v-form>

    <!-- 操作按钮 -->
    <v-row class="mt-4">
      <v-col cols="12" class="d-flex gap-2">
        <v-btn
          color="primary"
          :loading="store.settingsLoading"
          :disabled="!formValid"
          @click="saveSettings"
        >
          <v-icon start>mdi-content-save</v-icon>
          保存设置
        </v-btn>
        
        <v-btn
          variant="outlined"
          :disabled="!store.isConfigured"
          @click="testConnection"
          :loading="store.testLoading"
        >
          <v-icon start>mdi-connection-test</v-icon>
          测试连接
        </v-btn>
        
        <v-btn
          variant="outlined"
          :disabled="!store.isConfigured"
          @click="triggerSync"
          :loading="store.syncLoading"
        >
          <v-icon start>mdi-sync</v-icon>
          立即同步
        </v-btn>
        
        <v-btn
          variant="text"
          @click="resetSettings"
        >
          <v-icon start>mdi-restore</v-icon>
          重置
        </v-btn>
      </v-col>
    </v-row>

    <!-- 状态显示 -->
    <v-row v-if="store.settings" class="mt-4">
      <v-col cols="12">
        <v-card variant="outlined">
          <v-card-title class="text-h6">
            <v-icon start>mdi-information</v-icon>
            同步状态
          </v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12" md="6">
                <v-list density="compact">
                  <v-list-item>
                    <v-list-item-title>上次同步时间</v-list-item-title>
                    <v-list-item-subtitle>
                      {{ formatDateTime(store.settings.last_sync_at) }}
                    </v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item>
                    <v-list-item-title>同步状态</v-list-item-title>
                    <v-list-item-subtitle>
                      <v-chip
                        :color="store.syncStatusColor"
                        size="small"
                        variant="flat"
                      >
                        {{ store.syncStatusText }}
                      </v-chip>
                    </v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-col>
              <v-col cols="12" md="6">
                <v-list density="compact">
                  <v-list-item v-if="store.settings.last_error">
                    <v-list-item-title>上次错误</v-list-item-title>
                    <v-list-item-subtitle class="text-error">
                      {{ store.settings.last_error }}
                    </v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item>
                    <v-list-item-title>配置状态</v-list-item-title>
                    <v-list-item-subtitle>
                      <v-chip
                        :color="store.isConfigured ? 'success' : 'warning'"
                        size="small"
                        variant="flat"
                      >
                        {{ store.isConfigured ? '已配置' : '未配置' }}
                      </v-chip>
                    </v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 连接测试结果 -->
    <v-row v-if="store.testResult" class="mt-4">
      <v-col cols="12">
        <v-alert
          :type="store.testResult.success ? 'success' : 'error'"
          variant="tonal"
          closable
        >
          <v-alert-title>
            {{ store.testResult.success ? '连接测试成功' : '连接测试失败' }}
          </v-alert-title>
          {{ store.testResult.message }}
        </v-alert>
      </v-col>
    </v-row>

    <!-- 同步结果 -->
    <v-row v-if="store.syncResult" class="mt-4">
      <v-col cols="12">
        <v-alert
          :type="store.syncResult.success ? 'success' : 'error'"
          variant="tonal"
          closable
        >
          <v-alert-title>
            {{ store.syncResult.success ? '同步完成' : '同步失败' }}
          </v-alert-title>
          <div>
            总站点: {{ store.syncResult?.total_sites || 0 }} | 
            成功: {{ store.syncResult?.synced_sites || 0 }} | 
            无匹配: {{ store.syncResult?.unmatched_sites || 0 }} | 
            错误: {{ store.syncResult?.error_sites || 0 }}
          </div>
          <div v-if="store.syncResult?.errors && store.syncResult.errors.length > 0" class="mt-2">
            <v-expansion-panels>
              <v-expansion-panel>
                <v-expansion-panel-title>查看详细错误</v-expansion-panel-title>
                <v-expansion-panel-text>
                  <ul>
                    <li v-for="error in store.syncResult.errors" :key="error">
                      {{ error }}
                    </li>
                  </ul>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </div>
        </v-alert>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useCookieCloudStore } from '@/stores/cookiecloud'
import { useToast } from 'vue-toastification'
import dayjs from 'dayjs'

const store = useCookieCloudStore()
const toast = useToast()

// 表单相关
const formRef = ref()
const formValid = ref(false)
const showPassword = ref(false)
const whitelistText = ref('')

// 表单验证规则
const hostRules = [
  (v: string) => !v || v.startsWith('http') || '主机地址必须以http://或https://开头',
  (v: string) => !v || v.length >= 10 || '主机地址长度不能少于10个字符'
]

const uuidRules = [
  (v: string) => !v || v.length >= 8 || 'UUID长度不能少于8个字符'
]

const passwordRules = [
  (v: string) => !v || v.length >= 4 || '密码长度不能少于4个字符'
]

const syncIntervalRules = [
  (v: number) => !v || (v >= 5 && v <= 1440) || '同步间隔必须在5-1440分钟之间'
]

// 编辑中的设置
const editingSettings = computed(() => store.editingSettings)

// 更新白名单文本
const updateWhitelist = (text: string) => {
  const domains = text
    .split('\n')
    .map(line => line.trim())
    .filter(line => line.length > 0)
  store.editingSettings.safe_host_whitelist = domains
}

// 格式化日期时间
const formatDateTime = (dateTime: string | null | undefined) => {
  if (!dateTime) return '从未同步'
  return dayjs(dateTime).format('YYYY-MM-DD HH:mm:ss')
}

// 保存设置
const saveSettings = async () => {
  try {
    await store.updateSettings()
    toast.success('CookieCloud设置保存成功')
  } catch (error: any) {
    toast.error(`保存失败: ${error.message}`)
  }
}

// 测试连接
const testConnection = async () => {
  try {
    await store.testConnection()
    if (store.testResult?.success) {
      toast.success('连接测试成功')
    } else {
      toast.error(`连接测试失败: ${store.testResult?.message}`)
    }
  } catch (error: any) {
    toast.error(`测试失败: ${error.message}`)
  }
}

// 触发同步
const triggerSync = async () => {
  try {
    await store.triggerSync()
    if (store.syncResult?.success) {
      toast.success(`同步完成: 成功${store.syncResult.synced_sites}个站点`)
    } else {
      toast.error(`同步失败: ${store.syncResult.errors.join(', ')}`)
    }
  } catch (error: any) {
    toast.error(`同步失败: ${error.message}`)
  }
}

// 重置设置
const resetSettings = () => {
  store.resetEditingSettings()
  updateWhitelistText()
  toast.info('设置已重置')
}

// 更新白名单文本显示
const updateWhitelistText = () => {
  if (store.editingSettings.safe_host_whitelist) {
    whitelistText.value = store.editingSettings.safe_host_whitelist.join('\n')
  } else {
    whitelistText.value = ''
  }
}

// 监听设置变化
watch(() => store.settings, () => {
  updateWhitelistText()
}, { immediate: true })

// 初始化
onMounted(async () => {
  try {
    await store.fetchSettings()
  } catch (error: any) {
    toast.error(`加载设置失败: ${error.message}`)
  }
})
</script>

<style scoped>
.cookiecloud-settings {
  padding: 16px 0;
}

.gap-2 {
  gap: 8px;
}
</style>
