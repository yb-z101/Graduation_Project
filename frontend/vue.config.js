module.exports = {
  devServer: {
    port: 8080,
    proxy: {
      '/': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        pathRewrite: {
          '^/': ''
        }
      }
    }
  }
}