<template>
  <div class="filter-rule-groups">
    <!-- 操作栏 -->
    <v-card variant="outlined" class="mb-4">
      <v-card-title class="d-flex align-center justify-space-between">
        <span>
          <v-icon class="mr-2">mdi-filter-variant</v-icon>
          过滤规则组管理
        </span>
        <v-btn
          color="primary"
          prepend-icon="mdi-plus"
          @click="showCreateDialog = true"
        >
          创建规则组
        </v-btn>
      </v-card-title>

      <v-card-text>
        <v-row>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="searchQuery"
              label="搜索规则组"
              prepend-inner-icon="mdi-magnify"
              clearable
              hide-details
              @input="debouncedSearch"
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="selectedMediaType"
              :items="mediaTypeOptions"
              label="媒体类型"
              placeholder="全部类型"
              clearable
              hide-details
              @update:model-value="loadRuleGroups"
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="enabledFilter"
              :items="[
                { title: '全部', value: undefined },
                { title: '启用', value: true },
                { title: '禁用', value: false }
              ]"
              label="状态"
              clearable
              hide-details
              @update:model-value="loadRuleGroups"
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-btn
              variant="outlined"
              prepend-icon="mdi-refresh"
              @click="loadRuleGroups"
              :loading="loading"
            >
              刷新
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- 规则组列表 -->
    <v-card variant="outlined">
      <v-card-text>
        <div v-if="loading" class="text-center py-12">
          <v-progress-circular indeterminate color="primary" size="64" />
          <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
        </div>

        <div v-else-if="ruleGroups.length === 0" class="text-center py-12">
          <v-icon size="64" color="grey-lighten-1">mdi-filter-off-outline</v-icon>
          <div class="mt-4 text-body-1 text-medium-emphasis">暂无规则组</div>
          <v-btn
            color="primary"
            class="mt-4"
            prepend-icon="mdi-plus"
            @click="showCreateDialog = true"
          >
            创建第一个规则组
          </v-btn>
        </div>

        <v-list v-else>
          <v-list-item
            v-for="group in ruleGroups"
            :key="group.id"
            :class="{ 'bg-grey-lighten-4': !group.enabled }"
          >
            <template v-slot:prepend>
              <v-icon
                :color="group.enabled ? 'primary' : 'grey'"
                :icon="group.enabled ? 'mdi-filter-variant' : 'mdi-filter-variant-off'"
              />
            </template>

            <v-list-item-title class="d-flex align-center">
              <span class="font-weight-medium">{{ group.name }}</span>
              <v-chip
                v-if="!group.enabled"
                size="x-small"
                color="grey"
                class="ml-2"
              >
                已禁用
              </v-chip>
            </v-list-item-title>

            <v-list-item-subtitle class="mt-1">
              {{ group.description || '暂无描述' }}
            </v-list-item-subtitle>

            <template v-slot:append>
              <div class="d-flex align-center">
                <!-- 媒体类型标签 -->
                <v-chip-group size="x-small" class="mr-4">
                  <v-chip
                    v-for="type in group.media_types"
                    :key="type"
                    size="x-small"
                    variant="outlined"
                  >
                    {{ getMediaTypeLabel(type) }}
                  </v-chip>
                </v-chip-group>

                <!-- 优先级 -->
                <v-chip
                  size="x-small"
                  color="primary"
                  variant="outlined"
                  class="mr-4"
                >
                  优先级: {{ group.priority }}
                </v-chip>

                <!-- 操作按钮 -->
                <v-btn
                  icon="mdi-pencil"
                  size="small"
                  variant="text"
                  @click="editRuleGroup(group)"
                />
                <v-btn
                  :icon="group.enabled ? 'mdi-toggle-switch' : 'mdi-toggle-switch-off'"
                  size="small"
                  variant="text"
                  :color="group.enabled ? 'success' : 'grey'"
                  @click="toggleRuleGroup(group)"
                />
                <v-btn
                  icon="mdi-delete"
                  size="small"
                  variant="text"
                  color="error"
                  @click="deleteRuleGroup(group)"
                />
              </div>
            </template>
          </v-list-item>

          <v-divider v-if="ruleGroups.length > 0" />
        </v-list>

        <!-- 分页 -->
        <div v-if="total > pageSize" class="d-flex justify-center mt-4">
          <v-pagination
            v-model="currentPage"
            :length="Math.ceil(total / pageSize)"
            :total-visible="7"
            @update:model-value="loadRuleGroups"
          />
        </div>
      </v-card-text>
    </v-card>

    <!-- 创建/编辑对话框 -->
    <RuleGroupDialog
      v-model="showCreateDialog"
      :rule-group="editingGroup"
      @saved="onRuleGroupSaved"
    />

    <!-- 删除确认对话框 -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title class="text-h5">
          确认删除
        </v-card-title>
        <v-card-text>
          确定要删除规则组 "{{ deletingGroup?.name }}" 吗？此操作不可撤销。
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            variant="text"
            @click="showDeleteDialog = false"
          >
            取消
          </v-btn>
          <v-btn
            color="error"
            variant="text"
            @click="confirmDelete"
            :loading="deleting"
          >
            删除
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 操作结果提示 -->
    <v-snackbar
      v-model="showSnackbar"
      :color="snackbarColor"
      :timeout="3000"
    >
      {{ snackbarMessage }}
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { filterRuleGroupsApi } from '@/api/index'
import type { FilterRuleGroup } from '@/api/index'
import RuleGroupDialog from './RuleGroupDialog.vue'

// 响应式数据
const loading = ref(false)
const deleting = ref(false)
const ruleGroups = ref<FilterRuleGroup[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 搜索和过滤
const searchQuery = ref('')
const selectedMediaType = ref<string | undefined>()
const enabledFilter = ref<boolean | undefined>()

// 对话框状态
const showCreateDialog = ref(false)
const showDeleteDialog = ref(false)
const editingGroup = ref<FilterRuleGroup | null>(null)
const deletingGroup = ref<FilterRuleGroup | null>(null)

// 提示消息
const showSnackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref('success')

// 媒体类型选项
const mediaTypeOptions = [
  { title: '电影', value: 'movie' },
  { title: '电视剧', value: 'tv' },
  { title: '短剧', value: 'short_drama' },
  { title: '动漫', value: 'anime' },
  { title: '音乐', value: 'music' }
]

// 防抖搜索
let searchTimeout: number
const debouncedSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 1
    loadRuleGroups()
  }, 500)
}

// 方法
const getMediaTypeLabel = (value: string) => {
  const option = mediaTypeOptions.find(opt => opt.value === value)
  return option?.title || value
}

const loadRuleGroups = async () => {
  loading.value = true
  try {
    const response = await filterRuleGroupsApi.getFilterRuleGroups({
      page: currentPage.value,
      size: pageSize.value,
      media_type: selectedMediaType.value,
      enabled: enabledFilter.value,
      search: searchQuery.value || undefined
    })
    
    ruleGroups.value = response.data.items
    total.value = response.data.total
  } catch (error) {
    console.error('加载规则组失败:', error)
    showSnackbar.value = true
    snackbarMessage.value = '加载规则组失败'
    snackbarColor.value = 'error'
  } finally {
    loading.value = false
  }
}

const editRuleGroup = (group: FilterRuleGroup) => {
  editingGroup.value = { ...group }
  showCreateDialog.value = true
}

const toggleRuleGroup = async (group: FilterRuleGroup) => {
  try {
    await filterRuleGroupsApi.toggleFilterRuleGroup(group.id, !group.enabled)
    showSnackbar.value = true
    snackbarMessage.value = `规则组已${!group.enabled ? '启用' : '禁用'}`
    snackbarColor.value = 'success'
    loadRuleGroups()
  } catch (error) {
    console.error('切换状态失败:', error)
    showSnackbar.value = true
    snackbarMessage.value = '操作失败'
    snackbarColor.value = 'error'
  }
}

const deleteRuleGroup = (group: FilterRuleGroup) => {
  deletingGroup.value = group
  showDeleteDialog.value = true
}

const confirmDelete = async () => {
  if (!deletingGroup.value) return
  
  deleting.value = true
  try {
    await filterRuleGroupsApi.deleteFilterRuleGroup(deletingGroup.value.id)
    showSnackbar.value = true
    snackbarMessage.value = '删除成功'
    snackbarColor.value = 'success'
    showDeleteDialog.value = false
    loadRuleGroups()
  } catch (error) {
    console.error('删除失败:', error)
    showSnackbar.value = true
    snackbarMessage.value = '删除失败'
    snackbarColor.value = 'error'
  } finally {
    deleting.value = false
    deletingGroup.value = null
  }
}

const onRuleGroupSaved = () => {
  showCreateDialog.value = false
  editingGroup.value = null
  loadRuleGroups()
}

// 生命周期
onMounted(() => {
  loadRuleGroups()
})
</script>

<style scoped>
.filter-rule-groups {
  min-height: 600px;
}

.v-list-item {
  transition: all 0.3s ease;
}

.v-list-item:hover {
  background-color: rgba(0, 0, 0, 0.04);
}
</style>
