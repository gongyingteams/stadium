<template>
  <div :class="['app-root', { 'mock-mode': appStore.isMockMode }]">
    <component :is="layoutComponent">
      <router-view />
    </component>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import { useThemeStore } from '@/stores/theme'
import DefaultLayout from '@/layouts/DefaultLayout.vue'
import BlankLayout from '@/layouts/BlankLayout.vue'
import TabletLayout from '@/layouts/TabletLayout.vue'

const route = useRoute()
const appStore = useAppStore()
const userStore = useUserStore()
const themeStore = useThemeStore()

onMounted(async () => {
  themeStore.hydrate()
  if (userStore.isLoggedIn) {
    await userStore.refreshUser()
    await appStore.hydrateMockMode()
    await appStore.hydrateOperationalData()
  }
})

const layoutComponent = computed(() => {
  if (route.meta.layout === 'blank') {
    return BlankLayout
  }
  if (route.meta.layout === 'tablet') {
    return TabletLayout
  }
  return DefaultLayout
})
</script>

<style>
.app-root {
  min-height: 100vh;
  background-color: var(--do-bg-page);
  color: var(--do-text-primary);
}
</style>
