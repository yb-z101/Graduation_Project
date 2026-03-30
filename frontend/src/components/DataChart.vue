<template>
  <div class="chart-wrapper">
    <div ref="echartsRef" v-show="chartLibId === 'echarts'" class="chart-container"></div>
    <div ref="g2Ref" v-show="chartLibId === 'antv-g2'" class="chart-container"></div>
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
  }
})

const echartsRef = ref(null)
const g2Ref = ref(null)
let echartsInstance = null
let g2Chart = null

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
        height: 400
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

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

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
</script>

<style scoped>
.chart-wrapper {
  width: 100%;
}

.chart-container {
  width: 100%;
  height: 400px;
  margin-top: 10px;
  background: #fff;
  border-radius: 4px;
}
</style>
