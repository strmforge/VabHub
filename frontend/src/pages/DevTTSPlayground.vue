<template>
  <div class="tts-playground-page">
    <v-container>
      <PageHeader
        title="TTS 开发调试操场"
        subtitle="输入文本，立即试听 TTS 效果（Dev Only）"
      >
        <template #actions>
          <v-chip size="small" color="warning">Dev Only</v-chip>
        </template>
      </PageHeader>

      <!-- 警告提示 -->
      <v-alert type="warning" variant="tonal" class="mb-4" icon="mdi-alert">
        <strong>仅用于开发调试</strong>：此功能可能产生 TTS 调用费用，请谨慎使用。
      </v-alert>

      <v-row>
        <!-- 左侧：参数表单 -->
        <v-col cols="12" md="6">
          <v-card>
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2" color="primary">mdi-tune</v-icon>
              <span>合成参数</span>
            </v-card-title>
            <v-divider />
            <v-card-text>
              <!-- 文本输入 -->
              <v-textarea
                v-model="request.text"
                label="输入文本"
                placeholder="请输入要合成的文本..."
                variant="outlined"
                rows="8"
                counter
                :maxlength="5000"
                required
                class="mb-4"
              >
                <template v-slot:append>
                  <span class="text-caption text-medium-emphasis">
                    {{ request.text.length }} / 5000
                  </span>
                </template>
              </v-textarea>

              <!-- 快捷按钮 -->
              <div class="d-flex gap-2 mb-4">
                <v-btn
                  size="small"
                  variant="outlined"
                  @click="fillDemoText('zh')"
                >
                  填充中文示例
                </v-btn>
                <v-btn
                  size="small"
                  variant="outlined"
                  @click="fillDemoText('en')"
                >
                  填充英文示例
                </v-btn>
                <v-btn
                  size="small"
                  variant="outlined"
                  color="error"
                  @click="clearForm"
                >
                  清空
                </v-btn>
              </div>

              <v-divider class="mb-4" />

              <!-- 可选参数 -->
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="request.ebook_id"
                    label="EBook ID（可选）"
                    placeholder="用于按作品 Profile 解析"
                    type="number"
                    variant="outlined"
                    density="compact"
                    clearable
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="request.provider"
                    label="Provider（可选）"
                    placeholder="覆盖全局 provider"
                    variant="outlined"
                    density="compact"
                    clearable
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="request.language"
                    label="Language（可选）"
                    placeholder="zh-CN / en-US 等"
                    variant="outlined"
                    density="compact"
                    clearable
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="request.voice"
                    label="Voice（可选）"
                    placeholder="声线名称"
                    variant="outlined"
                    density="compact"
                    clearable
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="request.speed"
                    label="Speed（可选）"
                    placeholder="0.5 ~ 2.0"
                    type="number"
                    step="0.1"
                    min="0.5"
                    max="2.0"
                    variant="outlined"
                    density="compact"
                    clearable
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="request.pitch"
                    label="Pitch（可选）"
                    placeholder="-10.0 ~ 10.0"
                    type="number"
                    step="0.1"
                    min="-10.0"
                    max="10.0"
                    variant="outlined"
                    density="compact"
                    clearable
                  />
                </v-col>
                <v-col cols="12">
                  <v-switch
                    v-model="request.skip_rate_limit"
                    label="跳过 RateLimiter（仅用于 Dev）"
                    color="warning"
                    density="compact"
                  />
                </v-col>
              </v-row>

              <!-- 提交按钮 -->
              <v-btn
                color="primary"
                size="large"
                block
                :loading="synthesizing"
                :disabled="!request.text || request.text.trim().length === 0"
                @click="synthesize"
                class="mt-4"
              >
                <v-icon start>mdi-play</v-icon>
                合成预览
              </v-btn>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- 右侧：结果区 -->
        <v-col cols="12" md="6">
          <v-card>
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2" color="success">mdi-check-circle</v-icon>
              <span>合成结果</span>
            </v-card-title>
            <v-divider />
            <v-card-text>
              <!-- 加载状态 -->
              <v-progress-linear
                v-if="synthesizing"
                indeterminate
                color="primary"
                class="mb-4"
              />

              <!-- 错误提示 -->
              <v-alert
                v-if="response && !response.success && !response.rate_limited"
                type="error"
                variant="tonal"
                class="mb-4"
              >
                {{ response.message }}
              </v-alert>

              <!-- 限流提示 -->
              <v-alert
                v-if="response && response.rate_limited"
                type="warning"
                variant="tonal"
                class="mb-4"
              >
                <strong>请求被限流</strong>：{{ response.rate_limit_reason || '未知原因' }}
                <br />
                {{ response.message }}
              </v-alert>

              <!-- 成功提示 -->
              <v-alert
                v-if="response && response.success"
                type="success"
                variant="tonal"
                class="mb-4"
              >
                合成成功！
              </v-alert>

              <!-- 实际使用的参数 -->
              <v-expansion-panels v-if="response" class="mb-4">
                <v-expansion-panel>
                  <v-expansion-panel-title>
                    <v-icon class="mr-2">mdi-information</v-icon>
                    实际使用的参数
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-list density="compact">
                      <v-list-item>
                        <v-list-item-title>Provider</v-list-item-title>
                        <template v-slot:append>
                          <span class="text-medium-emphasis">
                            {{ response.provider || '未指定' }}
                          </span>
                        </template>
                      </v-list-item>
                      <v-list-item>
                        <v-list-item-title>Language</v-list-item-title>
                        <template v-slot:append>
                          <span class="text-medium-emphasis">
                            {{ response.language || '未指定' }}
                          </span>
                        </template>
                      </v-list-item>
                      <v-list-item>
                        <v-list-item-title>Voice</v-list-item-title>
                        <template v-slot:append>
                          <span class="text-medium-emphasis">
                            {{ response.voice || '未指定' }}
                          </span>
                        </template>
                      </v-list-item>
                      <v-list-item v-if="response.speed !== null && response.speed !== undefined">
                        <v-list-item-title>Speed</v-list-item-title>
                        <template v-slot:append>
                          <span class="text-medium-emphasis">
                            {{ response.speed }}
                          </span>
                        </template>
                      </v-list-item>
                      <v-list-item v-if="response.pitch !== null && response.pitch !== undefined">
                        <v-list-item-title>Pitch</v-list-item-title>
                        <template v-slot:append>
                          <span class="text-medium-emphasis">
                            {{ response.pitch }}
                          </span>
                        </template>
                      </v-list-item>
                      <v-list-item>
                        <v-list-item-title>字符数</v-list-item-title>
                        <template v-slot:append>
                          <span class="text-medium-emphasis">
                            {{ response.char_count }}
                          </span>
                        </template>
                      </v-list-item>
                      <v-list-item v-if="response.duration_seconds">
                        <v-list-item-title>时长</v-list-item-title>
                        <template v-slot:append>
                          <span class="text-medium-emphasis">
                            {{ formatDuration(response.duration_seconds) }}
                          </span>
                        </template>
                      </v-list-item>
                    </v-list>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>

              <!-- 音频播放器 -->
              <div v-if="response && response.success && response.audio_url" class="mt-4">
                <v-card variant="outlined">
                  <v-card-title class="text-subtitle-1">
                    <v-icon class="mr-2">mdi-music</v-icon>
                    音频播放
                  </v-card-title>
                  <v-card-text>
                    <audio
                      :src="getAudioFullUrl(response.audio_url)"
                      controls
                      class="w-100"
                      style="width: 100%;"
                    />
                  </v-card-text>
                </v-card>
              </div>

              <!-- 空状态 -->
              <v-empty-state
                v-if="!response && !synthesizing"
                title="暂无结果"
                text="请在左侧输入文本并点击「合成预览」"
                icon="mdi-music-note-off"
              />
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useToast } from '@/composables/useToast'
import { devTTSApi } from '@/services/api'
import type { TTSPlaygroundRequest, TTSPlaygroundResponse } from '@/types/tts'
import PageHeader from '@/components/common/PageHeader.vue'

const toast = useToast()

// 请求参数
const request = ref<TTSPlaygroundRequest>({
  text: '',
  skip_rate_limit: false
})

// 响应结果
const response = ref<TTSPlaygroundResponse | null>(null)
const synthesizing = ref(false)

// 获取音频完整 URL
const getAudioFullUrl = (audioUrl: string | null | undefined): string => {
  if (!audioUrl) return ''
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
  // 如果 audioUrl 已经是完整 URL，直接返回
  if (audioUrl.startsWith('http://') || audioUrl.startsWith('https://')) {
    return audioUrl
  }
  // 否则拼接 baseURL
  return `${baseURL}${audioUrl}`
}

// 格式化时长
const formatDuration = (seconds: number | null | undefined): string => {
  if (!seconds) return '-'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 填充示例文本
const fillDemoText = (lang: 'zh' | 'en') => {
  if (lang === 'zh') {
    request.value.text = '这是一段中文测试文本。用于测试 TTS 文本转语音功能的效果。'
  } else {
    request.value.text = 'This is an English test text. Used to test the TTS text-to-speech functionality.'
  }
}

// 清空表单
const clearForm = () => {
  request.value = {
    text: '',
    skip_rate_limit: false
  }
  response.value = null
}

// 合成
const synthesize = async () => {
  if (!request.value.text || request.value.text.trim().length === 0) {
    toast.error('请输入文本')
    return
  }

  synthesizing.value = true
  response.value = null

  try {
    const result = await devTTSApi.playgroundSynthesize(request.value)
    response.value = result

    if (result.success) {
      toast.success('合成成功')
    } else if (result.rate_limited) {
      toast.warning('请求被限流')
    } else {
      toast.error(result.message || '合成失败')
    }
  } catch (err: any) {
    console.error('TTS Playground 合成失败:', err)
    toast.error(err.response?.data?.message || err.message || '合成失败')
    response.value = {
      success: false,
      message: err.response?.data?.message || err.message || '合成失败',
      char_count: request.value.text.length,
      rate_limited: false
    }
  } finally {
    synthesizing.value = false
  }
}
</script>

<style scoped>
.tts-playground-page {
  min-height: 100vh;
}
</style>

