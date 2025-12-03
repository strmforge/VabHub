/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

/**
 * 前端环境变量类型声明
 * RELEASE-1 R2-2 实现
 * 
 * 配置方式：
 * - 本地开发：创建 .env.local 文件
 * - Docker 部署：通过 --build-arg 或 environment 传入
 */
interface ImportMetaEnv {
  /** API 基础 URL */
  readonly VITE_API_BASE_URL: string
  
  /** 开发模式标识 */
  readonly VITE_DEV_MODE?: string
  
  /** Demo 模式提示文案（可选） */
  readonly VITE_APP_DEMO_HINT?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
