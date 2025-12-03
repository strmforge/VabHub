<template>
  <div class="manga-source-admin-page">
    <!-- 顶部 PageHeader -->
    <PageHeader title="漫画源配置">
      <template v-slot:actions>
        <v-btn
          color="primary"
          prepend-icon="mdi-plus"
          @click="openCreateDialog"
        >
          新增漫画源
        </v-btn>
      </template>
    </PageHeader>

    <!-- 内容区域 -->
    <v-container fluid>
      <!-- 搜索框 -->
      <v-row class="mb-4">
        <v-col cols="12" md="4">
          <v-text-field
            v-model="searchKeyword"
            variant="outlined"
            density="compact"
            placeholder="搜索漫画源名称..."
            prepend-inner-icon="mdi-magnify"
            hide-details
            clearable
            @keyup.enter="loadList"
          />
        </v-col>
      </v-row>

      <!-- 加载状态 -->
      <div v-if="loading" class="text-center py-12">
        <v-progress-circular indeterminate color="primary" size="64" />
        <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
      </div>

      <!-- 错误状态 -->
      <v-alert
        v-else-if="error"
        type="error"
        variant="tonal"
        class="mb-4"
      >
        {{ error }}
      </v-alert>

      <!-- 列表 -->
      <v-card v-else>
        <v-table>
          <thead>
            <tr>
              <th>名称</th>
              <th>类型</th>
              <th>Base URL</th>
              <th>启用状态</th>
              <th>最近更新</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.id">
              <td>{{ item.name }}</td>
              <td>
                <v-chip size="small" variant="outlined">
                  {{ getSourceTypeName(item.type) }}
                </v-chip>
              </td>
              <td class="text-truncate" style="max-width: 300px;">
                {{ item.base_url }}
              </td>
              <td>
                <v-switch
                  :model-value="item.is_enabled"
                  @update:model-value="toggleEnabled(item.id, $event)"
                  hide-details
                  density="compact"
                  color="primary"
                />
              </td>
              <td>{{ formatDate(item.updated_at) }}</td>
              <td>
                <div class="d-flex gap-2">
                  <v-btn
                    icon
                    size="small"
                    variant="text"
                    @click="openEditDialog(item)"
                  >
                    <v-icon>mdi-pencil</v-icon>
                    <v-tooltip activator="parent">编辑</v-tooltip>
                  </v-btn>
                  <v-btn
                    icon
                    size="small"
                    variant="text"
                    @click="testConnection(item.id)"
                  >
                    <v-icon>mdi-wifi-check</v-icon>
                    <v-tooltip activator="parent">测试连接</v-tooltip>
                  </v-btn>
                  <v-btn
                    icon
                    size="small"
                    variant="text"
                    color="error"
                    @click="confirmDelete(item)"
                  >
                    <v-icon>mdi-delete</v-icon>
                    <v-tooltip activator="parent">删除</v-tooltip>
                  </v-btn>
                </div>
              </td>
            </tr>
          </tbody>
        </v-table>

        <!-- 空状态 -->
        <div v-if="!loading && items.length === 0" class="text-center py-12">
          <v-icon size="64" color="grey-lighten-1">mdi-book-multiple-outline</v-icon>
          <div class="mt-4 text-body-1 text-medium-emphasis">暂无漫画源</div>
          <v-btn
            color="primary"
            class="mt-4"
            prepend-icon="mdi-plus"
            @click="openCreateDialog"
          >
            新增漫画源
          </v-btn>
        </div>

        <!-- 分页 -->
        <div v-if="totalPages > 1" class="d-flex justify-center align-center pa-4">
          <v-pagination
            v-model="page"
            :length="totalPages"
            :total-visible="7"
            @update:model-value="loadList"
          />
        </div>
      </v-card>
    </v-container>

    <!-- 新增/编辑对话框 -->
    <v-dialog
      v-model="showDialog"
      max-width="600"
      persistent
    >
      <v-card>
        <v-card-title>
          <span class="text-h6">{{ dialogMode === 'create' ? '新增漫画源' : '编辑漫画源' }}</span>
          <v-spacer />
          <v-btn icon variant="text" @click="closeDialog">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-form ref="formRef" v-model="formValid">
            <v-text-field
              v-model="form.name"
              label="名称"
              variant="outlined"
              density="compact"
              :rules="[v => !!v || '名称不能为空']"
              required
              class="mb-3"
            />

            <v-select
              v-model="form.type"
              :items="sourceTypeOptions"
              label="源类型"
              variant="outlined"
              density="compact"
              :rules="[v => !!v || '请选择源类型']"
              required
              class="mb-3"
            />

            <v-text-field
              v-model="form.base_url"
              label="Base URL"
              variant="outlined"
              density="compact"
              :rules="[v => !!v || 'Base URL 不能为空', v => isValidUrl(v) || '请输入有效的 URL']"
              required
              class="mb-3"
            />

            <v-text-field
              v-model="form.api_key"
              label="API Key"
              variant="outlined"
              density="compact"
              type="password"
              class="mb-3"
            />

            <v-text-field
              v-model="form.username"
              label="Username"
              variant="outlined"
              density="compact"
              class="mb-3"
            />

            <v-text-field
              v-model="form.password"
              label="Password"
              variant="outlined"
              density="compact"
              type="password"
              class="mb-3"
            />

            <v-switch
              v-model="form.is_enabled"
              label="启用"
              color="primary"
              hide-details
              class="mb-3"
            />

            <v-textarea
              v-model="extraConfigText"
              label="Extra Config (JSON)"
              variant="outlined"
              density="compact"
              rows="4"
              hint="JSON 格式的额外配置，例如：{'library_id': '123'}"
              persistent-hint
              class="mb-3"
            />
          </v-form>
        </v-card-text>
        <v-divider />
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="closeDialog">取消</v-btn>
          <v-btn
            color="primary"
            :loading="saving"
            @click="saveSource"
          >
            保存
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 测试连接结果：库列表预览对话框 -->
    <v-dialog v-model="showLibrariesDialog" max-width="500">
        <v-card>
          <v-card-title class="d-flex align-center">
            <span class="text-h6">连接测试结果</span>
            <v-spacer />
            <v-btn icon variant="text" @click="showLibrariesDialog = false">
              <v-icon>mdi-close</v-icon>
            </v-btn>
          </v-card-title>
          <v-divider />
          <v-card-text>
            <div class="mb-2" v-if="lastTestSourceName">
              当前源：<strong>{{ lastTestSourceName }}</strong>
            </div>
            <div v-if="testLibraries.length > 0">
              <div class="text-body-2 text-medium-emphasis mb-2">检测到的库 / 书架：</div>
              <v-list density="compact">
                <v-list-item
                  v-for="lib in testLibraries"
                  :key="lib.id"
                  :title="lib.name"
                  :subtitle="lib.id"
                />
              </v-list>
            </div>
            <div v-else class="text-body-2 text-medium-emphasis">
              连接成功，但未返回可用的库列表。
            </div>
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn color="primary" variant="text" @click="showLibrariesDialog = false">
              关闭
            </v-btn>
          </v-card-actions>
        </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useToast } from '@/composables/useToast'
import { mangaSourceAdminApi } from '@/services/api'
import type { MangaSource, MangaSourceType } from '@/types/mangaSource'
import PageHeader from '@/components/common/PageHeader.vue'

const toast = useToast()

// 列表状态
const loading = ref(false)
const error = ref<string | null>(null)
const items = ref<MangaSource[]>([])
const searchKeyword = ref('')
const page = ref(1)
const pageSize = 20
const total = ref(0)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

// 表单与对话框
type DialogMode = 'create' | 'edit'

const showDialog = ref(false)
const dialogMode = ref<DialogMode>('create')
const formRef = ref<{ validate: () => Promise<{ valid: boolean }> | void } | null>(null)
const formValid = ref(false)

const emptyForm = (): MangaSource => ({
  id: 0,
  name: '',
  type: 'OPDS',
  base_url: '',
  api_key: '',
  username: '',
  password: '',
  is_enabled: true,
  extra_config: {},
  created_at: '',
  updated_at: ''
})

const form = ref<MangaSource>(emptyForm())
const extraConfigText = ref('')
const saving = ref(false)

// 源类型选项
const sourceTypeOptions = [
  { title: 'OPDS', value: 'OPDS' },
  { title: 'Suwayomi', value: 'SUWAYOMI' },
  { title: 'Komga', value: 'KOMGA' },
  { title: '通用 HTTP', value: 'GENERIC_HTTP' }
] as { title: string; value: MangaSourceType }[]

// 工具：校验 URL
const isValidUrl = (value: string): boolean => {
  if (!value) return false
  try {
    // eslint-disable-next-line no-new
    new URL(value)
    return true
  } catch {
    return false
  }
}

// 工具：格式化时间
const formatDate = (dateStr: string | null): string => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  if (Number.isNaN(d.getTime())) return dateStr
  return d.toLocaleString('zh-CN')
}

// 工具：源类型名称
const getSourceTypeName = (type: MangaSourceType): string => {
  const map: Record<MangaSourceType, string> = {
    OPDS: 'OPDS',
    SUWAYOMI: 'Suwayomi',
    KOMGA: 'Komga',
    GENERIC_HTTP: '通用 HTTP'
  }
  return map[type] || type
}

// 加载列表
const loadList = async () => {
  try {
    loading.value = true
    error.value = null

    const params: { keyword?: string; page?: number; page_size?: number } = {
      page: page.value,
      page_size: pageSize
    }
    if (searchKeyword.value.trim()) {
      params.keyword = searchKeyword.value.trim()
    }

    const result = await mangaSourceAdminApi.list(params)
    items.value = result.items
    total.value = result.total
    page.value = result.page
  } catch (err: any) {
    console.error('加载漫画源列表失败:', err)
    error.value = err.response?.data?.detail || err.message || '加载列表失败'
    toast.error(error.value || '加载失败')
    items.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 打开新增对话框
const openCreateDialog = () => {
  dialogMode.value = 'create'
  form.value = emptyForm()
  extraConfigText.value = ''
  showDialog.value = true
}

// 打开编辑对话框
const openEditDialog = (item: MangaSource) => {
  dialogMode.value = 'edit'
  form.value = { ...item }
  extraConfigText.value = item.extra_config ? JSON.stringify(item.extra_config, null, 2) : ''
  showDialog.value = true
}

// 关闭对话框
const closeDialog = () => {
  showDialog.value = false
}

// 保存漫画源
const saveSource = async () => {
  if (formRef.value && typeof formRef.value.validate === 'function') {
    const result = await formRef.value.validate()
    if (result && 'valid' in result && !result.valid) {
      return
    }
  }

  // 解析 extra_config
  let extraConfig: Record<string, any> | undefined
  if (extraConfigText.value.trim()) {
    try {
      extraConfig = JSON.parse(extraConfigText.value)
    } catch (e: any) {
      toast.error('Extra Config 不是有效的 JSON')
      return
    }
  }

  const payload = {
    name: form.value.name,
    type: form.value.type,
    base_url: form.value.base_url,
    api_key: form.value.api_key || undefined,
    username: form.value.username || undefined,
    password: form.value.password || undefined,
    is_enabled: form.value.is_enabled,
    extra_config: extraConfig
  }

  saving.value = true
  try {
    if (dialogMode.value === 'create') {
      await mangaSourceAdminApi.create(payload)
      toast.success('已新增漫画源')
    } else {
      await mangaSourceAdminApi.update(form.value.id, payload)
      toast.success('已更新漫画源')
    }
    showDialog.value = false
    await loadList()
  } catch (err: any) {
    console.error('保存漫画源失败:', err)
    toast.error(err.response?.data?.detail || err.message || '保存失败')
  } finally {
    saving.value = false
  }
}

// 启用状态切换
const toggleEnabled = async (id: number, enabled: boolean | null) => {
  const target = items.value.find(it => it.id === id)
  if (!target) return

  try {
    const next = !!enabled
    await mangaSourceAdminApi.update(id, { is_enabled: next })
    target.is_enabled = next
  } catch (err: any) {
    console.error('切换启用状态失败:', err)
    toast.error(err.response?.data?.detail || err.message || '切换启用状态失败')
  }
}

// 删除漫画源
const confirmDelete = async (item: MangaSource) => {
  if (!confirm(`确定要删除漫画源 "${item.name}" 吗？`)) return
  try {
    await mangaSourceAdminApi.remove(item.id)
    toast.success('已删除漫画源')
    await loadList()
  } catch (err: any) {
    console.error('删除漫画源失败:', err)
    toast.error(err.response?.data?.detail || err.message || '删除失败')
  }
}

// 测试连接库列表弹窗状态
const showLibrariesDialog = ref(false)
const testLibraries = ref<{ id: string; name: string }[]>([])
const lastTestSourceName = ref<string | null>(null)

// 测试连接
const testConnection = async (id: number) => {
  try {
    // 后端目前返回 { ok, message }，未来如扩展库列表，可在 extra 中附带
    const result: any = await mangaSourceAdminApi.ping(id)
    if (result.ok) {
      toast.success(result.message || '连接正常')

      const item = items.value.find(i => i.id === id)
      lastTestSourceName.value = item?.name || null

      const libs = (result.libraries || []) as any[]
      testLibraries.value = libs.map((lib) => ({
        id: String(lib.id),
        name: String(lib.name ?? lib.id ?? '')
      }))
      showLibrariesDialog.value = true
    } else {
      toast.error(result.message || '连接失败')
      testLibraries.value = []
    }
  } catch (err: any) {
    console.error('测试连接失败:', err)
    toast.error(err.response?.data?.detail || err.message || '测试连接失败')
    testLibraries.value = []
  }
}

onMounted(() => {
  loadList()
})
</script>

<style scoped lang="scss">
.manga-source-admin-page {
  min-height: 100vh;
  background-color: #f5f5f5;
}
</style>
