<!-- 日志标签页 -->
<template>
  <div>
    <v-row>
      <v-col cols="12" md="6">
        <v-switch
          v-model="modelValue.DEBUG"
          label="调试模式"
          hint="启用调试模式"
          persistent-hint
          @update:model-value="$emit('update:modelValue', modelValue)"
        />
      </v-col>
      <v-col cols="12" md="6">
        <v-select
          v-if="!modelValue.DEBUG"
          v-model="modelValue.LOG_LEVEL"
          label="日志级别"
          hint="日志级别"
          persistent-hint
          :items="logLevelItems"
          variant="outlined"
          density="compact"
          prepend-inner-icon="mdi-format-list-bulleted"
          @update:model-value="$emit('update:modelValue', modelValue)"
        />
      </v-col>
      <v-col cols="12" md="6">
        <v-text-field
          v-model="modelValue.LOG_MAX_FILE_SIZE"
          label="日志文件最大大小"
          hint="单个日志文件最大大小"
          persistent-hint
          type="number"
          min="1"
          suffix="MB"
          variant="outlined"
          density="compact"
          prepend-inner-icon="mdi-file-document"
          :rules="[
            (v: any) => v === 0 || !!v || '日志文件最大大小不能为空',
            (v: any) => v >= 1 || '日志文件最大大小至少1MB'
          ]"
          @update:model-value="$emit('update:modelValue', modelValue)"
        />
      </v-col>
      <v-col cols="12" md="6">
        <v-text-field
          v-model="modelValue.LOG_BACKUP_COUNT"
          label="日志备份数量"
          hint="日志文件备份数量"
          persistent-hint
          type="number"
          min="1"
          variant="outlined"
          density="compact"
          prepend-inner-icon="mdi-backup-restore"
          :rules="[
            (v: any) => v === 0 || !!v || '日志备份数量不能为空',
            (v: any) => v >= 1 || '日志备份数量至少1个'
          ]"
          @update:model-value="$emit('update:modelValue', modelValue)"
        />
      </v-col>
      <v-col cols="12">
        <v-text-field
          v-model="modelValue.LOG_FILE_FORMAT"
          label="日志文件格式"
          hint="日志文件格式"
          persistent-hint
          variant="outlined"
          density="compact"
          prepend-inner-icon="mdi-format-text"
          @update:model-value="$emit('update:modelValue', modelValue)"
        />
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
interface Props {
  modelValue: any
}

defineProps<Props>()
defineEmits<{ 'update:modelValue': [value: any] }>()

const logLevelItems = [
  { title: 'DEBUG', value: 'DEBUG' },
  { title: 'INFO', value: 'INFO' },
  { title: 'WARNING', value: 'WARNING' },
  { title: 'ERROR', value: 'ERROR' },
  { title: 'CRITICAL', value: 'CRITICAL' }
]
</script>

