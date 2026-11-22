<template>
  <div class="system-setting-container">
    <!-- 隐藏的原生文件上传选择器 (用于选取本地Logo图片) -->
    <input
      ref="logoFileInputRef"
      type="file"
      style="display: none"
      accept="image/png,image/jpeg,image/svg+xml,image/webp,image/gif"
      @change="handleLogoFileSelected"
    />

    <!-- 1. 顶部操作与标题面板 -->
    <div class="setting-header-panel glass-panel">
      <div class="header-left-meta page-heading">
        <div class="header-icon-box">
          <SvgIcon name="SvgSettingGear" size="24" />
        </div>
        <div class="header-title-group">
          <div class="title-row">
            <h1 class="page-title">系统基础设置与存储配置</h1>
            <span class="setting-badge">SYSTEM CONFIG</span>
          </div>
          <p class="page-desc">
            统一维护场馆管理平台系统Logo标牌、版权法律声明以及本地文件系统/云端OSS对象存储引擎。
          </p>
        </div>
      </div>

      <div class="header-action-group">
        <button class="btn-header-action btn-header-neutral" @click="confirmResetSettings" title="恢复场馆管理平台出厂预设品牌与存储参数">
          <el-icon><RefreshRight /></el-icon>
          <span>恢复出厂默认</span>
        </button>
        <button
          class="btn-header-action btn-header-primary"
          :disabled="isSaving"
          @click="saveSystemSettings"
          title="持久化并保存系统品牌与存储参数配置"
        >
          <el-icon><Check /></el-icon>
          <span>{{ isSaving ? '正在保存中...' : '保存全部配置' }}</span>
        </button>
      </div>
    </div>

    <!-- 2. 主体两栏布局：左侧表单编辑区 (68%) + 右侧实时效果仿真看板 (32%) -->
    <div class="setting-main-grid">
      <!-- 左侧：多板块表单设置区域 -->
      <div class="form-scroll-column">
        <!-- 板块 1: 系统Logo与品牌标牌设置 -->
        <div class="setting-card glass-panel">
          <div class="card-section-head">
            <div class="section-title-wrap">
              <span class="section-num">01</span>
              <h2 class="section-title">系统品牌与 Logo 标牌设置</h2>
            </div>
            <span class="section-tag">品牌形象</span>
          </div>

          <div class="card-section-body">
            <!-- Logo上传与形态选择 -->
            <div class="logo-config-layout">
              <!-- 左侧：交互式Logo展示预览台 -->
              <div class="logo-preview-stage">
                <div class="stage-label">当前生效 Logo 预览:</div>
                <div class="logo-display-box" :class="{ 'is-custom': form.logoType === 'CUSTOM' && form.logoUrl }">
                  <img
                    v-if="form.logoType === 'CUSTOM' && form.logoUrl"
                    :src="form.logoUrl"
                    class="custom-logo-img"
                    alt="系统自定义Logo"
                  />
                  <div v-else class="preset-logo-wrap">
                    <SvgIcon :name="form.logoPresetName || 'SvgPortal'" size="38" />
                  </div>
                </div>

                <div class="stage-actions">
                  <el-button type="primary" class="upload-logo-btn" @click="triggerSelectLogoFile">
                    <el-icon class="mr-1"><Upload /></el-icon>
                    上传新 Logo
                  </el-button>
                  <el-button
                    v-if="form.logoType === 'CUSTOM' && form.logoUrl"
                    class="clear-logo-btn"
                    @click="resetToPresetLogo"
                  >
                    恢复默认图标
                  </el-button>
                </div>
                <span class="upload-tip-text">推荐规格: 1:1 正方形 (48×48px+) 或透明底 PNG/SVG，大小 ≤ 2MB</span>
              </div>

              <!-- 右侧：品牌文字信息配置 -->
              <div class="brand-text-fields">
                <el-form label-position="top" class="custom-setting-form">
                  <el-form-item label="系统平台全称 (顶部Header与登录页主标题)">
                    <el-input
                      v-model="form.systemName"
                      placeholder="例如：体育场馆应用集成管控平台"
                      maxlength="32"
                      show-word-limit
                    />
                  </el-form-item>

                  <el-form-item label="系统副标题 / 英文代号 (主标牌副标识)">
                    <el-input
                      v-model="form.systemSubTitle"
                      placeholder="例如：IBMS CONSOLE v1.0"
                      maxlength="30"
                    />
                  </el-form-item>

                  <el-form-item label="系统预设矢量图标库 (未上传自定义图片时使用)">
                    <div class="preset-icon-selector">
                      <div
                        v-for="item in presetIcons"
                        :key="item.name"
                        :class="['preset-icon-chip', { active: form.logoPresetName === item.name && form.logoType === 'PRESET' }]"
                        @click="selectPresetLogo(item.name)"
                      >
                        <SvgIcon :name="item.name" size="20" />
                        <span class="icon-chip-label">{{ item.label }}</span>
                      </div>
                    </div>
                  </el-form-item>

                  <div class="card-inline-action-bar" style="margin-top: 16px; display: flex; justify-content: flex-end;">
                    <el-button type="primary" :loading="isSaving" @click="saveSystemSettings" style="background: linear-gradient(135deg, #0284C7, #0369A1); border: none;">
                      <el-icon style="margin-right: 4px;"><Check /></el-icon>
                      保存品牌与标牌设置
                    </el-button>
                  </div>
                </el-form>
              </div>
            </div>
          </div>
        </div>

        <!-- 板块 2: 版权信息与备案法律声明 -->
        <div class="setting-card glass-panel">
          <div class="card-section-head">
            <div class="section-title-wrap">
              <span class="section-num">02</span>
              <h2 class="section-title">版权所有信息与备案权属</h2>
            </div>
            <span class="section-tag">法律合规</span>
          </div>

          <div class="card-section-body">
            <el-form label-position="top" class="custom-setting-form">
              <div class="form-two-cols">
                <el-form-item label="完整版权说明文字 (Copyright Statement)">
                  <el-input
                    v-model="form.copyrightText"
                    placeholder="例如：Copyright © 2026 体育场馆应用集成管控平台 版权所有"
                  />
                </el-form-item>

                <el-form-item label="版权归属主体机构">
                  <el-input
                    v-model="form.copyrightOwner"
                    placeholder="例如：华体智能体育场馆集成工程技术中心"
                  />
                </el-form-item>
              </div>

              <div class="form-three-cols">
                <el-form-item label="版权有效年份跨度">
                  <el-input v-model="form.copyrightYears" placeholder="2024 - 2026" />
                </el-form-item>

                <el-form-item label="工信部 ICP 备案号">
                  <el-input v-model="form.icpNumber" placeholder="例如：京ICP备20260118号-1" />
                </el-form-item>

                <el-form-item label="全国公安机关网安备案号">
                  <el-input v-model="form.securityFilingNumber" placeholder="例如：京公网安备 11010802026001号" />
                </el-form-item>
              </div>

              <el-form-item label="商业使用授权等级声明">
                <el-input v-model="form.commercialLicense" placeholder="例如：商业授权版 (Enterprise Tier - 26台纳管设备全功能就绪)" />
              </el-form-item>
            </el-form>
          </div>
        </div>

        <!-- 板块 3: 文件与对象存储配置 (本地存储 / 云端OSS存储) -->
        <div class="setting-card glass-panel">
          <div class="card-section-head">
            <div class="section-title-wrap">
              <span class="section-num">03</span>
                <h2 class="section-title">文件与对象存储配置 (本地存储 / 阿里云 / 腾讯云)</h2>
                <p class="section-desc">管理场馆多媒体大屏视频、广播音频、设备固件及应用素材的本地物理落盘与云端分发引擎</p>
            </div>
            <!-- 右侧：当前生产激活存储引擎快速徽章 -->
            <div class="active-engine-badge">
              <span class="status-indicator-dot online"></span>
              <span class="badge-label">生产环境当前生效：</span>
              <strong class="badge-value">{{ getActiveVendorInfo().name }}</strong>
            </div>
          </div>

          <div class="card-section-body">
            <!-- 1. 核心态势大横幅：当前系统生效运行存储引擎看板 (Hero Status Banner) -->
            <div class="storage-active-hero-banner">
              <div class="hero-left-info">
                <div class="hero-status-pill">
                  <span class="pulse-dot"></span>
                  <span class="status-text">系统当前生产激活存储模式 · RUNNING</span>
                </div>
                <div class="hero-main-title">
                  <span class="hero-engine-name">{{ getActiveVendorInfo().name }}</span>
                  <span class="hero-engine-sub num-mono">({{ getActiveVendorInfo().subTitle }})</span>
                  <span class="hero-engine-driver-tag" :class="form.storageDriver.toLowerCase()">
                    {{ form.storageDriver === 'LOCAL' ? '本地文件系统 POSIX' : '云端对象存储 S3 REST' }}
                  </span>
                </div>
                <div class="hero-engine-specs">
                  <div v-if="form.storageDriver === 'LOCAL'" class="spec-chip">
                    <span class="spec-k">落盘根目录:</span>
                    <span class="spec-v num-mono">{{ form.localConfig.storagePath }}</span>
                  </div>
                  <div v-if="form.storageDriver === 'LOCAL'" class="spec-chip">
                    <span class="spec-k">反代前缀:</span>
                    <span class="spec-v num-mono">{{ form.localConfig.urlPrefix }}</span>
                  </div>
                  <div v-if="form.storageDriver === 'LOCAL'" class="spec-chip">
                    <span class="spec-k">单文件配额:</span>
                    <span class="spec-v num-mono">{{ form.localConfig.maxFileSizeMb }} MB</span>
                  </div>
                  <div v-if="form.storageDriver === 'OSS'" class="spec-chip">
                    <span class="spec-k">存储桶 (Bucket):</span>
                    <span class="spec-v num-mono" :style="{ color: form.ossConfig.bucket ? 'inherit' : '#EF4444' }">
                      {{ form.ossConfig.bucket || '未配置真实Bucket' }}
                    </span>
                  </div>
                  <div v-if="form.storageDriver === 'OSS'" class="spec-chip">
                    <span class="spec-k">接入节点 (Endpoint):</span>
                    <span class="spec-v num-mono" :style="{ color: form.ossConfig.endpoint ? 'inherit' : '#EF4444' }">
                      {{ form.ossConfig.endpoint || '未配置' }}
                    </span>
                  </div>
                  <div v-if="form.storageDriver === 'OSS'" class="spec-chip">
                    <span class="spec-k">访问控制:</span>
                    <span class="spec-v">{{ form.ossConfig.acl === 'public-read' ? '公共读 (推荐)' : (form.ossConfig.acl === 'private' ? '私有鉴权' : '公共读写') }}</span>
                  </div>
                </div>
              </div>

              <!-- 右侧健康度与快捷操作 -->
              <div class="hero-right-actions">
                <div class="health-indicator-box">
                  <span class="health-title">连通性健康探针</span>
                  <div v-if="lastTestStatus.tested" class="health-result" :class="{ success: lastTestStatus.success, failed: !lastTestStatus.success }">
                    <el-icon v-if="lastTestStatus.success"><CircleCheck /></el-icon>
                    <el-icon v-else><CircleClose /></el-icon>
                    <span>{{ lastTestStatus.success ? `探针正常 (${lastTestStatus.latency})` : '探针握手异常' }}</span>
                  </div>
                  <div v-else class="health-result pending">
                    <el-icon><InfoFilled /></el-icon>
                    <span>尚未执行网络握手探针</span>
                  </div>
                </div>

                <div class="hero-btn-group">
                  <el-button
                    v-if="form.storageDriver === 'OSS'"
                    type="primary"
                    size="small"
                    class="hero-probe-btn"
                    :loading="isTestingOss"
                    @click="handleTestOssConnection"
                  >
                    <el-icon class="mr-1"><Link /></el-icon>
                    测试连通性 (真实探针)
                  </el-button>
                  <el-button
                    v-else
                    type="primary"
                    size="small"
                    class="hero-probe-btn"
                    :loading="isTestingLocal"
                    @click="handleTestLocalStorage"
                  >
                    <el-icon class="mr-1"><FolderChecked /></el-icon>
                    检测本地路径与读写
                  </el-button>
                </div>
              </div>
            </div>

            <!-- 2. 存储引擎选型卡片矩阵 (Card Grid) -->
            <div class="engine-selector-container">
              <div class="selector-header">
                <span class="selector-title">
                  <el-icon class="mr-1"><Operation /></el-icon>
                  存储引擎模式矩阵 (点击卡片切换配置，一键设为系统激活引擎)
                </span>
                <span class="selector-tip">注：切换激活引擎或修改参数后，点击页面右上角【保存全部配置】在全系统生效</span>
              </div>

              <div class="engine-cards-grid">
                <div
                  v-for="v in storageVendors"
                  :key="v.key"
                  class="engine-card"
                  :class="{
                    'is-active-running': isCurrentActive(v.key),
                    'is-editing': currentEditingVendor === v.key
                  }"
                  @click="selectEditingVendor(v.key)"
                >
                  <div class="card-head">
                    <div class="vendor-icon-wrap">
                      <el-icon v-if="v.key === 'LOCAL'"><Folder /></el-icon>
                      <el-icon v-else><Cloudy /></el-icon>
                    </div>
                    <div class="vendor-name-meta">
                      <span class="v-name">{{ v.name }}</span>
                      <span class="v-sub num-mono">{{ v.subTitle }}</span>
                    </div>
                    <span class="v-tag">{{ v.badge }}</span>
                  </div>

                  <p class="card-desc">{{ v.desc }}</p>

                  <div class="card-footer">
                    <span v-if="isCurrentActive(v.key)" class="active-pill">
                      <el-icon><Check /></el-icon>
                      当前激活生效
                    </span>
                    <button
                      v-else
                      type="button"
                      class="set-active-action-btn"
                      @click.stop="setActiveVendor(v.key)"
                    >
                      设为当前激活模式
                    </button>
                    <span v-if="currentEditingVendor === v.key" class="editing-indicator">正在编辑</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 3. 具体表单编辑区 (根据 currentEditingVendor 切换表单) -->
            <!-- 3.A 本地存储表单 -->
            <div v-if="currentEditingVendor === 'LOCAL'" class="storage-sub-form">
              <div class="sub-form-header">
                <div class="sub-form-title">
                  <el-icon><FolderChecked /></el-icon>
                  <span>本地文件系统物理存储参数配置</span>
                </div>
                <el-button
                  type="success"
                  size="small"
                  plain
                  :loading="isTestingLocal"
                  @click="handleTestLocalStorage"
                >
                  <el-icon class="mr-1"><CircleCheck /></el-icon>
                  测试本地目录读写与规范
                </el-button>
              </div>

              <el-form label-position="top" class="custom-setting-form mt-2">
                <div class="form-two-cols">
                  <el-form-item label="服务器本地物理落盘目录 (Storage Path)">
                    <el-input v-model="form.localConfig.storagePath" placeholder="/data/venue-ibms/uploads/ 或 D:/uploads/gym/" />
                    <span class="input-helper-tip">必须为 Linux 绝对路径（如 /data/...）或 Windows 盘符路径（如 D:/...）</span>
                  </el-form-item>

                  <el-form-item label="资源外链反代访问前缀 (URL Prefix)">
                    <el-input v-model="form.localConfig.urlPrefix" placeholder="/uploads/" />
                    <span class="input-helper-tip">推荐使用同源相对前缀 /uploads/（自动跟随当前域名与端口）；如需独立媒体域名可填写完整 http(s) 地址</span>
                  </el-form-item>
                </div>

                <div class="form-two-cols">
                  <el-form-item label="单文件上传体积上限 (MB)">
                    <el-input-number
                      v-model="form.localConfig.maxFileSizeMb"
                      :min="1"
                      :max="2048"
                      :step="10"
                      class="full-width-number"
                    />
                  </el-form-item>

                  <el-form-item label="允许上传的文件扩展名白名单">
                    <el-input
                      v-model="form.localConfig.allowedExtensions"
                      placeholder=".jpg,.png,.svg,.webp,.mp3,.wav,.mp4,.json,.bin,.pdf"
                    />
                  </el-form-item>
                </div>
              </el-form>
            </div>

            <!-- 3.B 云端 OSS / COS 对象存储表单 -->
            <div v-else class="storage-sub-form">
              <div class="sub-form-header">
                <div class="sub-form-title">
                  <el-icon><Cloudy /></el-icon>
                  <span>{{ getVendorNameByKey(currentEditingVendor) }} 参数配置与连通探测</span>
                </div>
                <div class="sub-form-actions">
                  <el-button
                    type="primary"
                    class="test-oss-btn"
                    :loading="isTestingOss"
                    @click="handleTestOssConnection"
                  >
                    <el-icon class="mr-1"><Link /></el-icon>
                    测试连通性 (真实网络握手探针)
                  </el-button>
                </div>
              </div>

              <!-- 严谨校验说明警告栏 -->
              <div class="probe-notice-bar">
                <el-icon><WarningFilled /></el-icon>
                <span>
                  <strong>严谨工业级连通性探测引擎：</strong>
                  本测试会严格校验 Bucket 命名规范 (仅支持 3~63 位小写字母/数字/短横线，严禁大写或中文)、厂商 AK/SK 格式特征，并通过浏览器发起底层 HEAD 探针真实握手。若参数错误或节点不可达将坚决拦截并给出错误诊断！
                </span>
              </div>

              <el-form label-position="top" class="custom-setting-form mt-3">
                <div class="form-three-cols">
                  <el-form-item label="对象存储服务商协议 (Cloud Vendor)">
                    <el-select v-model="form.ossConfig.vendor" class="full-width-select" @change="onVendorSelectChange">
                      <el-option label="阿里云对象存储 (Aliyun OSS)" value="ALIYUN" />
                      <el-option label="腾讯云对象存储 (Tencent COS)" value="TENCENT" />
                    </el-select>
                  </el-form-item>

                  <el-form-item label="存储桶名称 (Bucket Name)">
                    <el-input v-model="form.ossConfig.bucket" placeholder="例如：venue-ibms-assets-bucket" />
                    <span class="input-helper-tip">必须为 3~63 位小写字母、数字或中划线，不可包含大写字母与下划线</span>
                  </el-form-item>

                  <el-form-item label="访问节点 (Endpoint)">
                    <el-input v-model="form.ossConfig.endpoint" placeholder="例如：oss-cn-beijing.aliyuncs.com 或 cos.ap-beijing.myqcloud.com" />
                    <span class="input-helper-tip">阿里云地域节点 (如 oss-cn-beijing.aliyuncs.com) 或腾讯云地域节点 (如 cos.ap-beijing.myqcloud.com)</span>
                  </el-form-item>
                </div>

                <div class="form-two-cols">
                  <el-form-item label="访问密钥 ID (AccessKey ID / SecretId)">
                    <el-input v-model="form.ossConfig.accessKeyId" placeholder="例如阿里云以 LTAI 开头，腾讯云以 AKID 开头" />
                  </el-form-item>

                  <el-form-item label="访问密钥密钥 (AccessKey Secret / SecretKey)">
                    <el-input
                      v-model="form.ossConfig.accessKeySecret"
                      :type="showSecretKey ? 'text' : 'password'"
                      placeholder="云厂商 IAM 安全凭证中心签发的访问密钥"
                    >
                      <template #suffix>
                        <el-button
                          type="text"
                          class="toggle-eye-btn"
                          @click="showSecretKey = !showSecretKey"
                        >
                          <el-icon><View v-if="showSecretKey" /><Hide v-else /></el-icon>
                        </el-button>
                      </template>
                    </el-input>
                  </el-form-item>
                </div>

                <div class="form-three-cols">
                  <el-form-item label="自定义 CDN 加速域名 (Custom CDN Domain)">
                    <el-input v-model="form.ossConfig.customDomain" placeholder="https://cdn-assets.venue-ibms.com" />
                  </el-form-item>

                  <el-form-item label="对象落盘目录前缀 (Path Prefix)">
                    <el-input v-model="form.ossConfig.pathPrefix" placeholder="venue-assets/2026-sport/" />
                  </el-form-item>

                  <el-form-item label="对象读写访问权限 (ACL 策略)">
                    <el-select v-model="form.ossConfig.acl" class="full-width-select">
                      <el-option label="公共读 (Public Read · 推荐)" value="public-read" />
                      <el-option label="私有鉴权 (Private Signed)" value="private" />
                      <el-option label="公共读写 (Public Read/Write · 慎用)" value="public-read-write" />
                    </el-select>
                  </el-form-item>
                </div>
              </el-form>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：前台实时效果仿真看板 (所见即所得 Live Showcase) -->
      <div class="preview-sticky-column">
        <div class="showcase-card glass-panel">
          <div class="showcase-head">
            <div class="showcase-title">
              <el-icon class="preview-sparkle"><Compass /></el-icon>
              <span>前台效果动态仿真看板</span>
            </div>
            <span class="live-pill">实时同步预览</span>
          </div>

          <div class="showcase-body">
            <!-- 仿真 1: 顶部 Header Bar 仿真 -->
            <div class="mock-device-window">
              <div class="window-titlebar">
                <span class="win-dot red"></span>
                <span class="win-dot yellow"></span>
                <span class="win-dot green"></span>
                <span class="win-label">顶部导航栏 (Header) 仿真视窗</span>
              </div>
              <div class="mock-header-content">
                <div class="mock-left-brand">
                  <div class="mock-logo-box">
                    <img
                      v-if="form.logoType === 'CUSTOM' && form.logoUrl"
                      :src="form.logoUrl"
                      class="mock-img"
                      alt="mock-logo"
                    />
                    <SvgIcon v-else :name="form.logoPresetName || 'SvgPortal'" size="18" />
                  </div>
                  <div class="mock-titles">
                    <span class="mock-main-name">{{ form.systemName || '体育场馆管控平台' }}</span>
                    <span class="mock-sub-name">{{ form.systemSubTitle || 'IBMS CONSOLE v1.0' }}</span>
                  </div>
                </div>

                <div class="mock-right-env">
                  <span class="mock-env-tag">正式环境</span>
                </div>
              </div>
            </div>

            <!-- 仿真 2: 登录认证页品牌卡片仿真 -->
            <div class="mock-device-window mt-3">
              <div class="window-titlebar">
                <span class="win-label">登录界面品牌标牌卡片</span>
              </div>
              <div class="mock-login-badge-content">
                <div class="login-badge-avatar">
                  <img
                    v-if="form.logoType === 'CUSTOM' && form.logoUrl"
                    :src="form.logoUrl"
                    class="mock-img-large"
                    alt="mock-login-logo"
                  />
                  <SvgIcon v-else :name="form.logoPresetName || 'SvgPortal'" size="32" />
                </div>
                <h3 class="login-brand-title">{{ form.systemName || '体育场馆应用集成管控平台' }}</h3>
                <span class="login-brand-sub">{{ form.systemSubTitle || 'IBMS CONSOLE v1.0' }}</span>
                <span class="login-license-tag">{{ form.commercialLicense || '商业授权企业版' }}</span>
              </div>
            </div>

            <!-- 仿真 3: 页脚版权与备案信息仿真 -->
            <div class="mock-device-window mt-3">
              <div class="window-titlebar">
                <span class="win-label">页脚版权与备案信息条</span>
              </div>
              <div class="mock-footer-content">
                <p class="mock-foot-copy">{{ form.copyrightText || 'Copyright © 2026 版权所有' }}</p>
                <div class="mock-beian-row">
                  <span class="beian-item">{{ form.icpNumber || '京ICP备20260118号-1' }}</span>
                  <span class="beian-item">{{ form.securityFilingNumber || '京公网安备' }}</span>
                </div>
              </div>
            </div>

            <!-- 仿真 4: 当前对象存储引擎状态卡片 -->
            <div class="storage-summary-card mt-3">
              <div class="summary-top-row">
                <span class="summary-lbl">当前生产激活存储模式:</span>
                <span class="driver-tag" :class="form.storageDriver.toLowerCase()">
                  {{ getActiveVendorInfo().name }}
                </span>
              </div>
              <div class="summary-mode-banner">
                <span class="active-pulse-circle"></span>
                <span class="active-mode-title">{{ form.storageDriver === 'LOCAL' ? '本地工控机物理磁盘持久化' : `${getActiveVendorInfo().subTitle} 云端对象存储` }}</span>
              </div>
              <div class="summary-details">
                <div v-if="form.storageDriver === 'OSS'" class="detail-row">
                  <span class="detail-k">云服务商:</span>
                  <span class="detail-v">{{ form.ossConfig.vendor }}</span>
                </div>
                <div v-if="form.storageDriver === 'OSS'" class="detail-row">
                  <span class="detail-k">Bucket:</span>
                  <span class="detail-v num-mono" :style="{ color: form.ossConfig.bucket ? 'inherit' : '#EF4444' }">
                    {{ form.ossConfig.bucket || '未配置' }}
                  </span>
                </div>
                <div v-if="form.storageDriver === 'OSS'" class="detail-row">
                  <span class="detail-k">接入节点:</span>
                  <span class="detail-v num-mono" :style="{ color: form.ossConfig.endpoint ? 'inherit' : '#EF4444' }">
                    {{ form.ossConfig.endpoint || '未配置' }}
                  </span>
                </div>
                <div v-if="form.storageDriver === 'OSS'" class="detail-row">
                  <span class="detail-k">读写权限:</span>
                  <span class="detail-v num-mono">{{ form.ossConfig.acl }}</span>
                </div>
                <div v-if="form.storageDriver === 'LOCAL'" class="detail-row">
                  <span class="detail-k">落盘路径:</span>
                  <span class="detail-v num-mono">{{ form.localConfig.storagePath }}</span>
                </div>
                <div v-if="form.storageDriver === 'LOCAL'" class="detail-row">
                  <span class="detail-k">单文件上限:</span>
                  <span class="detail-v num-mono">{{ form.localConfig.maxFileSizeMb }} MB</span>
                </div>
                <div class="detail-row">
                  <span class="detail-k">探针健康度:</span>
                  <span class="detail-v" :style="{ color: lastTestStatus.tested ? (lastTestStatus.success ? '#10B981' : '#EF4444') : '#F59E0B' }">
                    {{ lastTestStatus.tested ? (lastTestStatus.success ? `已就绪 (${lastTestStatus.latency})` : '探针未通过') : '待连通测试' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import SvgIcon from '@/components/SvgIcon.vue'
import {
  systemSettingService,
  DEFAULT_SYSTEM_SETTINGS
} from '@/services/systemSettingService'
import {
  Check,
  RefreshRight,
  Upload,
  Folder,
  FolderChecked,
  Cloudy,
  Connection,
  Link,
  View,
  Hide,
  Compass,
  CircleCheck,
  CircleClose,
  InfoFilled,
  Operation,
  WarningFilled
} from '@element-plus/icons-vue'

// 表单响应式数据
const form = reactive({
  ...DEFAULT_SYSTEM_SETTINGS,
  localConfig: { ...DEFAULT_SYSTEM_SETTINGS.localConfig },
  ossConfig: { ...DEFAULT_SYSTEM_SETTINGS.ossConfig }
})

const logoFileInputRef = ref(null)
const isSaving = ref(false)
const isTestingOss = ref(false)
const isTestingLocal = ref(false)
const showSecretKey = ref(false)

// 当前正在编辑的存储引擎卡片视图 (默认跟随激活引擎)
const currentEditingVendor = ref('OSS')

// 存储引擎厂商元数据选型池 (仅保留本地文件存储、阿里云OSS、腾讯云COS)
const storageVendors = [
  {
    key: 'LOCAL',
    name: '本地文件存储',
    subTitle: 'Local Disk Storage',
    icon: 'Folder',
    badge: '离线私有',
    driver: 'LOCAL',
    desc: '直接存储在工控主机物理磁盘中，适用于局域网或内网纯离线机房部署。'
  },
  {
    key: 'ALIYUN',
    name: '阿里云对象存储',
    subTitle: 'Aliyun OSS',
    icon: 'Cloudy',
    badge: '高可用推荐',
    driver: 'OSS',
    desc: '国内主流基础设施，超大吞吐并发与低时延，多可用区容灾。'
  },
  {
    key: 'TENCENT',
    name: '腾讯云对象存储',
    subTitle: 'Tencent COS',
    icon: 'Cloudy',
    badge: '音视频优化',
    driver: 'OSS',
    desc: '多媒体处理生态完善，广播级高清赛事直播推流与大文件传输首选。'
  }
]

// 连通性测试探针诊断状态记录
const lastTestStatus = reactive({
  tested: false,
  success: false,
  latency: '',
  message: '',
  timestamp: '',
  target: ''
})

// 预设矢量工控图标选项
const presetIcons = [
  { name: 'SvgPortal', label: '寰宇门户' },
  { name: 'SvgSecurityShield', label: '安全神盾' },
  { name: 'SvgIotControl', label: '物联总线' },
  { name: 'SvgLedScreen', label: '全彩大屏' },
  { name: 'SvgMasterClock', label: '北斗授时' },
  { name: 'SvgSettingGear', label: '工控齿轮' }
]

// 判断某个引擎是否是系统当前生产激活的模式
const isCurrentActive = (vendorKey) => {
  if (vendorKey === 'LOCAL') {
    return form.storageDriver === 'LOCAL'
  }
  return form.storageDriver === 'OSS' && (form.activeStorageVendor === vendorKey || form.ossConfig.vendor === vendorKey)
}

// 获取当前系统生产激活存储引擎的元数据
const getActiveVendorInfo = () => {
  if (form.storageDriver === 'LOCAL') {
    return storageVendors[0]
  }
  const vendor = form.activeStorageVendor || form.ossConfig.vendor || 'ALIYUN'
  const match = storageVendors.find(v => v.key === vendor)
  return match || storageVendors[1]
}

// 根据 Key 获取厂商名称
const getVendorNameByKey = (vendorKey) => {
  const match = storageVendors.find(v => v.key === vendorKey)
  return match ? `${match.name} (${match.subTitle})` : vendorKey
}

// 切换当前正在编辑配置的厂商视图
const selectEditingVendor = (vendorKey) => {
  currentEditingVendor.value = vendorKey
  if (vendorKey !== 'LOCAL') {
    form.ossConfig.vendor = vendorKey
  }
}

// 下拉框改变时同步联动当前视图
const onVendorSelectChange = (val) => {
  currentEditingVendor.value = val
}

// 将指定厂商一键设为【当前系统生产激活存储引擎】
const setActiveVendor = (vendorKey) => {
  if (vendorKey === 'LOCAL') {
    form.storageDriver = 'LOCAL'
    form.activeStorageVendor = 'LOCAL'
  } else {
    form.storageDriver = 'OSS'
    form.activeStorageVendor = vendorKey
    form.ossConfig.vendor = vendorKey
  }
  currentEditingVendor.value = vendorKey

  ElMessage.success({
    message: `已将 [${getActiveVendorInfo().name}] 设为当前生产激活存储引擎！点击右上角【保存全部配置】后全系统生效。`,
    duration: 3500
  })
}

// 实时同步当前配置到全局 Header 标牌（所见即所得即时联动）
const emitPreviewChanges = () => {
  if (typeof window !== 'undefined') {
    const isCustom = form.logoType === 'CUSTOM' && !!form.logoUrl
    const payload = {
      ...form,
      logoType: form.logoType,
      logoUrl: form.logoUrl,
      systemLogo: isCustom ? form.logoUrl : '',
      logoPresetName: form.logoPresetName,
      systemLogoPreset: form.logoPresetName,
      systemName: form.systemName,
      systemSubTitle: form.systemSubTitle,
      version: form.systemSubTitle,
      activeStorageVendor: form.storageDriver === 'LOCAL' ? 'LOCAL' : (form.activeStorageVendor || form.ossConfig.vendor || 'ALIYUN')
    }
    window.dispatchEvent(new CustomEvent('ibms-system-settings-changed', { detail: payload }))
  }
}

// 监听核心品牌字段，修改即联动
watch(
  () => [form.systemName, form.systemSubTitle, form.logoType, form.logoUrl, form.logoPresetName, form.storageDriver, form.activeStorageVendor],
  () => {
    emitPreviewChanges()
  },
  { deep: true }
)

// 初始化加载系统配置
const loadSettings = async () => {
  const data = systemSettingService.getSettings()
  Object.assign(form, data)
  if (data.localConfig) form.localConfig = { ...data.localConfig }
  if (data.ossConfig) form.ossConfig = { ...data.ossConfig }
  
  // 异步获取服务端最新持久化配置，保证多终端一致
  try {
    const remote = await systemSettingService.fetchRemoteSettings()
    if (remote) {
      Object.assign(form, remote)
      if (remote.localConfig) form.localConfig = { ...remote.localConfig }
      if (remote.ossConfig) form.ossConfig = { ...remote.ossConfig }
    }
  } catch (err) {
    console.warn('SystemSetting: 加载远程设置预警', err)
  }

  // 初始化加载系统配置并确保仅在三大存储模式白名单中
  const validVendors = ['LOCAL', 'ALIYUN', 'TENCENT']
  if (!validVendors.includes(form.activeStorageVendor)) {
    form.activeStorageVendor = form.storageDriver === 'LOCAL' ? 'LOCAL' : 'ALIYUN'
  }
  if (!['ALIYUN', 'TENCENT'].includes(form.ossConfig.vendor)) {
    form.ossConfig.vendor = 'ALIYUN'
  }

  // 初始化当前视图
  if (form.storageDriver === 'LOCAL') {
    currentEditingVendor.value = 'LOCAL'
  } else {
    currentEditingVendor.value = form.activeStorageVendor === 'TENCENT' ? 'TENCENT' : 'ALIYUN'
  }
  emitPreviewChanges()
}

onMounted(() => {
  loadSettings()
})

// 触发本地 Logo 图片选择
const triggerSelectLogoFile = () => {
  if (logoFileInputRef.value) {
    logoFileInputRef.value.value = ''
    logoFileInputRef.value.click()
  }
}

// 处理 Logo 文件选择并转 Base64 预览
const handleLogoFileSelected = (event) => {
  const file = event.target.files?.[0]
  if (!file) return

  // 体积校验 (≤ 2MB)
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.warning('Logo 图片体积不得超过 2MB！')
    return
  }

  const reader = new FileReader()
  reader.onload = (e) => {
    form.logoType = 'CUSTOM'
    form.logoUrl = e.target.result
    emitPreviewChanges()
    ElMessage.success(`已载入新 Logo 文件: ${file.name}，点击右上角【保存全部配置】后持久化落盘`)
  }
  reader.readAsDataURL(file)
}

// 恢复预设图标
const resetToPresetLogo = () => {
  form.logoType = 'PRESET'
  form.logoUrl = ''
  emitPreviewChanges()
  ElMessage.info('已恢复为官方内置矢量图标')
}

const selectPresetLogo = (iconName) => {
  form.logoType = 'PRESET'
  form.logoPresetName = iconName
  emitPreviewChanges()
}

// 本地物理存储落盘路径与权限规范检测
const handleTestLocalStorage = async () => {
  isTestingLocal.value = true
  try {
    const res = await systemSettingService.testLocalStorage(form.localConfig)
    if (res.success) {
      lastTestStatus.tested = true
      lastTestStatus.success = true
      lastTestStatus.latency = '0.5ms'
      lastTestStatus.message = res.message
      lastTestStatus.timestamp = new Date().toLocaleTimeString()
      lastTestStatus.target = res.storagePath

      ElMessageBox.alert(
        `<div style="line-height: 1.6; color: #1E293B;">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
            <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #10B981;"></span>
            <strong style="color: #059669; font-size: 15px;">✓ 本地物理落盘环境体检就绪</strong>
          </div>
          <div style="background: #F0FDF4; border-left: 3px solid #10B981; padding: 10px 12px; margin-bottom: 12px; border-radius: 4px;">
            <p style="color: #166534; font-size: 13.5px; margin: 0;">${res.message}</p>
          </div>
          <div style="font-size: 13px; color: #475569;">
            <p style="margin: 4px 0;"><strong>物理落盘目录:</strong> <code style="background: #E2E8F0; padding: 2px 6px; border-radius: 4px;">${res.storagePath}</code></p>
            <p style="margin: 4px 0;"><strong>外链反代前缀:</strong> <code style="background: #E2E8F0; padding: 2px 6px; border-radius: 4px;">${res.urlPrefix}</code></p>
            <p style="margin: 4px 0;"><strong>单文件限制:</strong> ${res.maxFileSizeMb}</p>
            <p style="margin: 4px 0;"><strong>磁盘可用配额:</strong> ${res.diskSpaceAvail}</p>
            <p style="margin: 4px 0;"><strong>系统 I/O 权限:</strong> <span style="color: #10B981; font-weight: 700;">${res.writePermission}</span></p>
          </div>
        </div>`,
        '本地存储落盘诊断报告',
        { dangerouslyUseHTMLString: true, confirmButtonText: '确定' }
      )
    } else {
      lastTestStatus.tested = true
      lastTestStatus.success = false
      lastTestStatus.latency = ''
      lastTestStatus.message = res.message
      lastTestStatus.timestamp = new Date().toLocaleTimeString()
      lastTestStatus.target = form.localConfig.storagePath

      ElMessageBox.alert(
        `<div style="line-height: 1.6; color: #1E293B;">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
            <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #EF4444;"></span>
            <strong style="color: #EF4444; font-size: 15px;">本地存储参数校验未通过</strong>
          </div>
          <div style="background: #FEF2F2; border-left: 3px solid #EF4444; padding: 10px 12px; margin-bottom: 12px; border-radius: 4px;">
            <p style="color: #991B1B; font-size: 13.5px; margin: 0; font-weight: 600;">${res.message}</p>
          </div>
          <p style="font-size: 13px; color: #64748B; margin: 4px 0;">请按照规范修正物理落盘路径或反代前缀格式。</p>
        </div>`,
        '本地存储校验失败',
        { dangerouslyUseHTMLString: true, confirmButtonText: '查看并修正' }
      )
    }
  } catch (e) {
    ElMessage.error('本地存储检测异常: ' + e.message)
  } finally {
    isTestingLocal.value = false
  }
}

// 严谨的云端存储 (阿里云 OSS / 腾讯云 COS) 网络链路与配置探测
const handleTestOssConnection = async () => {
  // 判空检查
  if (!form.ossConfig.bucket || !form.ossConfig.endpoint || !form.ossConfig.accessKeyId || !form.ossConfig.accessKeySecret) {
    ElMessage.warning('请先完整输入云控制台真实开通的存储桶名称、接入节点及访问密钥凭证！')
    return
  }

  isTestingOss.value = true
  try {
    const res = await systemSettingService.testOssConnection(form.ossConfig)
    if (res.success) {
      lastTestStatus.tested = true
      lastTestStatus.success = true
      lastTestStatus.latency = res.latency
      lastTestStatus.message = res.message
      lastTestStatus.timestamp = new Date().toLocaleTimeString()
      lastTestStatus.target = res.bucket

      ElMessageBox.alert(
        `<div style="line-height: 1.6; color: #1E293B;">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
            <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #10B981;"></span>
            <strong style="color: #059669; font-size: 15px;">✓ 云存储桶网络链路寻址通过</strong>
          </div>
          <div style="background: #F0FDF4; border-left: 3px solid #10B981; padding: 10px 12px; margin-bottom: 12px; border-radius: 4px;">
            <p style="color: #166534; font-size: 13.5px; margin: 0;">${res.message}</p>
          </div>
          <div style="font-size: 13px; color: #475569;">
            <p style="margin: 4px 0;"><strong>存储厂商:</strong> ${res.vendor}</p>
            <p style="margin: 4px 0;"><strong>存储桶二级域名:</strong> <code style="background: #E2E8F0; padding: 2px 6px; border-radius: 4px;">${res.bucketHost}</code></p>
            <p style="margin: 4px 0;"><strong>传输链路协议:</strong> <span style="color: #2563EB; font-weight: 700;">${res.protocol}</span></p>
            <p style="margin: 4px 0;"><strong>物理往返握手时延:</strong> <span style="color: #10B981; font-weight: 700;">${res.latency}</span></p>
            <div style="margin-top: 10px; padding: 8px 10px; background: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 4px; color: #64748B; font-size: 12px; line-height: 1.5;">
              <strong style="color: #334155; display: block; margin-bottom: 2px;">⚠️ 安全鉴权提示 (技术说明)：</strong>
              前端探针已确认目标存储桶二级域名存在且物理网络握手正常。由于云厂商安全策略限制，纯前端不应在浏览器中私自签名暴露 SecretKey。您配置的访问密钥（AK/SK）最终读写授权，将在保存后由后端微服务在执行实际文件落盘时向云端 IAM 校验。
            </div>
          </div>
        </div>`,
        '云存储域名连通探测报告',
        { dangerouslyUseHTMLString: true, confirmButtonText: '确定' }
      )
    } else {
      lastTestStatus.tested = true
      lastTestStatus.success = false
      lastTestStatus.latency = ''
      lastTestStatus.message = res.message
      lastTestStatus.timestamp = new Date().toLocaleTimeString()
      lastTestStatus.target = form.ossConfig.bucket

      ElMessageBox.alert(
        `<div style="line-height: 1.6; color: #1E293B;">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #EF4444;"></span>
            <strong style="color: #EF4444; font-size: 15px;">连通性探测未通过 · 拦截并阻断</strong>
          </div>
          <div style="background: #FEF2F2; border-left: 3px solid #EF4444; padding: 10px 12px; margin-bottom: 12px; border-radius: 4px;">
            <p style="color: #991B1B; font-size: 13.5px; margin: 0; font-weight: 600;">拦截原因: ${res.message}</p>
          </div>
          <div style="font-size: 13px; color: #64748B;">
            <p style="margin: 4px 0;"><strong>目标厂商:</strong> ${form.ossConfig.vendor}</p>
            <p style="margin: 4px 0;"><strong>填写的存储桶:</strong> <code style="background: #F1F5F9; padding: 1px 5px; border-radius: 3px;">${form.ossConfig.bucket || '(空)'}</code></p>
            <p style="margin: 4px 0;"><strong>填写的接入节点:</strong> <code style="background: #F1F5F9; padding: 1px 5px; border-radius: 3px;">${form.ossConfig.endpoint || '(空)'}</code></p>
            <p style="margin: 8px 0 0 0; color: #B91C1C;"><strong>排查建议:</strong> 系统已开启存储桶真实二级域名寻址校验。请确认存储桶是否已在云控制台真实开通且全网 DNS 已生效，且密钥长度符合安全规范。</p>
          </div>
        </div>`,
        '连通性测试未通过',
        { dangerouslyUseHTMLString: true, confirmButtonText: '查看并修正参数' }
      )
    }
  } catch (e) {
    ElMessage.error('连通探测通信异常: ' + e.message)
  } finally {
    isTestingOss.value = false
  }
}

// 保存系统配置
const saveSystemSettings = async () => {
  isSaving.value = true
  try {
    const res = await systemSettingService.saveSettings(form)
    if (res.success) {
      if (res.remoteSaved === false) {
        ElMessage.warning({
          message: '配置仅保存到本机浏览器缓存，后端服务不可达，未能写入服务器数据库！其它终端不会生效，请检查后端连通性后重新保存。',
          duration: 6000
        })
      } else {
        ElMessage.success(`系统全局配置已持久化保存（已同步至服务器数据库与本地缓存）！当前生效存储引擎：${getActiveVendorInfo().name}`)
      }
    } else {
      ElMessage.error(res.error || '保存失败')
    }
  } catch (e) {
    ElMessage.error('保存失败: ' + e.message)
  } finally {
    setTimeout(() => {
      isSaving.value = false
    }, 400)
  }
}

// 确认恢复出厂设置
const confirmResetSettings = () => {
  ElMessageBox.confirm(
    '此操作将恢复系统Logo、版权信息、开发商与存储配置为出厂初始预设，是否继续？',
    '恢复出厂设置确认',
    {
      confirmButtonText: '确认恢复',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    await systemSettingService.resetToDefault()
    await loadSettings()
    ElMessage.success('已恢复出厂默认系统配置并同步服务器数据库')
  }).catch(() => {})
}
</script>

<style scoped>
.system-setting-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
}

/* 顶部操作与标题面板 */
.setting-header-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 22px;
  background: linear-gradient(145deg, var(--do-bg-card) 0%, rgba(var(--th-accent-rgb), 0.04) 100%);
  border: 1px solid rgba(var(--th-accent-rgb), 0.22);
  border-radius: var(--radius-md);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  gap: 16px;
  flex-wrap: wrap;
}

.header-left-meta {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-icon-box {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  background: rgba(var(--th-accent-rgb), 0.12);
  color: var(--do-gold-deep);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--do-text-primary);
  margin: 0;
  letter-spacing: 0.2px;
}

.setting-badge {
  font-size: 13px;
  font-weight: 700;
  padding: 1px 7px;
  border-radius: 4px;
  background: rgba(var(--th-accent-rgb), 0.12);
  color: var(--do-gold-deep);
  font-family: var(--font-family-mono);
}

.page-desc {
  font-size: 14px;
  color: var(--do-text-secondary);
  margin: 4px 0 0 0;
}

.header-action-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.reset-btn {
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  color: var(--do-text-regular);
  font-size: 14px;
  font-weight: 600;
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  transition: all 0.2s ease;
}

.reset-btn:hover {
  color: var(--do-warning-deep);
  border-color: var(--do-warning);
}

.save-primary-btn {
  background: linear-gradient(135deg, var(--do-gold) 0%, var(--do-gold-deep) 100%);
  border: 1px solid var(--do-gold-deep);
  color: #FFFFFF;
  font-size: 14px;
  font-weight: 700;
  padding: 8px 20px;
  border-radius: var(--radius-sm);
  box-shadow: 0 2px 6px rgba(var(--th-accent-deep-rgb), 0.25);
  transition: all 0.2s ease;
}

.save-primary-btn:hover {
  box-shadow: 0 4px 12px rgba(var(--th-accent-deep-rgb), 0.35);
  transform: translateY(-1px);
}

/* 主体两栏栅格 */
.setting-main-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 380px;
  gap: 16px;
  align-items: start;
}

@media (max-width: 1400px) {
  .setting-main-grid {
    grid-template-columns: 1fr;
  }
}

/* 表单卡片通用规范 (四周微边框 + 温和微渐变，绝无仅左边框与多层套框) */
.setting-card {
  background: linear-gradient(145deg, var(--do-bg-card) 0%, rgba(var(--th-accent-rgb), 0.03) 100%);
  border: 1px solid rgba(var(--th-accent-rgb), 0.22);
  border-radius: var(--radius-md);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  margin-bottom: 16px;
  overflow: hidden;
  transition: border-color 0.22s ease;
}

.setting-card:hover {
  border-color: var(--do-gold);
}

.card-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  background: rgba(var(--th-accent-rgb), 0.04);
  border-bottom: 1px solid rgba(var(--th-accent-rgb), 0.12);
}

.section-title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-num {
  font-family: var(--font-family-mono);
  font-size: 14px;
  font-weight: 800;
  color: var(--do-gold-deep);
  background: rgba(var(--th-accent-rgb), 0.12);
  padding: 1px 6px;
  border-radius: 4px;
}

.section-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--do-text-primary);
  margin: 0;
  letter-spacing: 0.2px;
}

.section-tag {
  font-size: 13px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(var(--th-accent-rgb), 0.1);
  color: var(--do-gold-deep);
}

.card-section-body {
  padding: 20px;
}

/* Logo 布局 */
.logo-config-layout {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 24px;
}

@media (max-width: 900px) {
  .logo-config-layout {
    grid-template-columns: 1fr;
  }
}

.logo-preview-stage {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(var(--th-accent-rgb), 0.035);
  border-radius: 8px;
  padding: 18px 14px;
  text-align: center;
}

.stage-label {
  font-size: 13.5px;
  color: var(--do-text-secondary);
  font-weight: 600;
  margin-bottom: 12px;
}

.logo-display-box {
  width: 96px;
  height: 96px;
  border-radius: 12px;
  background: #FFFFFF;
  border: 1px solid rgba(var(--th-accent-rgb), 0.28);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
  margin-bottom: 14px;
  overflow: hidden;
}

.custom-logo-img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.preset-logo-wrap {
  color: var(--do-gold-deep);
}

.stage-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.upload-logo-btn {
  background: linear-gradient(135deg, var(--do-gold) 0%, var(--do-gold-deep) 100%);
  border: none;
  color: #fff;
  font-size: 13.5px;
  font-weight: 600;
  width: 100%;
}

.clear-logo-btn {
  width: 100%;
  font-size: 13px;
}

.upload-tip-text {
  font-size: 13px;
  color: var(--do-text-secondary);
  line-height: 1.4;
  margin-top: 10px;
}

/* 预设图标选择器 */
.preset-icon-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
}

.preset-icon-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 6px;
  background: rgba(var(--th-accent-rgb), 0.06);
  color: var(--do-text-regular);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 13.5px;
  font-weight: 500;
  user-select: none;
}

.preset-icon-chip:hover {
  background: rgba(var(--th-accent-rgb), 0.12);
  color: var(--do-gold-deep);
}

.preset-icon-chip.active {
  background: var(--do-gold-deep);
  color: #FFFFFF;
  box-shadow: 0 2px 6px rgba(var(--th-accent-deep-rgb), 0.3);
}

/* 表单栅格排版规范 */
.form-two-cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-three-cols {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

@media (max-width: 768px) {
  .form-two-cols,
  .form-three-cols {
    grid-template-columns: 1fr;
  }
}

.custom-setting-form :deep(.el-form-item) {
  margin-bottom: 16px;
}

.custom-setting-form :deep(.el-form-item__label) {
  font-size: 14px !important;
  font-weight: 600 !important;
  color: var(--do-text-primary) !important;
  line-height: 22px !important;
  padding-bottom: 6px !important;
}

.full-width-select,
.full-width-number {
  width: 100% !important;
}

/* 存储模式切换单选胶囊 */
.driver-switch-pills {
  display: inline-flex;
  align-items: center;
  background: rgba(var(--th-accent-rgb), 0.08);
  border-radius: 6px;
  padding: 3px;
  gap: 4px;
}

/* 顶部当前生效引擎徽章 */
.active-engine-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.25);
  padding: 5px 12px;
  border-radius: 20px;
}

.status-indicator-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10B981;
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.6);
}

.status-indicator-dot.online {
  animation: pulse-green 2s infinite ease-in-out;
}

@keyframes pulse-green {
  0% { transform: scale(0.95); opacity: 0.8; }
  50% { transform: scale(1.2); opacity: 1; }
  100% { transform: scale(0.95); opacity: 0.8; }
}

.badge-label {
  font-size: 13px;
  color: var(--do-text-secondary);
}

.badge-value {
  font-size: 13px;
  color: #059669;
  font-weight: 700;
}

/* 核心态势大横幅：当前系统生效运行存储引擎看板 */
.storage-active-hero-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 16px 20px;
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(var(--th-accent-rgb), 0.08) 0%, rgba(16, 185, 129, 0.07) 100%);
  border: 1px solid rgba(var(--th-accent-rgb), 0.25);
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}

@media (max-width: 1024px) {
  .storage-active-hero-banner {
    flex-direction: column;
    align-items: stretch;
  }
}

.hero-left-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

.hero-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  width: fit-content;
  padding: 2px 10px;
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 12px;
}

.pulse-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #10B981;
}

.status-text {
  font-size: 12px;
  font-weight: 700;
  color: #047857;
  letter-spacing: 0.3px;
}

.hero-main-title {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.hero-engine-name {
  font-size: 18px;
  font-weight: 800;
  color: var(--do-text-primary);
}

.hero-engine-sub {
  font-size: 14px;
  color: var(--do-text-secondary);
}

.hero-engine-driver-tag {
  font-size: 12px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
}

.hero-engine-driver-tag.local {
  background: #E0F2FE;
  color: #0284C7;
  border: 1px solid rgba(2, 132, 199, 0.2);
}

.hero-engine-driver-tag.oss {
  background: #DCFCE7;
  color: #15803D;
  border: 1px solid rgba(21, 128, 61, 0.2);
}

.hero-engine-specs {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.spec-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  background: rgba(255, 255, 255, 0.7);
  padding: 3px 8px;
  border-radius: 4px;
  border: 1px solid rgba(var(--th-accent-rgb), 0.15);
}

.spec-k {
  color: var(--do-text-secondary);
}

.spec-v {
  color: var(--do-text-primary);
  font-weight: 600;
}

.hero-right-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
  flex-shrink: 0;
}

@media (max-width: 1024px) {
  .hero-right-actions {
    align-items: flex-start;
  }
}

.health-indicator-box {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

@media (max-width: 1024px) {
  .health-indicator-box {
    align-items: flex-start;
  }
}

.health-title {
  font-size: 12px;
  color: var(--do-text-secondary);
}

.health-result {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 4px;
}

.health-result.success {
  background: #DCFCE7;
  color: #15803D;
}

.health-result.failed {
  background: #FEE2E2;
  color: #B91C1C;
}

.health-result.pending {
  background: #F1F5F9;
  color: #64748B;
}

.hero-probe-btn {
  font-weight: 700;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}

/* 存储引擎选型矩阵 */
.engine-selector-container {
  margin-bottom: 22px;
}

.selector-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}

.selector-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--do-text-primary);
  display: flex;
  align-items: center;
}

.selector-tip {
  font-size: 12.5px;
  color: var(--do-text-secondary);
}

.engine-cards-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

@media (max-width: 1200px) {
  .engine-cards-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .engine-cards-grid {
    grid-template-columns: 1fr;
  }
}

.engine-card {
  position: relative;
  border: 1px solid rgba(var(--th-accent-rgb), 0.2);
  border-radius: 8px;
  background: var(--do-bg-card);
  padding: 14px;
  cursor: pointer;
  transition: all 0.22s ease;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 10px;
}

.engine-card:hover {
  border-color: var(--do-gold);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.engine-card.is-editing {
  border-color: var(--do-gold-deep);
  background: linear-gradient(145deg, var(--do-bg-card) 0%, rgba(var(--th-accent-rgb), 0.05) 100%);
  box-shadow: 0 0 0 2px rgba(var(--th-accent-deep-rgb), 0.2);
}

.engine-card.is-active-running {
  border-color: #10B981;
}

.engine-card.is-active-running.is-editing {
  border-color: #059669;
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.25);
}

.card-head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.vendor-icon-wrap {
  width: 34px;
  height: 34px;
  border-radius: 6px;
  background: rgba(var(--th-accent-rgb), 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: var(--do-gold-deep);
  flex-shrink: 0;
}

.engine-card.is-active-running .vendor-icon-wrap {
  background: rgba(16, 185, 129, 0.12);
  color: #10B981;
}

.vendor-name-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.v-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.v-sub {
  font-size: 12px;
  color: var(--do-text-secondary);
}

.v-tag {
  font-size: 11.5px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(var(--th-accent-rgb), 0.1);
  color: var(--do-gold-deep);
}

.card-desc {
  font-size: 12.5px;
  color: var(--do-text-secondary);
  line-height: 1.45;
  margin: 0;
  min-height: 36px;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px dashed rgba(var(--th-accent-rgb), 0.15);
  padding-top: 10px;
}

.active-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 700;
  color: #059669;
  background: rgba(16, 185, 129, 0.12);
  padding: 3px 8px;
  border-radius: 12px;
}

.set-active-action-btn {
  border: 1px solid rgba(var(--th-accent-rgb), 0.25);
  background: rgba(var(--th-accent-rgb), 0.06);
  color: var(--do-text-primary);
  font-size: 12px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.set-active-action-btn:hover {
  background: var(--do-gold-deep);
  color: #FFFFFF;
  border-color: var(--do-gold-deep);
}

.editing-indicator {
  font-size: 11.5px;
  color: var(--do-gold-deep);
  font-weight: 700;
}

/* 子表单面板 */
.storage-sub-form {
  border: 1px solid rgba(var(--th-accent-rgb), 0.18);
  border-radius: 8px;
  padding: 16px 20px;
  background: rgba(var(--th-accent-rgb), 0.02);
}

.sub-form-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(var(--th-accent-rgb), 0.12);
  margin-bottom: 14px;
}

.sub-form-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.sub-form-title .el-icon {
  font-size: 18px;
  color: var(--do-gold-deep);
}

.probe-notice-bar {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  background: rgba(245, 158, 11, 0.08);
  border-left: 3px solid #F59E0B;
  border-radius: 4px;
  padding: 10px 14px;
  margin-bottom: 16px;
  font-size: 13px;
  color: #78350F;
  line-height: 1.5;
}

.probe-notice-bar .el-icon {
  font-size: 16px;
  color: #D97706;
  margin-top: 2px;
  flex-shrink: 0;
}

.input-helper-tip {
  font-size: 12px;
  color: var(--do-text-secondary);
  line-height: 1.3;
  margin-top: 3px;
  display: block;
}

.test-oss-btn {
  background: #10B981;
  border-color: #059669;
  font-size: 13.5px;
  font-weight: 700;
  padding: 8px 16px;
  border-radius: 4px;
}

.test-oss-btn:hover {
  background: #059669;
}

.toggle-eye-btn {
  padding: 0 4px;
  color: var(--do-text-secondary);
}

/* 右侧预览粘滞列 */
.preview-sticky-column {
  position: sticky;
  top: 76px;
}

.showcase-card {
  background: linear-gradient(145deg, var(--do-bg-card) 0%, rgba(var(--th-accent-rgb), 0.03) 100%);
  border: 1px solid rgba(var(--th-accent-rgb), 0.22);
  border-radius: var(--radius-md);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.showcase-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  background: rgba(var(--th-accent-rgb), 0.04);
  border-bottom: 1px solid rgba(var(--th-accent-rgb), 0.12);
}

.showcase-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14.5px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.preview-sparkle {
  color: var(--do-gold);
}

.live-pill {
  font-size: 13px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(16, 185, 129, 0.12);
  color: #10B981;
}

.showcase-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
}

/* 拟真设备视窗 */
.mock-device-window {
  background: #FFFFFF;
  border: 1px solid rgba(var(--th-accent-rgb), 0.22);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
}

.window-titlebar {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 10px;
  background: #F1F5F9;
  border-bottom: 1px solid #E2E8F0;
}

.win-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}
.win-dot.red { background: #EF4444; }
.win-dot.yellow { background: #F59E0B; }
.win-dot.green { background: #10B981; }

.win-label {
  font-size: 13px;
  color: #64748B;
  font-weight: 600;
  margin-left: 4px;
}

.mock-header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: #172554;
  color: #FFFFFF;
}

.mock-left-brand {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mock-logo-box {
  width: 26px;
  height: 26px;
  border-radius: 5px;
  background: rgba(255, 255, 255, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.mock-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.mock-titles {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}

.mock-main-name {
  font-size: 13.5px;
  font-weight: 700;
  color: #FFFFFF;
}

.mock-sub-name {
  font-size: 13px;
  color: #94A3B8;
  font-family: var(--font-family-mono);
}

.mock-env-tag {
  font-size: 13px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(16, 185, 129, 0.2);
  color: #6EE7B7;
}

/* 登录卡片仿真 */
.mock-login-badge-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  background: linear-gradient(180deg, #F8FAFC 0%, #EFF6FF 100%);
  text-align: center;
}

.login-badge-avatar {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: #FFFFFF;
  border: 1px solid rgba(var(--th-accent-rgb), 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.mock-img-large {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.login-brand-title {
  font-size: 14.5px;
  font-weight: 700;
  color: #0F172A;
  margin: 0;
}

.login-brand-sub {
  font-size: 13px;
  color: #64748B;
  font-family: var(--font-family-mono);
  margin-top: 2px;
}

.login-license-tag {
  font-size: 13px;
  padding: 2px 8px;
  background: #E0F2FE;
  color: #0284C7;
  border-radius: 4px;
  margin-top: 6px;
  font-weight: 600;
}

/* 页脚仿真 */
.mock-footer-content {
  padding: 12px 14px;
  background: #F8FAFC;
  text-align: center;
}

.mock-foot-copy {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
  margin: 0 0 3px 0;
}

.mock-foot-operator {
  font-size: 13px;
  color: #64748B;
  margin: 0 0 5px 0;
}

.mock-beian-row {
  display: flex;
  justify-content: center;
  gap: 10px;
  font-size: 13px;
  color: #94A3B8;
}

/* 存储概览卡片 */
.storage-summary-card {
  background: rgba(var(--th-accent-rgb), 0.05);
  border-radius: 8px;
  padding: 12px 14px;
}

.summary-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.summary-lbl {
  font-size: 13px;
  font-weight: 600;
  color: var(--do-text-secondary);
}

.driver-tag {
  font-size: 13px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
}
.driver-tag.oss {
  background: #DCFCE7;
  color: #15803D;
}
.driver-tag.local {
  background: #E0F2FE;
  color: #0369A1;
}

.summary-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.detail-k {
  color: var(--do-text-secondary);
}

.detail-v {
  color: var(--do-text-primary);
  font-weight: 600;
}
</style>
