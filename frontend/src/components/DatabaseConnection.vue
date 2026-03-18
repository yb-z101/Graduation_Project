<template>
  <div class="database-connection">
    <!-- 数据库连接对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="连接数据库"
      width="500px"
      :close-on-click-modal="false"
      @close="handleClose"
    >
      <el-form
        :model="connectionForm"
        :rules="connectionRules"
        ref="connectionFormRef"
        label-width="80px"
      >
        <el-form-item label="主机地址" prop="host">
          <el-input v-model="connectionForm.host" placeholder="请输入数据库主机地址" />
        </el-form-item>
        <el-form-item label="端口" prop="port">
          <el-input-number v-model="connectionForm.port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="connectionForm.username" placeholder="请输入数据库用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="connectionForm.password" type="password" placeholder="请输入数据库密码" />
        </el-form-item>
        <el-form-item label="数据库" prop="database">
          <el-input v-model="connectionForm.database" placeholder="请输入数据库名称" />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleClose">取消</el-button>
          <el-button type="primary" @click="testConnection" :loading="testingConnection">
            测试连接
          </el-button>
          <el-button type="primary" @click="connectDatabase" :loading="connecting">
            连接
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import { Database, Check, ChatLineSquare } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { databaseService } from '../api/services'

// 组件事件
const emit = defineEmits(['connection-success', 'query-result', 'close'])

// 组件属性
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

// 连接表单
const dialogVisible = ref(false)
const connectionFormRef = ref(null)
const testingConnection = ref(false)
const connecting = ref(false)
const executingQuery = ref(false)

// 监听visible属性变化
watch(() => props.visible, (newVal) => {
  dialogVisible.value = newVal
})

// 处理对话框关闭
const handleClose = () => {
  emit('close')
}

onMounted(() => {
  dialogVisible.value = props.visible
})

const connectionForm = reactive({
  host: 'localhost',
  port: 3306,
  username: 'root',
  password: '',
  database: ''
})

const connectionRules = {
  host: [{ required: true, message: '请输入主机地址', trigger: 'blur' }],
  port: [{ required: true, message: '请输入端口', trigger: 'blur' }],
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  database: [{ required: true, message: '请输入数据库名称', trigger: 'blur' }]
}

// 测试连接
const testConnection = async () => {
  if (!await connectionFormRef.value.validate()) {
    return
  }

  testingConnection.value = true
  try {
    const response = await databaseService.testConnection(connectionForm)
    if (response.status === 'ok') {
      ElMessage.success('连接测试成功')
    } else {
      ElMessage.error(response.message)
    }
  } catch (error) {
    ElMessage.error('测试连接失败：' + error.message)
  } finally {
    testingConnection.value = false
  }
}

// 连接数据库
const connectDatabase = async () => {
  if (!await connectionFormRef.value.validate()) {
    return
  }

  connecting.value = true
  try {
    const response = await databaseService.connectDatabase(connectionForm)
    if (response.status === 'ok') {
      ElMessage.success('数据库连接成功')
      dialogVisible.value = false
      
      // 触发连接成功事件
      emit('connection-success', {
        connectionId: response.connection_id,
        connectionInfo: {
          host: connectionForm.host,
          port: connectionForm.port,
          username: connectionForm.username,
          password: connectionForm.password,
          database: connectionForm.database
        }
      })
    } else {
      ElMessage.error(response.message)
    }
  } catch (error) {
    ElMessage.error('连接失败：' + error.message)
  } finally {
    connecting.value = false
  }
}
</script>

<style scoped>
.database-connection {
  /* 对话框模式下不需要额外的margin */
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
