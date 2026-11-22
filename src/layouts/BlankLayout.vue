<template>
  <div class="blank-layout">
    <slot />
  </div>
</template>

<style scoped>
.blank-layout {
  min-height: 100vh;
  width: 100%;
  background: var(--do-bg-page);
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
