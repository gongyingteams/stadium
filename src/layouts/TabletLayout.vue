<template>
  <div class="tablet-layout">
    <!-- 平板专属顶部状态栏 -->
    <header class="tablet-header">
      <div class="left-brand">
        <SvgIcon name="SvgTablet" size="22" class="brand-icon" />
        <span class="system-title">体育场馆现场触控工作台</span>
        <span class="venue-tag">{{ appStore.currentVenue }}</span>
      </div>

      <div class="right-status">
        <div v-if="appStore.isMockMode" class="mock-tag">
          <span>● 模拟沙箱</span>
        </div>
        <div class="link-tag">
          <span class="status-dot online"></span>
          <span>链路正常 ({{ appStore.linkStats.online }}/{{ appStore.linkStats.total }})</span>
        </div>
        <div class="time-clock num-mono">
          {{ currentTime }}
        </div>
        <button class="btn-pc-switch" @click="goToPc">
          电脑端
        </button>
      </div>
    </header>

    <!-- 主操作区 (自适应铺满) -->
    <main class="tablet-body">
      <slot />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const appStore = useAppStore()

const currentTime = ref('')
let timer = null

const updateClock = () => {
  const now = new Date()
  currentTime.value = now.toTimeString().split(' ')[0]
}

onMounted(() => {
  updateClock()
  timer = setInterval(updateClock, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

const goToPc = () => {
  router.push('/dashboard')
}
</script>

<style scoped>
.tablet-layout {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--do-bg-page);
  overflow: hidden;
  user-select: none;
}

.tablet-header {
  height: 52px;
  background: var(--do-bg-header);
  border-bottom: 1px solid rgba(var(--th-accent-rgb), 0.3);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(var(--th-shadow-rgb), 0.25);
}

.left-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-icon {
  color: var(--do-gold);
}

.system-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--do-bg-card);
}

.venue-tag {
  font-size: 14px;
  color: var(--do-border);
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(var(--th-accent-rgb), 0.3);
  padding: 3px 10px;
  border-radius: 4px;
}

.right-status {
  display: flex;
  align-items: center;
  gap: 14px;
}

.mock-tag {
  font-size: 14px;
  color: var(--do-warning-deep);
  background: var(--do-warning-bg);
  border: 1px dashed var(--do-warning);
  padding: 3px 10px;
  border-radius: 4px;
  font-weight: 600;
}

.link-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: var(--do-success-bg);
  background: rgba(var(--th-success-rgb), 0.2);
  border: 1px solid var(--do-success);
  padding: 3px 10px;
  border-radius: 4px;
}

.time-clock {
  font-size: 16px;
  font-weight: bold;
  color: var(--do-gold);
  letter-spacing: 1px;
}

.btn-pc-switch {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(var(--th-accent-rgb), 0.35);
  color: var(--do-bg-card);
  font-size: 14px;
  padding: 5px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: var(--transition-fast);
}
.btn-pc-switch:hover {
  background: rgba(var(--th-accent-rgb), 0.2);
  border-color: var(--do-gold);
  color: var(--do-bg-card-hover);
}

.tablet-body {
  flex: 1;
  overflow: hidden;
  padding: 12px;
}
</style>
