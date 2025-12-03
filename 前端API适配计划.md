# 前端API适配计划

## 📋 当前状态

### ✅ 后端已完成
- 所有19个API模块已迁移到统一响应模型
- 统一响应格式：`{success, message, data, timestamp}`
- 错误响应格式：`{success: false, error_code, error_message, details, timestamp}`

### ⚠️ 前端需要更新
- 前端代码仍然使用旧的响应格式（直接使用 `response.data`）
- 需要适配新的统一响应格式（使用 `response.data.data`）
- 需要更新错误处理逻辑

---

## 🎯 更新计划

### 1. 更新API客户端 (`src/services/api.ts`)

**当前问题**：
- 响应拦截器直接返回 `response.data`
- 没有处理统一响应格式

**需要更新**：
- 在响应拦截器中处理统一响应格式
- 自动提取 `data` 字段
- 统一错误处理

### 2. 更新Store文件

**需要更新的Store**：
- `src/stores/auth.ts` - 认证相关
- `src/stores/dashboard.ts` - 仪表盘数据
- `src/stores/search.ts` - 搜索功能

### 3. 更新页面组件

**需要更新的页面**：
- `src/pages/Subscriptions.vue` - 订阅管理
- `src/pages/Downloads.vue` - 下载管理
- `src/pages/Search.vue` - 搜索页面
- `src/pages/Dashboard.vue` - 仪表盘
- 其他使用API的页面

### 4. 更新组件

**需要更新的组件**：
- 所有使用API调用的组件
- 错误处理组件
- 分页组件（适配新的分页格式）

---

## 📝 实施步骤

### 步骤1: 更新API客户端

在 `src/services/api.ts` 中添加统一响应处理：

```typescript
// 响应拦截器
api.interceptors.response.use(
  (response) => {
    // 处理统一响应格式
    if (response.data && typeof response.data === 'object') {
      // 检查是否是统一响应格式
      if ('success' in response.data && 'data' in response.data) {
        // 如果是成功响应，返回data字段
        if (response.data.success) {
          return {
            ...response,
            data: response.data.data
          }
        } else {
          // 如果是错误响应，抛出错误
          const error = new Error(response.data.error_message || '请求失败')
          error.response = response
          return Promise.reject(error)
        }
      }
    }
    return response
  },
  (error) => {
    // 处理错误响应
    if (error.response?.data) {
      const errorData = error.response.data
      // 检查是否是统一错误格式
      if (errorData.error_code && errorData.error_message) {
        error.message = errorData.error_message
        error.errorCode = errorData.error_code
        error.errorDetails = errorData.details
      }
    }
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
      router.push('/login')
    }
    return Promise.reject(error)
  }
)
```

### 步骤2: 更新Store文件

更新所有Store文件，移除直接访问 `response.data.data` 的代码，因为API客户端已经处理了。

### 步骤3: 更新页面组件

更新所有页面组件，确保错误处理正确。

### 步骤4: 测试

测试所有API调用，确保：
- 成功响应正确处理
- 错误响应正确显示
- 分页功能正常工作

---

## 🔍 需要检查的文件

### Store文件
- [ ] `src/stores/auth.ts`
- [ ] `src/stores/dashboard.ts`
- [ ] `src/stores/search.ts`

### 页面文件
- [ ] `src/pages/Subscriptions.vue`
- [ ] `src/pages/Downloads.vue`
- [ ] `src/pages/Search.vue`
- [ ] `src/pages/Dashboard.vue`
- [ ] `src/pages/Sites.vue`
- [ ] `src/pages/Workflows.vue`
- [ ] `src/pages/Notifications.vue`
- [ ] `src/pages/MusicSubscriptions.vue`
- [ ] `src/pages/Calendar.vue`
- [ ] `src/pages/HNRMonitoring.vue`
- [ ] `src/pages/Recommendations.vue`
- [ ] `src/pages/MediaIdentification.vue`
- [ ] `src/pages/CloudStorage.vue`
- [ ] `src/pages/Settings.vue`

### 组件文件
- [ ] 所有使用API调用的组件

---

## ✅ 验收标准

- [ ] 所有API调用正确处理统一响应格式
- [ ] 错误消息正确显示
- [ ] 分页功能正常工作
- [ ] 认证功能正常（登录、登出、获取用户信息）
- [ ] 所有页面功能正常

---

## 📚 参考文档

- `API统一响应模型迁移最终总结.md` - 后端响应格式说明
- `API迁移验证报告.md` - 验证报告

---

**创建时间**: 2025-01-XX  
**状态**: 待实施

