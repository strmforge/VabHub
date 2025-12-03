<template>
  <v-dialog v-model="dialogVisible" max-width="800" persistent>
    <v-card>
      <v-card-title class="text-h5">
        <v-icon class="mr-2">mdi-filter-variant</v-icon>
        {{ isEditing ? '编辑规则组' : '创建规则组' }}
      </v-card-title>

      <v-card-text>
        <v-form ref="formRef" v-model="formValid">
          <v-row>
            <!-- 基础信息 -->
            <v-col cols="12">
              <v-card variant="flat" color="grey-lighten-5">
                <v-card-title class="text-subtitle-1">
                  <v-icon class="mr-2">mdi-information</v-icon>
                  基础信息
                </v-card-title>
                <v-card-text>
                  <v-row>
                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model="formData.name"
                        label="规则组名称"
                        placeholder="请输入规则组名称"
                        :rules="[rules.required]"
                        required
                        hide-details
                      />
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model.number="formData.priority"
                        type="number"
                        label="优先级"
                        placeholder="数字越小优先级越高"
                        :rules="[rules.required, rules.minNumber]"
                        required
                        hide-details
                      />
                    </v-col>
                  </v-row>
                  <v-row>
                    <v-col cols="12">
                      <v-textarea
                        v-model="formData.description"
                        label="描述"
                        placeholder="请输入规则组描述"
                        rows="3"
                        hide-details
                      />
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>
            </v-col>

            <!-- 媒体类型 -->
            <v-col cols="12">
              <v-card variant="flat" color="grey-lighten-5">
                <v-card-title class="text-subtitle-1">
                  <v-icon class="mr-2">mdi-play-box-multiple</v-icon>
                  媒体类型
                </v-card-title>
                <v-card-text>
                  <v-checkbox-group
                    v-model="formData.media_types"
                    :rules="[rules.atLeastOne]"
                  >
                    <v-checkbox
                      v-for="type in mediaTypeOptions"
                      :key="type.value"
                      :label="type.title"
                      :value="type.value"
                      hide-details
                    />
                  </v-checkbox-group>
                </v-card-text>
              </v-card>
            </v-col>

            <!-- 状态设置 -->
            <v-col cols="12">
              <v-card variant="flat" color="grey-lighten-5">
                <v-card-title class="text-subtitle-1">
                  <v-icon class="mr-2">mdi-cog</v-icon>
                  状态设置
                </v-card-title>
                <v-card-text>
                  <v-switch
                    v-model="formData.enabled"
                    label="启用规则组"
                    color="primary"
                    hide-details
                  />
                </v-card-text>
              </v-card>
            </v-col>

            <!-- 规则配置 -->
            <v-col cols="12">
              <v-card variant="flat" color="grey-lighten-5">
                <v-card-title class="text-subtitle-1">
                  <v-icon class="mr-2">mdi-code-json</v-icon>
                  规则配置
                  <v-spacer />
                  <v-btn
                    size="small"
                    variant="outlined"
                    prepend-icon="mdi-help-circle"
                    @click="showRuleHelp = true"
                  >
                    规则格式说明
                  </v-btn>
                </v-card-title>
                <v-card-text>
                  <v-textarea
                    v-model="rulesJson"
                    label="过滤规则 (JSON格式)"
                    placeholder='[{"field": "title", "operator": "contains", "value": "关键词"}]'
                    rows="8"
                    :rules="[rules.validJson]"
                    hint="请输入有效的JSON格式的过滤规则"
                    persistent-hint
                    @input="validateRules"
                  />
                  <v-alert
                    v-if="ruleError"
                    type="error"
                    variant="tonal"
                    class="mt-2"
                  >
                    {{ ruleError }}
                  </v-alert>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          variant="text"
          @click="closeDialog"
        >
          取消
        </v-btn>
        <v-btn
          color="primary"
          variant="text"
          @click="saveRuleGroup"
          :loading="saving"
          :disabled="!formValid || !!ruleError"
        >
          {{ isEditing ? '更新' : '创建' }}
        </v-btn>
      </v-card-actions>
    </v-card>

    <!-- 规则格式说明对话框 -->
    <v-dialog v-model="showRuleHelp" max-width="600">
      <v-card>
        <v-card-title class="text-h5">
          规则格式说明
        </v-card-title>
        <v-card-text>
          <v-alert type="info" variant="tonal" class="mb-4">
            过滤规则使用JSON数组格式，每个规则对象包含以下字段：
          </v-alert>
          
          <v-code class="language-json">
{
  "field": "title|size|seeders|uploaders|...",
  "operator": "contains|equals|greater|less|regex|...",
  "value": "匹配值",
  "case_sensitive": false
}
          </v-code>

          <v-divider class="my-4" />

          <h4 class="text-h6 mb-2">常用字段：</h4>
          <ul>
            <li><code>title</code> - 标题</li>
            <li><code>size</code> - 文件大小</li>
            <li><code>seeders</code> - 做种数</li>
            <li><code>uploaders</code> - 发布者</li>
            <li><code>tags</code> - 标签</li>
          </ul>

          <h4 class="text-h6 mb-2 mt-4">常用操作符：</h4>
          <ul>
            <li><code>contains</code> - 包含</li>
            <li><code>equals</code> - 等于</li>
            <li><code>greater</code> - 大于</li>
            <li><code>less</code> - 小于</li>
            <li><code>regex</code> - 正则匹配</li>
          </ul>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            color="primary"
            variant="text"
            @click="showRuleHelp = false"
          >
            关闭
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { filterRuleGroupsApi } from '@/api'
import type { FilterRuleGroup, FilterRuleGroupRequest } from '@/api'

// Props
interface Props {
  modelValue: boolean
  ruleGroup?: FilterRuleGroup | null
}

const props = withDefaults(defineProps<Props>(), {
  ruleGroup: null
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'saved': []
}>()

// 响应式数据
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const formValid = ref(false)
const formRef = ref()
const saving = ref(false)
const showRuleHelp = ref(false)
const ruleError = ref('')

const isEditing = computed(() => !!props.ruleGroup)

// 表单数据
const formData = reactive<FilterRuleGroupRequest>({
  name: '',
  description: '',
  media_types: [],
  priority: 100,
  rules: [],
  enabled: true
})

const rulesJson = ref('')

// 媒体类型选项
const mediaTypeOptions = [
  { title: '电影', value: 'movie' },
  { title: '电视剧', value: 'tv' },
  { title: '短剧', value: 'short_drama' },
  { title: '动漫', value: 'anime' },
  { title: '音乐', value: 'music' }
]

// 验证规则
const rules = {
  required: (value: any) => !!value || '此字段必填',
  minNumber: (value: number) => value >= 0 || '优先级必须大于等于0',
  atLeastOne: (value: string[]) => value.length > 0 || '请至少选择一个媒体类型',
  validJson: () => !ruleError.value || ruleError.value
}

// 方法
const validateRules = () => {
  if (!rulesJson.value.trim()) {
    formData.rules = []
    ruleError.value = ''
    return
  }

  try {
    const parsed = JSON.parse(rulesJson.value)
    if (!Array.isArray(parsed)) {
      throw new Error('规则必须是数组格式')
    }
    
    // 验证每个规则对象的基本结构
    for (const rule of parsed) {
      if (!rule.field || !rule.operator || rule.value === undefined) {
        throw new Error('每个规则必须包含 field、operator 和 value 字段')
      }
    }
    
    formData.rules = parsed
    ruleError.value = ''
  } catch (error) {
    ruleError.value = error instanceof Error ? error.message : 'JSON格式错误'
    formData.rules = []
  }
}

const resetForm = () => {
  Object.assign(formData, {
    name: '',
    description: '',
    media_types: [],
    priority: 100,
    rules: [],
    enabled: true
  })
  rulesJson.value = ''
  ruleError.value = ''
  formRef.value?.resetValidation()
}

const loadRuleGroup = () => {
  if (props.ruleGroup) {
    Object.assign(formData, {
      name: props.ruleGroup.name,
      description: props.ruleGroup.description || '',
      media_types: [...props.ruleGroup.media_types],
      priority: props.ruleGroup.priority,
      rules: [...props.ruleGroup.rules],
      enabled: props.ruleGroup.enabled
    })
    rulesJson.value = JSON.stringify(props.ruleGroup.rules, null, 2)
  } else {
    resetForm()
  }
}

const closeDialog = () => {
  dialogVisible.value = false
}

const saveRuleGroup = async () => {
  if (!formRef.value?.validate()) return
  
  saving.value = true
  try {
    if (isEditing.value && props.ruleGroup) {
      await filterRuleGroupsApi.updateFilterRuleGroup(props.ruleGroup.id, formData)
    } else {
      await filterRuleGroupsApi.createFilterRuleGroup(formData)
    }
    
    emit('saved')
  } catch (error) {
    console.error('保存规则组失败:', error)
    ruleError.value = '保存失败，请检查输入数据'
  } finally {
    saving.value = false
  }
}

// 监听对话框打开
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    loadRuleGroup()
  }
})
</script>

<style scoped>
.v-code {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  background-color: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
  white-space: pre-wrap;
}

code {
  background-color: #f0f0f0;
  padding: 2px 4px;
  border-radius: 2px;
  font-family: 'Courier New', monospace;
}
</style>
