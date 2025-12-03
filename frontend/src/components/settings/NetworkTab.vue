<!-- 网络标签页 -->
<template>
  <div>
    <v-row>
      <v-col cols="12" md="6">
        <v-text-field
          v-model="modelValue.PROXY_HOST"
          label="代理服务器"
          placeholder="http://127.0.0.1:7890"
          hint="网络代理服务器地址"
          persistent-hint
          variant="outlined"
          density="compact"
          prepend-inner-icon="mdi-server-network"
          @update:model-value="$emit('update:modelValue', modelValue)"
        />
      </v-col>
      <v-col cols="12" md="6">
        <v-combobox
          v-model="githubProxyDisplay"
          label="Github代理"
          placeholder="Github加速代理"
          hint="Github加速代理"
          persistent-hint
          clearable
          variant="outlined"
          density="compact"
          prepend-inner-icon="mdi-github"
        />
      </v-col>
      <v-col cols="12">
        <v-combobox
          v-model="pipProxyDisplay"
          label="PIP代理"
          placeholder="PIP镜像站"
          hint="PIP镜像站"
          persistent-hint
          :items="pipMirrorsItems"
          clearable
          variant="outlined"
          density="compact"
          prepend-inner-icon="mdi-package"
        />
      </v-col>
      <v-col cols="12" md="6">
        <v-switch
          v-model="modelValue.DOH_ENABLE"
          label="DOH启用"
          hint="启用DNS over HTTPS"
          persistent-hint
          @update:model-value="$emit('update:modelValue', modelValue)"
        />
      </v-col>
      <v-col cols="12" v-show="modelValue.DOH_ENABLE">
        <v-textarea
          v-model="modelValue.DOH_RESOLVERS"
          label="DOH解析器"
          placeholder="1.0.0.1,1.1.1.1,9.9.9.9,149.112.112.112"
          hint="DOH解析服务器列表（逗号分隔）"
          persistent-hint
          variant="outlined"
          density="compact"
          prepend-inner-icon="mdi-dns"
          @update:model-value="$emit('update:modelValue', modelValue)"
        />
      </v-col>
      <v-col cols="12" v-show="modelValue.DOH_ENABLE">
        <v-textarea
          v-model="modelValue.DOH_DOMAINS"
          label="DOH域名"
          placeholder="api.themoviedb.org,api.tmdb.org,webservice.fanart.tv,api.github.com,github.com"
          hint="使用DOH解析的域名列表（逗号分隔）"
          persistent-hint
          variant="outlined"
          density="compact"
          prepend-inner-icon="mdi-domain"
          @update:model-value="$emit('update:modelValue', modelValue)"
        />
      </v-col>
    </v-row>

    <!-- 安全图片域名 -->
    <v-row>
      <v-col cols="12">
        <v-expansion-panels variant="accordion">
          <v-expansion-panel>
            <v-expansion-panel-title class="text-lg">
              <template #default>
                <v-icon icon="mdi-shield-check" class="me-2" />
                安全图片域名
              </template>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <div class="d-flex flex-wrap gap-2 mb-3">
                <v-chip
                  v-for="(domain, index) in modelValue.SECURITY_IMAGE_DOMAINS"
                  :key="index"
                  closable
                  @click:close="removeSecurityDomain(index)"
                >
                  {{ domain }}
                </v-chip>
                <v-chip v-if="modelValue.SECURITY_IMAGE_DOMAINS.length === 0" color="warning">
                  暂无安全图片域名
                </v-chip>
              </div>
              <div class="d-flex align-center gap-2">
                <v-text-field
                  v-model="newSecurityDomain"
                  placeholder="添加安全图片域名"
                  hide-details
                  density="compact"
                  prepend-inner-icon="mdi-shield-check"
                  variant="outlined"
                >
                  <template #append>
                    <v-btn icon color="primary" @click="addSecurityDomain" :disabled="!newSecurityDomain">
                      <v-icon icon="mdi-plus" />
                    </v-btn>
                  </template>
                </v-text-field>
              </div>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  modelValue: any
}

const props = defineProps<Props>()
const emit = defineEmits<{ 'update:modelValue': [value: any] }>()

const newSecurityDomain = ref('')

const pipMirrorsItems = [
  'https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple',
  'https://pypi.mirrors.ustc.edu.cn/simple',
  'https://mirrors.pku.edu.cn/pypi/web/simple',
  'https://mirrors.aliyun.com/pypi/simple',
  'https://mirrors.cloud.tencent.com/pypi/simple',
  'https://mirrors.163.com/pypi/simple',
  'https://pypi.doubanio.com/simple'
]

const githubProxyDisplay = computed({
  get: () => {
    return props.modelValue.GITHUB_PROXY || null
  },
  set: (val: string | null) => {
    props.modelValue.GITHUB_PROXY = val === null ? '' : val
    emit('update:modelValue', props.modelValue)
  }
})

const pipProxyDisplay = computed({
  get: () => {
    return props.modelValue.PIP_PROXY || null
  },
  set: (val: string | null) => {
    props.modelValue.PIP_PROXY = val === null ? '' : val
    emit('update:modelValue', props.modelValue)
  }
})

const addSecurityDomain = () => {
  if (newSecurityDomain.value && !props.modelValue.SECURITY_IMAGE_DOMAINS.includes(newSecurityDomain.value)) {
    props.modelValue.SECURITY_IMAGE_DOMAINS.push(newSecurityDomain.value)
    newSecurityDomain.value = ''
    emit('update:modelValue', props.modelValue)
  }
}

const removeSecurityDomain = (index: number) => {
  props.modelValue.SECURITY_IMAGE_DOMAINS.splice(index, 1)
  emit('update:modelValue', props.modelValue)
}
</script>

