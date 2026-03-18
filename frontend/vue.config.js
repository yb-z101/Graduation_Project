module.exports = {
  devServer: {
    port: 8083,
    // 关闭 webpack-dev-server 的全屏 overlay（开发期偶发 ResizeObserver 警告会被误当成 runtime error 弹窗）
    // Vue CLI 5 使用 webpack-dev-server v4：用 client.overlay 关闭
    // 同时保留 overlay=false 兼容旧写法，确保不再红屏遮罩。
    client: {
      overlay: {
        errors: false,
        warnings: false,
        runtimeErrors: false
      }
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
}