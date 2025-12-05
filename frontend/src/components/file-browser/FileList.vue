<template>
  <div class="file-list">
    <!-- 列表视图 -->
    <v-card v-if="viewMode === 'list'">
      <v-data-table
        :headers="headers"
        :items="files"
        :loading="loading"
        item-value="fileid"
        v-model="internalSelected"
        show-select
        class="file-table"
      >
        <template v-slot:item.name="{ item }">
          <div class="d-flex align-center">
            <v-icon
              :icon="item.type === 'dir' ? 'mdi-folder' : getFileIcon(item.extension)"
              :color="item.type === 'dir' ? 'warning' : 'primary'"
              class="me-2"
            />
            <span
              class="file-name"
              :class="{ 'text-primary': item.type === 'dir' }"
              @click="handleItemClick(item)"
            >
              {{ item.name }}
            </span>
            <v-chip
              v-if="item.is_media"
              size="x-small"
              color="success"
              class="ms-2"
            >
              媒体
            </v-chip>
          </div>
        </template>
        
        <template v-slot:item.size="{ item }">
          <span v-if="item.type === 'file'">{{ formatBytes(item.size) }}</span>
          <span v-else class="text-medium-emphasis">-</span>
        </template>
        
        <template v-slot:item.modify_time="{ item }">
          {{ formatTime(item.modify_time) }}
        </template>
        
        <template v-slot:item.actions="{ item }">
          <v-menu>
            <template v-slot:activator="{ props }">
              <v-btn
                v-bind="props"
                icon="mdi-dots-vertical"
                variant="text"
                size="small"
              />
            </template>
            <v-list>
              <v-list-item
                v-if="item.type === 'file' && item.is_media"
                @click="$emit('action', 'recognize', item)"
              >
                <v-list-item-title>
                  <v-icon class="me-2">mdi-text-recognition</v-icon>
                  识别
                </v-list-item-title>
              </v-list-item>
              
              <v-list-item
                v-if="item.type === 'file' && item.is_media"
                @click="$emit('action', 'scrape', item)"
              >
                <v-list-item-title>
                  <v-icon class="me-2">mdi-auto-fix</v-icon>
                  刮削
                </v-list-item-title>
              </v-list-item>
              
              <v-list-item @click="$emit('action', 'rename', item)">
                <v-list-item-title>
                  <v-icon class="me-2">mdi-rename</v-icon>
                  重命名
                </v-list-item-title>
              </v-list-item>
              
              <v-list-item
                v-if="item.type === 'file'"
                @click="$emit('action', 'transfer', item)"
              >
                <v-list-item-title>
                  <v-icon class="me-2">mdi-folder-arrow-right</v-icon>
                  整理
                </v-list-item-title>
              </v-list-item>
              
              <v-list-item
                v-if="item.type === 'file'"
                @click="$emit('action', 'download', item)"
              >
                <v-list-item-title>
                  <v-icon class="me-2">mdi-download</v-icon>
                  下载
                </v-list-item-title>
              </v-list-item>
              
              <v-divider />
              
              <v-list-item
                @click="$emit('action', 'delete', item)"
                class="text-error"
              >
                <v-list-item-title>
                  <v-icon class="me-2">mdi-delete</v-icon>
                  删除
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
        </template>
      </v-data-table>
    </v-card>
    
    <!-- 网格视图 -->
    <v-card v-else>
      <v-container v-if="loading" class="text-center py-8">
        <v-progress-circular indeterminate color="primary" />
      </v-container>
      
      <v-container v-else-if="files.length === 0" class="text-center py-8">
        <v-icon size="64" color="grey-lighten-1">mdi-folder-open-outline</v-icon>
        <div class="text-h6 mt-4 text-medium-emphasis">目录为空</div>
      </v-container>
      
      <v-row v-else class="pa-4">
        <v-col
          v-for="item in files"
          :key="item.fileid"
          cols="12"
          sm="6"
          md="4"
          lg="3"
        >
          <v-card
            :class="{ 'selected': internalSelected.includes(item.fileid) }"
            @click="handleItemClick(item)"
            @contextmenu.prevent="handleContextMenu($event, item)"
            hover
          >
            <v-card-text class="text-center">
              <v-icon
                :icon="item.type === 'dir' ? 'mdi-folder' : getFileIcon(item.extension)"
                :color="item.type === 'dir' ? 'warning' : 'primary'"
                size="64"
                class="mb-2"
              />
              <div class="text-body-2 font-weight-medium text-truncate">
                {{ item.name }}
              </div>
              <div v-if="item.type === 'file'" class="text-caption text-medium-emphasis mt-1">
                {{ formatBytes(item.size) }}
              </div>
              <v-chip
                v-if="item.is_media"
                size="x-small"
                color="success"
                class="mt-1"
              >
                媒体
              </v-chip>
            </v-card-text>
            
            <v-card-actions v-if="internalSelected.includes(item.fileid)">
              <v-spacer />
              <v-btn
                icon="mdi-close"
                size="small"
                @click.stop="toggleSelection(item.fileid)"
              />
            </v-card-actions>
          </v-card>
        </v-col>
      </v-row>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface Props {
  files: any[]
  loading: boolean
  viewMode: 'list' | 'grid'
  selectedFiles: string[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  select: [fileIds: string[]]
  navigate: [file: any]
  action: [action: string, file: any]
}>()

const internalSelected = ref<string[]>([])

// 监听外部选择变化
watch(() => props.selectedFiles, (newVal) => {
  internalSelected.value = [...newVal]
}, { immediate: true })

// 监听内部选择变化
watch(internalSelected, (newVal) => {
  emit('select', newVal)
})

const headers = [
  { title: '名称', key: 'name', sortable: true },
  { title: '大小', key: 'size', sortable: true, width: '120px' },
  { title: '修改时间', key: 'modify_time', sortable: true, width: '180px' },
  { title: '操作', key: 'actions', sortable: false, width: '80px', align: 'end' as const }
] as const

// 获取文件图标（参考MoviePilot的图标映射）
const getFileIcon = (extension: string | null): string => {
  if (!extension) return 'mdi-file-outline'
  
  const ext = extension.toLowerCase()
  
  // 压缩包
  if (['.zip', '.rar', '.bak', '.tar', '.gz', '.bz2', '.7z'].includes(ext)) {
    return 'mdi-folder-zip-outline'
  }
  
  // 开发文件
  if (['.htm', '.html'].includes(ext)) return 'mdi-language-html5'
  if (['.vue'].includes(ext)) return 'mdi-vuejs'
  if (['.js'].includes(ext)) return 'mdi-nodejs'
  if (['.ts'].includes(ext)) return 'mdi-language-typescript'
  if (['.json'].includes(ext)) return 'mdi-file-document-outline'
  if (['.css', '.scss', '.less'].includes(ext)) return 'mdi-language-css3'
  if (['.php'].includes(ext)) return 'mdi-language-php'
  if (['.py'].includes(ext)) return 'mdi-language-python'
  if (['.java'].includes(ext)) return 'mdi-language-java'
  if (['.go'].includes(ext)) return 'mdi-language-go'
  if (['.c', '.h'].includes(ext)) return 'mdi-language-c'
  if (['.cpp'].includes(ext)) return 'mdi-language-cpp'
  if (['.cs'].includes(ext)) return 'mdi-language-csharp'
  if (['.sql'].includes(ext)) return 'mdi-database'
  if (['.sh', '.bat'].includes(ext)) return 'mdi-language-bash'
  if (['.ps1'].includes(ext)) return 'mdi-language-powershell'
  
  // Markdown
  if (['.md', '.markdown'].includes(ext)) return 'mdi-language-markdown-outline'
  
  // 图片
  if (['.png'].includes(ext)) return 'mdi-file-png-box'
  if (['.jpg', '.jpeg'].includes(ext)) return 'mdi-file-jpg-box'
  if (['.gif'].includes(ext)) return 'mdi-file-gif-box'
  if (['.bmp', '.webp', '.ico', '.svg'].includes(ext)) return 'mdi-file-image-box'
  
  // 视频
  if (['.mp4', '.mkv', '.avi', '.wmv', '.mov', '.flv', '.rmvb'].includes(ext)) {
    return 'mdi-filmstrip'
  }
  
  // 文档
  if (['.txt', '.log'].includes(ext)) return 'mdi-file-document-outline'
  if (['.env', '.yml', '.yaml', '.conf'].includes(ext)) return 'mdi-file-cog-outline'
  if (['.csv'].includes(ext)) return 'mdi-file-delimited'
  
  // Office
  if (['.xls', '.xlsx'].includes(ext)) return 'mdi-file-excel'
  if (['.doc', '.docx'].includes(ext)) return 'mdi-file-word'
  if (['.ppt', '.pptx'].includes(ext)) return 'mdi-file-powerpoint'
  if (['.pdf'].includes(ext)) return 'mdi-file-pdf'
  
  // 音频
  if (['.mp2', '.mp3', '.m4a', '.wma', '.aac', '.ogg', '.flac', '.wav'].includes(ext)) {
    return 'mdi-music'
  }
  
  // 字体
  if (['.ttf', '.otf', '.woff', '.woff2', '.eot'].includes(ext)) {
    return 'mdi-format-font'
  }
  
  // 字幕
  if (['.srt', '.ass', '.sub'].includes(ext)) return 'mdi-subtitles-outline'
  
  return 'mdi-file-outline'
}

// 格式化字节
const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// 格式化时间
const formatTime = (timestamp: number): string => {
  if (!timestamp) return '-'
  const date = new Date(timestamp * 1000)
  return date.toLocaleString('zh-CN')
}

// 点击项目
const handleItemClick = (item: any) => {
  if (item.type === 'dir') {
    emit('navigate', item)
  } else {
    toggleSelection(item.fileid)
  }
}

// 切换选择
const toggleSelection = (fileId: string) => {
  const index = internalSelected.value.indexOf(fileId)
  if (index > -1) {
    internalSelected.value.splice(index, 1)
  } else {
    internalSelected.value.push(fileId)
  }
}

// 右键菜单
const handleContextMenu = (event: MouseEvent, item: any) => {
  // 可以在这里实现右键菜单
  event.preventDefault()
}
</script>

<style scoped>
.file-list {
  width: 100%;
}

.file-table {
  width: 100%;
}

.file-name {
  cursor: pointer;
}

.file-name:hover {
  text-decoration: underline;
}

.selected {
  border: 2px solid rgb(var(--v-theme-primary));
}
</style>

