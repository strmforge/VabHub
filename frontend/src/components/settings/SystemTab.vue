<!-- 系统标签页 -->
<template>
  <div>
    <v-row>
      <v-col cols="12" md="6">
        <v-switch
          v-model="modelValue.AUXILIARY_AUTH_ENABLE"
          label="用户辅助认证"
          hint="允许外部服务进行登录认证以及自动创建用户"
          persistent-hint
          @update:model-value="$emit('update:modelValue', modelValue)"
        />
      </v-col>
      <v-col cols="12" md="6">
        <v-switch
          v-model="modelValue.GLOBAL_IMAGE_CACHE"
          label="全局图片缓存"
          hint="将媒体图片缓存到本地，提升图片加载速度"
          persistent-hint
          @update:model-value="$emit('update:modelValue', modelValue)"
        />
      </v-col>
      <v-col cols="12" md="6">
        <v-switch
          v-model="modelValue.SUBSCRIBE_STATISTIC_SHARE"
          label="分享订阅数据"
          hint="分享订阅统计数据到热门订阅，供其他用户参考"
          persistent-hint
          @update:model-value="$emit('update:modelValue', modelValue)"
        />
      </v-col>
      <v-col cols="12" md="6">
        <v-switch
          v-model="modelValue.PLUGIN_STATISTIC_SHARE"
          label="上报插件安装数据"
          hint="上报插件安装数据给服务器，用于统计展示插件安装情况"
          persistent-hint
          @update:model-value="$emit('update:modelValue', modelValue)"
        />
      </v-col>
      <v-col cols="12" md="6">
        <v-switch
          v-model="modelValue.WORKFLOW_STATISTIC_SHARE"
          label="分享工作流数据"
          hint="分享工作流统计数据到热门工作流，供其他用户参考"
          persistent-hint
          @update:model-value="$emit('update:modelValue', modelValue)"
        />
      </v-col>
      <v-col cols="12" md="6">
        <v-switch
          v-model="modelValue.BIG_MEMORY_MODE"
          label="大内存模式"
          hint="使用更大的内存缓存数据，提升系统性能"
          persistent-hint
          @update:model-value="$emit('update:modelValue', modelValue)"
        />
      </v-col>
      <v-col v-if="dbType === 'sqlite'" cols="12" md="6">
        <v-switch
          v-model="modelValue.DB_WAL_ENABLE"
          label="数据库WAL模式"
          hint="启用SQLite WAL模式"
          persistent-hint
          @update:model-value="$emit('update:modelValue', modelValue)"
        />
      </v-col>
      <v-col cols="12" md="6">
        <v-switch
          v-model="moviePilotAutoUpdate"
          label="自动更新VabHub"
          hint="重启时自动更新VabHub到最新发行版本"
          persistent-hint
          @update:model-value="handleAutoUpdateChange"
        />
      </v-col>
      <v-col cols="12" md="6">
        <v-switch
          v-model="modelValue.AUTO_UPDATE_RESOURCE"
          label="自动更新站点资源"
          hint="重启时自动检测和更新站点资源包"
          persistent-hint
          @update:model-value="$emit('update:modelValue', modelValue)"
        />
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  modelValue: any
  dbType?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{ 'update:modelValue': [value: any] }>()

const moviePilotAutoUpdate = computed({
  get: () => {
    return ['release', 'dev'].includes(props.modelValue.VABHUB_AUTO_UPDATE)
  },
  set: (val: boolean) => {
    props.modelValue.VABHUB_AUTO_UPDATE = val ? 'release' : 'false'
    emit('update:modelValue', props.modelValue)
  }
})

const handleAutoUpdateChange = (val: boolean) => {
  moviePilotAutoUpdate.value = val
}
</script>

