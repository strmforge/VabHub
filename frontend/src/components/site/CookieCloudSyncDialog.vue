<template>
  <v-dialog
    v-model="modelValue"
    max-width="600"
    scrollable
    persistent
  >
    <v-card class="cookiecloud-dialog">
      <v-card-item class="py-3">
        <template #prepend>
          <v-icon icon="mdi-cloud-sync" class="me-2" />
        </template>
        <v-card-title class="text-h6">
          CookieCloud同步
        </v-card-title>
        <v-card-subtitle>
          从CookieCloud同步Cookie到站点
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
                v-model="form.server_url"
                label="CookieCloud服务器地址 *"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-server-network"
                hint="CookieCloud服务器地址，如：https://cookiecloud.example.com"
                persistent-hint
                :rules="[v => !!v || '请输入服务器地址', v => isValidUrl(v) || '请输入有效的URL']"
                required
              />
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="form.uuid"
                label="UUID *"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-identifier"
                hint="CookieCloud的UUID"
                persistent-hint
                :rules="[v => !!v || '请输入UUID']"
                required
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="form.password"
                label="密码"
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
              <v-autocomplete
                v-model="form.site_ids"
                :items="siteOptions"
                label="选择站点（留空同步所有站点）"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-web"
                hint="选择要同步的站点，不选则同步所有激活的站点"
                persistent-hint
                multiple
                chips
                clearable
              />
            </v-col>
          </v-row>
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
          :loading="syncing"
          @click="handleSync"
        >
          开始同步
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import api from '@/services/api'

interface Props {
  modelValue: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'synced': []
}>()

const formRef = ref()
const syncing = ref(false)
const siteOptions = ref<Array<{ title: string; value: number }>>([])

const form = ref({
  server_url: '',
  uuid: '',
  password: '',
  site_ids: [] as number[]
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

const loadSites = async () => {
  try {
    const response = await api.get('/sites?active_only=true')
    siteOptions.value = response.data.map((s: any) => ({
      title: s.name,
      value: s.id
    }))
  } catch (error) {
    console.error('加载站点列表失败:', error)
  }
}

const handleSync = async () => {
  const { valid } = await formRef.value.validate()
  if (!valid) return

  syncing.value = true
  try {
    const response = await api.post('/sites/sync-cookiecloud', {
      server_url: form.value.server_url,
      uuid: form.value.uuid,
      password: form.value.password || undefined,
      site_ids: form.value.site_ids.length > 0 ? form.value.site_ids : undefined
    })

    alert(response.data.message || '同步完成')
    emit('synced')
    modelValue.value = false
  } catch (error: any) {
    console.error('CookieCloud同步失败:', error)
    alert('同步失败：' + (error.response?.data?.detail || '未知错误'))
  } finally {
    syncing.value = false
  }
}

watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    loadSites()
    form.value = {
      server_url: '',
      uuid: '',
      password: '',
      site_ids: []
    }
  }
})

onMounted(() => {
  loadSites()
})
</script>

<style scoped>
.cookiecloud-dialog {
  background: rgba(30, 30, 30, 0.95);
  backdrop-filter: blur(10px);
}
</style>

