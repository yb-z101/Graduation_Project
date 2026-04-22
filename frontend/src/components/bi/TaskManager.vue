<template><div class="task-manager"><div class="toolbar"><el-radio-group v-model="statusFilter" size="default" @change="loadTasks"><el-radio-button label="all">全部</el-radio-button><el-radio-button :label="2">成功</el-radio-button><el-radio-button :label="3">失败</el-radio-button></el-radio-group><el-button type="primary" size="default" @click="handleDecision" :loading="decisionLoading" :disabled="!sessionId">AI 决策建议</el-button></div><el-table :data="taskList" stripe border size="small" v-loading="loading" class="task-table" max-height="380"><el-table-column prop="id" label="ID" width="55" /><el-table-column prop="task_name" label="任务名称" min-width="140" show-overflow-tooltip /><el-table-column prop="user_prompt" label="用户提问" min-width="160" show-overflow-tooltip /><el-table-column prop="task_status" label="状态" width="80"><template #default="{ row }"><el-tag size="small">{{ row.task_status === 2 ? "成功" : "失败" }}</el-tag></template></el-table-column><el-table-column prop="create_time" label="创建时间" width="150" /><el-table-column label="操作" width="100" fixed="right"><template #default="{ row }"><el-button size="small" link type="primary" @click="viewTaskDetail(row)">详情</el-button></template></el-table-column></el-table><div v-if="!taskList.length && !loading" class="empty-state"><p>暂无分析任务记录</p></div><el-dialog v-model="showDetailDialog" title="任务详情" width="600px"><div v-if="currentTask.id"><p>任务名称: {{ currentTask.task_name }}</p><p>状态: {{ currentTask.task_status === 2 ? "成功" : "失败" }}</p><p>创建时间: {{ currentTask.create_time }}</p></div><template #footer><el-button @click="showDetailDialog = false">关闭</el-button></template></el-dialog><el-dialog v-model="showDecisionDialog" title="AI 决策建议" width="560px"><div v-if="decisionLoading" style="padding:40px;text-align:center;color:#869099;"><p>正在分析...</p></div><div v-else-if="decisionResult" style="padding:16px;line-height:1.8;">{{ decisionResult }}</div><template #footer><el-button @click="showDecisionDialog = false">关闭</el-button></template></el-dialog></div></template>
<script setup>
import { ref, onMounted } from "vue"
import { ElMessage } from "element-plus"
import { taskService } from "../../api/services"

const props = defineProps({ sessionId: { type: String, default: "" } })
const loading = ref(false)
const decisionLoading = ref(false)
const taskList = ref([])
const statusFilter = ref("all")
const showDetailDialog = ref(false)
const showDecisionDialog = ref(false)
const decisionResult = ref("")
const currentTask = ref({})

const loadTasks = async () => {
  loading.value = true
  try {
    const res = await taskService.list(undefined, statusFilter.value === "all" ? undefined : Number(statusFilter.value))
    taskList.value = Array.isArray(res) ? res : []
  } catch (e) {
    ElMessage.error("加载失败")
  } finally {
    loading.value = false
  }
}

const viewTaskDetail = (row) => {
  currentTask.value = { ...row }
  showDetailDialog.value = true
}

const handleDecision = async () => {
  if (!props.sessionId) { ElMessage.warning("请先选择会话"); return }
  showDecisionDialog.value = true
  decisionResult.value = ""
  decisionLoading.value = true
  try {
    const res = await taskService.getDecision(props.sessionId)
    decisionResult.value = res.status === "ok" ? (typeof res.data === "string" ? res.data : JSON.stringify(res.data)) : "无结果"
  } catch (e) {
    decisionResult.value = "失败"
  } finally {
    decisionLoading.value = false
  }
}

onMounted(() => { loadTasks() })
defineExpose({ loadTasks })
</script>
<style scoped>
.task-manager{height:100%;overflow-y:auto;padding:16px;background:#F8F9FA}
.toolbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.task-table{border-radius:8px;overflow:hidden}
.empty-state{text-align:center;padding:40px 0;color:#869099}
</style>
