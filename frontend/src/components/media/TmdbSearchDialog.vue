<template>
  <v-dialog 
    v-model="dialogVisible" 
    max-width="800px" 
    persistent
    scrollable
  >
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="me-2">mdi-movie-search</v-icon>
        TMDB 媒体搜索
        <v-spacer />
        <v-btn icon variant="text" @click="closeDialog">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      
      <v-divider />
      
      <v-card-text class="pa-4">
        <div class="text-center py-8">
          <v-icon size="48" color="medium-emphasis">mdi-movie-search</v-icon>
          <div class="text-h6 mt-2">搜索 TMDB 媒体库</div>
        </div>
      </v-card-text>

      <v-divider />
      
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="closeDialog">取消</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface Props {
  initialQuery?: string
  mediaType?: string
}

const props = withDefaults(defineProps<Props>(), {
  mediaType: 'all'
})

const emit = defineEmits<{
  select: [media: any]
  close: []
}>()

const dialogVisible = ref(false)
const searchQuery = ref(props.initialQuery || '')
const searchResults = ref([])
const searching = ref(false)

const closeDialog = () => {
  dialogVisible.value = false
  emit('close')
}

defineExpose({
  show: () => { dialogVisible.value = true }
})
</script>

<style scoped>
.search-result-item {
  cursor: pointer;
  transition: background-color 0.2s;
}

.search-result-item:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

.v-avatar {
  border-radius: 8px;
  overflow: hidden;
}
</style>
