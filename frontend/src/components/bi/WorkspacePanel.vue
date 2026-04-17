<template>
  <div class="workspace-panel">
    <div class="panel-header">
      <span class="panel-title">分析结果区</span>
    </div>
    
    <div class="tabs-area" v-if="tabs.length">
      <el-tabs
        v-model="localActiveTab"
        type="card"
        class="workspace-tabs"
        closable
        @tab-click="handleTabClick"
        @tab-remove="handleTabRemove"
      >
        <el-tab-pane
          v-for="tab in tabs"
          :key="tab.id"
          :label="tab.title"
          :name="tab.id"
        >
          <template #label>
            <span class="tab-label">
              <svg v-if="tab.type === 'table'" viewBox="0 0 16 16" width="14" height="14" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 4px;">
                <rect x="2" y="3" width="12" height="10" rx="1" stroke="#6B5CE8" stroke-width="1.2"/>
                <path d="M2 7H14M6 3V13" stroke="#6B5CE8" stroke-width="1.2"/>
              </svg>
              <svg v-else-if="tab.type === 'chart'" viewBox="0 0 16 16" width="14" height="14" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 4px;">
                <rect x="3" y="10" width="3" height="3" rx="0.5" fill="#6B5CE8"/>
                <rect x="8" y="7" width="3" height="6" rx="0.5" fill="#8B7DF2"/>
                <path d="M2 13H14" stroke="#E5E6EB" stroke-width="1.2"/>
              </svg>
              {{ tab.title }}
            </span>
          </template>
        </el-tab-pane>
      </el-tabs>
    </div>
    
    <div class="panel-content">
      <div v-if="!tabs.length" class="empty-workspace">
        <div class="empty-icon">
          <svg viewBox="0 0 80 80" width="80" height="80" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="16" y="12" width="48" height="56" rx="4" fill="#F8F9FA" stroke="#E5E6EB" stroke-width="2"/>
            <path d="M24 26H56M24 38H44M24 50H52" stroke="#E5E6EB" stroke-width="2" stroke-linecap="round"/>
            <circle cx="58" cy="22" r="8" fill="#F9F0FF"/>
            <path d="M55 22H61M58 19V25" stroke="#6B5CE8" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </div>
        <h3>暂无分析结果</h3>
        <p>上传文件或发送分析请求后，结果将在这里展示</p>
      </div>
      
      <div v-else class="workspace-content">
        <div v-for="tab in tabs" :key="tab.id" v-show="localActiveTab === tab.id" class="tab-content">
          <DataTable
            v-if="tab.type === 'table'"
            :data="formatTableData(tab.data)"
            :columns="formatTableColumns(tab.data)"
            style="height: 100%;"
          />
          <DataChart
            v-else-if="tab.type === 'chart'"
            :option="tab.chartOption"
            style="width: 100%; height: 100%;"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import DataTable from '../DataTable.vue'
import DataChart from '../DataChart.vue'

const props = defineProps({
  tabs: {
    type: Array,
    default: () => []
  },
  activeTab: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['tab-change', 'tab-close'])

const localActiveTab = ref('')

watch(() => props.activeTab, (newVal) => {
  if (newVal) {
    localActiveTab.value = newVal
  }
}, { immediate: true })

watch(() => props.tabs, (newTabs) => {
  if (newTabs.length && !localActiveTab.value) {
    localActiveTab.value = newTabs[0].id
  } else if (newTabs.length > 0 && !newTabs.find(t => t.id === localActiveTab.value)) {
    localActiveTab.value = newTabs[0].id
    emit('tab-change', newTabs[0].id)
  }
}, { immediate: true, deep: true })

const handleTabClick = (tab) => {
  emit('tab-change', tab.props.name)
}

const handleTabRemove = (tabId) => {
  emit('tab-close', tabId)
}

const formatTableData = (data) => {
  if (!data) return []
  if (Array.isArray(data)) return data
  if (typeof data === 'object') {
    const keys = Object.keys(data)
    if (keys.length && Array.isArray(data[keys[0]])) {
      const firstCol = data[keys[0]]
      return firstCol.map((_, idx) => {
        const row = {}
        keys.forEach(k => {
          row[k] = data[k][idx]
        })
        return row
      })
    }
  }
  return []
}

const formatTableColumns = (data) => {
  if (!data) return []
  if (Array.isArray(data) && data.length) {
    return Object.keys(data[0]).map(key => ({
      prop: key,
      label: key
    }))
  }
  if (typeof data === 'object') {
    return Object.keys(data).map(key => ({
      prop: key,
      label: key
    }))
  }
  return []
}
</script>

<style lang="less" scoped>
.workspace-panel {
  height: 100%;
  background: #FFFFFF;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  
  .panel-header {
    padding: 20px 24px 12px;
    border-bottom: 1px solid #E5E6EB;
    background: linear-gradient(135deg, #FFFFFF 0%, #F8F9FA 100%);
    
    .panel-title {
      font-size: 16px;
      font-weight: 600;
      color: #1D2129;
      letter-spacing: 0.3px;
    }
  }
  
  .tabs-area {
    padding: 12px 24px 0;
    background: #FFFFFF;
    
    .workspace-tabs {
      :deep(.el-tabs__header) {
        margin: 0;
      }
      
      :deep(.el-tabs__nav-wrap) {
        padding-right: 0;
      }
      
      :deep(.el-tabs__item) {
        font-size: 13px;
        height: 38px;
        line-height: 38px;
        font-weight: 500;
        color: #869099;
        border-radius: 8px 8px 0 0;
        padding: 0 16px;
        transition: all 0.2s ease;
        
        &:hover {
          color: #6B5CE8;
        }
        
        &.is-active {
          color: #6B5CE8;
          background: linear-gradient(135deg, #F9F0FF 0%, #FFFFFF 100%);
          font-weight: 600;
        }
      }
      
      .tab-label {
        display: flex;
        align-items: center;
        gap: 4px;
      }
    }
  }
  
  .panel-content {
    flex: 1;
    overflow: hidden;
    padding: 16px 24px 24px;
    background: #F8F9FA;
    
    .empty-workspace {
      height: 100%;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      color: #869099;
      
      .empty-icon {
        margin-bottom: 20px;
      }
      
      h3 {
        margin: 0 0 10px;
        font-size: 18px;
        color: #1D2129;
        font-weight: 600;
      }
      
      p {
        margin: 0 0 20px;
        font-size: 14px;
        color: #869099;
      }
    }
    
    .workspace-content {
      height: 100%;
      
      .tab-content {
        height: 100%;
        overflow: auto;
        background: #FFFFFF;
        border-radius: 8px;
        border: 1px solid #E5E6EB;
        padding: 4px;
      }
    }
  }
}
</style>
