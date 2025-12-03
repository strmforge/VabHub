<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="700"
    scrollable
  >
    <v-card>
      <v-card-title>
        <span class="text-h5">{{ server ? '编辑媒体服务器' : '创建媒体服务器' }}</span>
      </v-card-title>

      <v-card-text>
        <v-form ref="formRef" v-model="valid">
          <v-select
            v-model="form.server_type"
            :items="serverTypeOptions"
            label="服务器类型 *"
            :rules="[rules.required]"
            required
            class="mb-2"
            @update:model-value="onServerTypeChange"
          />

          <v-text-field
            v-model="form.name"
            label="服务器名称 *"
            :rules="[rules.required]"
            required
            class="mb-2"
          />

          <v-text-field
            v-model="form.url"
            label="服务器地址 *"
            :rules="[rules.required, rules.url]"
            required
            hint="例如: http://192.168.1.100:32400"
            persistent-hint
            class="mb-2"
          />

          <!-- Plex认证 -->
          <template v-if="form.server_type === 'plex'">
            <v-text-field
              v-model="form.token"
              label="Plex Token"
              type="password"
              hint="Plex认证Token"
              persistent-hint
              class="mb-2"
            />
          </template>

          <!-- Jellyfin/Emby认证 -->
          <template v-if="form.server_type === 'jellyfin' || form.server_type === 'emby'">
            <v-text-field
              v-model="form.api_key"
              label="API Key *"
              type="password"
              :rules="form.server_type === 'jellyfin' || form.server_type === 'emby' ? [rules.required] : []"
              :required="form.server_type === 'jellyfin' || form.server_type === 'emby'"
              hint="Jellyfin/Emby API密钥"
              persistent-hint
              class="mb-2"
            />
            <v-text-field
              v-model="form.user_id"
              label="用户ID"
              hint="可选，用于特定用户的数据同步"
              persistent-hint
              class="mb-2"
            />
          </template>

          <v-divider class="my-4" />

          <v-switch
            v-model="form.enabled"
            label="启用服务器"
            color="primary"
            class="mb-2"
          />

          <v-switch
            v-model="form.sync_enabled"
            label="启用自动同步"
            color="primary"
            class="mb-2"
          />

          <v-text-field
            v-model.number="form.sync_interval"
            label="同步间隔（秒）"
            type="number"
            min="60"
            hint="自动同步的时间间隔，最小60秒"
            persistent-hint
            class="mb-2"
          />

          <v-divider class="my-4" />

          <div class="text-subtitle-2 mb-2">同步选项</div>

          <v-switch
            v-model="form.sync_watched_status"
            label="同步观看状态"
            color="primary"
            class="mb-2"
          />

          <v-switch
            v-model="form.sync_playback_status"
            label="同步播放状态"
            color="primary"
            class="mb-2"
          />

          <v-switch
            v-model="form.sync_metadata"
            label="同步元数据"
            color="primary"
            class="mb-2"
          />
        </v-form>
      </v-card-text>

      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn
          variant="text"
          @click="$emit('update:modelValue', false)"
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
import { ref, watch } from 'vue'
import { mediaServerApi } from '@/services/api'
import { useToast } from '@/composables/useToast'

const props = defineProps<{
  modelValue: boolean
  server?: any
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  saved: []
}>()

const { showToast } = useToast()

const formRef = ref()
const valid = ref(false)
const saving = ref(false)

const serverTypeOptions = [
  { title: 'Plex', value: 'plex' },
  { title: 'Jellyfin', value: 'jellyfin' },
  { title: 'Emby', value: 'emby' }
]

const form = ref({
  server_type: 'plex',
  name: '',
  url: '',
  api_key: '',
  token: '',
  username: '',
  password: '',
  user_id: '',
  enabled: true,
  sync_enabled: true,
  sync_interval: 3600,
  sync_watched_status: true,
  sync_playback_status: true,
  sync_metadata: true
})

const rules = {
  required: (v: any) => !!v || '此字段为必填项',
  url: (v: string) => {
    if (!v) return true
    try {
      new URL(v)
      return true
    } catch {
      return '请输入有效的URL地址'
    }
  }
}

// 监听server变化，填充表单
watch(() => props.server, (newServer) => {
  if (newServer) {
    form.value = {
      server_type: newServer.server_type || 'plex',
      name: newServer.name || '',
      url: newServer.url || '',
      api_key: newServer.api_key || '',
      token: newServer.token || '',
      username: newServer.username || '',
      password: '',
      user_id: newServer.user_id || '',
      enabled: newServer.enabled !== undefined ? newServer.enabled : true,
      sync_enabled: newServer.sync_enabled !== undefined ? newServer.sync_enabled : true,
      sync_interval: newServer.sync_interval || 3600,
      sync_watched_status: newServer.sync_watched_status !== undefined ? newServer.sync_watched_status : true,
      sync_playback_status: newServer.sync_playback_status !== undefined ? newServer.sync_playback_status : true,
      sync_metadata: newServer.sync_metadata !== undefined ? newServer.sync_metadata : true
    }
  } else {
    // 重置表单
    form.value = {
      server_type: 'plex',
      name: '',
      url: '',
      api_key: '',
      token: '',
      username: '',
      password: '',
      user_id: '',
      enabled: true,
      sync_enabled: true,
      sync_interval: 3600,
      sync_watched_status: true,
      sync_playback_status: true,
      sync_metadata: true
    }
  }
}, { immediate: true })

// 服务器类型变化时的处理
const onServerTypeChange = () => {
  // 清空认证信息
  form.value.api_key = ''
  form.value.token = ''
  form.value.user_id = ''
}

// 保存
const handleSave = async () => {
  const { valid: isValid } = await formRef.value.validate()
  if (!isValid) {
    return
  }

  try {
    saving.value = true

    // 准备数据
    const data: any = {
      name: form.value.name,
      server_type: form.value.server_type,
      url: form.value.url,
      enabled: form.value.enabled,
      sync_enabled: form.value.sync_enabled,
      sync_interval: form.value.sync_interval,
      sync_watched_status: form.value.sync_watched_status,
      sync_playback_status: form.value.sync_playback_status,
      sync_metadata: form.value.sync_metadata
    }

    // 根据服务器类型添加认证信息
    if (form.value.server_type === 'plex') {
      if (form.value.token) {
        data.token = form.value.token
      }
    } else if (form.value.server_type === 'jellyfin' || form.value.server_type === 'emby') {
      if (form.value.api_key) {
        data.api_key = form.value.api_key
      }
      if (form.value.user_id) {
        data.user_id = form.value.user_id
      }
    }

    if (props.server) {
      // 更新
      await mediaServerApi.updateMediaServer(props.server.id, data)
      showToast('更新成功', 'success')
    } else {
      // 创建
      await mediaServerApi.createMediaServer(data)
      showToast('创建成功', 'success')
    }

    emit('saved')
    emit('update:modelValue', false)
  } catch (error: any) {
    showToast('保存失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    saving.value = false
  }
}
</script>

