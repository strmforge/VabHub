<template>
  <div>
    <v-menu
      v-model="menuVisible"
      :close-on-content-click="false"
      location="bottom"
      max-width="400"
    >
      <template v-slot:activator="{ props: menuProps }">
        <v-text-field
          :model-value="modelValue"
          @update:model-value="$emit('update:modelValue', $event)"
          :label="label"
          :hint="hint"
          :persistent-hint="persistentHint"
          :rules="rules"
          :required="required"
          :disabled="disabled"
          variant="outlined"
          density="compact"
          :prepend-inner-icon="prependIcon || 'mdi-folder'"
          readonly
          v-bind="menuProps"
          class="cursor-pointer"
        >
          <template v-slot:append-inner>
            <v-btn
              icon="mdi-folder-open"
              variant="text"
              size="small"
              @click.stop="menuVisible = !menuVisible"
              :disabled="disabled"
            />
          </template>
        </v-text-field>
      </template>

      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon icon="mdi-folder" class="me-2" />
          <span>选择路径</span>
          <v-spacer />
          <v-btn
            icon="mdi-close"
            variant="text"
            size="small"
            @click="menuVisible = false"
          />
        </v-card-title>

        <v-card-text>
          <!-- 路径导航 -->
          <v-breadcrumbs
            :items="pathBreadcrumbs"
            density="compact"
            class="pa-2 mb-2"
          >
            <template v-slot:divider>
              <v-icon size="small">mdi-chevron-right</v-icon>
            </template>
            <template v-slot:item="{ item }">
              <v-btn
                variant="text"
                size="small"
                @click="navigateToPath(item.path)"
              >
                {{ item.title }}
              </v-btn>
            </template>
          </v-breadcrumbs>

          <!-- 目录列表 -->
          <v-list
            v-if="loading"
            class="pa-0"
          >
            <v-list-item>
              <v-progress-circular
                indeterminate
                color="primary"
                size="24"
                class="mx-auto"
              />
            </v-list-item>
          </v-list>

          <v-list
            v-else
            density="compact"
            class="pa-0"
            style="max-height: 300px; overflow-y: auto"
          >
            <v-list-item
              v-for="item in directoryItems"
              :key="item.path"
              :prepend-icon="item.type === 'dir' ? 'mdi-folder' : 'mdi-file'"
              :title="item.name"
              :subtitle="item.type === 'file' ? formatSize(item.size) : ''"
              @click="handleItemClick(item)"
              class="cursor-pointer"
            >
              <template v-slot:append v-if="item.type === 'dir'">
                <v-icon icon="mdi-chevron-right" size="small" />
              </template>
            </v-list-item>

            <v-list-item v-if="directoryItems.length === 0">
              <v-list-item-title class="text-center text-medium-emphasis">
                目录为空
              </v-list-item-title>
            </v-list-item>
          </v-list>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn
            variant="text"
            @click="handleConfirm"
            color="primary"
            :disabled="!modelValue"
          >
            确认
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-menu>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import api from '@/services/api'

interface Props {
  modelValue: string
  label?: string
  hint?: string
  persistentHint?: boolean
  rules?: any[]
  required?: boolean
  disabled?: boolean
  prependIcon?: string
  root?: string
  storage?: string
}

const props = withDefaults(defineProps<Props>(), {
  label: '路径',
  hint: '点击选择或手动输入路径',
  persistentHint: true,
  rules: () => [],
  required: false,
  disabled: false,
  prependIcon: 'mdi-folder',
  root: '/',
  storage: 'local'
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const menuVisible = ref(false)
const loading = ref(false)
const directoryItems = ref<Array<{
  name: string
  path: string
  type: string
  size?: number
}>>([])
const currentPath = ref(props.modelValue || props.root)

// 路径面包屑导航
const pathBreadcrumbs = computed(() => {
  const paths = currentPath.value.split('/').filter(p => p)
  const items = [
    { title: '根目录', path: props.root }
  ]
  
  let current = props.root
  paths.forEach((path, index) => {
    current = current === '/' ? `/${path}` : `${current}/${path}`
    items.push({
      title: path,
      path: current
    })
  })
  
  return items
})

// 加载目录列表
const loadDirectory = async (path: string) => {
  try {
    loading.value = true
    currentPath.value = path
    
    const response = await api.post('/storage/list', {
      path: path,
      storage: props.storage,
      recursive: false
    })
    
    if (response.data.success) {
      // 只显示目录
      directoryItems.value = response.data.data.filter((item: any) => item.type === 'dir')
    } else {
      directoryItems.value = []
      console.error('加载目录失败:', response.data.message)
    }
  } catch (error) {
    console.error('加载目录异常:', error)
    directoryItems.value = []
  } finally {
    loading.value = false
  }
}

// 处理项目点击
const handleItemClick = (item: any) => {
  if (item.type === 'dir') {
    loadDirectory(item.path)
  }
}

// 导航到路径
const navigateToPath = (path: string) => {
  loadDirectory(path)
}

// 确认选择
const handleConfirm = () => {
  emit('update:modelValue', currentPath.value)
  menuVisible.value = false
}

// 格式化文件大小
const formatSize = (bytes?: number): string => {
  if (!bytes) return ''
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  return `${size.toFixed(2)} ${units[unitIndex]}`
}

// 监听菜单显示状态
watch(menuVisible, (visible) => {
  if (visible) {
    // 菜单打开时，加载当前路径的目录
    const pathToLoad = props.modelValue || props.root
    loadDirectory(pathToLoad)
  }
})

// 监听modelValue变化
watch(() => props.modelValue, (newVal) => {
  if (newVal && menuVisible.value) {
    loadDirectory(newVal)
  }
})
</script>

<style scoped>
.cursor-pointer {
  cursor: pointer;
}
</style>

