<template>
  <aside class="sidebar" :class="{ collapsed: collapsed }">
    <!-- 收起按钮 -->
    <div class="sidebar-toggle" @click="$emit('toggle')">
      <el-icon :class="{ 'flipped': collapsed }"><Fold /></el-icon>
    </div>

    <!-- 项目标题 -->
    <div class="sidebar-title" v-show="!collapsed">
      <div class="title-main">
        <span class="title-zh">智析</span>
        <span class="title-en">zhixi</span>
      </div>
      <div class="title-sub">智能数据分析系统</div>
    </div>

    <div class="sidebar-top" v-show="!collapsed">
      <el-button class="new-chat-btn" @click="$emit('new-chat')">
        <el-icon><Plus /></el-icon>
        <span>新建对话</span>
      </el-button>
    </div>

    <div class="sidebar-history" v-show="!collapsed">
      <div class="history-group">
        <div class="group-title">
          <span>最近会话</span>
          <el-button link size="small" :icon="Delete" title="清空全部会话" @click.stop="$emit('clear-all-sessions')" />
        </div>
        <div 
          v-for="session in recentSessions" 
          :key="session.id"
          class="history-item"
          :class="{ active: session.id === currentSessionId }"
          @click="$emit('load-session', session)"
        >
          <el-icon><ChatLineRound /></el-icon>
          <span class="text-truncate">{{ session.displayName || session.fileName }}</span>
          <el-button
            class="history-delete-btn"
            link
            size="small"
            :icon="Delete"
            title="删除会话"
            @click.stop="$emit('delete-session', session)"
          />
        </div>
      </div>
      
      <div class="history-group" v-if="archivedSessions.length > 0">
        <div class="group-title">历史存档</div>
        <div 
          v-for="session in archivedSessions" 
          :key="session.id"
          class="history-item"
          :class="{ active: session.id === currentSessionId }"
          @click="$emit('load-session', session)"
        >
          <el-icon><Folder /></el-icon>
          <span class="text-truncate">{{ session.displayName || session.fileName }}</span>
        </div>
      </div>

      <div v-if="sessions.length === 0" class="empty-history">
        <span>暂无历史对话</span>
      </div>
    </div>

    <div class="sidebar-bottom" v-show="!collapsed">
      <!-- 主题选择器 -->
      <div class="theme-selector" @click="showThemeDropdown = !showThemeDropdown">
        <el-icon><Moon v-if="theme === 'dark'" /><Sunny v-else /></el-icon>
        <span>{{ theme === 'dark' ? '深色' : '浅色' }}</span>
        <el-icon :class="{ 'rotate': showThemeDropdown }"><ArrowDown /></el-icon>
        
        <div v-if="showThemeDropdown" class="theme-dropdown">
          <div 
            class="theme-option"
            :class="{ active: theme === 'dark' }"
            @click="$emit('change-theme', 'dark'); showThemeDropdown = false"
          >
            <el-icon><Moon /></el-icon>
            <span>深色模式</span>
            <el-icon v-if="theme === 'dark'"><Check /></el-icon>
          </div>
          <div 
            class="theme-option"
            :class="{ active: theme === 'light' }"
            @click="$emit('change-theme', 'light'); showThemeDropdown = false"
          >
            <el-icon><Sunny /></el-icon>
            <span>浅色模式</span>
            <el-icon v-if="theme === 'light'"><Check /></el-icon>
          </div>
        </div>
      </div>

      <!-- 用户信息 -->
      <div class="user-profile">
        <div class="avatar">
          <el-avatar :size="32" :style="{ backgroundColor: themeAccent }">JS</el-avatar>
        </div>
        <div class="info">
          <div class="name">数据分析师</div>
          <div class="email">Pro 版本</div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue'
import { 
  Plus, ChatLineRound, Folder, Delete, ArrowDown, Check, 
  Moon, Sunny, Fold 
} from '@element-plus/icons-vue'

const props = defineProps({
  collapsed: {
    type: Boolean,
    default: false
  },
  sessions: {
    type: Array,
    default: () => []
  },
  currentSessionId: {
    type: String,
    default: null
  },
  theme: {
    type: String,
    default: 'dark'
  }
})

const emit = defineEmits([
  'toggle',
  'new-chat',
  'load-session',
  'delete-session',
  'clear-all-sessions',
  'change-theme'
])

const showThemeDropdown = ref(false)

const recentSessions = computed(() => props.sessions.slice(0, 5))
const archivedSessions = computed(() => props.sessions.slice(5))

const themeAccent = computed(() => props.theme === 'dark' ? '#6366f1' : '#4f46e5')
</script>

<style scoped>
.sidebar {
  width: 260px;
  background-color: var(--bg-secondary);
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-color);
  flex-shrink: 0;
  transition: width 0.3s ease;
  position: relative;
}

.sidebar.collapsed {
  width: 60px;
}

.sidebar-toggle {
  position: absolute;
  top: 16px;
  right: -12px;
  width: 24px;
  height: 24px;
  background-color: var(--bg-hover);
  border: 1px solid var(--border-color);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  transition: all 0.2s;
  color: var(--text-secondary);
}

.sidebar-toggle:hover {
  background-color: var(--accent-color);
  color: white;
  border-color: var(--accent-color);
}

.sidebar-toggle .el-icon {
  transition: transform 0.3s;
}

.sidebar-toggle .flipped {
  transform: rotate(180deg);
}

.sidebar-title {
  padding: 20px 16px 16px;
  text-align: center;
}

.title-main {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 8px;
  margin-bottom: 4px;
}

.title-zh {
  font-size: 24px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--accent-color), #a855f7);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 2px 4px rgba(99, 102, 241, 0.3);
  position: relative;
  display: inline-block;
}

.title-zh::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, var(--accent-color), transparent);
  border-radius: 1px;
}

.title-en {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  font-style: italic;
  letter-spacing: 0.5px;
}

.title-sub {
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 1px;
}

.sidebar-top {
  padding: 0 16px 16px;
}

.new-chat-btn {
  width: 100%;
  background-color: var(--accent-color);
  color: white;
  border: none;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 500;
  transition: all 0.2s;
}

.new-chat-btn:hover {
  background-color: var(--accent-hover);
}

.sidebar-history {
  flex: 1;
  overflow-y: auto;
  padding: 0 12px;
}

.history-group {
  margin-bottom: 24px;
}

.group-title {
  font-size: 12px;
  color: var(--text-secondary);
  padding: 8px 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 14px;
  transition: background 0.2s;
}

.history-delete-btn {
  margin-left: auto;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.history-item:hover .history-delete-btn {
  opacity: 1;
}

.history-item:hover {
  background-color: var(--bg-hover);
  color: var(--text-primary);
}

.history-item.active {
  background-color: var(--bg-hover);
  color: var(--accent-color);
}

.text-truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.empty-history {
  text-align: center;
  padding: 20px;
  color: var(--text-muted);
  font-size: 13px;
}

.sidebar-bottom {
  padding: 12px;
  border-top: 1px solid var(--border-color);
}

.theme-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 8px;
  transition: all 0.2s;
  position: relative;
}

.theme-selector:hover {
  background-color: var(--bg-hover);
  color: var(--text-primary);
}

.theme-dropdown {
  position: absolute;
  bottom: 100%;
  left: 0;
  margin-bottom: 8px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 6px;
  min-width: 140px;
  box-shadow: 0 10px 40px var(--shadow-color);
  z-index: 100;
}

.theme-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 13px;
}

.theme-option:hover {
  background-color: var(--bg-hover);
}

.theme-option.active {
  background-color: var(--bg-hover);
  color: var(--accent-color);
}

.theme-option .el-icon:last-child {
  margin-left: auto;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: background 0.2s;
}

.user-profile:hover {
  background-color: var(--bg-hover);
}

.info .name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.info .email {
  font-size: 12px;
  color: var(--text-secondary);
}
</style>