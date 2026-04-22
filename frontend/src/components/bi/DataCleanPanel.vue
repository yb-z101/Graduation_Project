<template>
  <div class="data-clean-panel">
    <div v-if="!profileData" class="profile-loading">
      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading" :size="32"><Loading /></el-icon>
        <p>正在分析数据质量...</p>
      </div>
      <div v-else class="no-session">
        <h3>请先上传数据文件</h3>
        <p>上传文件后即可查看数据质量报告并执行清洗操作</p>
      </div>
    </div>
    <div v-else class="profile-content">
      <div class="quality-overview">
        <div class="score-card">
          <div class="score-ring" :style="{'--score': profileData.overall_quality_score}">
            <span class="score-value">{{ profileData.overall_quality_score }}</span>
          </div>
          <div class="score-label">数据质量评分</div>
        </div>
        <div class="stat-cards">
          <div class="stat-card"><div class="stat-info"><span class="stat-value">{{ profileData.total_rows }}</span><span class="stat-label">总行数</span></div></div>
          <div class="stat-card"><div class="stat-info"><span class="stat-value">{{ profileData.total_columns }}</span><span class="stat-label">总列数</span></div></div>
          <div class="stat-card"><div class="stat-info"><span class="stat-value">{{ profileData.total_null_cells }}</span><span class="stat-label">空值数</span></div></div>
          <div class="stat-card"><div class="stat-info"><span class="stat-value">{{ profileData.duplicate_rows }}</span><span class="stat-label">重复行</span></div></div>
        </div>
      </div>
      <div class="column-detail-section">
        <h4 class="section-title">列详情</h4>
        <el-table :data="profileData.column_profiles" size="small" border stripe max-height="280">
          <el-table-column prop="name" label="列名" min-width="100" show-overflow-tooltip />
          <el-table-column prop="dtype" label="类型" width="100" />
          <el-table-column label="空值" width="120">
            <template #default="{ row }">
              <span>{{ row.null_count }}</span>
              <el-progress v-if="row.null_percentage > 0" :percentage="row.null_percentage" :stroke-width="6" :color="row.null_percentage > 30 ? '#F5222D' : row.null_percentage > 10 ? '#FAAD14' : '#52C41A'" style="width:80px;display:inline-block;margin-left:6px;" />
            </template>
          </el-table-column>
          <el-table-column prop="unique_count" label="唯一值" width="80" />
          <el-table-column label="统计" min-width="160">
            <template #default="{ row }">
              <span v-if="row.mean !== undefined" style="font-size:11px;color:#869099;">Min:{{ row.min }} Max:{{ row.max }} Mean:{{ row.mean }}</span>
              <span v-else-if="row.top_values" style="font-size:11px;">
                <el-tag v-for="(tv, i) in row.top_values.slice(0, 2)" :key="i" size="small" type="info" style="margin-right:4px;">{{ Object.keys(tv)[0] }}:{{ Object.values(tv)[0] }}</el-tag>
              </span>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div class="clean-actions-section">
        <h4 class="section-title">快速清洗</h4>
        <div class="quick-actions">
          <el-button type="primary" :disabled="cleaning || profileData.total_null_cells === 0" @click="handleQuickClean('删除所有包含空值的行')">删除空值行</el-button>
          <el-button type="primary" :disabled="cleaning || profileData.duplicate_rows === 0" @click="handleQuickClean('删除所有重复行')">删除重复行</el-button>
          <el-button type="primary" :disabled="cleaning || profileData.total_null_cells === 0" @click="handleQuickClean('用各列的均值填充数值列的空值，用众数填充分类列的空值')">填充空值</el-button>
          <el-button type="warning" :disabled="cleaning" @click="handleQuickClean('将所有文本列转为小写并去除首尾空格')">文本标准化</el-button>
        </div>
        <div class="custom-clean">
          <h4 class="section-title">自定义清洗</h4>
          <div class="custom-input-row">
            <el-input v-model="customInstruction" placeholder="输入清洗指令，如：删除年龄小于0的行..." :disabled="cleaning" @keydown.enter="handleCustomClean" clearable />
            <el-button type="primary" :loading="cleaning" :disabled="!customInstruction.trim()" @click="handleCustomClean">AI 清洗</el-button>
          </div>
        </div>
      </div>
      <div v-if="cleanResults.length > 0" class="clean-results-section">
        <h4 class="section-title">清洗记录</h4>
        <div v-for="(result, idx) in cleanResults" :key="idx" class="result-item" :class="result.success ? 'success' : 'error'">
          <span>#{{ idx + 1 }} {{ result.instruction }}</span>
          <el-tag :type="result.success ? 'success' : 'danger'" size="small" style="margin-left:8px;">{{ result.success ? '成功' : '失败' }}</el-tag>
          <span v-if="result.success" style="font-size:12px;color:#869099;margin-left:8px;">行数: {{ result.rowCountBefore }} -> {{ result.rowCountAfter }}</span>
          <span v-else style="font-size:12px;color:#F5222D;margin-left:8px;">{{ result.error }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { sessionService } from '../../api/services'

const props = defineProps({ sessionId: { type: String, default: '' } })
const emit = defineEmits(['clean-completed'])

const profileData = ref(null)
const loading = ref(false)
const cleaning = ref(false)
const customInstruction = ref('')
const cleanResults = ref([])

const loadProfile = async () => {
  if (!props.sessionId) { profileData.value = null; return }
  loading.value = true
  try {
    const res = await sessionService.getDataProfile(props.sessionId)
    if (res.status === 'ok') { profileData.value = res }
    else { ElMessage.error('获取数据质量报告失败') }
  } catch (e) { ElMessage.error('获取数据质量报告失败') }
  finally { loading.value = false }
}

const handleQuickClean = (instruction) => { customInstruction.value = instruction; handleCustomClean() }

const handleCustomClean = async () => {
  const instruction = customInstruction.value.trim()
  if (!instruction || !props.sessionId) return
  cleaning.value = true
  const rowCountBefore = profileData.value?.total_rows || 0
  try {
    const res = await sessionService.cleanSessionData(props.sessionId, instruction)
    const rowCountAfter = res.row_count_after
    cleanResults.value.unshift({ instruction, success: true, rowCountBefore, rowCountAfter })
    ElMessage.success(`清洗完成：${rowCountBefore} -> ${rowCountAfter} 行`)
    customInstruction.value = ''
    await loadProfile()
    emit('clean-completed', { sessionId: props.sessionId, preview: res.preview, columns: res.columns, rowCountAfter })
  } catch (e) {
    const errMsg = e?.response?.data?.detail || e?.message || '清洗失败'
    cleanResults.value.unshift({ instruction, success: false, error: errMsg })
    ElMessage.error('清洗失败：' + errMsg)
  } finally { cleaning.value = false }
}

watch(() => props.sessionId, (v) => { if (v) loadProfile(); else { profileData.value = null; cleanResults.value = [] } }, { immediate: true })
defineExpose({ loadProfile })
</script>

<style lang="less" scoped>
.data-clean-panel { height: 100%; overflow-y: auto; padding: 20px; background: #F8F9FA;
  .profile-loading { height: 100%; display: flex; align-items: center; justify-content: center;
    .loading-state { display: flex; flex-direction: column; align-items: center; gap: 12px; color: #869099; p { margin: 0; } }
    .no-session { text-align: center; color: #869099; h3 { margin: 0 0 8px; color: #1D2129; } p { margin: 0; font-size: 13px; } }
  }
  .profile-content {
    .section-title { font-size: 14px; font-weight: 600; color: #1D2129; margin: 0 0 12px; padding-left: 8px; border-left: 3px solid #6B5CE8; }
    .quality-overview { display: flex; gap: 20px; margin-bottom: 24px; padding: 20px; background: #FFF; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
      .score-card { display: flex; flex-direction: column; align-items: center; min-width: 120px;
        .score-ring { width: 80px; height: 80px; border-radius: 50%; background: conic-gradient(#6B5CE8 calc(var(--score) * 1%), #E5E6EB calc(var(--score) * 1%)); display: flex; align-items: center; justify-content: center; position: relative;
          &::before { content: ''; position: absolute; width: 60px; height: 60px; border-radius: 50%; background: #FFF; }
          .score-value { position: relative; z-index: 1; font-size: 22px; font-weight: 700; color: #6B5CE8; }
        }
        .score-label { margin-top: 8px; font-size: 12px; color: #869099; }
      }
      .stat-cards { flex: 1; display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;
        .stat-card { padding: 12px 16px; background: #F8F9FA; border-radius: 8px; border: 1px solid #E5E6EB;
          .stat-info { display: flex; flex-direction: column; .stat-value { font-size: 18px; font-weight: 700; color: #1D2129; } .stat-label { font-size: 12px; color: #869099; } }
        }
      }
    }
    .column-detail-section { margin-bottom: 24px; }
    .clean-actions-section { margin-bottom: 24px;
      .quick-actions { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }
      .custom-clean { .custom-input-row { display: flex; gap: 10px; :deep(.el-input) { flex: 1; } } }
    }
    .clean-results-section {
      .result-item { padding: 10px 14px; border-radius: 8px; border: 1px solid #E5E6EB; background: #FFF; margin-bottom: 8px; font-size: 13px;
        &.success { border-left: 3px solid #52C41A; }
        &.error { border-left: 3px solid #F5222D; }
      }
    }
  }
}
</style>
