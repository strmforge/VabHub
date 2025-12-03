<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="600"
  >
    <v-card>
      <v-card-title class="d-flex align-center justify-space-between">
        <span>推荐设置</span>
        <v-btn
          icon="mdi-close"
          variant="text"
          @click="$emit('update:modelValue', false)"
        />
      </v-card-title>

      <v-card-text>
        <v-form ref="formRef">
          <!-- 推荐算法 -->
          <v-select
            v-model="settings.algorithm"
            label="推荐算法"
            :items="algorithms"
            item-title="label"
            item-value="value"
            variant="outlined"
            class="mb-4"
          />

          <!-- 推荐数量 -->
          <v-slider
            v-model="settings.limit"
            label="推荐数量"
            min="10"
            max="100"
            step="10"
            thumb-label
            class="mb-4"
          >
            <template v-slot:append>
              <v-text-field
                v-model="settings.limit"
                type="number"
                style="width: 80px"
                density="compact"
                variant="outlined"
                hide-details
              />
            </template>
          </v-slider>

          <!-- 推荐偏好 -->
          <v-expansion-panels class="mb-4">
            <v-expansion-panel>
              <v-expansion-panel-title>推荐偏好</v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-checkbox
                  v-model="settings.preferences.includeMovies"
                  label="包含电影"
                  hide-details
                  class="mb-2"
                />
                <v-checkbox
                  v-model="settings.preferences.includeTVShows"
                  label="包含电视剧"
                  hide-details
                  class="mb-2"
                />
                <v-checkbox
                  v-model="settings.preferences.includeAnime"
                  label="包含动漫"
                  hide-details
                />
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>

          <!-- 算法权重（高级设置） -->
          <v-expansion-panels>
            <v-expansion-panel>
              <v-expansion-panel-title>算法权重（高级）</v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-slider
                  v-model.number="settings.weights.collaborative"
                  label="协同过滤权重"
                  min="0"
                  max="100"
                  step="10"
                  thumb-label
                  class="mb-4"
                />
                <v-slider
                  v-model.number="settings.weights.content"
                  label="内容推荐权重"
                  min="0"
                  max="100"
                  step="10"
                  thumb-label
                  class="mb-4"
                />
                <v-slider
                  v-model.number="settings.weights.popularity"
                  label="热门推荐权重"
                  min="0"
                  max="100"
                  step="10"
                  thumb-label
                />
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-form>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          variant="text"
          @click="$emit('update:modelValue', false)"
        >
          取消
        </v-btn>
        <v-btn
          color="primary"
          @click="handleSave"
        >
          保存
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'

interface Props {
  modelValue: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'save': []
}>()

const formRef = ref()
const loading = ref(false)
const authStore = useAuthStore()

const algorithms = [
  { value: 'hybrid', label: '混合推荐（推荐）' },
  { value: 'collaborative', label: '协同过滤' },
  { value: 'content', label: '内容推荐' },
  { value: 'popularity', label: '热门推荐' }
]

const settings = reactive({
  algorithm: 'hybrid',
  limit: 20,
  preferences: {
    includeMovies: true,
    includeTVShows: true,
    includeAnime: true
  },
  weights: {
    collaborative: 50,
    content: 30,
    popularity: 20
  }
})

const loadSettings = async () => {
  if (!authStore.user?.id) {
    console.warn('用户未登录，无法加载推荐设置')
    return
  }

  loading.value = true
  try {
    const response = await api.get(`/recommendations/${authStore.user.id}/settings`)
    if (response.data?.settings) {
      Object.assign(settings, response.data.settings)
    }
  } catch (error: any) {
    console.error('加载推荐设置失败:', error)
    // 如果失败，使用默认设置
  } finally {
    loading.value = false
  }
}

const handleSave = async () => {
  if (!authStore.user?.id) {
    console.warn('用户未登录，无法保存推荐设置')
    return
  }

  loading.value = true
  try {
    await api.post(`/recommendations/${authStore.user.id}/settings`, settings)
    emit('save')
    emit('update:modelValue', false)
  } catch (error: any) {
    console.error('保存推荐设置失败:', error)
    alert('保存推荐设置失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    loadSettings()
  }
})
</script>

