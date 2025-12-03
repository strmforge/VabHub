<template>
  <v-card variant="tonal" class="file-operation-card">
    <v-card-item>
      <v-text-field
        v-model="config.name"
        variant="underlined"
        label="操作名称"
        class="me-20 text-high-emphasis font-weight-bold"
        density="compact"
      />
      <span class="absolute top-3 right-12">
        <v-btn
          icon="mdi-close"
          variant="text"
          size="small"
          @click="handleClose"
        />
      </span>
    </v-card-item>

    <v-card-text v-if="!isCollapsed">
      <v-form>
        <!-- 源存储和目标存储选择 -->
        <v-row>
          <v-col cols="6">
            <v-autocomplete
              v-model="config.source_storage"
              :items="storageOptions"
              variant="underlined"
              label="源存储"
              density="compact"
              @update:model-value="handleStorageChange"
            />
          </v-col>
          <v-col cols="6">
            <v-autocomplete
              v-model="config.target_storage"
              :items="storageOptions"
              variant="underlined"
              label="目标存储"
              density="compact"
              @update:model-value="handleStorageChange"
            />
          </v-col>
        </v-row>

        <!-- 源路径和目标路径 -->
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="config.source_path"
              variant="underlined"
              label="源路径"
              density="compact"
              prepend-inner-icon="mdi-folder"
            />
          </v-col>
          <v-col cols="12">
            <v-text-field
              v-model="config.target_path"
              variant="underlined"
              label="目标路径"
              density="compact"
              prepend-inner-icon="mdi-folder"
            />
          </v-col>
        </v-row>

        <!-- 文件操作模式（根据源存储和目标存储动态显示） -->
        <v-row v-if="availableModes.length > 0">
          <v-col cols="12">
            <v-select
              v-model="config.operation_mode"
              :items="availableModes"
              variant="underlined"
              label="文件操作模式"
              density="compact"
            />
          </v-col>
        </v-row>

        <!-- 覆盖模式 -->
        <v-row>
          <v-col cols="12">
            <v-select
              v-model="config.overwrite_mode"
              :items="overwriteModeItems"
              variant="underlined"
              label="覆盖模式"
              density="compact"
            />
          </v-col>
        </v-row>

        <!-- 其他选项 -->
        <v-row>
          <v-col cols="6">
            <v-switch
              v-model="config.delete_source"
              label="删除源文件"
              color="primary"
              hide-details
              :disabled="config.operation_mode !== 'move'"
            />
          </v-col>
          <v-col cols="6">
            <v-switch
              v-model="config.keep_seeding"
              label="保留做种"
              color="primary"
              hide-details
              :disabled="config.operation_mode === 'move'"
            />
          </v-col>
        </v-row>

        <!-- STRM配置（仅当目标存储为网盘时显示） -->
        <v-divider v-if="isCloudTarget" class="my-3 bg-primary" />
        
        <v-row v-if="isCloudTarget">
          <v-col cols="12">
            <v-switch
              v-model="strmConfig.enabled"
              label="启用STRM功能"
              color="primary"
              hide-details
              class="mb-2"
            />
          </v-col>
        </v-row>

        <!-- STRM详细配置（仅当启用STRM且目标存储为网盘时显示） -->
        <template v-if="isCloudTarget && strmConfig.enabled">
          <v-row>
            <v-col cols="12">
              <v-combobox
                v-model="strmConfig.media_library_path"
                :items="mediaLibraryPathOptions"
                variant="underlined"
                label="本地STRM文件存放的媒体库地址 *"
                density="compact"
                prepend-inner-icon="mdi-folder"
                hint="本地STRM文件存放的媒体库地址，可通过输入或点击选择按钮选择路径"
                persistent-hint
                clearable
                required
              >
                <template #append>
                  <v-btn
                    icon="mdi-folder-open"
                    variant="text"
                    size="small"
                    @click="browseMediaLibraryPath"
                    title="浏览文件夹（输入路径）"
                  />
                </template>
              </v-combobox>
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="6">
              <v-switch
                v-model="strmConfig.generate_nfo"
                label="生成NFO文件"
                color="primary"
                hide-details
              />
            </v-col>
            <v-col cols="6">
              <v-switch
                v-model="strmConfig.generate_subtitle_files"
                label="生成字幕文件"
                color="primary"
                hide-details
              />
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="6">
              <v-switch
                v-model="strmConfig.scrape_cloud_files"
                label="对网盘文件进行刮削"
                color="primary"
                hide-details
              />
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="6">
              <v-switch
                v-model="strmConfig.scrape_local_strm"
                label="对本地STRM文件进行刮削"
                color="primary"
                hide-details
              />
            </v-col>
          </v-row>
        </template>
      </v-form>
    </v-card-text>

    <v-card-actions class="text-center py-0">
      <v-spacer />
      <v-btn
        :icon="isCollapsed ? 'mdi-chevron-down' : 'mdi-chevron-up'"
        @click.stop="isCollapsed = !isCollapsed"
      />
      <v-spacer />
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import api from '@/services/api'

interface Props {
  config: any
  storages?: any[]
}

const props = defineProps<Props>()
const emit = defineEmits(['close', 'changed', 'update:config'])

const isCollapsed = ref(true)

// 存储选项
const storageOptions = computed(() => {
  const options = [
    { title: '本地存储', value: 'local' }
  ]
  
  // 添加云存储选项
  if (props.storages && props.storages.length > 0) {
    props.storages.forEach(storage => {
      if (storage.enabled && storage.provider) {
        options.push({
          title: storage.name || storage.provider,
          value: storage.provider
        })
      }
    })
  }
  
  return options
})

// 可用的文件操作模式
const availableModes = computed(() => {
  const source = props.config.source_storage || 'local'
  const target = props.config.target_storage || 'local'
  
  // 本地到本地：支持所有模式
  if (source === 'local' && target === 'local') {
    return [
      { title: '复制', value: 'copy' },
      { title: '移动', value: 'move' },
      { title: '硬链接', value: 'link' },
      { title: '软链接', value: 'softlink' }
    ]
  }
  // 其他情况（本地到云存储、云存储到本地、云存储到云存储）：只支持复制和移动
  else {
    return [
      { title: '复制', value: 'copy' },
      { title: '移动', value: 'move' }
    ]
  }
})

// 覆盖模式选项
const overwriteModeItems = [
  { title: '从不覆盖', value: 'never' },
  { title: '总是覆盖', value: 'always' },
  { title: '按文件大小', value: 'size' },
  { title: '保留最新', value: 'latest' }
]

// 判断目标存储是否为网盘
const isCloudTarget = computed(() => {
  const target = props.config.target_storage || 'local'
  return target !== 'local'
})

// STRM配置
const strmConfig = ref({
  enabled: false,
  media_library_path: '/media_library',
  generate_nfo: true,
  generate_subtitle_files: true,
  scrape_cloud_files: false,
  scrape_local_strm: true
})

// 媒体库路径选项
const mediaLibraryPathOptions = ref<string[]>([])

// 处理存储变化
const handleStorageChange = () => {
  // 如果目标存储不是网盘，禁用STRM
  if (!isCloudTarget.value) {
    strmConfig.value.enabled = false
  }
  
  // 重新计算可用的操作模式
  if (availableModes.value.length > 0) {
    // 如果当前操作模式不在可用模式中，设置为第一个可用模式
    const currentMode = props.config.operation_mode
    if (!availableModes.value.find(m => m.value === currentMode)) {
      props.config.operation_mode = availableModes.value[0].value
    }
  }
  
  emit('changed')
}

// 浏览媒体库路径
const browseMediaLibraryPath = () => {
  const currentPath = strmConfig.value.media_library_path || '/media_library'
  const newPath = prompt('请输入或选择本地STRM文件存放的媒体库地址:\n\n提示：可以直接输入路径，或从常用路径中选择', currentPath)
  if (newPath !== null && newPath.trim()) {
    const trimmedPath = newPath.trim()
    strmConfig.value.media_library_path = trimmedPath
    // 如果路径不在选项中，添加到选项列表
    if (!mediaLibraryPathOptions.value.includes(trimmedPath)) {
      mediaLibraryPathOptions.value.push(trimmedPath)
    }
  }
}

// 处理关闭
const handleClose = () => {
  emit('close')
}

// 加载常用路径选项
const loadMediaLibraryPathOptions = async () => {
  try {
    // 从设置中获取默认保存路径
    const settingsResponse = await api.get('/settings')
    if (settingsResponse.data?.default_save_path) {
      mediaLibraryPathOptions.value.push(settingsResponse.data.default_save_path)
    }
    
    // 从STRM配置中获取路径
    try {
      const strmResponse = await api.get('/strm/config')
      if (strmResponse.data?.media_library_path) {
        const path = strmResponse.data.media_library_path
        if (!mediaLibraryPathOptions.value.includes(path)) {
          mediaLibraryPathOptions.value.push(path)
        }
        // 如果当前配置中没有路径，使用STRM配置中的路径
        if (!strmConfig.value.media_library_path || strmConfig.value.media_library_path === '/media_library') {
          strmConfig.value.media_library_path = path
        }
      }
    } catch (error) {
      console.warn('加载STRM配置失败:', error)
    }
    
    // 添加一些常用路径
    const commonPaths = [
      '/media_library',
      '/mnt/media_library',
      '/volume1/media_library',
      'D:/media_library',
      'E:/media_library'
    ]
    commonPaths.forEach(path => {
      if (!mediaLibraryPathOptions.value.includes(path)) {
        mediaLibraryPathOptions.value.push(path)
      }
    })
  } catch (error) {
    console.error('加载媒体库路径选项失败:', error)
  }
}

// 监听STRM配置变化，同步到主配置
watch(() => strmConfig.value, (newVal) => {
  if (props.config) {
    props.config.strm_config = { ...newVal }
    emit('changed')
  }
}, { deep: true })

// 初始化时加载STRM配置
onMounted(() => {
  loadMediaLibraryPathOptions()
  
  // 如果配置中已有STRM配置，加载它
  if (props.config?.strm_config) {
    strmConfig.value = { ...strmConfig.value, ...props.config.strm_config }
  }
})
</script>

<style scoped>
.file-operation-card {
  transition: var(--vabhub-transition);
}

.file-operation-card:hover {
  box-shadow: var(--vabhub-shadow-md);
}
</style>

