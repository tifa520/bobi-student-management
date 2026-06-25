// 声明 Vue 文件模块
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// 声明全局属性
declare module '@vue/runtime-core' {
  export interface ComponentCustomProperties {
    $formatDate: (date: string | Date, format?: string) => string
    $formatMoney: (amount: number, showSymbol?: boolean) => string
    $maskPhone: (phone: string) => string
    $maskName: (name: string) => string
    $getStatusText: (status: string, type?: string) => string
    $appVersion: string
    $isDev: boolean
    $isProd: boolean
    $apiBase: string
  }
}

export {}