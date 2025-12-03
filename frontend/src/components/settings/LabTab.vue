<!-- 实验室标签页 -->
<template>
  <div>
    <v-row>
      <v-col cols="12" md="6">
        <v-switch
          v-model="modelValue.PLUGIN_AUTO_RELOAD"
          label="插件自动重载"
          hint="启用插件自动重载"
          persistent-hint
          @update:model-value="$emit('update:modelValue', modelValue)"
        />
      </v-col>
      <v-col cols="12" md="6">
        <v-switch
          v-model="modelValue.ENCODING_DETECTION_PERFORMANCE_MODE"
          label="编码检测性能模式"
          hint="启用编码检测性能模式"
          persistent-hint
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
</script>

