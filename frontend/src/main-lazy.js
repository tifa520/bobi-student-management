/**
 * 懒加载版本的 main.js
 * 适用于首屏加载优化
 */

// 异步加载 Element Plus
async function loadElementPlus() {
  const [ElementPlus, zhCn, icons] = await Promise.all([
    import('element-plus'),
    import('element-plus/dist/locale/zh-cn.mjs'),
    import('@element-plus/icons-vue')
  ])
  return { ElementPlus: ElementPlus.default, zhCn: zhCn.default, icons: icons.default }
}

// 异步加载样式
async function loadStyles() {
  await import('element-plus/dist/index.css')
  await import('./styles/global.css')
}

// 初始化应用
async function initApp() {
  // 显示加载动画
  const loadingElement = document.createElement('div')
  loadingElement.innerHTML = '<div style="display:flex;justify-content:center;align-items:center;height:100vh">加载中...</div>'
  document.body.appendChild(loadingElement)
  
  // 并行加载资源
  const [{ createApp }, { createPinia }, { default: App }, { default: router }] = await Promise.all([
    import('vue'),
    import('pinia'),
    import('./App.vue'),
    import('./router'),
    loadElementPlus(),
    loadStyles()
  ])
  
  // 移除加载动画
  loadingElement.remove()
  
  const app = createApp(App.default || App)
  const pinia = createPinia()
  
  // 注册图标
  const icons = await import('@element-plus/icons-vue')
  for (const [key, component] of Object.entries(icons)) {
    app.component(key, component)
  }
  
  app.use(pinia)
  app.use(router.default || router)
  
  const { ElementPlus, zhCn } = await loadElementPlus()
  app.use(ElementPlus, { locale: zhCn })
  
  app.mount('#app')
}

// 启动应用
initApp()