<template>
  <v-container fluid class="pa-4">
    <!-- 顶部说明 -->
    <v-alert type="info" variant="tonal" class="mb-4" closable>
      <v-alert-title>
        <div class="d-flex align-center">
          AI 订阅助手 (Beta)
          <v-chip size="x-small" color="primary" variant="flat" class="ml-2">SUBS_ADVISOR</v-chip>
          <v-chip size="x-small" color="success" variant="outlined" class="ml-2">只读建议</v-chip>
        </div>
      </v-alert-title>
      <div class="text-body-2 mt-2">
        <p>用自然语言描述您的订阅需求，AI 将为您生成订阅规则草案。</p>
        <p class="mt-1">草案需要您确认后才会创建实际订阅，创建的订阅默认处于<strong>暂停状态</strong>。</p>
      </div>
    </v-alert>

    <!-- AI 状态提示 -->
    <AiStatusAlert />

    <!-- 输入区 -->
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-robot</v-icon>
        描述您的订阅需求
      </v-card-title>
      <v-card-text>
        <!-- 示例提示 -->
        <div class="mb-4">
          <span class="text-caption text-grey mr-2">试试这些示例：</span>
          <v-chip
            v-for="(example, index) in promptExamples"
            :key="index"
            size="small"
            variant="outlined"
            class="mr-2 mb-2"
            @click="prompt = example.prompt"
          >
            {{ example.description }}
          </v-chip>
        </div>

        <v-textarea
          v-model="prompt"
          label="自然语言描述"
          placeholder="例如：帮我订阅最近热门的韩剧，优先 1080p，要有中文字幕"
          variant="outlined"
          rows="3"
          :disabled="loading"
          @keydown.ctrl.enter="generateDrafts"
        />

        <v-row class="mt-2">
          <v-col cols="12" md="4">
            <v-select
              v-model="mediaTypeHint"
              :items="mediaTypes"
              item-title="label"
              item-value="value"
              label="媒体类型提示（可选）"
              variant="outlined"
              density="comfortable"
              clearable
              hide-details
            />
          </v-col>
          <v-col cols="12" md="4">
            <v-switch
              v-model="forceDummy"
              label="使用 Dummy LLM（调试模式）"
              color="warning"
              hide-details
              density="comfortable"
            />
          </v-col>
          <v-col cols="12" md="4" class="d-flex justify-end align-center">
            <v-btn
              color="primary"
              size="large"
              :loading="loading"
              :disabled="!prompt.trim()"
              @click="generateDrafts"
            >
              <v-icon start>mdi-magic-staff</v-icon>
              生成草案
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- 结果展示 -->
    <template v-if="previewResult">
      <!-- 总结信息 -->
      <v-card class="mb-4" v-if="previewResult.summary">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-text-box-outline</v-icon>
          AI 分析总结
        </v-card-title>
        <v-card-text>
          <div class="text-body-1" style="white-space: pre-wrap;">{{ previewResult.summary }}</div>
          <v-alert v-if="previewResult.notes" type="warning" variant="tonal" class="mt-3" density="compact">
            {{ previewResult.notes }}
          </v-alert>
        </v-card-text>
      </v-card>

      <!-- 草案列表 -->
      <template v-if="previewResult.drafts?.length">
        <div class="text-h6 mb-3">
          <v-icon class="mr-2">mdi-clipboard-list</v-icon>
          生成的订阅草案（{{ previewResult.drafts.length }} 个）
        </div>

        <v-row>
          <v-col
            v-for="(draft, index) in previewResult.drafts"
            :key="index"
            cols="12"
            md="6"
            lg="4"
          >
            <v-card variant="outlined" class="h-100">
              <v-card-title class="d-flex align-center justify-space-between">
                <span>{{ draft.name }}</span>
                <v-chip :color="getMediaTypeColor(draft.media_type)" size="small">
                  {{ getMediaTypeLabel(draft.media_type) }}
                </v-chip>
              </v-card-title>

              <v-card-text>
                <!-- 描述 -->
                <div v-if="draft.description" class="text-body-2 text-grey mb-3">
                  {{ draft.description }}
                </div>

                <!-- 来源 -->
                <div class="mb-3" v-if="draft.sources?.length">
                  <div class="text-caption text-grey mb-1">来源</div>
                  <v-chip
                    v-for="(source, sIndex) in draft.sources"
                    :key="sIndex"
                    size="small"
                    :color="source.valid === false ? 'error' : 'default'"
                    variant="tonal"
                    class="mr-1 mb-1"
                  >
                    <v-icon start size="small">
                      {{ source.type === 'rsshub' ? 'mdi-rss' : 'mdi-web' }}
                    </v-icon>
                    {{ source.name || source.id || source.type }}
                  </v-chip>
                </div>

                <!-- 过滤规则 -->
                <div class="mb-3">
                  <div class="text-caption text-grey mb-1">过滤规则</div>
                  <div class="d-flex flex-wrap gap-1">
                    <v-chip v-if="draft.filter_rule?.min_resolution" size="x-small" variant="tonal">
                      {{ draft.filter_rule.min_resolution }}+
                    </v-chip>
                    <v-chip v-if="draft.filter_rule?.hr_safe" size="x-small" variant="tonal" color="success">
                      HR 安全
                    </v-chip>
                    <v-chip v-if="draft.filter_rule?.free_only" size="x-small" variant="tonal" color="info">
                      仅 Free
                    </v-chip>
                    <v-chip
                      v-for="kw in (draft.filter_rule?.include_keywords || []).slice(0, 3)"
                      :key="kw"
                      size="x-small"
                      variant="outlined"
                    >
                      +{{ kw }}
                    </v-chip>
                    <v-chip
                      v-for="kw in (draft.filter_rule?.exclude_keywords || []).slice(0, 2)"
                      :key="kw"
                      size="x-small"
                      variant="outlined"
                      color="error"
                    >
                      -{{ kw }}
                    </v-chip>
                  </div>
                </div>

                <!-- AI 解释 -->
                <div v-if="draft.ai_explanation" class="text-body-2 text-grey-darken-1 mb-3">
                  <v-icon size="small" class="mr-1">mdi-lightbulb-outline</v-icon>
                  {{ draft.ai_explanation }}
                </div>

                <!-- 验证警告 -->
                <v-alert
                  v-if="draft.validation_warnings?.length"
                  type="warning"
                  variant="tonal"
                  density="compact"
                  class="mb-3"
                >
                  <ul class="text-caption ma-0 pa-0" style="list-style: none;">
                    <li v-for="(warn, wIndex) in draft.validation_warnings" :key="wIndex">
                      • {{ warn }}
                    </li>
                  </ul>
                </v-alert>

                <!-- 验证错误 -->
                <v-alert
                  v-if="draft.validation_errors?.length"
                  type="error"
                  variant="tonal"
                  density="compact"
                  class="mb-3"
                >
                  <ul class="text-caption ma-0 pa-0" style="list-style: none;">
                    <li v-for="(err, eIndex) in draft.validation_errors" :key="eIndex">
                      • {{ err }}
                    </li>
                  </ul>
                </v-alert>
              </v-card-text>

              <v-card-actions>
                <v-btn variant="text" size="small" @click="showDraftDetail(draft)">
                  <v-icon start>mdi-eye</v-icon>
                  查看详情
                </v-btn>
                <v-spacer />
                <v-btn
                  color="primary"
                  :disabled="draft.valid === false"
                  :loading="applyingIndex === index"
                  @click="confirmApply(draft, index)"
                >
                  <v-icon start>mdi-check</v-icon>
                  应用
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-col>
        </v-row>
      </template>

      <!-- 无草案 -->
      <v-alert v-else-if="!loading" type="info" variant="tonal">
        AI 未能生成订阅草案，请尝试更具体的描述。
      </v-alert>
    </template>

    <!-- 错误提示 -->
    <v-alert v-if="error" type="error" variant="tonal" closable class="mt-4">
      {{ error }}
    </v-alert>

    <!-- 应用成功提示 -->
    <v-snackbar v-model="showSuccessSnackbar" color="success" :timeout="5000">
      <v-icon class="mr-2">mdi-check-circle</v-icon>
      {{ successMessage }}
      <template #actions>
        <v-btn variant="text" @click="goToSubscriptions">
          查看订阅
        </v-btn>
      </template>
    </v-snackbar>

    <!-- 详情对话框 -->
    <v-dialog v-model="showDetailDialog" max-width="600">
      <v-card>
        <v-card-title>草案详情</v-card-title>
        <v-card-text>
          <pre class="text-caption bg-grey-lighten-4 pa-3 rounded overflow-auto" style="max-height: 400px;">{{ JSON.stringify(selectedDraft, null, 2) }}</pre>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showDetailDialog = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 确认对话框 -->
    <v-dialog v-model="showConfirmDialog" max-width="500">
      <v-card>
        <v-card-title>确认应用草案</v-card-title>
        <v-card-text>
          <p>即将创建订阅：<strong>{{ selectedDraft?.name }}</strong></p>
          <v-alert type="info" variant="tonal" density="compact" class="mt-3">
            <ul class="text-body-2 ma-0 pl-4">
              <li>订阅将以<strong>暂停状态</strong>创建</li>
              <li>自动下载默认<strong>关闭</strong></li>
              <li>您可以在订阅中心进行后续调整</li>
            </ul>
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showConfirmDialog = false">取消</v-btn>
          <v-btn color="primary" :loading="applying" @click="applyDraft">
            确认应用
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { aiSubsWorkflowApi, type SubsWorkflowDraft, type PreviewResponse, type SubsTargetMediaType } from '@/api/aiSubsWorkflow'
import AiStatusAlert from '@/components/ai/AiStatusAlert.vue'

const router = useRouter()

// 状态
const loading = ref(false)
const applying = ref(false)
const applyingIndex = ref(-1)
const error = ref('')

// 表单
const prompt = ref('')
const mediaTypeHint = ref<SubsTargetMediaType | null>(null)
const forceDummy = ref(false)

// 结果
const previewResult = ref<PreviewResponse | null>(null)

// 对话框
const showDetailDialog = ref(false)
const showConfirmDialog = ref(false)
const selectedDraft = ref<SubsWorkflowDraft | null>(null)
const selectedIndex = ref(-1)

// 成功提示
const showSuccessSnackbar = ref(false)
const successMessage = ref('')

// 媒体类型和示例
const mediaTypes = ref([
  { value: 'movie', label: '电影' },
  { value: 'tv', label: '电视剧' },
  { value: 'anime', label: '动漫' },
])

const promptExamples = ref([
  { prompt: '帮我订阅最近热门的韩剧，优先 1080p，要有中文字幕', description: '韩剧热门' },
  { prompt: '我想追新番动漫，不要 HR 种子，只要 1080p 以上', description: '新番动漫' },
  { prompt: '订阅豆瓣高分电影，评分 8 分以上，优先 4K HDR', description: '高分电影' },
])

// 生成草案
async function generateDrafts() {
  if (!prompt.value.trim()) return
  
  loading.value = true
  error.value = ''
  previewResult.value = null
  
  try {
    const result = await aiSubsWorkflowApi.preview({
      prompt: prompt.value,
      media_type_hint: mediaTypeHint.value || undefined,
      force_dummy: forceDummy.value,
    })
    
    previewResult.value = result
    
    if (!result.success && result.error) {
      error.value = result.error
    }
  } catch (e: any) {
    console.error('生成草案失败:', e)
    error.value = e.response?.data?.detail || e.message || '生成草案失败'
  } finally {
    loading.value = false
  }
}

// 显示详情
function showDraftDetail(draft: SubsWorkflowDraft) {
  selectedDraft.value = draft
  showDetailDialog.value = true
}

// 确认应用
function confirmApply(draft: SubsWorkflowDraft, index: number) {
  selectedDraft.value = draft
  selectedIndex.value = index
  showConfirmDialog.value = true
}

// 应用草案
async function applyDraft() {
  if (!selectedDraft.value) return
  
  applying.value = true
  applyingIndex.value = selectedIndex.value
  
  try {
    const result = await aiSubsWorkflowApi.apply({
      draft: selectedDraft.value,
      confirm: true,
    })
    
    showConfirmDialog.value = false
    
    if (result.success) {
      successMessage.value = `订阅「${result.subscription_name || selectedDraft.value.name}」已创建`
      if (result.rsshub_subscriptions_created > 0) {
        successMessage.value += `，同时启用了 ${result.rsshub_subscriptions_created} 个 RSSHub 源`
      }
      showSuccessSnackbar.value = true
      
      // 从列表中移除已应用的草案
      if (previewResult.value?.drafts) {
        previewResult.value.drafts.splice(selectedIndex.value, 1)
      }
    } else {
      error.value = result.error || '应用草案失败'
    }
  } catch (e: any) {
    console.error('应用草案失败:', e)
    error.value = e.response?.data?.detail || e.message || '应用草案失败'
  } finally {
    applying.value = false
    applyingIndex.value = -1
  }
}

// 跳转到订阅中心
function goToSubscriptions() {
  router.push('/subscriptions')
}

// 辅助函数
function getMediaTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    movie: '电影',
    tv: '电视剧',
    anime: '动漫',
    short_drama: '短剧',
    music: '音乐',
    book: '小说',
    comic: '漫画',
  }
  return labels[type] || type
}

function getMediaTypeColor(type: string): string {
  const colors: Record<string, string> = {
    movie: 'blue',
    tv: 'purple',
    anime: 'pink',
    short_drama: 'orange',
    music: 'green',
    book: 'brown',
    comic: 'cyan',
  }
  return colors[type] || 'grey'
}

// 初始化
onMounted(async () => {
  try {
    // 加载示例
    const examples = await aiSubsWorkflowApi.getPromptExamples()
    promptExamples.value = examples.examples
  } catch (e) {
    console.error('加载示例失败:', e)
  }
})
</script>

<style scoped>
pre {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 12px;
}

.gap-1 {
  gap: 4px;
}
</style>
