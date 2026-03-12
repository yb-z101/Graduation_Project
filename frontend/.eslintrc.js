module.exports = {
  root: true,
  env: {
    node: true,
    // 识别 Vue 3 的 defineProps, defineEmits 等宏
    'vue/setup-compiler-macros': true
  },
  extends: [
    'plugin:vue/vue3-essential',
    'eslint:recommended'
  ],
  parserOptions: {
    parser: '@babel/eslint-parser'
  },
  rules: {
    'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'vue/multi-word-component-names': 'off',
    // 暂时忽略未使用变量的报错，让项目先跑起来
    'no-unused-vars': 'off',
    'vue/no-unused-vars': 'off'
  }
}