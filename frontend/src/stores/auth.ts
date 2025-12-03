/**
 * 认证状态管理
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'

interface User {
  id: number
  username: string
  email: string
  avatar?: string
}

export const useAuthStore = defineStore('auth', () => {
  const router = useRouter()
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const isAuthenticated = ref(!!token.value)
  
  const login = async (username: string, password: string) => {
    try {
      // OAuth2PasswordRequestForm 需要 form-data 格式
      const formData = new URLSearchParams()
      formData.append('username', username)
      formData.append('password', password)
      
      const response = await api.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      })
      
      // 统一响应格式：response.data 已经是 data 字段的内容
      // 登录API返回: {access_token, token_type}
      const loginData = response.data
      token.value = loginData.access_token || loginData.token?.access_token
      if (token.value) {
        localStorage.setItem('token', token.value)
        isAuthenticated.value = true
        
        // 获取用户信息
        await fetchUser()
        
        return true
      } else {
        throw new Error('登录响应格式错误：缺少access_token')
      }
    } catch (error: any) {
      console.error('Login failed:', error)
      // 返回错误信息以便前端显示
      // 统一响应格式的错误已经在API拦截器中处理
      if (error.message) {
        throw new Error(error.message)
      }
      if (error.response?.data?.error_message) {
        throw new Error(error.response.data.error_message)
      }
      if (error.response?.data?.detail) {
        throw new Error(typeof error.response.data.detail === 'string' 
          ? error.response.data.detail 
          : error.response.data.detail.error_message || '登录失败')
      }
      throw error
    }
  }
  
  const logout = () => {
    user.value = null
    token.value = null
    isAuthenticated.value = false
    localStorage.removeItem('token')
    router.push('/login')
  }
  
  const fetchUser = async () => {
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
    } catch (error) {
      console.error('Fetch user failed:', error)
      logout()
    }
  }
  
  // 初始化时获取用户信息
  if (isAuthenticated.value) {
    fetchUser()
  }
  
  return {
    user,
    token,
    isAuthenticated,
    login,
    logout,
    fetchUser
  }
})

