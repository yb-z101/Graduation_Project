<template>
  <div class="dashboard-page">
    <div class="dashboard-header">
      <h1>📌 我的看板</h1>
      <div class="header-actions">
        <el-button type="primary" @click="showExportDialog = true" :disabled="pinnedCharts.length === 0">
          导出全部
        </el-button>
        <el-button @click="handleClearAll" :disabled="pinnedCharts.length === 0" type="danger" plain>
          清空
        </el-button>
      </div>
    </div>

    <div v-if="pinnedCharts.length === 0" class="empty-state">
      <div class="empty-icon">📊</div>
      <h3>看板是空的</h3>
      <p>在分析结果中点击图表右上角的📌图标，将喜欢的图表保存到这里</p>
      <el-button type="primary" @click="$router.push('/')">开始分析</el-button>
    </div>

    <div v-else class="charts-grid">
      <div
        v-for="chart in pinnedCharts"
        :key="chart.chartId"
        class="chart-card"
      >
        <div class="card-header">
          <span class="card-title">{{ chart.title }}</span>
          <div class="card-actions">
            <el-button size="small" text type="primary" @click="viewOriginalSession(chart)">
              来源
            </el-button>
            <el-button size="small" text type="danger" @click="removeChart(chart.chartId)">
              ✕
            </el-button>
          </div>
        </div>
        <div class="card-body">
          <DataChart
            :option="chart.option"
            :chart-lib-id="chart.chartLibId"
            :chart-id="chart.chartId"
          />
        </div>
        <div class="card-footer">
          <span class="pin-time">{{ formatTime(chart.pinnedAt) }}</span>
        </div>
      </div>
    </div>

    <el-dialog v-model="showExportDialog" title="导出看板" width="400px">
      <div class="export-options">
        <p style="font-size:14px; color:#1D2129; margin-bottom:16px;">将看板中的所有图表导出为长图</p>
      </div>
      <template #footer>
        <el-button @click="showExportDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmExport" :loading="exporting">
          导出长图
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import DataChart from '@/components/DataChart.vue'

const router = useRouter()
const pinnedCharts = ref([])
const showExportDialog = ref(false)
const exporting = ref(false)

onMounted(() => {
  loadPinnedCharts()
})

function loadPinnedCharts() {
  pinnedCharts.value = JSON.parse(localStorage.getItem('pinnedCharts') || '[]')
}

function removeChart(chartId) {
  ElMessageBox.confirm('确定从看板移除此图表吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    pinnedCharts.value = pinnedCharts.value.filter(c => c.chartId !== chartId)
    localStorage.setItem('pinnedCharts', JSON.stringify(pinnedCharts.value))
    ElMessage.success('已移除')
  })
}

function handleClearAll() {
  ElMessageBox.confirm('确定清空整个看板吗？此操作不可恢复！', '警告', {
    confirmButtonText: '确定清空',
    cancelButtonText: '取消',
    type: 'error'
  }).then(() => {
    pinnedCharts.value = []
    localStorage.setItem('pinnedCharts', JSON.stringify([]))
    ElMessage.success('看板已清空')
  })
}

function viewOriginalSession(chart) {
  if (chart.sessionId) {
    router.push({ path: '/', query: { session: chart.sessionId } })
  } else {
    ElMessage.warning('该图表没有关联的会话信息')
  }
}

async function confirmExport() {
  exporting.value = true
  try {
    await exportAsLongImage()
    showExportDialog.value = false
    ElMessage.success('导出成功！')
  } catch (error) {
    ElMessage.error('导出失败：' + error.message)
  } finally {
    exporting.value = false
  }
}

async function exportAsLongImage() {
  const { default: html2canvas } = await import('html2canvas')

  const container = document.createElement('div')
  container.style.width = '1100px'
  container.style.background = '#fff'
  container.style.padding = '40px'
  container.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'

  let html = `
    <div style="text-align:center; margin-bottom:36px;">
      <h1 style="color:#6B5CE8; margin-bottom:8px; font-size:26px;">📊 智析数据分析看板</h1>
      <p style="color:#869099; font-size:14px;">生成时间：${new Date().toLocaleString('zh-CN')}</p>
    </div>
  `

  pinnedCharts.value.forEach((chart, index) => {
    html += `
      <div style="margin-bottom:28px; padding:20px; border:1px solid #E5E6EB; border-radius:12px; background:#fafbfc;">
        <h3 style="color:#1D2129; margin-bottom:14px; font-size:15px;">${index + 1}. ${chart.title}</h3>
        <img src="${chart.screenshot}" style="width:100%; border-radius:8px; border:1px solid #eee;" />
        <p style="color:#869099; font-size:12px; margin-top:10px;">保存于 ${formatTime(chart.pinnedAt)}</p>
      </div>
    `
  })

  container.innerHTML = html
  document.body.appendChild(container)

  try {
    const canvas = await html2canvas(container, {
      scale: 2,
      useCORS: true,
      backgroundColor: '#ffffff'
    })

    const link = document.createElement('a')
    link.download = `智析看板_${new Date().toISOString().slice(0, 10)}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()
  } finally {
    document.body.removeChild(container)
  }
}

function formatTime(isoString) {
  return new Date(isoString).toLocaleString('zh-CN')
}
</script>

<style scoped>
.dashboard-page {
  min-height: calc(100vh - 48px);
  background: #F5F7FA;
  padding: 24px;
  overflow-y: auto;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 20px 28px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.dashboard-header h1 {
  margin: 0;
  font-size: 22px;
  color: #1D2129;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.empty-state {
  text-align: center;
  padding: 100px 20px;
  color: #869099;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 18px;
  color: #1D2129;
  margin: 0 0 8px;
}

.empty-state p {
  font-size: 14px;
  margin: 0 0 24px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(460px, 1fr));
  gap: 20px;
  align-content: start;
}

.chart-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.chart-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafbfc;
}

.card-title {
  font-weight: 600;
  color: #1D2129;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 280px;
}

.card-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.card-body {
  padding: 16px;
  min-height: 380px;
  background: #fff;
}

.card-footer {
  padding: 10px 18px;
  border-top: 1px solid #f5f7fa;
  background: #fafbfc;
}

.pin-time {
  font-size: 12px;
  color: #869099;
}

.export-options h4 {
  font-size: 15px;
  color: #1D2129;
  margin: 0 0 14px;
}
</style>
