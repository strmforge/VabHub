<template>
  <div class="global-search-bar-wrapper">
    <v-text-field
      ref="searchFieldRef"
      v-model="searchQuery"
      placeholder="搜索媒体、音乐、订阅... (Ctrl+K)"
      prepend-inner-icon="mdi-magnify"
      variant="outlined"
      density="compact"
      hide-details
      class="global-search-bar"
      @focus="showSuggestions = true"
      @blur="handleBlur"
      @keydown.enter="handleSearch"
    >
      <template v-slot:append-inner>
        <v-chip
          v-if="searchQuery"
          size="x-small"
          variant="flat"
          color="primary"
          class="mr-2"
        >
          {{ searchType }}
        </v-chip>
        <v-btn
          v-if="searchQuery"
          icon
          size="x-small"
          variant="text"
          @click="clearSearch"
        >
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </template>
    </v-text-field>

    <!-- 搜索建议下拉 -->
    <v-menu
      v-model="showSuggestions"
      :activator="searchFieldRef"
      location="bottom"
      offset-y
      max-width="600"
    >
      <v-card>
        <v-list>
          <v-list-subheader>最近搜索</v-list-subheader>
          <v-list-item
            v-for="(item, index) in recentSearches"
            :key="index"
            :title="item.query"
            :subtitle="item.type"
            prepend-icon="mdi-clock-outline"
            @click="selectSearch(item)"
          />
        </v-list>
        <v-divider />
        <v-list>
          <v-list-subheader>快速操作</v-list-subheader>
          <v-list-item
            prepend-icon="mdi-movie"
            title="搜索电影"
            @click="searchByType('movie')"
          />
          <v-list-item
            prepend-icon="mdi-television"
            title="搜索电视剧"
            @click="searchByType('tv')"
          />
          <v-list-item
            prepend-icon="mdi-music"
            title="搜索音乐"
            @click="searchByType('music')"
          />
        </v-list>
      </v-card>
    </v-menu>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSearchStore } from '@/stores/search'

const router = useRouter()
const searchStore = useSearchStore()

const searchFieldRef = ref()
const searchQuery = ref('')
const showSuggestions = ref(false)
const recentSearches = computed(() => searchStore.recentSearches)
const searchType = computed(() => {
  if (!searchQuery.value) return ''
  // 简单的类型检测逻辑
  return '全部'
})

const handleSearch = () => {
  if (!searchQuery.value.trim()) return
  
  searchStore.addRecentSearch({
    query: searchQuery.value,
    type: searchType.value
  })
  
  router.push({
    name: 'Search',
    query: { q: searchQuery.value }
  })
  
  showSuggestions.value = false
}

const clearSearch = () => {
  searchQuery.value = ''
  showSuggestions.value = false
}

const handleBlur = () => {
  // 延迟隐藏，允许点击建议项
  setTimeout(() => {
    showSuggestions.value = false
  }, 200)
}

const selectSearch = (item: any) => {
  searchQuery.value = item.query
  handleSearch()
}

const searchByType = (type: string) => {
  router.push({
    name: 'Search',
    query: { type }
  })
  showSuggestions.value = false
}
</script>

<style lang="scss" scoped>
.global-search-bar-wrapper {
  max-width: 500px;
  width: 100%;
}

.global-search-bar {
  width: 100%;
}
</style>

