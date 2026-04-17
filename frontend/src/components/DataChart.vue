<template>
  <div class="chart-wrapper">
    <div class="chart-header">
      <span class="chart-title">{{ option?.title?.text || '未命名图表' }}</span>
      <div class="chart-toolbar">
        <button 
          class="chart-btn pin-btn" 
          :class="{ pinned: isPinned }"
          @click="togglePin"
          :title="isPinned ? '已保存到看板' : '保存到我的看板'"
        >
          <span class="btn-icon">📌</span>
          <span class="btn-text">{{ isPinned ? '已钉住' : '钉住' }}</span>
        </button>
        <button class="chart-btn" @click="copyChart" title="复制图表">
          <span class="btn-icon">📋</span>
          <span class="btn-text">复制</span>
        </button>
        <button class="chart-btn" @click="downloadChart" title="下载图表">
          <span class="btn-icon">⬇️</span>
          <span class="btn-text">下载</span>
        </button>
      </div>
    </div>
    <div class="chart-scroll-container">
      <div ref="echartsRef" v-show="chartLibId === 'echarts'" class="chart-container"></div>
      <div ref="g2Ref" v-show="chartLibId === 'antv-g2'" class="chart-container"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { Chart } from '@antv/g2'

const props = defineProps({
  option: {
    type: Object,
    required: true
  },
  chartLibId: {
    type: String,
    default: 'echarts'
  },
  chartId: {
    type: String,
    default: ''
  },
  sessionId: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['pin-chart', 'unpin-chart'])

const echartsRef = ref(null)
const g2Ref = ref(null)
let echartsInstance = null
let g2Chart = null
const isPinned = ref(false)

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
  checkPinnedStatus()
})

function checkPinnedStatus() {
  const pinnedCharts = JSON.parse(localStorage.getItem('pinnedCharts') || '[]')
  const id = props.chartId || `chart-${Date.now()}`
  isPinned.value = pinnedCharts.some(c => c.chartId === id)
}

function togglePin() {
  isPinned.value = !isPinned.value
  const chartData = {
    chartId: props.chartId || `chart-${Date.now()}`,
    title: props.option?.title?.text || '未命名图表',
    option: JSON.parse(JSON.stringify(props.option)),
    chartLibId: props.chartLibId,
    sessionId: props.sessionId,
    pinnedAt: new Date().toISOString(),
    screenshot: getChartImageBase64()
  }

  if (isPinned.value) {
    saveToDashboard(chartData)
    emit('pin-chart', chartData)
  } else {
    removeFromDashboard(props.chartId)
    emit('unpin-chart', props.chartId)
  }
}

function saveToDashboard(chartData) {
  let pinnedCharts = JSON.parse(localStorage.getItem('pinnedCharts') || '[]')
  const existingIndex = pinnedCharts.findIndex(c => c.chartId === chartData.chartId)
  if (existingIndex > -1) {
    pinnedCharts[existingIndex] = chartData
  } else {
    pinnedCharts.unshift(chartData)
  }
  if (pinnedCharts.length > 20) {
    pinnedCharts = pinnedCharts.slice(0, 20)
  }
  localStorage.setItem('pinnedCharts', JSON.stringify(pinnedCharts))
}

function removeFromDashboard(chartId) {
  let pinnedCharts = JSON.parse(localStorage.getItem('pinnedCharts') || '[]')
  pinnedCharts = pinnedCharts.filter(c => c.chartId !== chartId)
  localStorage.setItem('pinnedCharts', JSON.stringify(pinnedCharts))
}

const initECharts = async () => {
  await nextTick()
  if (echartsRef.value) {
    if (echartsInstance) {
      echartsInstance.dispose()
    }
    echartsInstance = echarts.init(echartsRef.value)
    echartsInstance.setOption(props.option, true)
  }
}

const handleEChartsResize = () => {
  if (!echartsInstance) return
  if (resizeRaf) cancelAnimationFrame(resizeRaf)
  resizeRaf = requestAnimationFrame(() => {
    echartsInstance && echartsInstance.resize()
    resizeRaf = 0
  })
}

const convertOptionToG2 = (option) => {
  if (!option) return null
  
  let chartType = 'interval'
  if (option.series && option.series.length > 0) {
    const seriesType = option.series[0].type
    if (seriesType === 'line') chartType = 'line'
    else if (seriesType === 'pie') chartType = 'pie'
    else if (seriesType === 'scatter') chartType = 'point'
  }
  
  let data = []
  let xName = '类别'
  let yName = '数值'
  
  if (option.xAxis && option.xAxis.data && option.series && option.series.length > 0) {
    const xData = option.xAxis.data
    const seriesData = option.series[0].data
    xName = option.xAxis.name || '类别'
    yName = option.series[0].name || '数值'
    
    data = xData.map((x, i) => ({
      [xName]: x,
      [yName]: seriesData[i] !== null && seriesData[i] !== undefined ? seriesData[i] : 0
    }))
  } else if (option.series && option.series.length > 0 && option.series[0].data) {
    data = option.series[0].data
  }
  
  return {
    type: chartType,
    data: data,
    title: option.title?.text || '',
    xField: xName,
    yField: yName
  }
}

const initG2 = async () => {
  await nextTick()
  if (g2Ref.value) {
    if (g2Chart) {
      g2Chart.destroy()
      g2Chart = null
    }
    
    const g2Config = convertOptionToG2(props.option)
    if (!g2Config || !g2Config.data || g2Config.data.length === 0) {
      return
    }
    
    try {
      g2Chart = new Chart({
        container: g2Ref.value,
        autoFit: true,
        height: 450
      })
      
      g2Chart.data(g2Config.data)
      
      if (g2Config.type === 'pie') {
        g2Chart
          .interval()
          .encode('x', g2Config.xField)
          .encode('y', g2Config.yField)
          .encode('color', g2Config.xField)
          .transform({ type: 'stackY' })
          .style('radius', 4)
      } else if (g2Config.type === 'line') {
        g2Chart
          .line()
          .encode('x', g2Config.xField)
          .encode('y', g2Config.yField)
          .encode('shape', 'smooth')
          .style('lineWidth', 3)
          .label({
            text: g2Config.yField,
            style: {
              fill: '#666',
            },
          })
      } else if (g2Config.type === 'point') {
        g2Chart
          .point()
          .encode('x', g2Config.xField)
          .encode('y', g2Config.yField)
          .encode('size', 6)
          .style('fill', '#5470c6')
      } else {
        g2Chart
          .interval()
          .encode('x', g2Config.xField)
          .encode('y', g2Config.yField)
          .style('radius', [4, 4, 0, 0])
          .label({
            text: g2Config.yField,
            position: 'outside',
          })
      }
      
      if (g2Config.title) {
        g2Chart.title({
          text: g2Config.title,
          style: {
            fontSize: 16,
            fontWeight: 'bold'
          }
        })
      }
      
      await g2Chart.render()
    } catch (error) {
      console.error('G2 图表渲染失败:', error)
    }
  }
}

let resizeRaf = 0

const initChart = () => {
  if (props.chartLibId === 'echarts') {
    initECharts()
  } else if (props.chartLibId === 'antv-g2') {
    initG2()
  }
}

const handleResize = () => {
  if (props.chartLibId === 'echarts') {
    handleEChartsResize()
  } else if (props.chartLibId === 'antv-g2' && g2Chart) {
    g2Chart.changeSize()
  }
}

onUnmounted(() => {
  if (echartsInstance) {
    echartsInstance.dispose()
    echartsInstance = null
  }
  if (g2Chart) {
    g2Chart.destroy()
    g2Chart = null
  }
  if (resizeRaf) {
    cancelAnimationFrame(resizeRaf)
    resizeRaf = 0
  }
  window.removeEventListener('resize', handleResize)
})

watch(
  [() => props.option, () => props.chartLibId],
  () => {
    initChart()
  },
  { deep: true, immediate: false }
)

const getChartImageBase64 = () => {
  if (props.chartLibId === 'echarts' && echartsInstance) {
    return echartsInstance.getDataURL({
      type: 'png',
      pixelRatio: 2,
      backgroundColor: '#fff'
    })
  } else if (props.chartLibId === 'antv-g2' && g2Ref.value) {
    const canvas = g2Ref.value.querySelector('canvas')
    if (canvas) {
      return canvas.toDataURL('image/png')
    }
  }
  return null
}

const copyChart = async () => {
  try {
    const base64 = getChartImageBase64()
    if (!base64) {
      alert('图表未渲染完成，无法复制')
      return
    }

    const response = await fetch(base64)
    const blob = await response.blob()
    
    if (navigator.clipboard && window.ClipboardItem) {
      await navigator.clipboard.write([
        new ClipboardItem({
          [blob.type]: blob
        })
      ])
      alert('图表已复制到剪贴板！')
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = base64
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
      alert('图表已复制（Base64格式）')
    }
  } catch (error) {
    console.error('复制图表失败:', error)
    alert('复制失败，请重试')
  }
}

const downloadChart = () => {
  try {
    const base64 = getChartImageBase64()
    if (!base64) {
      alert('图表未渲染完成，无法下载')
      return
    }

    const link = document.createElement('a')
    const chartTitle = props.option?.title?.text || 'chart'
    const fileName = `${chartTitle.replace(/[^\w\u4e00-\u9fa5]/g, '_')}_${Date.now()}.png`
    
    link.href = base64
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } catch (error) {
    console.error('下载图表失败:', error)
    alert('下载失败，请重试')
  }
}
</script>

<style scoped>
.chart-wrapper {
  width: 100%;
  max-width: 100%;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 12px;
}

.chart-toolbar {
  display: flex;
  gap: 6px;
  justify-content: flex-end;
}

.chart-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 13px;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s ease;
}

.chart-btn:hover {
  background: #e2e8f0;
  border-color: #cbd5e1;
  color: #1e293b;
}

.chart-btn:active {
  transform: scale(0.98);
}

.pin-btn.pinned {
  background: #fef3c7;
  border-color: #f59e0b;
  color: #d97706;
}

.pin-btn.pinned:hover {
  background: #fde68a;
}

.btn-icon {
  font-size: 14px;
}

.btn-text {
  font-weight: 500;
}

.chart-scroll-container {
  width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
}

.chart-container {
  width: 900px;
  min-width: 900px;
  height: 450px;
  margin-top: 10px;
  background: #fff;
  border-radius: 4px;
}
</style>
