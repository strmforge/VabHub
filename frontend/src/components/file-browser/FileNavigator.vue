<template>
  <v-card class="file-navigator" :height="`${availableHeight}px`">
    <v-card-title class="pa-2">
      <v-icon class="me-2">mdi-folder-tree</v-icon>
      目录树
    </v-card-title>
    
    <v-divider />
    
    <div class="tree-container">
      <!-- 根目录项 -->
      <div
        class="tree-item root-item"
        :class="{ 'active': currentPath === '/' }"
        @click="handleRootClick"
      >
        <div class="folder-content">
          <v-icon class="me-2" color="primary">mdi-home</v-icon>
          <span>根目录</span>
        </div>
      </div>
      
      <!-- 加载中状态 -->
      <div v-if="loading['/']" class="tree-loading">
        <v-progress-circular indeterminate size="24" color="primary" class="ma-2" />
        <span class="text-caption">加载目录结构...</span>
      </div>
      
      <!-- 目录树结构 -->
      <template v-else>
        <!-- 一级目录 -->
        <div v-for="directory in rootDirectories" :key="directory.path" class="tree-item-container">
          <!-- 目录项 -->
          <div
            class="tree-item"
            :class="{ 'active': currentPath === directory.path }"
          >
            <div class="folder-toggle" @click.stop="toggleFolder(directory.path)">
              <v-progress-circular
                v-if="loading[directory.path]"
                indeterminate
                size="14"
                width="2"
                color="primary"
              />
              <v-icon
                v-else
                size="small"
                :icon="isFolderExpanded(directory.path) ? 'mdi-chevron-down' : 'mdi-chevron-right'"
              />
            </div>
            <div class="folder-content" @click.stop="handleFolderClick(directory)">
              <v-icon
                size="small"
                :icon="isFolderExpanded(directory.path) ? 'mdi-folder-open' : 'mdi-folder'"
                :color="currentPath === directory.path ? 'primary' : 'warning'"
                class="me-1"
              />
              <span class="folder-name">{{ directory.name }}</span>
            </div>
          </div>
          
          <!-- 子目录容器 -->
          <div v-if="isFolderExpanded(directory.path)">
            <!-- 加载中状态 -->
            <div v-if="loading[directory.path]" class="tree-loading pl-8">
              <v-progress-circular indeterminate size="14" color="primary" class="ma-2" />
              <span class="text-caption">加载中...</span>
            </div>
            
            <!-- 子目录列表 -->
            <div v-else>
              <div
                v-for="item in getChildDirectories(directory.path)"
                :key="item.path"
                class="tree-item"
                :class="{ 'active': currentPath === item.path }"
                :style="{ paddingLeft: 16 + getIndentLevel(item.path, directory.path) * 12 + 'px' }"
              >
                <!-- 展开/折叠按钮 -->
                <div class="folder-toggle" @click.stop="toggleFolder(item.path)">
                  <v-progress-circular
                    v-if="loading[item.path]"
                    indeterminate
                    size="14"
                    width="2"
                    color="primary"
                  />
                  <v-icon
                    v-else
                    size="small"
                    :icon="isFolderExpanded(item.path) ? 'mdi-chevron-down' : 'mdi-chevron-right'"
                  />
                </div>
                
                <!-- 文件夹图标和名称 -->
                <div class="folder-content" @click.stop="handleFolderClick(item)">
                  <v-icon
                    size="small"
                    :icon="isFolderExpanded(item.path) ? 'mdi-folder-open' : 'mdi-folder'"
                    :color="currentPath === item.path ? 'primary' : 'warning'"
                    class="me-1"
                  />
                  <span class="folder-name">{{ item.name }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import api from '@/services/api'

interface Props {
  storage: string
  currentPath: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  navigate: [file: any]
}>()

// 计算可用高度
const availableHeight = computed(() => {
  const viewportHeight = window.innerHeight || document.documentElement.clientHeight
  const navbarHeight = 72
  const toolbarHeight = 64
  const footerHeight = 16
  return Math.max(viewportHeight - navbarHeight - toolbarHeight - footerHeight - 200, 300)
})

// 树形节点缓存
const treeCache = ref<{ [key: string]: any[] }>({})

// 展开的文件夹
const expandedFolders = ref<string[]>([])

// 是否正在加载
const loading = ref<{ [key: string]: boolean }>({})

// 根目录列表
const rootDirectories = computed(() => {
  return treeCache.value['/'] || []
})

// 点击根目录
const handleRootClick = () => {
  emit('navigate', {
    storage: props.storage,
    type: 'dir',
    name: '/',
    path: '/'
  })
}

// 点击目录
const handleFolderClick = (item: any) => {
  emit('navigate', item)
}

// 切换文件夹展开状态
const toggleFolder = async (path: string) => {
  const index = expandedFolders.value.indexOf(path)
  if (index >= 0) {
    expandedFolders.value.splice(index, 1)
  } else {
    expandedFolders.value.push(path)
    if (!treeCache.value[path]) {
      await loadSubdirectories(path)
    }
  }
}

// 判断文件夹是否展开
const isFolderExpanded = (path: string): boolean => {
  return expandedFolders.value.includes(path)
}

// 加载子目录
const loadSubdirectories = async (path: string) => {
  if (loading.value[path] || treeCache.value[path]) return
  
  loading.value[path] = true
  
  try {
    const response = await api.get('/file-browser/list', {
      params: {
        storage: props.storage,
        path: path,
        recursion: false,
        sort: 'name'
      }
    })
    
    const items = response.data.items || []
    const dirs = items.filter((item: any) => item.type === 'dir')
    treeCache.value[path] = dirs
  } catch (error) {
    console.error('加载目录失败:', path, error)
  } finally {
    loading.value[path] = false
  }
}

// 获取子目录
const getChildDirectories = (parentPath: string): any[] => {
  const allDirs: any[] = []
  
  const addSubdirectories = (path: string, level: number) => {
    if (treeCache.value[path]) {
      treeCache.value[path].forEach((dir: any) => {
        if (isChildOrDescendant(dir.path, parentPath)) {
          allDirs.push(dir)
          if (isFolderExpanded(dir.path)) {
            addSubdirectories(dir.path, level + 1)
          }
        }
      })
    }
  }
  
  addSubdirectories(parentPath, 0)
  return allDirs
}

// 检查路径是否为指定目录的子目录
const isChildOrDescendant = (path: string, ancestorPath: string): boolean => {
  if (!path || !ancestorPath) return false
  if (ancestorPath === '/') return true
  
  const normalizedPath = path.endsWith('/') ? path : path + '/'
  const normalizedAncestorPath = ancestorPath.endsWith('/') ? ancestorPath : ancestorPath + '/'
  
  return normalizedPath.startsWith(normalizedAncestorPath) && normalizedPath !== normalizedAncestorPath
}

// 计算目录相对于其祖先的缩进级别
const getIndentLevel = (path: string, ancestorPath: string): number => {
  if (!path || !ancestorPath) return 0
  if (ancestorPath === '/') {
    return path.split('/').filter(p => p).length - 1
  }
  
  const pathParts = path.split('/').filter(p => p).length
  const ancestorParts = ancestorPath.split('/').filter(p => p).length
  
  return pathParts - ancestorParts
}

// 初始加载根目录
const loadRootDirectories = async () => {
  await loadSubdirectories('/')
}

// 监听当前路径变化，自动展开当前路径
watch(
  () => props.currentPath,
  async (newPath) => {
    if (!newPath) return
    
    if (newPath !== '/') {
      const parts = newPath.split('/').filter(p => p)
      let currentPath = ''
      
      for (const part of parts) {
        currentPath += '/' + part
        
        if (!expandedFolders.value.includes(currentPath)) {
          expandedFolders.value.push(currentPath)
          if (!treeCache.value[currentPath]) {
            await loadSubdirectories(currentPath)
          }
        }
        
        const parentPath = currentPath.substring(0, currentPath.lastIndexOf('/')) || '/'
        if (!treeCache.value[parentPath]) {
          await loadSubdirectories(parentPath)
        }
      }
    }
  },
  { immediate: true }
)

// 监听存储变化，清空缓存
watch(
  () => props.storage,
  () => {
    treeCache.value = {}
    expandedFolders.value = []
    loadRootDirectories()
  }
)

// 初始化
onMounted(() => {
  loadRootDirectories()
})
</script>

<style scoped>
.file-navigator {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  width: 240px;
  border-end-start-radius: 12px;
}

.tree-container {
  overflow-y: auto;
  flex: 1;
  padding: 8px;
}

.tree-item-container {
  width: 100%;
}

.tree-item {
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: background-color 0.2s ease;
  border-radius: 4px;
  margin-bottom: 2px;
}

.tree-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.tree-item.active {
  background-color: rgba(var(--v-theme-primary), 0.08);
}

.root-item {
  font-weight: 500;
}

.folder-toggle {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  margin-right: 4px;
  padding: 6px 12px 6px 0;
}

.folder-content {
  display: flex;
  flex: 1;
  align-items: center;
  padding: 6px 8px 6px 16px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.folder-name {
  display: inline-block;
  overflow: hidden;
  max-width: 150px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-loading {
  display: flex;
  align-items: center;
  padding: 4px 16px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.pl-8 {
  padding-left: 20px !important;
}
</style>

