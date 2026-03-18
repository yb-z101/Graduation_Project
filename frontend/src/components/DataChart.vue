<template>
  <div ref="chartRef" class="chart-container"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  // ECharts 配置项对象
  option: {
    type: Object,
    required: true
  }
})

const chartRef = ref(null)
let chartInstance = null

// 初始化图表
const initChart = () => {
  if (chartRef.value) {
    // 如果实例已存在，先销毁以防内存泄漏
    if (chartInstance) {
      chartInstance.dispose()
    }
    chartInstance = echarts.init(chartRef.value)
    chartInstance.setOption(props.option, true)
  }
}

// 监听窗口大小变化，自适应调整图表
let resizeRaf = 0
const handleResize = () => {
  if (!chartInstance) return
  if (resizeRaf) cancelAnimationFrame(resizeRaf)
  resizeRaf = requestAnimationFrame(() => {
    chartInstance && chartInstance.resize()
    resizeRaf = 0
  })
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  if (resizeRaf) {
    cancelAnimationFrame(resizeRaf)
    resizeRaf = 0
  }
  window.removeEventListener('resize', handleResize)
})

// 监听 option 变化，动态更新图表
watch(
  () => props.option,
  (newOption) => {
    if (chartInstance && newOption) {
      // 用 rAF 合并重绘，降低 ResizeObserver 触发概率
      requestAnimationFrame(() => {
        chartInstance && chartInstance.setOption(newOption, true)
      })
    }
  },
  { deep: true }
)
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 400px; /* 默认高度，可根据需要调整 */
  margin-top: 10px;
  background: #fff;
  border-radius: 4px;
}
</style>