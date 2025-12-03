/**
 * API utility for VabHub frontend
 * Implements proper HTTP client with error handling
 */

export interface ApiResponse<T = any> {
  success: boolean
  data: T
  message?: string
}

interface ApiOptions {
  params?: Record<string, any>
  headers?: Record<string, string>
  timeout?: number
}

class ApiClient {
  private baseURL: string
  private defaultTimeout: number = 10000

  constructor(baseURL: string = '/api') {
    this.baseURL = baseURL
  }

  private async request<T>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE',
    url: string,
    data?: any,
    options: ApiOptions = {}
  ): Promise<ApiResponse<T>> {
    // Construct full URL properly
    let fullUrl: string
    if (url.startsWith('/')) {
      fullUrl = `${window.location.origin}${this.baseURL}${url}`
    } else {
      fullUrl = `${window.location.origin}${this.baseURL}/${url}`
    }
    
    // Add query parameters for GET requests
    if (method === 'GET' && options.params) {
      const urlObj = new URL(fullUrl)
      Object.entries(options.params).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
          urlObj.searchParams.append(key, String(value))
        }
      })
      fullUrl = urlObj.toString()
    }

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), options.timeout || this.defaultTimeout)

    try {
      const response = await fetch(fullUrl.toString(), {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        body: method !== 'GET' ? JSON.stringify(data) : undefined,
        signal: controller.signal
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const result: ApiResponse<T> = await response.json()
      return result
    } catch (error) {
      clearTimeout(timeoutId)
      
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new Error('请求超时')
        }
        throw error
      }
      
      throw new Error('未知网络错误')
    }
  }

  async get<T>(url: string, options: ApiOptions = {}): Promise<ApiResponse<T>> {
    return this.request<T>('GET', url, undefined, options)
  }

  async post<T>(url: string, data?: any, options: ApiOptions = {}): Promise<ApiResponse<T>> {
    return this.request<T>('POST', url, data, options)
  }

  async put<T>(url: string, data?: any, options: ApiOptions = {}): Promise<ApiResponse<T>> {
    return this.request<T>('PUT', url, data, options)
  }

  async delete<T>(url: string, options: ApiOptions = {}): Promise<ApiResponse<T>> {
    return this.request<T>('DELETE', url, undefined, options)
  }
}

export const api = new ApiClient()
