<template>
  <v-app>
    <v-main class="onboarding-page">
      <v-container class="fill-height" fluid>
        <v-row justify="center" align="center">
          <v-col cols="12" sm="10" md="8" lg="6">
            <v-card class="pa-4" elevation="8">
              <!-- 标题 -->
              <v-card-title class="text-center text-h4 mb-4">
                <v-icon size="48" color="primary" class="mr-2">mdi-rocket-launch</v-icon>
                欢迎使用 VabHub
              </v-card-title>
              <v-card-subtitle class="text-center mb-6">
                让我们完成一些基础设置
              </v-card-subtitle>

              <!-- 步骤指示器 -->
              <v-stepper v-model="currentStep" alt-labels class="elevation-0">
                <v-stepper-header>
                  <v-stepper-item
                    :complete="currentStep > 1"
                    :value="1"
                    title="语言时区"
                    icon="mdi-translate"
                  />
                  <v-divider />
                  <v-stepper-item
                    :complete="currentStep > 2"
                    :value="2"
                    title="管理员账号"
                    icon="mdi-account-key"
                  />
                  <v-divider />
                  <v-stepper-item
                    :complete="currentStep > 3"
                    :value="3"
                    title="存储路径"
                    icon="mdi-folder-cog"
                  />
                  <v-divider />
                  <v-stepper-item
                    :value="4"
                    title="完成"
                    icon="mdi-check-circle"
                  />
                </v-stepper-header>

                <v-stepper-window>
                  <!-- Step 1: 语言和时区 -->
                  <v-stepper-window-item :value="1">
                    <v-card-text>
                      <h3 class="text-h6 mb-4">选择语言和时区</h3>
                      <v-select
                        v-model="settings.language"
                        :items="languageOptions"
                        label="界面语言"
                        variant="outlined"
                        class="mb-4"
                      />
                      <v-select
                        v-model="settings.timezone"
                        :items="timezoneOptions"
                        label="时区"
                        variant="outlined"
                      />
                    </v-card-text>
                  </v-stepper-window-item>

                  <!-- Step 2: 管理员账号 -->
                  <v-stepper-window-item :value="2">
                    <v-card-text>
                      <h3 class="text-h6 mb-4">创建管理员账号</h3>
                      <v-alert type="info" variant="tonal" class="mb-4">
                        如果系统已有用户，可以跳过此步骤
                      </v-alert>
                      <v-text-field
                        v-model="settings.adminUsername"
                        label="用户名"
                        variant="outlined"
                        class="mb-4"
                        prepend-inner-icon="mdi-account"
                      />
                      <v-text-field
                        v-model="settings.adminEmail"
                        label="邮箱"
                        type="email"
                        variant="outlined"
                        class="mb-4"
                        prepend-inner-icon="mdi-email"
                      />
                      <v-text-field
                        v-model="settings.adminPassword"
                        label="密码"
                        :type="showPassword ? 'text' : 'password'"
                        variant="outlined"
                        prepend-inner-icon="mdi-lock"
                        :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                        @click:append-inner="showPassword = !showPassword"
                      />
                    </v-card-text>
                  </v-stepper-window-item>

                  <!-- Step 3: 存储路径 -->
                  <v-stepper-window-item :value="3">
                    <v-card-text>
                      <h3 class="text-h6 mb-4">配置存储路径</h3>
                      <v-alert type="info" variant="tonal" class="mb-4">
                        这些路径用于存储媒体文件，可以稍后在设置中修改
                      </v-alert>
                      <v-text-field
                        v-model="settings.ebookLibraryRoot"
                        label="电子书/小说库路径"
                        variant="outlined"
                        class="mb-4"
                        prepend-inner-icon="mdi-book-open-page-variant"
                        hint="例如: /data/novels 或 ./data/ebooks"
                        persistent-hint
                      />
                      <v-text-field
                        v-model="settings.comicLibraryRoot"
                        label="漫画库路径"
                        variant="outlined"
                        class="mb-4"
                        prepend-inner-icon="mdi-book-open-variant"
                        hint="例如: /data/comics"
                        persistent-hint
                      />
                      <v-text-field
                        v-model="settings.musicLibraryRoot"
                        label="音乐库路径"
                        variant="outlined"
                        class="mb-4"
                        prepend-inner-icon="mdi-music"
                        hint="例如: /data/music"
                        persistent-hint
                      />
                      <v-text-field
                        v-model="settings.ttsOutputRoot"
                        label="TTS 输出路径"
                        variant="outlined"
                        prepend-inner-icon="mdi-text-to-speech"
                        hint="TTS 生成的音频文件存储位置"
                        persistent-hint
                      />
                    </v-card-text>
                  </v-stepper-window-item>

                  <!-- Step 4: 完成 -->
                  <v-stepper-window-item :value="4">
                    <v-card-text class="text-center">
                      <v-icon size="80" color="success" class="mb-4">mdi-check-circle</v-icon>
                      <h3 class="text-h5 mb-4">设置完成！</h3>
                      <p class="text-body-1 text-medium-emphasis mb-6">
                        基础配置已完成，你可以开始使用 VabHub 了。
                        更多高级设置可以在"系统控制台"中调整。
                      </p>
                      <v-btn
                        color="primary"
                        size="large"
                        @click="finishOnboarding"
                        :loading="finishing"
                      >
                        开始使用
                      </v-btn>
                    </v-card-text>
                  </v-stepper-window-item>
                </v-stepper-window>
              </v-stepper>

              <!-- 底部按钮 -->
              <v-card-actions v-if="currentStep < 4" class="justify-space-between px-4">
                <v-btn
                  variant="text"
                  @click="skipOnboarding"
                  :disabled="finishing"
                >
                  跳过设置
                </v-btn>
                <div>
                  <v-btn
                    v-if="currentStep > 1"
                    variant="outlined"
                    class="mr-2"
                    @click="currentStep--"
                  >
                    上一步
                  </v-btn>
                  <v-btn
                    color="primary"
                    @click="nextStep"
                  >
                    {{ currentStep === 3 ? '完成设置' : '下一步' }}
                  </v-btn>
                </div>
              </v-card-actions>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { onboardingApi } from '@/services/api'
import api from '@/services/api'
import type { OnboardingSettings } from '@/types/onboarding'

const router = useRouter()
const toast = useToast()

const currentStep = ref(1)
const showPassword = ref(false)
const finishing = ref(false)

const settings = reactive<OnboardingSettings>({
  language: 'zh-CN',
  timezone: 'Asia/Shanghai',
  adminUsername: '',
  adminPassword: '',
  adminEmail: '',
  ebookLibraryRoot: './data/ebooks',
  comicLibraryRoot: './data/library/comics',
  musicLibraryRoot: './data/library/music',
  ttsOutputRoot: './data/tts_output'
})

const languageOptions = [
  { title: '简体中文', value: 'zh-CN' },
  { title: 'English', value: 'en-US' }
]

const timezoneOptions = [
  { title: '(UTC+8) 中国标准时间', value: 'Asia/Shanghai' },
  { title: '(UTC+9) 日本标准时间', value: 'Asia/Tokyo' },
  { title: '(UTC+0) 格林威治时间', value: 'UTC' },
  { title: '(UTC-5) 美国东部时间', value: 'America/New_York' },
  { title: '(UTC-8) 美国太平洋时间', value: 'America/Los_Angeles' }
]

const nextStep = async () => {
  // Step 2: 创建管理员账号
  if (currentStep.value === 2 && settings.adminUsername && settings.adminPassword && settings.adminEmail) {
    try {
      await api.post('/auth/register', {
        username: settings.adminUsername,
        email: settings.adminEmail,
        password: settings.adminPassword
      })
      toast.success('管理员账号创建成功')
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } }; message?: string }
      // 如果用户已存在，继续下一步
      if (e.response?.data?.detail?.includes('已存在') || e.response?.data?.detail?.includes('exist')) {
        toast.info('用户已存在，继续下一步')
      } else {
        toast.error(e.response?.data?.detail || '创建账号失败')
        return
      }
    }
  }
  
  if (currentStep.value < 4) {
    currentStep.value++
  }
}

const finishOnboarding = async () => {
  try {
    finishing.value = true
    await onboardingApi.complete()
    toast.success('欢迎使用 VabHub！')
    router.push('/')
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } }; message?: string }
    toast.error(e.response?.data?.detail || '完成设置失败')
  } finally {
    finishing.value = false
  }
}

const skipOnboarding = async () => {
  try {
    finishing.value = true
    await onboardingApi.skip()
    toast.info('已跳过设置向导')
    router.push('/login')
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } }; message?: string }
    toast.error(e.response?.data?.detail || '跳过失败')
  } finally {
    finishing.value = false
  }
}
</script>

<style scoped lang="scss">
.onboarding-page {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

:deep(.v-stepper) {
  background: transparent;
}
</style>
