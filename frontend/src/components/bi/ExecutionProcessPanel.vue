<template>
  <div class="execution-process-panel">
    <div v-if="!processLog.length && !loading" class="empty-state">
      <el-empty description="暂无执行记录" :image-size="60" />
    </div>
    
    <div v-else class="process-log">
      <div class="log-timeline">
        <div v-for="(item, idx) in displayLog" :key="idx" class="timeline-item" :class="item.status">
          <div class="timeline-dot">
            <el-icon v-if="item.status === 'success'" color="#67c23a"><Check /></el-icon>
            <el-icon v-else-if="item.status === 'error'" color="#f56c6c"><Close /></el-icon>
            <el-icon v-else-if="item.status === 'running'" color="#409eff"><Loading /></el-icon>
            <span v-else class="dot-pending"></span>
          </div>
          <div class="timeline-content">
            <div class="item-header">
              <span class="node-name">{{ item.node }}</span>
              <span class="timestamp">{{ formatTime(item.timestamp) }}</span>
            </div>
            <div class="item-detail">
              <p class="description">{{ item.description }}</p>
              
              <div v-if="item.code" class="code-section">
                <div class="code-header" @click="toggleCode(idx)">
                  <span>代码 ({{ item.language || 'python' }})</span>
                  <el-icon :class="{ 'rotated': codeVisible[idx] }"><ArrowRight /></el-icon>
                </div>
                <div v-show="codeVisible[idx]" class="code-block">
                  <pre><code>{{ item.code }}</code></pre>
                </div>
              </div>
              
              <div v-if="item.logs?.length" class="logs-section">
                <div class="logs-header" @click="toggleLogs(idx)">
                  <span>执行日志 ({{ item.logs.length }})</span>
                  <el-icon :class="{ 'rotated': logsVisible[idx] }"><ArrowRight /></el-icon>
                </div>
                <div v-show="logsVisible[idx]" class="logs-list">
                  <div v-for="(log, lidx) in item.logs" :key="lidx" class="log-item">
                    <span class="log-level" :class="log.level">{{ log.level }}</span>
                    <span class="log-message">{{ log.message }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="loading" class="timeline-item pending">
          <div class="timeline-dot">
            <span class="dot-pending"></span>
          </div>
          <div class="timeline-content">
            <div class="item-header">
              <span class="node-name">处理中...</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Check, Close, Loading, ArrowRight } from '@element-plus/icons-vue'

const props = defineProps({
  processLog: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const codeVisible = ref({})
const logsVisible = ref({})

const displayLog = computed(() => {
  if (!props.processLog.length) {
    return [
      {
        node: '准备分析',
        status: 'pending',
        description: '等待用户输入...',
        timestamp: new Date()
      }
    ]
  }
  return props.processLog
})

const formatTime = (ts) => {
  if (!ts) return ''
  const d = new Date(ts)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

const toggleCode = (idx) => {
  codeVisible.value[idx] = !codeVisible.value[idx]
}

const toggleLogs = (idx) => {
  logsVisible.value[idx] = !logsVisible.value[idx]
}
</script>

<style lang="less" scoped>
.execution-process-panel {
  height: 100%;
  overflow-y: auto;
  padding: 8px 0;
  
  .empty-state {
    padding: 40px 0;
  }
  
  .process-log {
    .log-timeline {
      .timeline-item {
        display: flex;
        gap: 12px;
        margin-bottom: 20px;
        
        &:last-child {
          margin-bottom: 0;
        }
        
        .timeline-dot {
          width: 28px;
          height: 28px;
          border-radius: 50%;
          background: #f0f2f5;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          
          .dot-pending {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #dcdfe6;
          }
        }
        
        &.success .timeline-dot {
          background: #f0f9eb;
        }
        
        &.error .timeline-dot {
          background: #fef0f0;
        }
        
        &.running .timeline-dot {
          background: #ecf5ff;
          animation: pulse 1.5s infinite;
        }
        
        .timeline-content {
          flex: 1;
          
          .item-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 4px;
            
            .node-name {
              font-size: 14px;
              font-weight: 600;
              color: #303133;
            }
            
            .timestamp {
              font-size: 12px;
              color: #909399;
            }
          }
          
          .item-detail {
            .description {
              font-size: 13px;
              color: #606266;
              margin: 0 0 8px;
            }
            
            .code-section,
            .logs-section {
              margin-top: 8px;
              
              .code-header,
              .logs-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 8px 12px;
                background: #f5f7fa;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
                color: #606266;
                user-select: none;
                
                .el-icon {
                  transition: transform 0.2s;
                  
                  &.rotated {
                    transform: rotate(90deg);
                  }
                }
              }
              
              .code-block {
                margin-top: 8px;
                background: #1e1e1e;
                border-radius: 4px;
                padding: 12px;
                overflow-x: auto;
                
                pre {
                  margin: 0;
                  
                  code {
                    color: #d4d4d4;
                    font-size: 12px;
                    font-family: 'Consolas', 'Monaco', monospace;
                    line-height: 1.6;
                  }
                }
              }
              
              .logs-list {
                margin-top: 8px;
                background: #fafafa;
                border-radius: 4px;
                padding: 8px;
                max-height: 200px;
                overflow-y: auto;
                
                .log-item {
                  display: flex;
                  gap: 8px;
                  padding: 4px 0;
                  font-size: 12px;
                  
                  .log-level {
                    flex-shrink: 0;
                    padding: 1px 6px;
                    border-radius: 2px;
                    font-weight: 500;
                    
                    &.info {
                      background: #ecf5ff;
                      color: #409eff;
                    }
                    
                    &.warn {
                      background: #fdf6ec;
                      color: #e6a23c;
                    }
                    
                    &.error {
                      background: #fef0f0;
                      color: #f56c6c;
                    }
                  }
                  
                  .log-message {
                    color: #606266;
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}
</style>
