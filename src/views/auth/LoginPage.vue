<template>
  <div class="login-wrapper">
    <!-- 撒哈拉微沙纹理与柔和场馆图腾底纹 -->
    <div class="sahara-bg-pattern"></div>

    <div class="login-card sahara-card">
      <!-- 场馆数字化徽标与系统标题 -->
      <div class="login-header">
        <div class="logo-shield-wrapper" aria-label="系统品牌标识">
          <div class="logo-shape">
            <img
              v-if="(systemSettings.logoType === 'CUSTOM' || !systemSettings.logoType) && (systemSettings.logoUrl || systemSettings.systemLogo)"
              :src="systemSettings.logoUrl || systemSettings.systemLogo" class="custom-login-logo" alt="系统Logo" />
            <SvgIcon v-else :name="systemSettings.logoPresetName || systemSettings.systemLogoPreset || 'SvgPortal'"
              size="64" class="logo-icon" />
          </div>
        </div>
        <div class="portal-kicker">VENUE OPERATIONS · SECURE ACCESS</div>
        <h1 class="portal-main-title">{{ systemSettings.systemName || '应用集成管控平台' }}</h1>
        <p class="portal-sub-desc">{{ systemSettings.systemSubTitle || '统一身份认证与单点登录管控门户' }}</p>
      </div>

      <!-- 快速身份切换演示栏 (UI已优化) -->
      <div class="quick-role-picker">
        <div class="picker-label">
          <span class="picker-label-mark"><i class="iconfont icon-safe"></i></span>
          <span>快速体验身份通道</span>
          <em>仅供评审演示</em>
        </div>
        <div class="role-tags">
          <span v-for="role in roleQuickList" :key="role.username"
            :class="['role-pill', { active: form.username === role.username }]" @click="pickRole(role)">
            <span>{{ role.label }}</span>
          </span>
        </div>
      </div>

      <!-- 登录表单 -->
      <el-form :model="form" class="login-form" @submit.prevent="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" class="industrial-input" placeholder="工号 / 登录账号" clearable>
            <template #prefix>
              <SvgIcon name="user" class="input-prefix-icon" />
            </template>
          </el-input>
        </el-form-item>

        <el-form-item prop="password">
          <el-input v-model="form.password" class="industrial-input" type="password" placeholder="登录密码" show-password>
            <template #prefix>
              <SvgIcon name="lock" class="input-prefix-icon" />
            </template>
          </el-input>
        </el-form-item>

        <div class="login-helpers">
          <el-checkbox v-model="form.rememberMe" class="custom-checkbox">保持 7 日单点会话</el-checkbox>
          <span class="security-tip">
            <SvgIcon name="warning" size="12" style="margin-right: 4px;" />
            密码连续错误 5 次锁定 15 分钟
          </span>
        </div>

        <button type="submit" class="btn-industrial btn-gold login-btn" :disabled="loading">
          <div v-if="loading" class="btn-loading">
            <div class="spinner"></div>
            <span>正在进行 RSA-2048 安全校验...</span>
          </div>
          <span v-else>立即安全登录</span>
        </button>
      </el-form>

      <!-- 底部版权与备案信息 -->
      <div class="login-footer">
        <p class="copyright-text">{{ systemSettings.copyrightText || 'Copyright © 2026 应用集成管控平台 版权所有' }}</p>
        <div class="beian-row">
          <span v-if="systemSettings.icpNumber" class="beian-item">
            {{ systemSettings.icpNumber }}
          </span>
          <span v-if="systemSettings.icpNumber && systemSettings.securityFilingNumber" class="beian-divider">|</span>
          <span v-if="systemSettings.securityFilingNumber" class="beian-item">
            <SvgIcon name="SvgSecurityShield" size="18" class="beian-icon" />
            {{ systemSettings.securityFilingNumber }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import { systemSettingService } from '@/services/systemSettingService'
import { ElMessage } from 'element-plus'

// 引入可能需要的图标，假设您使用了 unplugin-svg-icons
// 如果没有配置 SvgIcon，请替换为 Element Plus 的 <el-icon><User /></el-icon> 等
import SvgIcon from '@/components/SvgIcon.vue'

const router = useRouter()
const userStore = useUserStore()
const appStore = useAppStore()

// 读取系统配置并监听全局联动更新
const systemSettings = ref({ ...systemSettingService.getSettings() })

const onSettingsChange = (e) => {
  const latest = e?.detail || systemSettingService.getSettings()
  systemSettings.value = { ...latest }
  if (latest?.systemName) {
    document.title = `${latest.systemName} · 统一身份认证登录页`
  }
}

const onStorageChange = (e) => {
  if (e.key === 'ibms_system_settings_v1') {
    systemSettings.value = { ...systemSettingService.getSettings() }
  }
}

onMounted(async () => {
  window.addEventListener('ibms-system-settings-changed', onSettingsChange)
  window.addEventListener('storage', onStorageChange)
  
  // 关键：挂载时强制向后端拉取最新的公开系统品牌配置，确保未登录访客、新标签或隐身窗口立即可见
  try {
    const remote = await systemSettingService.fetchRemoteSettings()
    if (remote) {
      systemSettings.value = { ...remote }
      if (remote.systemName) {
        document.title = `${remote.systemName} · 统一身份认证登录页`
      }
    }
  } catch (err) {
    console.warn('LoginPage: 拉取公共系统配置异常，已使用缓存预设', err)
  }
})

onUnmounted(() => {
  window.removeEventListener('ibms-system-settings-changed', onSettingsChange)
  window.removeEventListener('storage', onStorageChange)
})

const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  rememberMe: false
})

const roleQuickList = [
  { username: 'admin', password: 'admin123', label: '系统管理员' },
  { username: 'ops', password: 'ops123', label: '运维工程师' },
  { username: 'operator', password: 'operator123', label: '现场操作员' },
  { username: 'viewer', password: 'viewer123', label: '只读监看员' }
]

const pickRole = (role) => {
  form.username = role.username
  form.password = role.password
}

const handleLogin = async () => {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入登录账号和密码')
    return
  }

  loading.value = true
  try {
    const result = await userStore.login(form.username.trim(), form.password)
    await appStore.hydrateMockMode()
    await appStore.hydrateOperationalData()
    ElMessage.success(`欢迎进入总控工作台，身份：${result.user.display_name}`)
    router.push(typeof router.currentRoute.value.query.redirect === 'string' ? router.currentRoute.value.query.redirect : '/dashboard')
  } catch (error) {
    ElMessage.error(error.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* ==============================================================================
   统一身份认证门户 · Sahara IBMS 自然主义工控美学
   全部色彩/圆角/阴影/动效一律复用全局令牌，保证与主控台完全一致
   ============================================================================== */
.login-wrapper {
  position: relative;
  min-height: 100svh;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 20px;
  box-sizing: border-box;
  background:
    radial-gradient(620px 500px at 50% 44%, rgba(255, 255, 255, 0.96), transparent 70%),
    radial-gradient(580px 440px at 8% 8%, rgba(var(--th-accent-rgb), 0.16), transparent 64%),
    radial-gradient(560px 420px at 92% 92%, rgba(var(--th-success-rgb), 0.11), transparent 64%),
    linear-gradient(145deg, #e8eff5 0%, #f5f8fa 48%, #eaf1f4 100%);
  overflow: hidden;
  font-family: var(--font-family-base);
}

/* 四角压暗，聚焦视线至登录卡片 */
.login-wrapper::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(980px 680px at 50% 44%, transparent 38%, rgba(44, 62, 78, 0.1) 100%);
  pointer-events: none;
}

/* 撒哈拉沙丘微光纹理底 */
.sahara-bg-pattern {
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(circle at 14% 20%, rgba(var(--th-accent-rgb), 0.13) 0 1px, transparent 1.5px),
    radial-gradient(circle at 78% 72%, rgba(var(--th-success-rgb), 0.08) 0 1px, transparent 1.5px),
    linear-gradient(125deg, transparent 0 47%, rgba(var(--th-accent-rgb), 0.1) 47.1% 47.2%, transparent 47.3%),
    linear-gradient(to right, rgba(var(--th-accent-rgb), 0.07) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(var(--th-accent-rgb), 0.07) 1px, transparent 1px);
  background-size: 140px 140px, 200px 200px, 100% 100%, 72px 72px, 72px 72px;
  pointer-events: none;
  opacity: 0.72;
}

.sahara-bg-pattern::before,
.sahara-bg-pattern::after {
  content: '';
  position: absolute;
  width: 34vw;
  height: 34vw;
  max-width: 520px;
  max-height: 520px;
  border: 1px solid rgba(var(--th-accent-rgb), 0.14);
  border-radius: 50%;
}

.sahara-bg-pattern::before {
  left: -12vw;
  top: -15vw;
}

.sahara-bg-pattern::after {
  right: -14vw;
  bottom: -18vw;
  border-color: rgba(var(--th-success-rgb), 0.10);
}

/* 大马士革象牙白登录卡片 */
.login-card {
  width: min(100%, 468px);
  padding: 42px 44px 30px;
  position: relative;
  z-index: 10;
  box-sizing: border-box;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.98), rgba(247, 250, 252, 0.97));
  box-shadow: 0 24px 60px rgba(31, 54, 73, 0.16), 0 4px 14px rgba(31, 54, 73, 0.08);
  border-radius: 22px;
  border: 1px solid rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(14px);
}

/* 卡片顶部阿特拉斯金工控饰线 */
.login-card::after {
  content: '';
  position: absolute;
  top: 0;
  left: 12%;
  right: 12%;
  height: 4px;
  border-radius: 0 0 8px 8px;
  background: linear-gradient(90deg, transparent, #4c82c7 20%, #78a6dc 50%, #4c82c7 80%, transparent);
  opacity: 0.95;
}

.login-header {
  position: relative;
  z-index: 1;
  text-align: center;
  margin-bottom: 28px;
}

.logo-shield-wrapper {
  margin: 0 auto 14px;
  display: flex;
  justify-content: center;
}

.logo-shape {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  width: 112px;
  height: 112px;
  border-radius: 28px;
  background: linear-gradient(145deg, #eef5fc, #ffffff);
  border: 1px solid #d9e5f0;
  box-shadow: 0 12px 24px rgba(51, 93, 132, 0.13), inset 0 1px 0 #ffffff;
}

.logo-icon {
  position: relative;
  z-index: 1;
  color: #3174c5;
  width: 72px;
  height: 72px;
  filter: drop-shadow(0 5px 12px rgba(49, 116, 197, 0.24));
}

.custom-login-logo {
  width: 86px;
  height: 86px;
  object-fit: contain;
  position: relative;
  z-index: 1;
  border-radius: 12px;
  filter: drop-shadow(0 5px 12px rgba(29, 65, 102, 0.12));
}

.portal-kicker {
  margin-bottom: 8px;
  color: #5c7d9d;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1.8px;
}

.portal-main-title {
  font-size: 23px;
  font-weight: 700;
  color: #203142;
  margin: 0 0 7px;
  letter-spacing: 0.8px;
  line-height: 1.3;
}

.portal-sub-desc {
  font-size: var(--fs-body);
  color: #718397;
  margin: 0;
  letter-spacing: 0.6px;
}

/* 快速身份通道 */
.quick-role-picker {
  position: relative;
  z-index: 1;
  background: #f4f8fb;
  border-radius: 16px;
  padding: 14px 15px 15px;
  margin-bottom: 22px;
  border: 1px solid #dce8f1;
}

.picker-label {
  font-size: var(--fs-sm);
  color: var(--do-text-secondary);
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  font-weight: 600;
  letter-spacing: 0.1px;
  gap: 7px;
}

.picker-label-mark {
  width: 20px;
  height: 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 7px;
  color: #3b78bd;
  background: #e2eef9;
}

.picker-label em {
  margin-left: auto;
  color: #95a4b3;
  font-size: 11px;
  font-style: normal;
  font-weight: 500;
}

.role-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  width: 100%;
}

.role-pill {
  flex: 1 1 calc(50% - 4px);
  min-width: 0;
  min-height: 36px;
  box-sizing: border-box;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  white-space: nowrap;
  font-size: 13px;
  line-height: 1.2;
  padding: 8px 10px;
  background: #ffffff;
  color: #516274;
  border-radius: 11px;
  cursor: pointer;
  transition: var(--transition-fast);
  border: 1px solid #d8e3ec;
  user-select: none;
  box-shadow: 0 2px 6px rgba(35, 67, 95, 0.05);
}

.role-pill:hover {
  transform: translateY(-1px);
  background: var(--do-bg-card-hover);
  color: var(--do-gold-deep);
  border-color: var(--do-gold);
  box-shadow: var(--shadow-sm);
}

.role-pill.active {
  background: linear-gradient(135deg, #4389d8, #2e6fbe);
  color: #FFFFFF;
  font-weight: 700;
  border-color: #2e6fbe;
  box-shadow: 0 5px 12px rgba(46, 111, 190, 0.24);
}

.login-form {
  position: relative;
  z-index: 1;
  margin-top: 8px;
}

::v-deep(.login-form .el-form-item) {
  margin-bottom: 15px;
}

::v-deep(.login-form .el-form-item:last-of-type) {
  margin-bottom: 0;
}

/* 工控质感输入框 */
::v-deep(.industrial-input .el-input__wrapper) {
  min-height: 50px;
  box-sizing: border-box;
  background: #f7fafc;
  border-radius: 12px;
  box-shadow: inset 0 0 0 1px #d9e4ed;
  padding: 0 14px;
  transition: var(--transition-fast);
}

::v-deep(.industrial-input .el-input__wrapper:hover) {
  background: #ffffff;
  box-shadow: inset 0 0 0 1px #7fa9d3, 0 3px 12px rgba(49, 95, 137, 0.08);
}

::v-deep(.industrial-input .el-input__wrapper.is-focus) {
  background: #ffffff;
  box-shadow: inset 0 0 0 1.5px #4389d8, 0 0 0 4px rgba(67, 137, 216, 0.13);
}

::v-deep(.industrial-input .el-input__inner) {
  color: var(--do-text-primary);
  font-size: var(--fs-body);
  padding: 8px 4px;
}

::v-deep(.industrial-input .el-input__inner::placeholder) {
  color: var(--do-text-placeholder);
}

.input-prefix-icon {
  color: #4389d8;
  margin-right: 7px;
  width: 16px;
  height: 16px;
}

.login-helpers {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin: 3px 2px 22px;
}

.security-tip {
  color: #7b8c9c;
  font-size: var(--fs-sm);
  line-height: 1.4;
  display: flex;
  align-items: center;
  text-align: right;
}

::v-deep(.custom-checkbox .el-checkbox__label) {
  font-size: var(--fs-sm);
  color: var(--do-text-regular);
}

::v-deep(.custom-checkbox .el-checkbox__inner) {
  width: 15px;
  height: 15px;
  border-color: var(--do-border);
  background: var(--do-bg-input);
  border-radius: var(--radius-sm);
}

::v-deep(.custom-checkbox.is-checked .el-checkbox__inner) {
  background-color: var(--do-gold);
  border-color: var(--do-gold-deep);
}

/* 阿特拉斯金主按钮 */
.btn-industrial {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  font-weight: 600;
  transition: var(--transition-fast);
  cursor: pointer;
  font-family: inherit;
}

.btn-gold {
  background: linear-gradient(180deg, var(--do-gold-hover) 0%, var(--do-gold) 55%, var(--do-gold-deep) 100%);
  color: #FFFFFF;
  border-color: var(--do-gold-deep);
  box-shadow: 0 8px 18px rgba(var(--th-accent-deep-rgb), 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.24);
}

.btn-gold:hover:not(:disabled) {
  background: linear-gradient(180deg, var(--do-gold-hover) 0%, var(--do-gold-hover) 55%, var(--do-gold) 100%);
  transform: translateY(-1px);
  box-shadow: 0 12px 24px rgba(var(--th-accent-deep-rgb), 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.28);
}

.btn-gold:active:not(:disabled) {
  transform: translateY(0);
}

.btn-gold:disabled {
  background: var(--do-text-placeholder);
  border-color: var(--do-border);
  color: var(--do-bg-card-hover);
  cursor: not-allowed;
  opacity: 0.7;
  box-shadow: none;
}

.login-btn {
  width: 100%;
  height: 50px;
  font-size: var(--fs-h3);
  letter-spacing: 0.6px;
  border-radius: var(--radius-md);
}

/* 简易加载 Spinner */
.spinner {
  width: 15px;
  height: 15px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-radius: 50%;
  border-top-color: #FFFFFF;
  animation: spin 0.8s linear infinite;
}

.login-footer {
  position: relative;
  z-index: 1;
  text-align: center;
  margin-top: 28px;
  border-top: 1px solid var(--do-border-light);
  padding-top: 17px;
  font-size: var(--fs-sm);
  color: var(--do-text-secondary);
  line-height: 1.6;
}

.login-footer p {
  margin: 0;
}

.copyright-text {
  letter-spacing: 0.2px;
}

.beian-row {
  margin-top: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 13px;
  color: var(--do-text-placeholder);
}

.beian-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  letter-spacing: 0.2px;
}

.beian-divider {
  color: var(--do-border);
  font-size: 10px;
}

.beian-icon {
  color: #4d86c5;
  flex-shrink: 0;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(var(--th-accent-rgb), 0.4);
  }

  70% {
    box-shadow: 0 0 0 10px transparent;
  }

  100% {
    box-shadow: 0 0 0 0 transparent;
  }
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

@media (max-width: 560px) {
  .login-wrapper {
    align-items: flex-start;
    padding: 22px 14px;
  }

  .login-card {
    width: 100%;
    padding: 32px 20px 24px;
    border-radius: var(--radius-lg);
  }

  .role-tags {
    flex-wrap: wrap;
  }

  .role-pill {
    flex: 1 1 calc(50% - 8px);
  }

  .picker-label {
    align-items: flex-start;
  }

  .picker-label em {
    max-width: 100px;
    line-height: 1.3;
    text-align: right;
  }

  .portal-main-title {
    font-size: 19px;
    letter-spacing: 0.4px;
  }

  .login-helpers {
    flex-direction: column;
    align-items: flex-start;
  }

  .security-tip {
    text-align: left;
  }
}

@media (prefers-reduced-motion: reduce) {

  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
