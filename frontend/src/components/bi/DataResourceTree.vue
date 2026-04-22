<template>
  <div class="data-resource-tree">
    <el-collapse v-model="activeNames" class="resource-collapse">
      <!-- 历史会话区域 -->
      <el-collapse-item title="历史会话" name="sessions">
        <div class="session-section">
          <div class="session-actions">
            <el-button
              class="new-session-btn"
              type="primary"
              size="default"
              @click="$emit('new-session')"
            >
              <svg viewBox="0 0 16 16" width="14" height="14" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 6px;">
                <path d="M8 3V13M3 8H13" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
              新建会话
            </el-button>
            <el-button
              v-if="sessionsList.length > 0"
              size="default"
              style="width:100%;height:32px;border:1px dashed #E5E6EB;color:#869099;font-size:12px;border-radius:8px;background:transparent;"
              @click="$emit('clear-all-sessions')"
            >
              清空全部
            </el-button>
          </div>
          
          <div v-if="!sessionsList.length" class="empty-state">
            <el-empty description="暂无历史会话" :image-size="48">
              <template #image>
                <svg viewBox="0 0 64 64" width="48" height="48" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="12" y="8" width="40" height="48" rx="4" stroke="#E5E6EB" stroke-width="2"/>
                  <path d="M20 22H44M20 30H44M20 38H32" stroke="#E5E6EB" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </template>
            </el-empty>
          </div>
          
          <div v-else class="session-list">
            <div 
              v-for="(session, idx) in sessionsList" 
              :key="session.id" 
              class="session-item"
              :class="{ 'active': session.id === currentSessionId }"
              @click="$emit('session-select', session)"
            >
              <div class="session-info">
                <div class="session-icon-wrapper">
                  <svg v-if="session.isDatabase" viewBox="0 0 40 40" width="32" height="32" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <ellipse cx="20" cy="12" rx="12" ry="5" fill="#F9F0FF" stroke="#6B5CE8" stroke-width="1.5"/>
                    <path d="M8 12V28" stroke="#6B5CE8" stroke-width="1.5"/>
                    <path d="M32 12V28" stroke="#6B5CE8" stroke-width="1.5"/>
                    <ellipse cx="20" cy="28" rx="12" ry="5" fill="#F9F0FF" stroke="#6B5CE8" stroke-width="1.5"/>
                  </svg>
                  <svg v-else viewBox="0 0 40 40" width="32" height="32" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect width="40" height="40" rx="8" fill="#F9F0FF"/>
                    <path d="M14 28V16L20 12L26 16V28" stroke="#6B5CE8" stroke-width="2" stroke-linecap="round"/>
                    <path d="M17 24V20M23 24V20M20 24V18" stroke="#6B5CE8" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                </div>
                <div class="session-details">
                  <span class="session-name">{{ session.displayName || session.fileName }}</span>
                  <span class="session-time">{{ formatTime(session.timestamp) }}</span>
                </div>
              </div>
              <el-button 
                class="delete-session-btn" 
                type="danger" 
                size="small" 
                circle
                @click.stop="$emit('session-delete', session.id)"
              >
                <svg viewBox="0 0 12 12" width="10" height="10" fill="none">
                  <path d="M2 2L10 10M10 2L2 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
              </el-button>
            </div>
          </div>
        </div>
      </el-collapse-item>
      
      <el-collapse-item title="数据库表" name="database">
        <div class="database-section">
          <div class="database-actions">
            <el-button
              class="connect-btn"
              type="primary"
              size="default"
              @click="$emit('connect-database')"
            >
              <svg viewBox="0 0 16 16" width="16" height="16" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 6px;">
                <ellipse cx="8" cy="4" rx="5" ry="2" stroke="white" stroke-width="1.2"/>
                <path d="M3 4V12" stroke="white" stroke-width="1.2"/>
                <path d="M13 4V12" stroke="white" stroke-width="1.2"/>
                <ellipse cx="8" cy="12" rx="5" ry="2" stroke="white" stroke-width="1.2"/>
                <ellipse cx="8" cy="8" rx="5" ry="2" stroke="white" stroke-width="1.2"/>
              </svg>
              连接数据源
            </el-button>
            
            <el-button
              v-if="databaseTables?.length > 0"
              class="disconnect-btn"
              type="danger"
              size="default"
              @click="$emit('disconnect-database')"
            >
              <svg viewBox="0 0 16 16" width="16" height="16" fill="none" style="margin-right: 6px;">
                <path d="M4 8H12M8 4V12" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
              断开连接
            </el-button>
          </div>
          
          <div v-if="savedConnections.length > 0" class="quick-connections">
            <div class="quick-connections-title">历史连接</div>
            <div class="quick-connections-list">
              <div 
                v-for="(conn, idx) in savedConnections" 
                :key="idx" 
                class="quick-connection-item"
                @click="$emit('quick-connect', conn)"
              >
                <svg viewBox="0 0 16 16" width="14" height="14" fill="none" style="flex-shrink: 0;">
                  <ellipse cx="8" cy="4" rx="5" ry="2" stroke="#6B5CE8" stroke-width="1.2"/>
                  <path d="M3 4V12" stroke="#6B5CE8" stroke-width="1.2"/>
                  <path d="M13 4V12" stroke="#6B5CE8" stroke-width="1.2"/>
                  <ellipse cx="8" cy="12" rx="5" ry="2" stroke="#6B5CE8" stroke-width="1.2"/>
                  <ellipse cx="8" cy="8" rx="5" ry="2" stroke="#6B5CE8" stroke-width="1.2"/>
                </svg>
                <div class="quick-connection-info">
                  <span class="quick-connection-name">{{ conn.database }}</span>
                  <span class="quick-connection-host">{{ conn.host }}:{{ conn.port }}</span>
                </div>
                <el-button 
                  class="delete-btn" 
                  type="danger" 
                  size="small" 
                  circle
                  @click.stop="$emit('delete-connection', idx)"
                >
                  <svg viewBox="0 0 12 12" width="12" height="12" fill="none">
                    <path d="M2 2L10 10M10 2L2 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                  </svg>
                </el-button>
              </div>
            </div>
          </div>
          
          <div class="table-list">
            <div v-if="!databaseTables?.length" class="empty-state">
              <el-empty description="暂无数据库连接" :image-size="48">
                <template #image>
                  <svg viewBox="0 0 64 64" width="48" height="48" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <ellipse cx="32" cy="18" rx="18" ry="8" stroke="#E5E6EB" stroke-width="2"/>
                    <path d="M14 18V46" stroke="#E5E6EB" stroke-width="2"/>
                    <path d="M50 18V46" stroke="#E5E6EB" stroke-width="2"/>
                    <ellipse cx="32" cy="46" rx="18" ry="8" stroke="#E5E6EB" stroke-width="2"/>
                    <ellipse cx="32" cy="32" rx="18" ry="8" stroke="#E5E6EB" stroke-width="2"/>
                  </svg>
                </template>
              </el-empty>
            </div>
            <div v-else class="db-tables">
              <div 
                v-for="(table, idx) in databaseTables" 
                :key="idx" 
                class="db-table"
                @click="$emit('table-click', table)"
              >
                <div class="table-name">{{ table.name }}</div>
                <div class="table-columns">
                  <div v-for="(col, cidx) in (table.columns || [])" :key="cidx" class="table-column">
                    <span>{{ col.name }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Plus } from '@element-plus/icons-vue'

const props = defineProps({
  databaseTables: {
    type: Array,
    default: () => []
  },
  savedConnections: {
    type: Array,
    default: () => []
  },
  sessionsList: {
    type: Array,
    default: () => []
  },
  currentSessionId: {
    type: String,
    default: null
  }
})

defineEmits(['connect-database', 'table-click', 'quick-connect', 'delete-connection', 'disconnect-database', 'new-session', 'session-select', 'session-delete', 'clear-all-sessions'])

const activeNames = ref(['sessions', 'database'])

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  
  return date.toLocaleDateString('zh-CN')
}
</script>

<style lang="less" scoped>
.data-resource-tree {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 16px 12px;
  
  .resource-collapse {
    flex: 1;
    overflow-y: auto;
    border: none;
    
    :deep(.el-collapse-item__header) {
      padding: 0 4px;
      font-size: 14px;
      font-weight: 600;
      color: #4E5969;
      height: 40px;
      line-height: 40px;
      border-radius: 6px;
      transition: all 0.2s ease;
      
      &:hover {
        background: #F5F7FA;
      }
    }
    
    :deep(.el-collapse-item__content) {
      padding: 0;
    }
  }
  
  .session-section {
    .session-actions {
      margin-bottom: 12px;
      
      .new-session-btn {
        width: 100%;
        height: 36px;
        background: linear-gradient(90deg, #6B5CE8, #8B7DF2);
        border: none;
        color: #FFFFFF;
        font-weight: 500;
        border-radius: 8px;
        box-shadow: 0 2px 6px rgba(107, 92, 232, 0.2);
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        
        &:hover {
          background: linear-gradient(90deg, #5A4BD9, #6B5CE8);
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(107, 92, 232, 0.35);
        }
        
        &:active {
          transform: translateY(0);
        }
      }
    }
    
    .session-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
      
      .session-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 12px;
        background: #FFFFFF;
        border-radius: 8px;
        border: 1px solid #E5E6EB;
        cursor: pointer;
        transition: all 0.2s ease;
        
        &:hover {
          background: #F9F0FF;
          border-color: #6B5CE8;
          
          .delete-session-btn {
            opacity: 1;
          }
        }
        
        &.active {
          background: linear-gradient(135deg, #F9F0FF 0%, #F3E8FF 100%);
          border-color: #6B5CE8;
          box-shadow: 0 2px 8px rgba(107, 92, 232, 0.15);
        }
        
        .session-info {
          flex: 1;
          display: flex;
          align-items: center;
          gap: 10px;
          overflow: hidden;
          
          .session-icon-wrapper {
            width: 32px;
            height: 32px;
            flex-shrink: 0;
            border-radius: 6px;
            overflow: hidden;
          }
          
          .session-details {
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 2px;
            overflow: hidden;
            
            .session-name {
              font-size: 13px;
              color: #1D2129;
              font-weight: 500;
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
            }
            
            .session-time {
              font-size: 11px;
              color: #869099;
            }
          }
        }
        
        .delete-session-btn {
          opacity: 0;
          width: 24px;
          height: 24px;
          padding: 0;
          background: transparent;
          border: none;
          color: #F53F3F;
          transition: all 0.2s ease;
          
          &:hover {
            background: #FFF1F0;
          }
        }
      }
    }
  }
  
  .database-section {
    .database-actions {
      display: flex;
      flex-direction: column;
      gap: 8px;
      margin-bottom: 12px;
    }
    
    .connect-btn {
      width: 100%;
      height: 36px;
      background: linear-gradient(90deg, #6B5CE8, #8B7DF2);
      border: none;
      color: #FFFFFF;
      font-weight: 500;
      border-radius: 8px;
      box-shadow: 0 2px 6px rgba(107, 92, 232, 0.2);
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      
      &:hover {
        background: linear-gradient(90deg, #5A4BD9, #6B5CE8);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(107, 92, 232, 0.35);
      }
      
      &:active {
        transform: translateY(0);
      }
    }
    
    .disconnect-btn {
      width: 100%;
      height: 36px;
      background: linear-gradient(90deg, #F53F3F, #FF6B6B);
      border: none;
      color: #FFFFFF;
      font-weight: 500;
      border-radius: 8px;
      box-shadow: 0 2px 6px rgba(245, 63, 63, 0.2);
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      
      &:hover {
        background: linear-gradient(90deg, #D92F2F, #F53F3F);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(245, 63, 63, 0.35);
      }
      
      &:active {
        transform: translateY(0);
      }
    }
    
    .quick-connections {
      margin-bottom: 12px;
      
      .quick-connections-title {
        font-size: 12px;
        font-weight: 600;
        color: #869099;
        margin-bottom: 8px;
        padding: 0 4px;
      }
      
      .quick-connections-list {
        display: flex;
        flex-direction: column;
        gap: 6px;
        
        .quick-connection-item {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 12px;
          background: #F5F7FA;
          border-radius: 8px;
          border: 1px solid #E5E6EB;
          cursor: pointer;
          transition: all 0.2s ease;
          
          &:hover {
            background: #F9F0FF;
            border-color: #6B5CE8;
            
            .delete-btn {
              opacity: 1;
            }
          }
          
          .quick-connection-info {
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 2px;
            overflow: hidden;
            
            .quick-connection-name {
              font-size: 14px;
              font-weight: 500;
              color: #1D2129;
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
            }
            
            .quick-connection-host {
              font-size: 11px;
              color: #869099;
            }
          }
          
          .delete-btn {
            opacity: 0;
            width: 24px;
            height: 24px;
            padding: 0;
            background: transparent;
            border: none;
            color: #F53F3F;
            transition: all 0.2s ease;
            
            &:hover {
              background: #FFF1F0;
            }
          }
        }
      }
    }
  }
  
  .table-list {
    padding: 8px 4px;
    
    .empty-state {
      padding: 20px 0;
    }
    
    .db-tables {
      display: flex;
      flex-direction: column;
      gap: 8px;
      
      .db-table {
        background: #F5F7FA;
        border-radius: 8px;
        padding: 12px;
        border: 1px solid #E5E6EB;
        transition: all 0.2s ease;
        cursor: pointer;
        
        &:hover {
          border-color: #6B5CE8;
          box-shadow: 0 2px 8px rgba(107, 92, 232, 0.08);
          background: #F9F0FF;
        }
        
        .table-name {
          font-size: 14px;
          font-weight: 600;
          color: #1D2129;
          margin-bottom: 8px;
        }
        
        .table-columns {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          
          .table-column {
            font-size: 12px;
            color: #4E5969;
            padding: 4px 8px;
            background: #FFFFFF;
            border-radius: 4px;
            border: 1px solid #E5E6EB;
          }
        }
      }
    }
  }
}
</style>
