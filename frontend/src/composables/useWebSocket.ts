/**
 * WebSocket Composables
 * 用于管理WebSocket连接和实时更新
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'

export interface WebSocketMessage {
  type: string
  data?: any
  timestamp?: number
}

export interface WebSocketOptions {
  url?: string
  autoConnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
  heartbeatInterval?: number
  topics?: string[]  // 订阅的主题列表
  onMessage?: (message: WebSocketMessage) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Event) => void
}

export function useWebSocket(options: WebSocketOptions = {}) {
  // 构建WebSocket URL
  const getWebSocketUrl = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8092/api/v1'
    
    try {
      // 从baseURL提取host和port
      const url = new URL(baseURL.replace('/api/v1', ''))
      const host = url.hostname
      const port = url.port || (protocol === 'wss:' ? '443' : '80')
      return `${protocol}//${host}:${port}/api/ws/ws`
    } catch {
      // 如果解析失败，使用当前页面的host和默认端口
      const host = window.location.hostname
      const port = window.location.port || '8092'
      return `${protocol}//${host}:${port}/api/ws/ws`
    }
  }

  const {
    url = getWebSocketUrl(),
    autoConnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
    heartbeatInterval = 30000,
    topics = [],
    onMessage,
    onConnect,
    onDisconnect,
    onError
  } = options

  const socket = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const isConnecting = ref(false)
  const reconnectAttempts = ref(0)
  const lastError = ref<string | null>(null)
  const subscribedTopics = ref<string[]>(topics)

  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let heartbeatTimer: ReturnType<typeof setInterval> | null = null

  const connect = () => {
    if (socket.value?.readyState === WebSocket.OPEN) {
      return
    }

    if (isConnecting.value) {
      return
    }

    isConnecting.value = true
    lastError.value = null

    try {
      const ws = new WebSocket(url)
      socket.value = ws

      ws.onopen = () => {
        isConnected.value = true
        isConnecting.value = false
        reconnectAttempts.value = 0
        console.log('[WebSocket] 连接已建立')

        // 启动心跳
        startHeartbeat()

        // 订阅主题
        if (subscribedTopics.value.length > 0) {
          subscribe(subscribedTopics.value)
        }

        if (onConnect) {
          onConnect()
        }
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          
          // 处理心跳
          if (message.type === 'pong') {
            return
          }

          if (onMessage) {
            onMessage(message)
          }
        } catch (error) {
          console.error('[WebSocket] 解析消息失败:', error)
        }
      }

      ws.onerror = (error) => {
        console.error('[WebSocket] 连接错误:', error)
        lastError.value = '连接错误'
        
        if (onError) {
          onError(error)
        }
      }

      ws.onclose = () => {
        isConnected.value = false
        isConnecting.value = false
        console.log('[WebSocket] 连接已关闭')

        stopHeartbeat()

        if (onDisconnect) {
          onDisconnect()
        }

        // 尝试重连
        if (reconnectAttempts.value < maxReconnectAttempts) {
          reconnectAttempts.value++
          console.log(`[WebSocket] 尝试重连 (${reconnectAttempts.value}/${maxReconnectAttempts})...`)
          
          reconnectTimer = setTimeout(() => {
            connect()
          }, reconnectInterval)
        } else {
          console.error('[WebSocket] 达到最大重连次数，停止重连')
        }
      }
    } catch (error) {
      console.error('[WebSocket] 创建连接失败:', error)
      isConnecting.value = false
      lastError.value = '创建连接失败'
    }
  }

  const disconnect = () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }

    stopHeartbeat()

    if (socket.value) {
      socket.value.close()
      socket.value = null
    }

    isConnected.value = false
    isConnecting.value = false
  }

  const send = (message: WebSocketMessage) => {
    if (socket.value?.readyState === WebSocket.OPEN) {
      socket.value.send(JSON.stringify(message))
    } else {
      console.warn('[WebSocket] 连接未建立，无法发送消息')
    }
  }

  const subscribe = (topics: string[]) => {
    subscribedTopics.value = [...new Set([...subscribedTopics.value, ...topics])]
    send({
      type: 'subscribe',
      data: { topics: subscribedTopics.value }
    })
    console.log('[WebSocket] 已订阅主题:', subscribedTopics.value)
  }

  const unsubscribe = (topics: string[]) => {
    subscribedTopics.value = subscribedTopics.value.filter(t => !topics.includes(t))
    send({
      type: 'subscribe',
      data: { topics: subscribedTopics.value }
    })
    console.log('[WebSocket] 已取消订阅主题:', topics)
  }

  const startHeartbeat = () => {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
    }

    heartbeatTimer = setInterval(() => {
      if (isConnected.value) {
        send({
          type: 'ping',
          timestamp: Date.now()
        })
      }
    }, heartbeatInterval)
  }

  const stopHeartbeat = () => {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
  }

  // 自动连接
  if (autoConnect) {
    onMounted(() => {
      connect()
    })
  }

  // 清理
  onUnmounted(() => {
    disconnect()
  })

  return {
    socket,
    isConnected,
    isConnecting,
    reconnectAttempts,
    lastError,
    subscribedTopics,
    connect,
    disconnect,
    send,
    subscribe,
    unsubscribe
  }
}

