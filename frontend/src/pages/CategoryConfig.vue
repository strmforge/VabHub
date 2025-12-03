<template>
  <div class="category-config-page">
    <PageHeader
      title="媒体分类配置"
      subtitle="配置电影、电视剧和音乐的二级分类策略（类似MoviePilot）"
    />

    <v-card variant="outlined" class="mb-4">
      <v-card-title class="d-flex align-center">
        <v-icon class="me-2">mdi-file-code</v-icon>
        分类配置文件
        <v-spacer />
        <v-btn
          color="primary"
          prepend-icon="mdi-reload"
          variant="text"
          @click="reloadConfig"
          :loading="reloading"
        >
          重新加载
        </v-btn>
        <v-btn
          color="success"
          prepend-icon="mdi-content-save"
          variant="elevated"
          @click="saveConfig"
          :loading="saving"
          :disabled="!hasChanges"
        >
          保存配置
        </v-btn>
      </v-card-title>
      <v-card-text>
        <v-alert type="info" variant="tonal" class="mb-4">
          <div class="text-body-2">
            <strong>配置文件路径：</strong>{{ configPath }}
          </div>
          <div class="text-body-2 mt-2">
            <strong>说明：</strong>配置文件采用YAML格式，支持电影、电视剧和音乐的二级分类。
            分类按配置顺序从上到下匹配，匹配到第一个符合条件的分类即返回。
          </div>
        </v-alert>

        <v-tabs v-model="activeTab" align-tabs="start" class="mb-4">
          <v-tab value="editor">
            <v-icon start>mdi-code-tags</v-icon>
            编辑器
          </v-tab>
          <v-tab value="preview">
            <v-icon start>mdi-eye</v-icon>
            预览
          </v-tab>
          <v-tab value="list">
            <v-icon start>mdi-format-list-bulleted</v-icon>
            分类列表
          </v-tab>
        </v-tabs>

        <v-window v-model="activeTab">
          <!-- 编辑器标签页 -->
          <v-window-item value="editor">
            <v-textarea
              v-model="configContent"
              label="YAML配置内容"
              variant="outlined"
              rows="30"
              auto-grow
              :readonly="loading"
              class="font-monospace"
              @input="onContentChange"
            />
            <v-alert
              v-if="yamlError"
              type="error"
              variant="tonal"
              class="mt-4"
              closable
              @click:close="yamlError = ''"
            >
              <div class="text-body-2">
                <strong>YAML格式错误：</strong>{{ yamlError }}
              </div>
            </v-alert>
          </v-window-item>

          <!-- 预览标签页 -->
          <v-window-item value="preview">
            <v-card variant="outlined" class="mb-4">
              <v-card-title>分类预览</v-card-title>
              <v-card-text>
                <v-row>
                  <v-col cols="12" md="4">
                    <v-select
                      v-model="previewMediaType"
                      :items="mediaTypeOptions"
                      label="媒体类型"
                      variant="outlined"
                      hide-details
                    />
                  </v-col>
                  <v-col cols="12" md="8">
                    <v-btn
                      color="primary"
                      prepend-icon="mdi-magnify"
                      @click="previewCategory"
                      :loading="previewing"
                    >
                      预览分类
                    </v-btn>
                  </v-col>
                </v-row>

                <v-textarea
                  v-model="previewTmdbData"
                  label="TMDB数据（JSON格式）"
                  variant="outlined"
                  rows="10"
                  class="mt-4 font-monospace"
                  placeholder='例如：{"genre_ids": [16], "original_language": "zh", "origin_country": ["CN"]}'
                />

                <v-alert
                  v-if="previewResult"
                  :type="previewResult.category ? 'success' : 'warning'"
                  variant="tonal"
                  class="mt-4"
                >
                  <div class="text-body-1">
                    <strong>分类结果：</strong>{{ previewResult.category || '未分类' }}
                  </div>
                  <div v-if="previewResult.matched_rules" class="text-body-2 mt-2">
                    <strong>匹配规则：</strong>
                    <pre class="mt-2">{{ JSON.stringify(previewResult.matched_rules, null, 2) }}</pre>
                  </div>
                </v-alert>
              </v-card-text>
            </v-card>
          </v-window-item>

          <!-- 分类列表标签页 -->
          <v-window-item value="list">
            <v-row>
              <v-col cols="12" md="4">
                <v-card variant="outlined">
                  <v-card-title>电影分类</v-card-title>
                  <v-card-text>
                    <v-list density="compact">
                      <v-list-item
                        v-for="category in categoryList.movie"
                        :key="category"
                        :title="category"
                        prepend-icon="mdi-movie"
                      />
                      <v-list-item v-if="categoryList.movie.length === 0" title="暂无分类" />
                    </v-list>
                  </v-card-text>
                </v-card>
              </v-col>
              <v-col cols="12" md="4">
                <v-card variant="outlined">
                  <v-card-title>电视剧分类</v-card-title>
                  <v-card-text>
                    <v-list density="compact">
                      <v-list-item
                        v-for="category in categoryList.tv"
                        :key="category"
                        :title="category"
                        prepend-icon="mdi-television"
                      />
                      <v-list-item v-if="categoryList.tv.length === 0" title="暂无分类" />
                    </v-list>
                  </v-card-text>
                </v-card>
              </v-col>
              <v-col cols="12" md="4">
                <v-card variant="outlined">
                  <v-card-title>音乐分类</v-card-title>
                  <v-card-text>
                    <v-list density="compact">
                      <v-list-item
                        v-for="category in categoryList.music"
                        :key="category"
                        :title="category"
                        prepend-icon="mdi-music"
                      />
                      <v-list-item v-if="categoryList.music.length === 0" title="暂无分类" />
                    </v-list>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-window-item>
        </v-window>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'vue-toastification'
import api from '@/services/api'
import PageHeader from '@/components/common/PageHeader.vue'

const toast = useToast()

const loading = ref(false)
const saving = ref(false)
const reloading = ref(false)
const previewing = ref(false)
const configContent = ref('')
const configPath = ref('')
const hasChanges = ref(false)
const yamlError = ref('')
const activeTab = ref('editor')

const previewMediaType = ref('movie')
const previewTmdbData = ref('')
const previewResult = ref<any>(null)

const categoryList = ref({
  movie: [] as string[],
  tv: [] as string[],
  music: [] as string[]
})

const mediaTypeOptions = [
  { title: '电影', value: 'movie' },
  { title: '电视剧', value: 'tv' },
  { title: '音乐', value: 'music' }
]

const loadConfig = async () => {
  loading.value = true
  try {
    const response = await api.get('/category/config')
    configContent.value = response.data.content
    configPath.value = response.data.path
    hasChanges.value = false
    yamlError.value = ''
  } catch (error: any) {
    console.error('Failed to load category config:', error)
    toast.error(error.message || '加载分类配置失败！')
  } finally {
    loading.value = false
  }
}

const loadCategoryList = async () => {
  try {
    const response = await api.get('/category/list')
    categoryList.value = response.data
  } catch (error: any) {
    console.error('Failed to load category list:', error)
  }
}

const saveConfig = async () => {
  // 验证YAML格式
  try {
    JSON.parse(previewTmdbData.value || '{}')
  } catch (e) {
    // 不是JSON，可能是YAML，继续
  }

  saving.value = true
  try {
    await api.put('/category/config', {
      content: configContent.value
    })
    hasChanges.value = false
    yamlError.value = ''
    await loadCategoryList()
    toast.success('分类配置保存成功！')
  } catch (error: any) {
    console.error('Failed to save category config:', error)
    if (error.response?.data?.error_code === 'INVALID_YAML_FORMAT') {
      yamlError.value = error.response.data.error_message || 'YAML格式错误'
    }
    toast.error(error.message || '保存分类配置失败！')
  } finally {
    saving.value = false
  }
}

const reloadConfig = async () => {
  reloading.value = true
  try {
    await api.post('/category/reload')
    await loadConfig()
    await loadCategoryList()
    toast.success('分类配置重新加载成功！')
  } catch (error: any) {
    console.error('Failed to reload category config:', error)
    toast.error(error.message || '重新加载分类配置失败！')
  } finally {
    reloading.value = false
  }
}

const previewCategory = async () => {
  if (!previewTmdbData.value) {
    toast.warning('请输入TMDB数据！')
    return
  }

  let tmdbData: any
  try {
    tmdbData = JSON.parse(previewTmdbData.value)
  } catch (e) {
    toast.error('TMDB数据格式错误，请输入有效的JSON格式！')
    return
  }

  previewing.value = true
  try {
    const response = await api.post('/category/preview', {
      media_type: previewMediaType.value,
      tmdb_data: tmdbData
    })
    previewResult.value = response.data
  } catch (error: any) {
    console.error('Failed to preview category:', error)
    toast.error(error.message || '预览分类失败！')
    previewResult.value = null
  } finally {
    previewing.value = false
  }
}

const onContentChange = () => {
  hasChanges.value = true
  yamlError.value = ''
}

onMounted(async () => {
  await loadConfig()
  await loadCategoryList()
})
</script>

<style scoped>
.category-config-page {
  padding: 24px;
}

.font-monospace {
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
}

pre {
  background-color: rgba(var(--v-theme-surface), 0.5);
  padding: 8px;
  border-radius: 4px;
  overflow-x: auto;
}
</style>

