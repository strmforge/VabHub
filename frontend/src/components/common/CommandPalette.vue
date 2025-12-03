<template>
  <v-dialog
    v-model="dialogOpen"
    max-width="600"
    :scrim="true"
    transition="dialog-top-transition"
  >
    <v-card class="command-palette">
      <!-- 搜索输入框 -->
      <v-card-text class="pa-0">
        <v-text-field
          ref="searchInput"
          v-model="searchQuery"
          placeholder="搜索小说、漫画、音乐..."
          prepend-inner-icon="mdi-magnify"
          variant="solo"
          hide-details
          autofocus
          @keydown.esc="close"
          @keydown.enter="selectFirst"
          @keydown.down.prevent="navigateDown"
          @keydown.up.prevent="navigateUp"
        >
          <template v-slot:append-inner>
            <v-chip size="x-small" variant="outlined" class="text-caption">
              ESC 关闭
            </v-chip>
          </template>
        </v-text-field>
      </v-card-text>

      <v-divider />

      <!-- 搜索结果 -->
      <v-card-text class="pa-0" style="max-height: 400px; overflow-y: auto;">
        <!-- 加载状态 -->
        <div v-if="loading" class="text-center py-8">
          <v-progress-circular indeterminate color="primary" size="32" />
          <div class="mt-2 text-caption text-medium-emphasis">搜索中...</div>
        </div>

        <!-- 搜索结果 -->
        <template v-else-if="groupedResults.length > 0">
          <div v-for="group in groupedResults" :key="group.type" class="mb-2">
            <div class="px-4 py-2 text-caption text-medium-emphasis bg-grey-lighten-4">
              {{ getMediaLabel(group.type) }}
            </div>
            <v-list density="compact">
              <v-list-item
                v-for="(item, index) in group.items"
                :key="item.id"
                :class="{ 'bg-primary-lighten-5': isSelected(group.type, index) }"
                @click="selectItem(item)"
                @mouseenter="setSelected(group.type, index)"
              >
                <template v-slot:prepend>
                  <v-avatar size="40" rounded class="mr-3">
                    <v-img v-if="item.cover_url" :src="item.cover_url" cover />
                    <v-icon v-else :color="getMediaColor(item.media_type)">
                      {{ getMediaIcon(item.media_type) }}
                    </v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title>{{ item.title }}</v-list-item-title>
                <v-list-item-subtitle v-if="item.sub_title">
                  {{ item.sub_title }}
                </v-list-item-subtitle>
                <template v-slot:append>
                  <v-icon size="small" color="grey">mdi-chevron-right</v-icon>
                </template>
              </v-list-item>
            </v-list>
          </div>
        </template>

        <!-- 空状态 -->
        <div v-else-if="searchQuery && !loading" class="text-center py-8">
          <v-icon size="48" color="grey-lighten-1" class="mb-2">mdi-magnify-close</v-icon>
          <div class="text-body-2 text-medium-emphasis">
            未找到 "{{ searchQuery }}" 相关结果
          </div>
        </div>

        <!-- 初始提示 -->
        <div v-else class="text-center py-8">
          <v-icon size="48" color="grey-lighten-1" class="mb-2">mdi-magnify</v-icon>
          <div class="text-body-2 text-medium-emphasis">
            输入关键词搜索小说、漫画、音乐
          </div>
          <div class="text-caption text-disabled mt-2">
            Ctrl+K 打开 · ESC 关闭 · ↑↓ 导航 · Enter 选择
          </div>
        </div>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { globalSearchApi } from '@/services/api'
import type { GlobalSearchItem } from '@/types/globalSearch'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const router = useRouter()

// 状态
const dialogOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})
const searchQuery = ref('')
const loading = ref(false)
const results = ref<GlobalSearchItem[]>([])
const selectedGroup = ref<string | null>(null)
const selectedIndex = ref(0)
const searchInput = ref<HTMLInputElement | null>(null)

// 防抖搜索
let searchTimeout: ReturnType<typeof setTimeout> | null = null

// 分组结果
const groupedResults = computed(() => {
  const groups: { type: string; items: GlobalSearchItem[] }[] = []
  const typeMap = new Map<string, GlobalSearchItem[]>()
  
  for (const item of results.value) {
    if (!typeMap.has(item.media_type)) {
      typeMap.set(item.media_type, [])
    }
    typeMap.get(item.media_type)!.push(item)
  }
  
  for (const [type, items] of typeMap) {
    groups.push({ type, items })
  }
  
  return groups
})

// 搜索
const search = async () => {
  if (!searchQuery.value.trim()) {
    results.value = []
    return
  }
  
  try {
    loading.value = true
    const data = await globalSearchApi.search(searchQuery.value.trim(), 5)
    results.value = data.items
    
    // 重置选择
    if (groupedResults.value.length > 0) {
      selectedGroup.value = groupedResults.value[0].type
      selectedIndex.value = 0
    } else {
      selectedGroup.value = null
      selectedIndex.value = 0
    }
  } catch (err) {
    console.error('搜索失败:', err)
    results.value = []
  } finally {
    loading.value = false
  }
}

// 监听搜索输入
watch(searchQuery, () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(search, 300)
})

// 监听对话框打开
watch(dialogOpen, (open) => {
  if (open) {
    searchQuery.value = ''
    results.value = []
    nextTick(() => {
      searchInput.value?.focus()
    })
  }
})

// 关闭
const close = () => {
  dialogOpen.value = false
}

// 选择项目
const selectItem = (item: GlobalSearchItem) => {
  close()
  if (item.route_name && item.route_params) {
    router.push({ name: item.route_name, params: item.route_params })
  } else if (item.route_name) {
    router.push({ name: item.route_name })
  }
}

// 选择第一个
const selectFirst = () => {
  if (groupedResults.value.length > 0 && selectedGroup.value) {
    const group = groupedResults.value.find(g => g.type === selectedGroup.value)
    if (group && group.items[selectedIndex.value]) {
      selectItem(group.items[selectedIndex.value])
    }
  }
}

// 导航
const navigateDown = () => {
  if (groupedResults.value.length === 0) return
  
  const currentGroupIndex = groupedResults.value.findIndex(g => g.type === selectedGroup.value)
  const currentGroup = groupedResults.value[currentGroupIndex]
  
  if (selectedIndex.value < currentGroup.items.length - 1) {
    selectedIndex.value++
  } else if (currentGroupIndex < groupedResults.value.length - 1) {
    selectedGroup.value = groupedResults.value[currentGroupIndex + 1].type
    selectedIndex.value = 0
  }
}

const navigateUp = () => {
  if (groupedResults.value.length === 0) return
  
  const currentGroupIndex = groupedResults.value.findIndex(g => g.type === selectedGroup.value)
  
  if (selectedIndex.value > 0) {
    selectedIndex.value--
  } else if (currentGroupIndex > 0) {
    const prevGroup = groupedResults.value[currentGroupIndex - 1]
    selectedGroup.value = prevGroup.type
    selectedIndex.value = prevGroup.items.length - 1
  }
}

const isSelected = (type: string, index: number): boolean => {
  return selectedGroup.value === type && selectedIndex.value === index
}

const setSelected = (type: string, index: number) => {
  selectedGroup.value = type
  selectedIndex.value = index
}

// 辅助函数
const getMediaIcon = (type: string): string => {
  const icons: Record<string, string> = {
    novel: 'mdi-book-open-page-variant',
    audiobook: 'mdi-headphones',
    manga: 'mdi-book-open-variant',
    music: 'mdi-music',
    movie: 'mdi-movie',
    series: 'mdi-television',
  }
  return icons[type] || 'mdi-file'
}

const getMediaColor = (type: string): string => {
  const colors: Record<string, string> = {
    novel: 'blue',
    audiobook: 'purple',
    manga: 'orange',
    music: 'green',
    movie: 'red',
    series: 'teal',
  }
  return colors[type] || 'grey'
}

const getMediaLabel = (type: string): string => {
  const labels: Record<string, string> = {
    novel: '小说 / 电子书',
    audiobook: '有声书',
    manga: '漫画',
    music: '音乐',
    movie: '电影',
    series: '剧集',
  }
  return labels[type] || type
}

// 全局快捷键
const handleKeydown = (e: KeyboardEvent) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    dialogOpen.value = !dialogOpen.value
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
})
</script>

<style scoped lang="scss">
.command-palette {
  border-radius: 12px !important;
  overflow: hidden;
}

:deep(.v-field__input) {
  font-size: 1.1rem;
}
</style>
