<template>
  <div class="plugin-panel-host">
    <!-- Loading -->
    <div v-if="loading" class="text-center pa-4">
      <v-progress-circular indeterminate color="primary" size="24" />
      <span class="ml-2 text-medium-emphasis">加载插件面板...</span>
    </div>

    <!-- Empty -->
    <v-alert
      v-else-if="panels.length === 0 && !hideEmpty"
      type="info"
      variant="tonal"
      class="ma-0"
    >
      <v-icon class="mr-2">mdi-puzzle-outline</v-icon>
      暂无插件面板
    </v-alert>

    <!-- Panels -->
    <div v-else class="panels-container">
      <v-card
        v-for="item in panels"
        :key="`${item.plugin_id}:${item.panel.id}`"
        variant="outlined"
        class="mb-4"
      >
        <v-card-title class="d-flex align-center py-2 px-4">
          <v-icon size="small" class="mr-2" color="primary">
            {{ getPanelTypeIcon(item.panel.type) }}
          </v-icon>
          <span class="text-subtitle-1">{{ item.panel.title }}</span>
          <v-chip size="x-small" variant="tonal" class="ml-2">
            {{ item.plugin_name }}
          </v-chip>
          <v-spacer />
          <v-btn
            icon
            variant="text"
            size="small"
            @click="refreshPanel(item)"
            :loading="loadingPanels[getPanelKey(item)]"
          >
            <v-icon size="small">mdi-refresh</v-icon>
          </v-btn>
        </v-card-title>

        <v-divider />

        <v-card-text class="pa-4">
          <!-- Panel Content -->
          <div v-if="loadingPanels[getPanelKey(item)]" class="text-center py-4">
            <v-progress-circular indeterminate size="24" />
          </div>
          <div v-else-if="panelErrors[getPanelKey(item)]" class="text-error">
            {{ panelErrors[getPanelKey(item)] }}
          </div>
          <component
            v-else-if="panelData[getPanelKey(item)]"
            :is="getPanelComponent(item.panel.type)"
            :payload="panelData[getPanelKey(item)]"
            :config="item.panel.config"
          />
          <div v-else class="text-medium-emphasis">无数据</div>
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { pluginPanelApi } from '@/services/api'
import type {
  PluginPanelPlacement,
  PluginPanelWithPlugin,
  PluginPanelType,
} from '@/types/pluginPanels'
import { getPanelTypeIcon } from '@/types/pluginPanels'

// 面板组件
import PanelMetricGrid from './panels/PanelMetricGrid.vue'
import PanelList from './panels/PanelList.vue'
import PanelMarkdown from './panels/PanelMarkdown.vue'
import PanelStatusCard from './panels/PanelStatusCard.vue'
import PanelLogStream from './panels/PanelLogStream.vue'

const props = withDefaults(defineProps<{
  placement: PluginPanelPlacement
  maxPanels?: number
  hideEmpty?: boolean
}>(), {
  maxPanels: 10,
  hideEmpty: false,
})

// State
const loading = ref(false)
const panels = ref<PluginPanelWithPlugin[]>([])
const panelData = ref<Record<string, any>>({})
const loadingPanels = ref<Record<string, boolean>>({})
const panelErrors = ref<Record<string, string>>({})

// Panel key
function getPanelKey(item: PluginPanelWithPlugin): string {
  return `${item.plugin_id}:${item.panel.id}`
}

// Get component by type
function getPanelComponent(type: PluginPanelType) {
  const components: Record<PluginPanelType, any> = {
    metric_grid: PanelMetricGrid,
    list: PanelList,
    markdown: PanelMarkdown,
    status_card: PanelStatusCard,
    log_stream: PanelLogStream,
  }
  return components[type] || PanelStatusCard
}

// Load panels list
async function loadPanels() {
  loading.value = true
  try {
    const result = await pluginPanelApi.listByPlacement(props.placement)
    panels.value = result.slice(0, props.maxPanels)
    
    // Load data for each panel
    for (const panel of panels.value) {
      loadPanelData(panel)
    }
  } catch (error: any) {
    console.error('Failed to load plugin panels:', error)
  } finally {
    loading.value = false
  }
}

// Load single panel data
async function loadPanelData(item: PluginPanelWithPlugin) {
  const key = getPanelKey(item)
  loadingPanels.value[key] = true
  panelErrors.value[key] = ''
  
  try {
    const response = await pluginPanelApi.getPanelData(item.plugin_id, item.panel.id)
    panelData.value[key] = response.payload
  } catch (error: any) {
    console.error(`Failed to load panel data ${key}:`, error)
    panelErrors.value[key] = error.response?.data?.detail || '加载失败'
  } finally {
    loadingPanels.value[key] = false
  }
}

// Refresh panel
function refreshPanel(item: PluginPanelWithPlugin) {
  loadPanelData(item)
}

// Watch placement change
watch(() => props.placement, () => {
  loadPanels()
})

// Init
onMounted(() => {
  loadPanels()
})
</script>

<style scoped>
.plugin-panel-host {
  width: 100%;
}
</style>
