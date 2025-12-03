/**
 * Vuetify 3 类型补丁
 * 解决 v-data-table slot 中 item 类型为 unknown 的问题
 */

// 扩展 Vue 的 ComponentCustomProperties
declare module 'vue' {
  interface ComponentCustomProperties {
    // 允许在模板中访问 unknown 类型的属性
  }
}

// 为 Vuetify 的 DataTable slot 提供更宽松的类型
declare module 'vuetify/components' {
  // 这里可以添加更具体的类型定义
}

export {}
