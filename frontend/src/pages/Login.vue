<template>
  <!-- 独立登录页面 -->
  <div class="login-page">
    <!-- 背景装饰 -->
    <div class="login-background">
      <div class="bg-gradient"></div>
      <div class="bg-pattern"></div>
    </div>
    
    <!-- 登录卡片容器 -->
    <div class="login-container">
      <v-card class="login-card" elevation="0">
        <!-- Logo和标题 -->
        <v-card-item class="pa-6 pb-4">
          <div class="d-flex align-center justify-center mb-4">
            <VabHubLogo :size="64" :show-text="false" :glow="true" variant="light" />
          </div>
          <v-card-title class="text-center text-h5 font-weight-bold pa-0">
            VabHub
          </v-card-title>
          <v-card-subtitle class="text-center text-body-2 pa-0 mt-2">
            智能媒体管理平台
          </v-card-subtitle>
        </v-card-item>
        
        <v-divider />
        
        <!-- 登录表单 -->
        <v-card-text class="pa-6">
          <v-form @submit.prevent="handleLogin" ref="loginForm">
            <!-- 用户名 -->
            <v-text-field
              v-model="username"
              label="用户名"
              prepend-inner-icon="mdi-account-outline"
              variant="outlined"
              density="comfortable"
              class="mb-4"
              :rules="[rules.required]"
              autofocus
            />
            
            <!-- 密码 -->
            <v-text-field
              v-model="password"
              label="密码"
              :type="showPassword ? 'text' : 'password'"
              prepend-inner-icon="mdi-lock-outline"
              :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
              @click:append-inner="showPassword = !showPassword"
              variant="outlined"
              density="comfortable"
              class="mb-4"
              :rules="[rules.required]"
            />
            
            <!-- 记住我 -->
            <div class="d-flex align-center justify-space-between mb-6">
              <v-checkbox
                v-model="remember"
                label="记住我"
                density="compact"
                hide-details
              />
              <v-btn
                variant="text"
                size="small"
                class="text-caption"
                disabled
              >
                忘记密码？
              </v-btn>
            </div>
            
            <!-- 错误提示 -->
            <v-alert
              v-if="errorMessage"
              type="error"
              density="compact"
              class="mb-4"
              closable
              @click:close="errorMessage = ''"
            >
              {{ errorMessage }}
            </v-alert>
            
            <!-- 登录按钮 -->
            <v-btn
              type="submit"
              color="primary"
              size="large"
              block
              :loading="loading"
              class="mb-4"
            >
              登录
            </v-btn>
            
            <!-- 注册链接 -->
            <div class="text-center">
              <v-btn
                variant="text"
                size="small"
                class="text-caption"
                disabled
              >
                还没有账号？注册
              </v-btn>
            </div>
          </v-form>
        </v-card-text>
        
        <!-- 特色功能提示 -->
        <v-divider />
        <v-card-text class="pa-4">
          <div class="text-center">
            <div class="text-caption text-medium-emphasis mb-2">✨ VabHub 特色功能</div>
            <div class="d-flex flex-wrap justify-center gap-2">
              <v-chip size="x-small" color="purple" variant="flat">音乐管理</v-chip>
              <v-chip size="x-small" color="orange" variant="flat">AI推荐</v-chip>
              <v-chip size="x-small" color="red" variant="flat">HNR检测</v-chip>
            </div>
          </div>
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import VabHubLogo from '@/components/common/VabHubLogo.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const remember = ref(true)
const showPassword = ref(false)
const loading = ref(false)
const errorMessage = ref('')
const loginForm = ref()

const rules = {
  required: (value: string) => !!value || '此字段为必填项'
}

const handleLogin = async () => {
  // 表单验证
  const { valid } = await loginForm.value?.validate()
  if (!valid) return
  
  errorMessage.value = ''
  loading.value = true
  
  try {
    await authStore.login(username.value, password.value)
    // 登录成功，跳转
    const redirect = (route.query.redirect as string) || '/dashboard'
    router.push(redirect)
  } catch (error: any) {
    // 显示错误信息
    if (error.message) {
      errorMessage.value = error.message
    } else if (error.response?.data?.detail) {
      errorMessage.value = error.response.data.detail
    } else {
      errorMessage.value = '登录失败，请稍后重试'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  width: 100%;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.login-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
  
  .bg-gradient {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, 
      #1a1a2e 0%,
      #16213e 25%,
      #0f3460 50%,
      #16213e 75%,
      #1a1a2e 100%);
  }
  
  .bg-pattern {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: 
      radial-gradient(circle at 20% 30%, rgba(0, 212, 255, 0.08) 0%, transparent 50%),
      radial-gradient(circle at 80% 70%, rgba(0, 153, 255, 0.08) 0%, transparent 50%),
      radial-gradient(circle at 50% 50%, rgba(0, 102, 204, 0.05) 0%, transparent 70%);
    opacity: 0.6;
  }
}

.login-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 400px;
  padding: 24px;
}

.login-card {
  backdrop-filter: blur(20px);
  background: rgba(30, 30, 46, 0.85) !important;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.4),
    0 0 0 1px rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  
  // 确保文字清晰可读
  :deep(.v-card-title) {
    color: rgba(255, 255, 255, 0.95);
  }
  
  :deep(.v-card-subtitle) {
    color: rgba(255, 255, 255, 0.7);
  }
  
  // 输入框样式
  :deep(.v-text-field) {
    .v-field {
      background: rgba(255, 255, 255, 0.05);
      border-color: rgba(255, 255, 255, 0.15);
      
      &:hover {
        border-color: rgba(255, 255, 255, 0.25);
      }
      
      &.v-field--focused {
        border-color: rgb(var(--v-theme-primary));
        background: rgba(255, 255, 255, 0.08);
      }
    }
    
    .v-label {
      color: rgba(255, 255, 255, 0.7);
    }
    
    input {
      color: rgba(255, 255, 255, 0.95);
    }
  }
  
  // 复选框样式
  :deep(.v-checkbox) {
    .v-label {
      color: rgba(255, 255, 255, 0.7);
    }
  }
  
  // 按钮样式
  :deep(.v-btn) {
    &.v-btn--variant-text {
      color: rgba(255, 255, 255, 0.6);
      
      &:hover {
        color: rgba(255, 255, 255, 0.9);
      }
    }
  }
  
  // Chip样式
  :deep(.v-chip) {
    opacity: 0.9;
  }
}

// 响应式设计
@media (max-width: 600px) {
  .login-container {
    padding: 16px;
  }
  
  .login-card {
    border-radius: 12px;
  }
}
</style>
