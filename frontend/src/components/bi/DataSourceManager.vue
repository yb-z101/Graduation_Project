<template>
  <div class="datasource-manager">
    <div class="toolbar">
      <el-button type="primary" @click="showCreateDialog = true">新增数据源</el-button>
      <el-select v-model="filterType" placeholder="筛选类型" clearable size="default" style="width:140px;" @change="loadList">
        <el-option label="全部" :value="null" /><el-option label="MySQL" :value="1" /><el-option label="PostgreSQL" :value="2" /><el-option label="SQLite" :value="3" />
      </el-select>
    </div>
    <el-table :data="dsList" stripe border size="small" v-loading="loading" max-height="400">
      <el-table-column prop="source_name" label="名称" min-width="120" show-overflow-tooltip />
      <el-table-column prop="source_type" label="类型" width="100">
        <template #default="{ row }"><el-tag size="small">{{ TYPE_MAP[row.source_type] || '未知' }}</el-tag></template>
      </el-table-column>
      <el-table-column label="连接信息" min-width="180">
        <template #default="{ row }"><span style="font-size:12px;color:#4E5969;">{{ row.host }}:{{ row.port }} / {{ row.db_name }}</span></template>
      </el-table-column>
      <el-table-column prop="username" label="用户名" width="90" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" link @click="testConnect(row)">测试连接</el-button>
          <el-button size="small" link @click="viewDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div v-if="!dsList.length && !loading" style="text-align:center;padding:40px 0;color:#869099;">暂无已保存的数据源</div>
    <el-dialog v-model="showCreateDialog" title="新增数据源" width="500px" :close-on-click-modal="false">
      <el-form :model="formData" label-width="90px" size="default">
        <el-form-item label="名称" required><el-input v-model="formData.source_name" placeholder="如：生产数据库" /></el-form-item>
        <el-form-item label="类型" required><el-select v-model="formData.source_type" placeholder="选择类型"><el-option label="MySQL" :value="1" /><el-option label="PostgreSQL" :value="2" /><el-option label="SQLite" :value="3" /></el-select></el-form-item>
        <el-form-item label="主机" required><el-input v-model="formData.host" placeholder="如：127.0.0.1" /></el-form-item>
        <el-form-item label="端口" required><el-input-number v-model="formData.port" :min="1" :max="65535" controls-position="right" style="width:100%" /></el-form-item>
        <el-form-item label="数据库名" required><el-input v-model="formData.db_name" /></el-form-item>
        <el-form-item label="用户名" required><el-input v-model="formData.username" /></el-form-item>
        <el-form-item label="密码" required><el-input v-model="formData.plain_password" type="password" show-password /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showCreateDialog = false">取消</el-button><el-button type="primary" :loading="submitting" @click="handleSubmit">保存</el-button></template>
    </el-dialog>
    <el-dialog v-model="showDetailDialog" title="数据源详情" width="480px">
      <el-descriptions v-if="detailData.id" :column="2" border size="small">
        <el-descriptions-item label="名称">{{ detailData.source_name }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ TYPE_MAP[detailData.source_type] || '未知' }}</el-descriptions-item>
        <el-descriptions-item label="主机">{{ detailData.host }}:{{ detailData.port }}</el-descriptions-item>
        <el-descriptions-item label="数据库">{{ detailData.db_name }}</el-descriptions-item>
      </el-descriptions>
      <template #footer><el-button @click="showDetailDialog = false">关闭</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { datasourceService } from '../../api/services'

const TYPE_MAP = { 1: 'MySQL', 2: 'PostgreSQL', 3: 'SQLite' }
const loading = ref(false)
const submitting = ref(false)
const dsList = ref([])
const filterType = ref(null)
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const detailData = ref({})
const formData = reactive({ source_name: '', source_type: 1, host: '127.0.0.1', port: 3306, db_name: '', username: 'root', plain_password: '' })

const loadList = async () => { loading.value = true; try { const res = await datasourceService.list(filterType.value); dsList.value = Array.isArray(res) ? res : [] } catch { ElMessage.error('加载数据源列表失败') } finally { loading.value = false } }
const handleSubmit = async () => {
  if (!formData.source_name || !formData.host || !formData.db_name) { ElMessage.warning('请填写完整信息'); return }
  submitting.value = true
  try { await datasourceService.create({ ...formData }); ElMessage.success('数据源创建成功'); showCreateDialog.value = false; Object.assign(formData, { source_name: '', source_type: 1, host: '127.0.0.1', port: 3306, db_name: '', username: 'root', plain_password: '' }); loadList() } catch (e) { ElMessage.error(e?.response?.data?.detail || '创建失败') }
  finally { submitting.value = false }
}
const testConnect = async (row) => { try { await datasourceService.testConnect(row.id); ElMessage.success(`${row.source_name} 连接成功`) } catch (e) { ElMessage.error(e?.response?.data?.detail || '连接测试失败') } }
const viewDetail = async (row) => { try { const res = await datasourceService.getDetail(row.id); detailData.value = res; showDetailDialog.value = true } catch { ElMessage.error('获取详情失败') } }
onMounted(() => { loadList() })
</script>

<style lang="less" scoped>
.datasource-manager { height: 100%; overflow-y: auto; padding: 16px; background: #F8F9FA; .toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; } }
</style>
