<template>
  <header class="top-bar">
    <!-- 模型选择器 -->
    <div class="model-selector" @click="showModelDropdown = !showModelDropdown">
      <span class="model-icon">
        <el-icon><Cpu /></el-icon>
      </span>
      <span class="model-name">{{ currentModel.name }}</span>
      <el-icon :class="{ 'rotate': showModelDropdown }"><ArrowDown /></el-icon>
      
      <div v-if="showModelDropdown" class="model-dropdown">
        <div 
          v-for="model in modelList" 
          :key="model.id"
          class="model-option"
          :class="{ active: currentModel.id === model.id }"
          @click.stop="$emit('select-model', model)"
        >
          <div class="option-info">
            <div class="option-name">{{ model.name }}</div>
            <div class="option-desc">{{ model.description }}</div>
          </div>
          <el-icon v-if="currentModel.id === model.id"><Check /></el-icon>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref } from 'vue'
import { Cpu, ArrowDown, Check } from '@element-plus/icons-vue'

const props = defineProps({
  modelList: {
    type: Array,
    default: () => []
  },
  currentModel: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['select-model'])

const showModelDropdown = ref(false)
</script>

<style scoped>
.top-bar {
  height: 60px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  border-bottom: 1px solid var(--border-color);
}

.model-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: var(--bg-secondary);
  padding: 8px 14px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  position: relative;
  transition: all 0.2s;
}

.model-selector:hover {
  background-color: var(--bg-hover);
  border-color: var(--accent-color);
}

.model-icon {
  color: var(--accent-color);
}

.model-selector .rotate {
  transform: rotate(180deg);
  transition: transform 0.2s;
}

.model-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 8px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 8px;
  min-width: 280px;
  box-shadow: 0 10px 40px var(--shadow-color);
  z-index: 100;
}

.model-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.model-option:hover {
  background-color: var(--bg-hover);
}

.model-option.active {
  background-color: var(--bg-hover);
  color: var(--accent-color);
}

.option-info {
  flex: 1;
}

.option-name {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 2px;
}

.option-desc {
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
