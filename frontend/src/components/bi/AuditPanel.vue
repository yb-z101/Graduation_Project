<template>
  <div class="audit-panel">
    <div class="stats-row">
      <div class="stat-card" v-for="(stat, key) in statsData" :key="key">
        <div class="stat-label">{{ STAT_LABELS[key] || key }}</div>
        <div class="stat-value">{{ stat }}</div>
      </div>
    </div>
    <div class="filter-bar">
      <el-input v-model="filters.keyword" placeholder="搜索关键词..." clearable size="default" style="width:180px;" />
      <el-select v-model="filters.operation_type" placeholder="操作类型" clearable size="default" style="width:130px;">
        <el-option label="全部" value="" /><el-option label="上传文件" value="FILE_UPLOAD" /><el-option label="查询分析" value="CHAT_SEND" /><el-option label="图表生成" value="CHART_GENERATE" /><el-option label="数据清洗" value="DATA_CLEAN" />
      </el-select>
      <el-select v-model="filters.status" placeholder="状态" clearable size="default" style="width:100px;">
        <el-option label="全部" value="" /><el-option label="成功" value="success" /><el-option label="失败" value="error" />
      </el-select>
      <el-button type="primary" @click="loadLogs">查询</el-button>
      <el-button @click="handleExport">导出</el-button>
    </div>
    <el-table :data="logList" stripe border size="small" max-height="420" v-loading="loading">
      <el-table-column prop="timestamp" label="时间" width="160" />
      <el-table-column prop="operation_name" label="操作类型" width="120" />
      <el-table-column prop="dataset_name" label="数据集" width="140" show-overflow-tooltip />
      <el-table-column prop="query_content" label="查询内容" min-width="200" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }"><el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">{{ row.status === 'success' ? '成功' : '失败' }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="ip_address" label="IP" width="130" show-overflow-tooltip />
    </el-table>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { auditService } from '../../api/services'

const STAT_LABELS = { total_logs: '总日志数', success_count: '成功数', error_count: '失败数', today_count: '今日操作', active_sessions: '活跃会话', active_datasets: '活跃数据集' }
const loading = ref(false)
const logList = ref([])
const statsData = ref({})
const filters = reactive({ keyword: '', operation_type: '', status: '' })

const loadStats = async () => { try { const res = await auditService.getStats(7); if (res.status === 'ok' && res.data) statsData.value = res.data } catch (e) { console.warn('加载统计失败', e) } }
const loadLogs = async () => {
  loading.value = true
  try { const params = { page: 1, page_size: 20 }; if (filters.keyword) params.keyword = filters.keyword; if (filters.operation_type) params.operation_type = filters.operation_type; if (filters.status) params.status = filters.status; const res = await auditService.getLogs(params); if (res.status === 'ok' && res.data) { logList.value = res.data.logs || [] } } catch { ElMessage.error('加载审计日志失败') }
  finally { loading.value = false }
}
const handleExport = async () => {
  try { const res = await auditService.exportLogs('csv'); const blob = new Blob([res], { type: 'text/csv;charset=utf-8' }); const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = `audit_logs_${new Date().toISOString().slice(0, 10)}.csv`; link.click(); URL.revokeObjectURL(url); ElMessage.success('导出成功') } catch { ElMessage.error('导出失败') }
}
onMounted(() => { loadStats(); loadLogs() })
</script>

<style lang="less" scoped>
.audit-panel { height: 100%; overflow-y: auto; padding: 16px; background: #F8F9FA;
  .stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 14px;
    .stat-card { background: #FFF; border-radius: 8px; padding: 12px; text-align: center; border: 1px solid #E5E6EB; .stat-label { font-size: 11px; color: #869099; margin-bottom: 4px; } .stat-value { font-size: 20px; font-weight: 700; color: #1D2129; } }
  }
  .filter-bar { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
}
</style>
