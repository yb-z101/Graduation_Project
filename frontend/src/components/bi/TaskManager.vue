<template><div class="task-manager"><div class="toolbar"><el-radio-group v-model="statusFilter" size="default" @change="loadTasks"><el-radio-button label="all">全部</el-radio-button><el-radio-button :label="2">成功</el-radio-button><el-radio-button :label="3">失败</el-radio-button></el-radio-group></div><el-table :data="taskList" stripe border size="small" v-loading="loading" class="task-table" max-height="420"><el-table-column prop="id" label="ID" width="55" /><el-table-column prop="task_name" label="任务名称" min-width="140" show-overflow-tooltip /><el-table-column prop="user_prompt" label="用户提问" min-width="160" show-overflow-tooltip /><el-table-column prop="task_status" label="状态" width="80"><template #default="{ row }"><el-tag size="small">{{ row.task_status === 2 ? "成功" : row.task_status === 3 ? "失败" : "执行中" }}</el-tag></template></el-table-column><el-table-column prop="create_time" label="创建时间" width="150" /><el-table-column label="操作" width="100" fixed="right"><template #default="{ row }"><el-button size="small" link type="primary" @click="viewTaskDetail(row)">详情</el-button></template></el-table-column></el-table><div v-if="!taskList.length && !loading" class="empty-state"><p>暂无分析任务记录</p></div><el-dialog v-model="showDetailDialog" title="任务详情" width="600px"><div v-if="currentTask.id"><p><b>任务名称:</b> {{ currentTask.task_name }}</p><p><b>状态:</b> {{ currentTask.task_status === 2 ? "成功" : "失败" }}</p><p><b>创建时间:</b> {{ currentTask.create_time }}</p><div v-if="currentTask.user_prompt" style="margin-top:12px;padding:10px 14px;background:#F5F7FA;border-radius:6px;font-size:13px;line-height:1.7;white-space:pre-wrap;word-break:break-word;"><b>用户提问:</b><br/>{{ currentTask.user_prompt }}</div><div v-if="currentTask.generated_sql" style="margin-top:12px;padding:12px;background:#1D2129;border-radius:6px;color:#F5F7FA;font-size:12px;font-family:monospace;line-height:1.6;white-space:pre-wrap;word-break:break-all;"><b style="color:#FAAD14;">生成的代码/SQL:</b><br/>{{ currentTask.generated_sql }}</div><div v-if="currentTask.llm_analysis" style="margin-top:12px;padding:10px 14px;background:#F5F7FA;border-radius:6px;font-size:13px;line-height:1.7;white-space:pre-wrap;word-break:break-word;"><b>分析结论:</b><br/>{{ currentTask.llm_analysis }}</div></div><template #footer><el-button @click="showDetailDialog = false">关闭</el-button></template></el-dialog></div></template>
<script setup>
import { ref, onMounted } from "vue"
import { ElMessage } from "element-plus"
import { taskService } from "../../api/services"

const loading = ref(false)
const taskList = ref([])
const statusFilter = ref("all")
const showDetailDialog = ref(false)
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

onMounted(() => { loadTasks() })
defineExpose({ loadTasks })
</script>
<style scoped>
.task-manager{height:100%;overflow-y:auto;padding:16px;background:#F8F9FA}
.toolbar{display:flex;justify-content:flex-start;align-items:center;margin-bottom:12px}
.task-table{border-radius:8px;overflow:hidden}
.empty-state{text-align:center;padding:40px 0;color:#869099}
</style>
