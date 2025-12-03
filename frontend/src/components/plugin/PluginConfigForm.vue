<template>
  <div class="plugin-config-form">
    <!-- 无 Schema -->
    <v-alert v-if="!schema" type="info" variant="tonal" class="mb-4">
      <v-icon class="mr-2">mdi-information-outline</v-icon>
      此插件未定义配置项
    </v-alert>

    <!-- 表单 -->
    <v-form v-else ref="formRef" @submit.prevent="handleSubmit">
      <template v-for="(propSchema, key) in schemaProperties" :key="String(key)">
        <!-- Boolean -->
        <v-switch
          v-if="propSchema.type === 'boolean'"
          v-model="localConfig[key]"
          :label="propSchema.title || key"
          :hint="propSchema.description"
          persistent-hint
          color="primary"
          class="mb-2"
        />

        <!-- String with enum -->
        <v-select
          v-else-if="propSchema.type === 'string' && propSchema.enum"
          v-model="localConfig[key]"
          :items="propSchema.enum"
          :label="propSchema.title || key"
          :hint="propSchema.description"
          :rules="getFieldRules(key, propSchema)"
          persistent-hint
          variant="outlined"
          density="comfortable"
          class="mb-2"
        />

        <!-- String -->
        <v-text-field
          v-else-if="propSchema.type === 'string'"
          v-model="localConfig[key]"
          :label="propSchema.title || key"
          :hint="propSchema.description"
          :rules="getFieldRules(key, propSchema)"
          :type="isPasswordField(key) ? 'password' : 'text'"
          persistent-hint
          variant="outlined"
          density="comfortable"
          class="mb-2"
        />

        <!-- Integer / Number -->
        <v-text-field
          v-else-if="propSchema.type === 'integer' || propSchema.type === 'number'"
          v-model.number="localConfig[key]"
          :label="propSchema.title || key"
          :hint="getNumberHint(propSchema)"
          :rules="getFieldRules(key, propSchema)"
          type="number"
          :min="propSchema.minimum"
          :max="propSchema.maximum"
          persistent-hint
          variant="outlined"
          density="comfortable"
          class="mb-2"
        />

        <!-- Array (简单字符串数组) -->
        <v-combobox
          v-else-if="propSchema.type === 'array'"
          v-model="localConfig[key]"
          :label="propSchema.title || key"
          :hint="propSchema.description"
          persistent-hint
          variant="outlined"
          density="comfortable"
          multiple
          chips
          closable-chips
          class="mb-2"
        />
      </template>

      <!-- 提交按钮 -->
      <div class="d-flex justify-end mt-4">
        <v-btn
          variant="text"
          class="mr-2"
          @click="handleReset"
        >
          重置
        </v-btn>
        <v-btn
          color="primary"
          type="submit"
          :loading="saving"
          :disabled="!hasChanges"
        >
          保存配置
        </v-btn>
      </div>
    </v-form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'

const props = defineProps<{
  schema: Record<string, any> | null | undefined
  value: Record<string, any>
  saving?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:value', value: Record<string, any>): void
  (e: 'submit', value: Record<string, any>): void
}>()

const formRef = ref<any>(null)
const localConfig = ref<Record<string, any>>({})
const originalConfig = ref<Record<string, any>>({})

// 解析 schema properties
const schemaProperties = computed((): Record<string, Record<string, any>> => {
  if (!props.schema || props.schema.type !== 'object') return {}
  return props.schema.properties || {}
})

// 必填字段
const requiredFields = computed(() => {
  if (!props.schema) return new Set<string>()
  return new Set<string>(props.schema.required || [])
})

// 是否有变更
const hasChanges = computed(() => {
  return JSON.stringify(localConfig.value) !== JSON.stringify(originalConfig.value)
})

// 初始化
function initConfig() {
  const config: Record<string, any> = { ...props.value }
  
  // 确保所有字段都有初始值
  for (const [key, propSchema] of Object.entries(schemaProperties.value)) {
    if (config[key] === undefined) {
      const schema = propSchema as Record<string, any>
      if (schema.default !== undefined) {
        config[key] = schema.default
      } else {
        // 根据类型设置默认值
        switch (schema.type) {
          case 'boolean':
            config[key] = false
            break
          case 'string':
            config[key] = ''
            break
          case 'integer':
          case 'number':
            config[key] = 0
            break
          case 'array':
            config[key] = []
            break
          default:
            config[key] = null
        }
      }
    }
  }
  
  localConfig.value = config
  originalConfig.value = JSON.parse(JSON.stringify(config))
}

// 获取字段校验规则
function getFieldRules(key: string, propSchema: Record<string, any>) {
  const rules: ((v: any) => boolean | string)[] = []
  
  // 必填检查
  if (requiredFields.value.has(key)) {
    rules.push((v: any) => {
      if (v === null || v === undefined || v === '') {
        return `${propSchema.title || key} 是必填项`
      }
      return true
    })
  }
  
  // 数字范围检查
  if (propSchema.type === 'integer' || propSchema.type === 'number') {
    if (propSchema.minimum !== undefined) {
      rules.push((v: any) => v >= propSchema.minimum || `不能小于 ${propSchema.minimum}`)
    }
    if (propSchema.maximum !== undefined) {
      rules.push((v: any) => v <= propSchema.maximum || `不能大于 ${propSchema.maximum}`)
    }
  }
  
  return rules
}

// 判断是否为密码字段
function isPasswordField(key: string): boolean {
  const lowerKey = key.toLowerCase()
  return lowerKey.includes('password') || lowerKey.includes('secret') || lowerKey.includes('key') || lowerKey.includes('token')
}

// 获取数字提示
function getNumberHint(propSchema: Record<string, any>): string {
  const parts: string[] = []
  if (propSchema.description) parts.push(propSchema.description)
  if (propSchema.minimum !== undefined || propSchema.maximum !== undefined) {
    const range: string[] = []
    if (propSchema.minimum !== undefined) range.push(`最小: ${propSchema.minimum}`)
    if (propSchema.maximum !== undefined) range.push(`最大: ${propSchema.maximum}`)
    parts.push(range.join(', '))
  }
  return parts.join(' | ')
}

// 重置表单
function handleReset() {
  localConfig.value = JSON.parse(JSON.stringify(originalConfig.value))
}

// 提交表单
async function handleSubmit() {
  const valid = await formRef.value?.validate()
  if (!valid?.valid) return
  
  emit('update:value', localConfig.value)
  emit('submit', localConfig.value)
}

// 监听 value 变化
watch(() => props.value, (newVal) => {
  if (JSON.stringify(newVal) !== JSON.stringify(originalConfig.value)) {
    initConfig()
  }
}, { deep: true })

onMounted(() => {
  initConfig()
})
</script>

<style scoped>
.plugin-config-form {
  width: 100%;
}
</style>
