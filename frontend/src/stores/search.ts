/**
 * 搜索状态管理
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'

interface RecentSearch {
  query: string
  type: string
  timestamp: number
}

export const useSearchStore = defineStore('search', () => {
  const recentSearches = ref<RecentSearch[]>([])
  
  const addRecentSearch = (search: Omit<RecentSearch, 'timestamp'>) => {
    recentSearches.value.unshift({
      ...search,
      timestamp: Date.now()
    })
    
    // 只保留最近10条
    if (recentSearches.value.length > 10) {
      recentSearches.value = recentSearches.value.slice(0, 10)
    }
  }
  
  return {
    recentSearches,
    addRecentSearch
  }
})

