<template>
  <div class="home">
    <h1>我的毕业设计 - 数据可视化展示</h1>
    <!-- 1. 定义图表容器，必须设置宽高 -->
    <div id="chart" style="width: 800px; height: 500px; margin: 20px auto;"></div>
  </div>
</template>

<script setup>
// 2. 引入 ECharts
import * as echarts from 'echarts'
import { onMounted } from 'vue'

// 3. 页面挂载后初始化图表（Vue 3 组合式API）
onMounted(() => {
  // 获取图表容器
  const chartDom = document.getElementById('chart')
  // 初始化 ECharts 实例
  const myChart = echarts.init(chartDom)
  
  // 4. 配置图表选项（以柱状图为例，毕设常用）
  const option = {
    // 图表标题
    title: {
      text: '2025年XX数据统计',
      left: 'center'
    },
    // 提示框
    tooltip: {
      trigger: 'axis'
    },
    // 图例
    legend: {
      data: ['销售额', '用户数'],
      bottom: 0
    },
    // X轴
    xAxis: {
      type: 'category',
      data: ['1月', '2月', '3月', '4月', '5月', '6月']
    },
    // Y轴
    yAxis: {
      type: 'value'
    },
    // 数据系列
    series: [
      {
        name: '销售额',
        type: 'bar',
        data: [120, 200, 150, 80, 70, 110],
        itemStyle: { color: '#42b983' } // Vue 主题色
      },
      {
        name: '用户数',
        type: 'line', // 折线图
        data: [50, 80, 60, 40, 30, 55],
        itemStyle: { color: '#e6a23c' }
      }
    ]
  }

  // 5. 渲染图表
  myChart.setOption(option)

  // 可选：适配窗口大小变化（图表自适应）
  window.addEventListener('resize', () => {
    myChart.resize()
  })
})
</script>

<style scoped>
.home {
  text-align: center;
  margin-top: 50px;
}
h1 {
  color: #42b983;
}
</style>