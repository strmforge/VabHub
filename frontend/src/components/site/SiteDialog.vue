<template>
  <v-dialog
    v-model="modelValue"
    max-width="800"
    scrollable
    persistent
  >
    <v-card class="site-dialog">
      <v-card-item class="py-3">
        <template #prepend>
          <v-icon icon="mdi-web" class="me-2" />
        </template>
        <v-card-title class="text-h6">
          {{ editingSite ? '编辑站点' : '添加站点' }}
        </v-card-title>
        <v-card-subtitle>
          {{ editingSite ? '修改站点信息' : '添加新的PT站点' }}
        </v-card-subtitle>
        <template #append>
          <v-btn
            icon="mdi-close"
            variant="text"
            size="small"
            @click="modelValue = false"
          />
        </template>
      </v-card-item>

      <v-card-text>
        <v-form ref="formRef">
          <v-row>
            <v-col cols="12">
              <v-text-field
                v-model="form.name"
                label="站点名称 *"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-tag"
                :rules="[v => !!v || '请输入站点名称']"
                required
              />
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="12">
              <v-text-field
                v-model="form.url"
                label="站点地址 *"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-link"
                hint="请输入完整的站点URL，如：https://example.com"
                persistent-hint
                :rules="[v => !!v || '请输入站点地址', v => isValidUrl(v) || '请输入有效的URL']"
                required
              />
            </v-col>
          </v-row>

          <v-divider class="my-4" />

          <div class="text-subtitle-1 font-weight-medium mb-3">
            Cookie配置
          </div>

          <v-row>
            <v-col cols="12">
              <v-textarea
                v-model="form.cookie"
                label="Cookie"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-cookie"
                hint="手动输入Cookie，或使用CookieCloud同步"
                persistent-hint
                rows="3"
                auto-grow
              />
            </v-col>
          </v-row>

          <v-divider class="my-4" />

          <div class="text-subtitle-1 font-weight-medium mb-3">
            CookieCloud配置（可选）
          </div>

          <v-row>
            <v-col cols="12">
              <v-text-field
                v-model="form.cookiecloud_server"
                label="CookieCloud服务器地址"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-cloud-sync"
                hint="CookieCloud服务器地址，如：https://cookiecloud.example.com"
                persistent-hint
              />
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="form.cookiecloud_uuid"
                label="CookieCloud UUID"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-identifier"
                hint="CookieCloud的UUID"
                persistent-hint
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="form.cookiecloud_password"
                label="CookieCloud密码"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-lock"
                type="password"
                hint="CookieCloud加密密码（如果有）"
                persistent-hint
              />
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="12">
              <v-switch
                v-model="form.is_active"
                label="启用站点"
                color="primary"
                hide-details
              />
            </v-col>
          </v-row>

          <!-- Phase AI-4: AI 适配设置（实验性功能）- 仅在开发者模式显示 -->
          <template v-if="isDevMode()">
            <v-divider class="my-4" />
            <div class="text-subtitle-1 font-weight-medium mb-3">
              AI 适配设置（实验性功能）
            </div>
            <v-alert
              type="info"
              variant="tonal"
              density="compact"
              class="mb-3"
            >
              这些设置控制本站点的 AI 适配行为。AI 适配是实验性功能，用于自动生成站点适配配置。
            </v-alert>
            <v-row>
              <v-col cols="12">
                <v-switch
                  v-model="form.ai_disabled"
                  label="禁用 AI 适配（本站点）"
                  color="warning"
                  hide-details
                  hint="启用后，本站点将不会使用 AI 生成的适配配置"
                  persistent-hint
                />
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="12">
                <v-switch
                  v-model="form.ai_manual_profile_preferred"
                  label="优先使用人工配置（存在人工配置时）"
                  color="primary"
                  hide-details
                  hint="启用后，如果既有人工配置也有 AI 配置，将优先使用人工配置"
                  persistent-hint
                />
              </v-col>
            </v-row>
          </template>
        </v-form>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          variant="text"
          @click="modelValue = false"
        >
          取消
        </v-btn>
        <v-btn
          color="primary"
          :loading="saving"
          @click="handleSave"
        >
          保存
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import api from '@/services/api'
import { isDevMode } from '@/utils/devMode'

interface Props {
  modelValue: boolean
  site?: any
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'saved': []
}>()

const formRef = ref()
const saving = ref(false)
const editingSite = computed(() => props.site)

const form = ref({
  name: '',
  url: '',
  cookie: '',
  cookiecloud_server: '',
  cookiecloud_uuid: '',
  cookiecloud_password: '',
  is_active: true,
  // Phase AI-4: AI 适配设置
  ai_disabled: false,
  ai_manual_profile_preferred: false
})

const modelValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const isValidUrl = (url: string): boolean => {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

const resetForm = () => {
  form.value = {
    name: '',
    url: '',
    cookie: '',
    cookiecloud_server: '',
    cookiecloud_uuid: '',
    cookiecloud_password: '',
    is_active: true,
    // Phase AI-4: AI 适配设置
    ai_disabled: false,
    ai_manual_profile_preferred: false
  }
}

const loadSiteData = () => {
  if (editingSite.value) {
    form.value = {
      name: editingSite.value.name || '',
      url: editingSite.value.url || '',
      cookie: editingSite.value.cookie || '',
      cookiecloud_server: editingSite.value.cookiecloud_server || '',
      cookiecloud_uuid: editingSite.value.cookiecloud_uuid || '',
      cookiecloud_password: editingSite.value.cookiecloud_password || '',
      is_active: editingSite.value.is_active !== false,
      // Phase AI-4: AI 适配设置
      ai_disabled: editingSite.value.ai_disabled || false,
      ai_manual_profile_preferred: editingSite.value.ai_manual_profile_preferred || false
    }
  } else {
    resetForm()
  }
}

const handleSave = async () => {
  const { valid } = await formRef.value.validate()
  if (!valid) return

  saving.value = true
  try {
    if (editingSite.value?.id) {
      await api.put(`/sites/${editingSite.value.id}`, form.value)
    } else {
      await api.post('/sites', form.value)
    }
    emit('saved')
    modelValue.value = false
  } catch (error: any) {
    console.error('保存站点失败:', error)
    alert('保存失败：' + (error.response?.data?.detail || '未知错误'))
  } finally {
    saving.value = false
  }
}

watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    loadSiteData()
  }
})

watch(() => props.site, () => {
  if (props.modelValue) {
    loadSiteData()
  }
})
</script>

<style scoped>
.site-dialog {
  background: rgba(30, 30, 30, 0.95);
  backdrop-filter: blur(10px);
}
</style>

