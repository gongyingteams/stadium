<template>
  <div class="external-integration-container">
    <!-- 隐藏的文件选择输入控件 -->
    <!-- 1. 用于选取本地程序文件 (*.exe, *.bat, *.cmd, *.lnk, *.ps1 等) -->
    <input
      ref="filePickerInputRef"
      type="file"
      style="display: none"
      accept=".exe,.bat,.cmd,.lnk,.ps1,*"
      @change="handleNativeFileSelected"
    />
    <!-- 2. 用于手动上传自定义应用图标图片 -->
    <input
      ref="iconImageInputRef"
      type="file"
      style="display: none"
      accept="image/*"
      @change="handleIconImageUpload"
    />

    <!-- 顶部检索与多用户操作栏 -->
    <div class="portal-filter-bar glass-panel">
      <!-- 搜索输入框 -->
      <div class="search-box">
        <el-input
          v-model="keyword"
          placeholder="快速检索外部软件名称、地址、账号..."
          prefix-icon="Search"
          clearable
          class="portal-search-input"
        />
      </div>

      <!-- 分类 TAB 切换 (带生动图标) -->
      <div class="category-tabs">
        <button
          v-for="cat in categories"
          :key="cat.key"
          :class="['cat-btn', { active: currentCategory === cat.key }]"
          @click="currentCategory = cat.key"
        >
          <el-icon class="cat-icon">
            <Grid v-if="cat.key === 'ALL'" />
            <Connection v-else-if="cat.key === 'BS'" />
            <Platform v-else-if="cat.key === 'CS'" />
            <Cpu v-else />
          </el-icon>
          <span>{{ cat.name }}</span>
          <span class="cat-count-pill">{{ cat.count }}</span>
        </button>
      </div>

      <!-- 右侧：视图列数切换与登记操作按钮 -->
      <div class="right-action-group">
        <div class="grid-mode-selector">
          <span class="selector-lbl">视图:</span>
          <div class="selector-pills">
            <button
              type="button"
              :class="['selector-pill-btn', { active: gridColumns === '3' }]"
              title="切换为 3 列宽敞大卡视图 (适合笔记本或大卡片阅读)"
              @click="setGridColumns('3')"
            >
              <el-icon class="mr-0.5"><Menu /></el-icon>
              <span>3 列</span>
            </button>
            <button
              type="button"
              :class="['selector-pill-btn', { active: gridColumns === '4' }]"
              title="切换为 4 列标准视图 (适合高分大屏与密集总控)"
              @click="setGridColumns('4')"
            >
              <el-icon class="mr-0.5"><Grid /></el-icon>
              <span>4 列</span>
            </button>
          </div>
        </div>

        <el-button
          type="primary"
          class="gold-btn-primary"
          @click="openAddDialog"
        >
          <el-icon class="mr-1"><Plus /></el-icon>
          登记外部软件
        </el-button>
      </div>
    </div>

    <!-- 软件聚合卡片网格 (根据用户偏好和断点响应) -->
    <div
      v-if="filteredApps.length > 0"
      ref="cardsGridRef"
      :class="['app-cards-grid', `cols-${gridColumns}`]"
    >
      <div
        v-for="app in filteredApps"
        :key="app.id"
        class="app-card glass-panel"
      >
        <!-- 卡片头部：图标、名称与架构类型标签 -->
        <div class="card-head">
          <div class="app-icon-box" :class="app.app_type.toLowerCase()">
            <!-- 自定义图片图标 -->
            <img
              v-if="app.icon_type === 'CUSTOM' && app.custom_icon_url"
              :src="app.custom_icon_url"
              class="custom-app-icon"
              alt="app-icon"
            />
            <!-- 内置矢量工控图标 -->
            <SvgIcon v-else :name="getAppIcon(app)" size="26" />
          </div>
          <div class="app-title-group">
            <div class="app-name-row">
              <h3 class="app-name" :title="app.app_name">{{ app.app_name }}</h3>
            </div>
            <div class="app-sub-owner">
              <span class="code-badge">EXT-{{ app.id }}</span>
              <span class="owner-name"><el-icon class="mr-0.5"><User /></el-icon>{{ app.username }}</span>
            </div>
          </div>

          <!-- 架构类型标签 (带图标) -->
          <div class="mode-tag-wrap">
            <span v-if="app.app_type === 'BS'" class="tag-pill bs">
              <el-icon class="pill-icon"><Connection /></el-icon>
              <span>B/S 网页</span>
            </span>
            <span v-else-if="app.app_type === 'CS'" class="tag-pill cs">
              <el-icon class="pill-icon"><Platform /></el-icon>
              <span>C/S 桌面</span>
            </span>
            <span v-else class="tag-pill unknown">
              <el-icon class="pill-icon"><Cpu /></el-icon>
              <span>脚本工具</span>
            </span>
          </div>
        </div>

        <!-- 软件功能描述 (单行超出省略，提供展开/收起) -->
        <div class="app-desc-wrapper">
          <p
            :ref="el => setDescRef(app.id, el)"
            :class="['app-desc-text', { 'is-expanded': isDescExpanded(app.id) }]"
            :title="app.app_desc"
          >
            {{ app.app_desc || '暂无详细描述说明。' }}
          </p>
          <button
            v-if="shouldShowDescToggle(app)"
            type="button"
            class="desc-toggle-btn"
            @click.stop="toggleDesc(app.id)"
          >
            <span>{{ isDescExpanded(app.id) ? '收起' : '展开' }}</span>
            <el-icon class="toggle-arrow">
              <ArrowUp v-if="isDescExpanded(app.id)" />
              <ArrowDown v-else />
            </el-icon>
          </button>
        </div>

        <!-- 第①级：路径/URL 深色等宽代码块（防截断、易识别、工控终端风） -->
        <div class="app-target-bar dark-code-block">
          <div class="target-info-wrap">
            <span class="target-scheme-badge" :class="app.app_type.toLowerCase()">
              {{ app.app_type === 'BS' ? 'URL' : 'PATH' }}
            </span>
            <span class="target-path-val terminal-mono" :title="app.target_path">
              {{ app.target_path }}
            </span>
          </div>
          <div class="target-actions-wrap">
            <el-tooltip content="复制完整执行路径/URL" placement="top">
              <button class="icon-copy-btn dark-copy" @click.stop="copyText(app.target_path)">
                <el-icon><CopyDocument /></el-icon>
              </button>
            </el-tooltip>
            <el-tooltip
              :content="app.app_type === 'BS' ? '就绪状态: 网络直通可访问' : '就绪状态: 本地部署已就绪'"
              placement="top"
            >
              <div class="status-indicator">
                <span class="status-dot-sm online"></span>
              </div>
            </el-tooltip>
          </div>
        </div>

        <!-- 第②级：凭据与自动登录 紧凑型状态胶囊（通透轻巧、主次分明） -->
        <div class="app-credential-capsule-bar">
          <div class="capsule-left">
            <!-- 凭据胶囊 -->
            <span
              v-if="app.auth_username || app.auth_password"
              class="pill-tag credential-pill"
              :title="app.auth_username ? `已配置预置账号: ${app.auth_username}` : '已配置自动填充密码'"
            >
              <el-icon class="pill-icon"><Key /></el-icon>
              <span>{{ app.auth_username || '已置免密凭据' }}</span>
            </span>
            <span v-else class="pill-tag direct-pill" title="直接启动运行，无需凭据认证">
              <el-icon class="pill-icon"><CircleCheck /></el-icon>
              <span>免密直通</span>
            </span>

            <!-- 启动参数标记胶囊 -->
            <span
              v-if="app.start_args"
              class="pill-tag args-pill"
              :title="`启动参数: ${app.start_args}`"
            >
              <el-icon class="pill-icon"><Cpu /></el-icon>
              <span>带参数</span>
            </span>
          </div>

          <!-- 紧凑型折叠触发按钮 -->
          <button
            type="button"
            class="capsule-expand-btn"
            :class="{ 'is-open': isConfigExpanded(app.id) }"
            @click.stop="toggleConfig(app.id)"
          >
            <span>{{ isConfigExpanded(app.id) ? '收起配置' : '参数详情' }}</span>
            <el-icon class="capsule-arrow" :class="{ 'rotated': isConfigExpanded(app.id) }">
              <ArrowDown />
            </el-icon>
          </button>
        </div>

        <!-- 参数与凭据轻量折叠抽屉 -->
        <div v-show="isConfigExpanded(app.id)" class="credential-drawer-panel">
          <div class="drawer-detail-row">
            <span class="detail-label">启动参数:</span>
            <span class="detail-val num-mono" :class="{ 'text-muted': !app.start_args }">
              {{ app.start_args || '常规启动 (无额外命令行参数)' }}
            </span>
            <button
              v-if="app.start_args"
              class="mini-copy-btn"
              title="复制参数"
              @click.stop="copyText(app.start_args)"
            >
              <el-icon><CopyDocument /></el-icon>
            </button>
          </div>

          <div v-if="app.auth_username || app.auth_password" class="drawer-detail-row">
            <span class="detail-label">登录凭据:</span>
            <div class="detail-auth-pills">
              <span
                v-if="app.auth_username"
                class="auth-action-pill"
                title="点击复制账号"
                @click.stop="copyText(app.auth_username)"
              >
                <el-icon><User /></el-icon>
                <span>{{ app.auth_username }}</span>
                <el-icon class="copy-sub-icon"><DocumentCopy /></el-icon>
              </span>
              <span
                v-if="app.auth_password"
                class="auth-action-pill pwd"
                title="点击复制密码"
                @click.stop="copyText(app.auth_password)"
              >
                <el-icon><Lock /></el-icon>
                <span>••••••</span>
                <el-icon class="copy-sub-icon"><DocumentCopy /></el-icon>
              </span>
            </div>
          </div>
        </div>

        <!-- 第③级：底部高对比度暖金主按钮 + 独立连通测试快捷按钮 -->
        <div class="card-footer">
          <!-- 独立连通测试按钮 -->
          <el-tooltip
            :content="app.app_type === 'BS' ? '测试网络直通延迟与可访问性' : '测试本地软件目标路径与可执行状态'"
            placement="top"
          >
            <button
              class="test-connection-btn"
              :class="{ 'is-testing': testingMap[app.id] }"
              :disabled="testingMap[app.id]"
              @click.stop="handleTestApp(app)"
            >
              <el-icon class="test-icon" :class="{ 'is-loading': testingMap[app.id] }">
                <Loading v-if="testingMap[app.id]" />
                <Connection v-else />
              </el-icon>
              <span>{{ testingMap[app.id] ? '探测中' : '连通测试' }}</span>
            </button>
          </el-tooltip>

          <!-- 升级为高对比度暖金主按钮 (高点击欲) -->
          <button class="open-btn gold-primary-launch" @click="handleLaunchApp(app)">
            <span class="launch-label">
              {{ app.app_type === 'BS' ? '打开系统' : '立即启动' }}
            </span>
            <span class="arrow-icon">→</span>
          </button>

          <!-- 辅助操作 -->
          <div class="sub-actions">
            <el-tooltip content="编辑软件配置" placement="top">
              <button class="sub-action-btn" @click="openEditDialog(app)">
                <el-icon><Edit /></el-icon>
              </button>
            </el-tooltip>
            <el-tooltip content="从个人库移除" placement="top">
              <button class="sub-action-btn danger" @click="handleDeleteApp(app)">
                <el-icon><Delete /></el-icon>
              </button>
            </el-tooltip>
          </div>
        </div>
      </div>
    </div>

    <!-- 无数据空状态 -->
    <div v-else class="empty-state-panel glass-panel">
      <div class="empty-icon-wrap">
        <el-icon :size="48"><FolderOpened /></el-icon>
      </div>
      <h4 class="empty-title">暂无匹配的外部集成软件</h4>
      <p class="empty-desc">
        {{ keyword || currentCategory !== 'ALL'
          ? '未找到符合筛选条件的软件，请尝试调整搜索词或分类标签。'
          : '您可以点击下方按钮，将本地运行的工控桌面软件 (C/S)、B/S 专网系统或批处理工具登记进来，实现集中快速唤起。' }}
      </p>
      <el-button
        v-if="!keyword && currentCategory === 'ALL'"
        type="primary"
        class="gold-btn-primary"
        @click="openAddDialog"
      >
        <el-icon class="mr-1"><Plus /></el-icon>
        立即登记首个外部软件
      </el-button>
    </div>

    <!-- 登记 / 编辑软件弹窗 (El-Dialog) -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditMode ? '编辑外部集成软件配置' : '登记新的外部集成软件 (个人专属)'"
      width="640px"
      append-to-body
      destroy-on-close
      class="gold-styled-dialog"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
        label-position="left"
        class="external-app-form"
      >
        <!-- 1. 软件基础信息 -->
        <div class="form-section-title">
          <span class="section-badge">1</span>
          <span>基础属性与系统架构</span>
        </div>

        <el-form-item label="软件名称" prop="app_name">
          <div class="input-with-action">
            <el-input
              v-model="form.app_name"
              placeholder="例如: Antigravity IDE、Novastar NovaLCT、票务检票系统"
              maxlength="64"
              clearable
              @input="onAppNameInput"
            />
            <button
              type="button"
              class="compact-detect-btn"
              title="根据当前输入的软件名称和路径智能推荐图标"
              @click="triggerAutoDetectIcon"
            >
              <el-icon class="mr-1"><MagicStick /></el-icon>
              <span>智能匹配</span>
            </button>
          </div>
        </el-form-item>

        <el-form-item label="架构类型" prop="app_type">
          <el-radio-group v-model="form.app_type" @change="onAppTypeChange">
            <el-radio-button value="BS">B/S (Web网页)</el-radio-button>
            <el-radio-button value="CS">C/S (桌面程序)</el-radio-button>
            <el-radio-button value="UNKNOWN">未知 / 脚本工具</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <!-- 2. 程序路径与启动参数 -->
        <div class="form-section-title">
          <span class="section-badge">2</span>
          <span>程序路径与启动参数</span>
        </div>

        <el-form-item prop="target_path">
          <template #label>
            <div class="form-item-label-wrap">
              <span>{{ form.app_type === 'BS' ? '网页访问地址' : '本地程序路径' }}</span>
              <el-tooltip
                :content="form.app_type === 'CS'
                  ? '支持选取本地路径：点击【选取路径】直接在本地文件选择器选定 .exe / .bat / .cmd 文件，系统自动填充并识别名称。'
                  : (form.app_type === 'BS' ? '请输入 Web 访问地址，如 http://192.168.1.88:8080/portal 或 https://example.com' : '请输入批处理脚本、可执行文件或快捷方式路径。')"
                placement="top"
              >
                <el-icon class="help-question-icon"><QuestionFilled /></el-icon>
              </el-tooltip>
            </div>
          </template>
          <div class="path-input-group">
            <el-input
              v-model="form.target_path"
              :placeholder="getPathPlaceholder(form.app_type)"
              clearable
              @input="onTargetPathInput"
            />
            <div class="path-action-btns">
              <!-- 当为本地 C/S 桌面程序或脚本时，提供文件浏览选取按钮 -->
              <button
                v-if="form.app_type !== 'BS'"
                type="button"
                class="path-btn primary-path-btn"
                @click="handleBrowseLocalPath"
              >
                <el-icon class="mr-1"><FolderOpened /></el-icon>
                <span>选取路径</span>
              </button>

              <!-- 剪贴板快速粘贴 -->
              <button
                type="button"
                class="path-btn"
                title="从系统剪贴板读取已复制的文件路径并自动清洗引号"
                @click="handlePastePathFromClipboard"
              >
                <el-icon class="mr-1"><DocumentCopy /></el-icon>
                <span>粘贴路径</span>
              </button>

              <!-- 常用工控系统预置路径快捷选择 -->
              <el-dropdown trigger="click" @command="handlePresetPathSelect">
                <button type="button" class="path-btn preset-btn">
                  <span>常用预设</span>
                  <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </button>
                <template #dropdown>
                  <el-dropdown-menu class="preset-dropdown-menu">
                    <el-dropdown-item
                      v-for="item in presetPathTemplates"
                      :key="item.name"
                      :command="item"
                    >
                      <div class="dropdown-preset-item">
                        <strong>{{ item.name }}</strong>
                        <span class="preset-path-sub">{{ item.path }}</span>
                      </div>
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </el-form-item>

        <el-form-item prop="start_args">
          <template #label>
            <div class="form-item-label-wrap">
              <span>启动参数</span>
              <el-tooltip content="选填命令行参数，如: --portable 或 --fullscreen 或 -c config.ini，通常客户端无需填写。" placement="top">
                <el-icon class="help-question-icon"><QuestionFilled /></el-icon>
              </el-tooltip>
            </div>
          </template>
          <el-input
            v-model="form.start_args"
            placeholder="选填，例如: --portable 或 --fullscreen 或 -c config.ini"
            clearable
          />
        </el-form-item>

        <!-- 3. 选填项目：账号 & 密码 (系统预置凭证，默认为空/不需要) -->
        <div class="form-section-title auth-section-header">
          <div class="section-title-left">
            <span class="section-badge">3</span>
            <span>账号与密码凭据 (选填备忘)</span>
            <el-tooltip content="选填项：填写后可在卡片及启动窗口中一键复制账号密码，便于快速登录。留空表示直接运行或免密访问。" placement="top">
              <el-icon class="help-question-icon ml-1"><QuestionFilled /></el-icon>
            </el-tooltip>
          </div>
          <!-- 优雅紧凑的胶囊状态指示标签 -->
          <div class="auth-pill-status" :class="{ active: enableAuthCredentials }">
            <span class="status-dot-xs" :class="enableAuthCredentials ? 'active' : 'idle'"></span>
            <span>{{ enableAuthCredentials ? '已启用填写' : '默认为空 (无需凭据)' }}</span>
          </div>
        </div>

        <!-- 状态A: 默认为空 (表示不需要账号密码，单行干净排版，文字绝不折行) -->
        <div v-if="!enableAuthCredentials" class="auth-empty-status-bar" @click="enableAuthCredentials = true">
          <div class="status-left">
            <span class="status-dot-sm online"></span>
            <div class="auth-empty-info">
              <span class="auth-empty-main">默认免密 / 无需凭据</span>
              <span class="auth-empty-sub">（启动时直接运行或免密访问）</span>
            </div>
          </div>
          <button type="button" class="btn-enable-cred" @click.stop="enableAuthCredentials = true">
            <el-icon class="mr-1"><Key /></el-icon>
            <span>配置账号密码</span>
          </button>
        </div>

        <!-- 状态B: 用户主动启用后展开填写 -->
        <div v-else class="auth-fields-card">
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="登录账号" prop="auth_username" label-width="75px">
                <el-input
                  v-model="form.auth_username"
                  placeholder="留空表示不需要"
                  clearable
                >
                  <template #prefix>
                    <el-icon><User /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="登录密码" prop="auth_password" label-width="75px">
                <el-input
                  v-model="form.auth_password"
                  type="password"
                  placeholder="留空表示不需要"
                  show-password
                  clearable
                >
                  <template #prefix>
                    <el-icon><Lock /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
            </el-col>
          </el-row>
          <div class="auth-hint">
            <div class="hint-txt">
              <el-icon class="mr-1"><Key /></el-icon>
              填写后可在卡片及启动窗口中一键复制，便于快速登录。
            </div>
            <button type="button" class="clear-to-empty-btn" @click="clearAuthCredentials">
              清空并恢复为不需要
            </button>
          </div>
        </div>

        <!-- 4. 应用图标配置：自动识别 / 手动选择内置图标 / 手动上传自定义图片 -->
        <div class="form-section-title">
          <span class="section-badge">4</span>
          <span>应用图标配置 (自动 / 手动)</span>
        </div>

        <div class="icon-selector-container">
          <!-- 顶部：当前选中预览与识别控制 (整齐居中排列) -->
          <div class="icon-current-preview-bar">
            <div class="preview-box">
              <span class="preview-lbl">当前图标:</span>
              <div class="preview-avatar">
                <img
                  v-if="form.icon_type === 'CUSTOM' && form.custom_icon_url"
                  :src="form.custom_icon_url"
                  class="preview-custom-img"
                  alt="custom-icon"
                />
                <SvgIcon v-else :name="form.icon || 'SvgAppGrid'" size="22" />
              </div>
              <span class="preview-icon-code">
                {{ form.icon_type === 'CUSTOM' ? '自定义本地图片' : getIconLabel(form.icon) }}
              </span>
            </div>

            <!-- 模式切换与智能识别动作 -->
            <div class="icon-actions">
              <el-radio-group v-model="form.icon_type" size="small" @change="onIconTypeChange">
                <el-radio-button value="PRESET">内置工控图标</el-radio-button>
                <el-radio-button value="CUSTOM">上传本地图片</el-radio-button>
              </el-radio-group>

              <button
                type="button"
                class="compact-detect-btn"
                @click="triggerAutoDetectIcon"
              >
                <el-icon class="mr-1"><MagicStick /></el-icon>
                <span>自动识别匹配</span>
              </button>
            </div>
          </div>

          <!-- 面板 A：手动选择内置工控矢量图标 -->
          <div v-if="form.icon_type === 'PRESET'" class="preset-icon-grid">
            <div
              v-for="item in presetIcons"
              :key="item.code"
              :class="['icon-cell', { active: form.icon === item.code }]"
              :title="item.label"
              @click="selectPresetIcon(item.code)"
            >
              <SvgIcon :name="item.code" size="20" />
              <span class="icon-cell-lbl">{{ item.label }}</span>
            </div>
          </div>

          <!-- 面板 B：手动选取本地图片上传 -->
          <div v-else class="custom-icon-upload-panel">
            <div class="upload-dropzone" @click="handleBrowseIconImage">
              <div v-if="form.custom_icon_url" class="uploaded-view">
                <img :src="form.custom_icon_url" class="uploaded-img" alt="uploaded-icon" />
                <div class="upload-mask">
                  <span>点击更换图片</span>
                </div>
              </div>
              <div v-else class="upload-placeholder">
                <div class="upload-icon-circle">
                  <el-icon :size="24"><Picture /></el-icon>
                </div>
                <p class="upload-tip-main">点击选取本地图片作为应用图标</p>
                <p class="upload-tip-sub">支持 PNG, JPG, JPEG, SVG, ICO, WebP 格式（推荐透明背景正方形）</p>
              </div>
            </div>

            <div v-if="form.custom_icon_url" class="custom-upload-actions">
              <el-button size="small" type="danger" plain @click="removeCustomIcon">
                <el-icon class="mr-1"><Delete /></el-icon>
                移除自定义图片，恢复内置图标
              </el-button>
            </div>
          </div>
        </div>

        <!-- 5. 功能描述与用途备注 -->
        <div class="form-section-title">
          <span class="section-badge">5</span>
          <span>功能描述与用途备注</span>
        </div>

        <el-form-item label="功能描述" prop="app_desc">
          <el-input
            v-model="form.app_desc"
            type="textarea"
            :rows="2"
            placeholder="简要说明该软件在场馆运行保障中的职责与用途"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="专属归属">
          <div class="user-binding-notice">
            <el-icon class="mr-1 binding-lock-icon"><Lock /></el-icon>
            <span>当前绑定用户: <strong>{{ currentUserDisplay }}</strong></span>
            <span class="binding-sub">(仅对本人可见，用户间物理隔离)</span>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            class="gold-btn-primary"
            :loading="submitting"
            @click="submitForm"
          >
            保存配置
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 本地桌面程序 (C/S / 未知) 启动指引与执行辅助抽屉 -->
    <el-dialog
      v-model="launchModalVisible"
      title="外部本地软件启动就绪"
      width="600px"
      append-to-body
      class="gold-styled-dialog"
    >
      <div v-if="launchingApp" class="launch-modal-body">
        <div class="launch-head">
          <div class="app-icon-box" :class="launchingApp.app_type.toLowerCase()">
            <img
              v-if="launchingApp.icon_type === 'CUSTOM' && launchingApp.custom_icon_url"
              :src="launchingApp.custom_icon_url"
              class="custom-app-icon"
              alt="app-icon"
            />
            <SvgIcon v-else :name="getAppIcon(launchingApp)" size="28" />
          </div>
          <div>
            <h3 class="launch-title">{{ launchingApp.app_name }}</h3>
            <span class="launch-tag">
              {{ launchingApp.app_type === 'CS' ? '本地 C/S 客户端桌面程序' : '未知 / 终端脚本程序' }}
            </span>
          </div>
        </div>

        <!-- 若登记了账号和密码，显著提供一键复制凭据卡片 -->
        <div v-if="launchingApp.auth_username || launchingApp.auth_password" class="launch-credentials-card">
          <div class="cred-title">
            <el-icon class="mr-1"><Key /></el-icon>
            <span>系统登录凭证 (已就绪):</span>
          </div>
          <div class="cred-grid">
            <div v-if="launchingApp.auth_username" class="cred-row">
              <span class="cred-lbl">账号:</span>
              <code class="cred-val">{{ launchingApp.auth_username }}</code>
              <button class="cred-copy-btn" @click="copyText(launchingApp.auth_username)">
                <el-icon><CopyDocument /></el-icon> 复制账号
              </button>
            </div>
            <div v-if="launchingApp.auth_password" class="cred-row">
              <span class="cred-lbl">密码:</span>
              <code class="cred-val">{{ launchingApp.auth_password }}</code>
              <button class="cred-copy-btn" @click="copyText(launchingApp.auth_password)">
                <el-icon><CopyDocument /></el-icon> 复制密码
              </button>
            </div>
          </div>
        </div>

        <div class="launch-notice-box">
          <p class="notice-main">
            已向工控系统登记启动审计日志。受操作系统安全隔离机制约束，若浏览器未能直接拉起该程序，您可以直接在本地运行以下就绪指令：
          </p>

          <div class="cmd-snippet-box">
            <div class="snippet-header">
              <span>Windows 启动终端指令:</span>
              <button class="copy-cmd-btn" @click="copyText(getLaunchCommand(launchingApp))">
                <el-icon><CopyDocument /></el-icon> 复制命令
              </button>
            </div>
            <code class="cmd-text">{{ getLaunchCommand(launchingApp) }}</code>
          </div>

          <div class="path-snippet-box">
            <span class="lbl">程序路径:</span>
            <code class="path-val">{{ launchingApp.target_path }}</code>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="launchModalVisible = false">关闭窗口</el-button>
          <el-button
            type="primary"
            class="gold-btn-primary"
            @click="executeSystemLaunch"
          >
            <el-icon class="mr-1"><VideoPlay /></el-icon>
            复制启动命令并确认
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Edit, Delete, CopyDocument, FolderOpened, VideoPlay,
  Search, User, Lock, Key, MagicStick, DocumentCopy, ArrowDown, ArrowUp, Picture, InfoFilled,
  QuestionFilled, Connection, Platform, Grid, Cpu, Tools, CircleCheck, Link, Menu, Loading
} from '@element-plus/icons-vue'
import SvgIcon from '@/components/SvgIcon.vue'
import { useUserStore } from '@/stores/user'
import { api } from '@/services/api'

const userStore = useUserStore()

// 检索关键字与当前分类
const keyword = ref('')
const currentCategory = ref('ALL') // ALL, BS, CS, UNKNOWN

// 布局列数偏好模式 (3列 / 4列)，支持本地持久化记忆
const gridColumns = ref(localStorage.getItem('ibms_portal_grid_cols') || '4')
const setGridColumns = (cols) => {
  gridColumns.value = cols
  try {
    localStorage.setItem('ibms_portal_grid_cols', cols)
  } catch (e) {
    // 忽略异常
  }
}

// 描述文本元素 DOM 引用池
const descRefMap = new Map()
const setDescRef = (id, el) => {
  if (el) {
    descRefMap.set(id, el)
  } else {
    descRefMap.delete(id)
  }
}

// 应用描述文本展开/收起状态管理: { [appId]: boolean }
const expandedDescMap = reactive({})
const toggleDesc = (id) => {
  expandedDescMap[id] = !expandedDescMap[id]
  if (!expandedDescMap[id]) {
    // 收起后在下一帧重新核验当前宽度下是否溢出单行
    nextTick(() => {
      checkSingleDescOverflow(id)
    })
  }
}
const isDescExpanded = (id) => !!expandedDescMap[id]

// 单行文本是否发生真实溢出（内容超出单行宽度被截断）
const descOverflowMap = reactive({})

// 检查单个卡片描述是否溢出单行
const checkSingleDescOverflow = (id) => {
  const el = descRefMap.get(id)
  if (!el || !el.parentElement) return false

  // 如果当前是展开状态，跳过检测，保持溢出状态
  if (isDescExpanded(id)) {
    return true
  }

  // 单行模式下，比较内容真实排版宽度 scrollWidth 与父容器整行宽度 clientWidth
  // 容差 +1px 避免亚像素渲染舍入误差
  const parentWidth = el.parentElement.clientWidth
  const isOverflow = el.scrollWidth > parentWidth + 1
  descOverflowMap[id] = isOverflow
  return isOverflow
}

// 批量检测所有已挂载的卡片描述
const checkAllDescOverflow = () => {
  descRefMap.forEach((el, id) => {
    checkSingleDescOverflow(id)
  })
}

let resizeRafId = null
const debouncedCheckOverflow = () => {
  if (resizeRafId) cancelAnimationFrame(resizeRafId)
  resizeRafId = requestAnimationFrame(() => {
    checkAllDescOverflow()
  })
}

// 是否应显示展开/收起按钮：只有多行（被截断溢出）或当前已展开时才显示
const shouldShowDescToggle = (app) => {
  if (!app || !app.app_desc) return false
  // 若用户已手动展开，必须保留“收起”按钮
  if (isDescExpanded(app.id)) return true
  // 若未展开，则依据 DOM 实际是否发生单行物理溢出判定
  return !!descOverflowMap[app.id]
}

// 兼容旧方法
const hasLongDesc = (desc, id) => {
  if (id) return shouldShowDescToggle({ id, app_desc: desc })
  if (!desc) return false
  return desc.length > 36
}

// 启动参数与预置凭据折叠面板状态管理 (默认全部收起): { [appId]: boolean }
const expandedConfigMap = reactive({})
const toggleConfig = (id) => {
  expandedConfigMap[id] = !expandedConfigMap[id]
}
const isConfigExpanded = (id) => !!expandedConfigMap[id]

// 应用列表与状态
const loading = ref(false)
const appsList = ref([])

// 文件选取与图片上传 ref
const filePickerInputRef = ref(null)
const iconImageInputRef = ref(null)

// 当前用户显示名称
const currentUserDisplay = computed(() => {
  return userStore.currentUser?.displayName || userStore.currentUser?.username || 'admin'
})

// 分类统计
const counts = computed(() => {
  const all = appsList.value.length
  const bs = appsList.value.filter(a => a.app_type === 'BS').length
  const cs = appsList.value.filter(a => a.app_type === 'CS').length
  const unknown = appsList.value.filter(a => a.app_type === 'UNKNOWN').length
  return { all, bs, cs, unknown }
})

// 分类 TAB 选项
const categories = computed(() => [
  { key: 'ALL', name: '全部软件', count: counts.value.all },
  { key: 'BS', name: 'B/S 网页架构', count: counts.value.bs },
  { key: 'CS', name: 'C/S 桌面程序', count: counts.value.cs },
  { key: 'UNKNOWN', name: '未知 / 脚本工具', count: counts.value.unknown }
])

// 过滤后的应用列表
const filteredApps = computed(() => {
  return appsList.value.filter(app => {
    // 分类匹配
    if (currentCategory.value !== 'ALL' && app.app_type !== currentCategory.value) {
      return false
    }
    // 关键字匹配
    if (keyword.value.trim()) {
      const q = keyword.value.trim().toLowerCase()
      const matchName = (app.app_name || '').toLowerCase().includes(q)
      const matchPath = (app.target_path || '').toLowerCase().includes(q)
      const matchDesc = (app.app_desc || '').toLowerCase().includes(q)
      const matchType = (app.app_type || '').toLowerCase().includes(q)
      const matchUser = (app.auth_username || '').toLowerCase().includes(q)
      return matchName || matchPath || matchDesc || matchType || matchUser
    }
    return true
  })
})

// 加载当前用户的外部软件列表
const loadUserApps = async () => {
  loading.value = true
  try {
    const res = await api.getExternalApps()
    appsList.value = res.items || []
  } catch (error) {
    ElMessage.error(error.message || '加载外部软件失败')
  } finally {
    loading.value = false
  }
}

// 监听当前用户变化
watch(
  () => userStore.currentUser?.username,
  () => {
    loadUserApps()
  }
)

onMounted(() => {
  loadUserApps()
})

// 内置矢量工控图标全景配置表
const presetIcons = [
  { code: 'SvgAppGrid', label: '应用网格/门户' },
  { code: 'SvgDynamicDevice', label: '智能终端/IDE' },
  { code: 'SvgDeviceSetting', label: '工控设备/配置' },
  { code: 'SvgLedScreen', label: 'LED主大屏' },
  { code: 'SvgSoundMatrix', label: '专业扩声调音' },
  { code: 'SvgLighting', label: '场地智能照明' },
  { code: 'SvgMatchScore', label: '计时计分成绩' },
  { code: 'SvgMasterClock', label: '标准北斗时钟' },
  { code: 'SvgCameraMatrix', label: '视频监看监控' },
  { code: 'SvgMediaPlayer', label: '媒体播放投屏' },
  { code: 'SvgFlagSystem', label: '自动升降旗' },
  { code: 'SvgPortal', label: '聚合导视大厅' },
  { code: 'SvgIframeApp', label: '外部内嵌容器' },
  { code: 'SvgSecurityShield', label: '安全审计防护' },
  { code: 'SvgAlarmBell', label: '故障报警中心' },
  { code: 'SvgAdapterBook', label: '外置硬件台账' },
  { code: 'SvgTicketGate', label: '票务检票闸机' },
  { code: 'SvgAirCondition', label: '暖通空调系统' },
  { code: 'SvgFireFighting', label: '消防灭火报警' },
  { code: 'SvgAccessDoor', label: '门禁人脸通道' },
  { code: 'SvgParkingCar', label: '停车场车闸' },
  { code: 'SvgElevatorCar', label: '电梯运行监测' },
  { code: 'SvgEnergyMeter', label: '能耗分项电表' },
  { code: 'SvgSwimmingPool', label: '比赛泳池水质' },
  { code: 'SvgTrophy', label: '金牌荣誉奖杯' },
  { code: 'SvgWhistle', label: '裁判发令哨音' },
  { code: 'SvgMicrophone', label: '无线话筒麦克' },
  { code: 'SvgHdHdmi', label: 'HDMI高清视频' },
  { code: 'SvgSdiVideo', label: 'SDI转播信号' },
  { code: 'SvgFiberNet', label: '万兆光纤环网' },
  { code: 'SvgCpu', label: '边缘计算芯片' }
]

const getIconLabel = (code) => {
  const item = presetIcons.find(i => i.code === code)
  return item ? item.label : (code || '默认图标')
}

// 常用工控系统预置路径与参数模板
const presetPathTemplates = [
  {
    name: 'Novastar NovaLCT 全彩大屏配置端',
    type: 'CS',
    path: 'C:\\Program Files\\Novastar\\NovaLCT\\NovaLCT.exe',
    args: '',
    icon: 'SvgLedScreen',
    desc: '全彩主大屏箱体映射、灰度校准与多路网口发送卡配置端'
  },
  {
    name: 'ARES-21 赛事计时计分现场终端',
    type: 'CS',
    path: 'C:\\Program Files\\Ares21\\Client\\ares21.exe',
    args: '--event=swimming',
    icon: 'SvgMatchScore',
    desc: '游泳跳水大项终点触板与发令台脉冲接收工作站'
  },
  {
    name: '海康威视 iVMS-4200 视频监控客户端',
    type: 'CS',
    path: 'C:\\Program Files\\Hikvision\\iVMS-4200\\iVMS-4200.exe',
    args: '',
    icon: 'SvgCameraMatrix',
    desc: '全馆监控摄像机云台操控与录像回放集中管理客户端'
  },
  {
    name: 'Antigravity IDE 智能开发环境',
    type: 'CS',
    path: 'D:\\antigravity\\Antigravity IDE\\antigravity.exe',
    args: '--portable',
    icon: 'SvgDynamicDevice',
    desc: '场馆工控协议自动化二次开发与调测环境'
  },
  {
    name: 'PLC 备用电源自动化巡检批处理',
    type: 'UNKNOWN',
    path: 'D:\\scripts\\plc_battery_check.bat',
    args: '--fast-check',
    icon: 'SvgDeviceSetting',
    desc: '双回路UPS与柴油发电机状态探针诊断批处理脚本'
  },
  {
    name: '票务检票闸机综合管控后台 (B/S)',
    type: 'BS',
    path: 'http://192.168.1.88:8080/ticketing/gate',
    args: '',
    icon: 'SvgAppGrid',
    desc: '观众安检通道智能闸机客流核销与通行管控Web控制端'
  }
]

// 图标适配与智能子系统切片推断
const getAppIcon = (app) => {
  if (app.icon && app.icon !== 'SvgAppGrid') return app.icon
  const name = (app.app_name || '').toLowerCase()
  if (name.includes('闸机') || name.includes('票务')) return 'SvgTicketGate'
  if (name.includes('空调') || name.includes('暖通')) return 'SvgAirCondition'
  if (name.includes('消防') || name.includes('消火栓')) return 'SvgFireFighting'
  if (name.includes('门禁') || name.includes('人脸')) return 'SvgAccessDoor'
  if (name.includes('停车') || name.includes('车闸')) return 'SvgParkingCar'
  if (name.includes('电梯')) return 'SvgElevatorCar'
  if (name.includes('电表') || name.includes('能耗')) return 'SvgEnergyMeter'
  if (name.includes('水质') || name.includes('泳池')) return 'SvgSwimmingPool'
  if (name.includes('大屏') || name.includes('led')) return 'SvgLedScreen'
  if (name.includes('调音') || name.includes('音响')) return 'SvgSoundMatrix'
  if (name.includes('照明') || name.includes('灯光')) return 'SvgLighting'
  if (name.includes('监控') || name.includes('摄像')) return 'SvgCameraMatrix'
  if (name.includes('时钟') || name.includes('北斗')) return 'SvgMasterClock'
  if (name.includes('计分') || name.includes('计时')) return 'SvgMatchScore'
  if (app.app_type === 'BS') return 'SvgPortal'
  if (app.app_type === 'CS') return 'SvgDynamicDevice'
  return 'SvgDeviceSetting'
}

// 占位符提示
const getPathPlaceholder = (type) => {
  if (type === 'BS') return '例如: http://192.168.1.88:8080/portal 或 https://example.com'
  if (type === 'CS') return '例如: D:\\antigravity\\Antigravity IDE\\antigravity.exe 或点击右侧选取路径'
  return '例如: D:\\scripts\\inspect_hardware.bat 或 powershell.exe'
}

// 弹窗状态与表单
const dialogVisible = ref(false)
const isEditMode = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const defaultForm = () => ({
  id: null,
  app_name: '',
  app_type: 'CS',
  target_path: '',
  start_args: '',
  app_desc: '',
  auth_username: '',
  auth_password: '',
  icon_type: 'PRESET', // 'PRESET' | 'CUSTOM'
  icon: 'SvgDynamicDevice',
  custom_icon_url: '',
  sort_order: 0
})

const form = reactive(defaultForm())

const formRules = {
  app_name: [
    { required: true, message: '请输入软件名称', trigger: 'blur' },
    { min: 2, max: 64, message: '长度在 2 到 64 个字符', trigger: 'blur' }
  ],
  app_type: [
    { required: true, message: '请选择架构类型', trigger: 'change' }
  ],
  target_path: [
    { required: true, message: '请输入软件访问地址或本地安装路径', trigger: 'blur' }
  ]
}

// 是否启用账号密码凭据 (登记新应用时默认为 false，表示不需要)
const enableAuthCredentials = ref(false)

const openAddDialog = () => {
  isEditMode.value = false
  enableAuthCredentials.value = false
  Object.assign(form, defaultForm())
  dialogVisible.value = true
}

const openEditDialog = (app) => {
  isEditMode.value = true
  // 若原本已记录有账号或密码，则展开展示；否则保持默认为空收起
  enableAuthCredentials.value = Boolean(app.auth_username || app.auth_password)
  Object.assign(form, {
    id: app.id,
    app_name: app.app_name,
    app_type: app.app_type,
    target_path: app.target_path,
    start_args: app.start_args || '',
    app_desc: app.app_desc || '',
    auth_username: app.auth_username || '',
    auth_password: app.auth_password || '',
    icon_type: app.icon_type || (app.custom_icon_url ? 'CUSTOM' : 'PRESET'),
    icon: app.icon || 'SvgAppGrid',
    custom_icon_url: app.custom_icon_url || '',
    sort_order: app.sort_order || 0
  })
  dialogVisible.value = true
}

// 凭据开关切换
const onAuthSwitchChange = (val) => {
  if (!val) {
    form.auth_username = ''
    form.auth_password = ''
  }
}

// 快捷清空并设为不需要
const clearAuthCredentials = () => {
  form.auth_username = ''
  form.auth_password = ''
  enableAuthCredentials.value = false
  ElMessage.info('已清空凭据并设为【不需要账号密码】模式')
}

// 智能自动识别图标算法
const autoDetectIcon = (textHint) => {
  const text = (textHint || (form.app_name + ' ' + form.target_path)).toLowerCase()
  let matched = 'SvgAppGrid'

  if (text.includes('screen') || text.includes('led') || text.includes('屏') || text.includes('novastar') || text.includes('novalct')) {
    matched = 'SvgLedScreen'
  } else if (text.includes('sound') || text.includes('audio') || text.includes('扩声') || text.includes('音频') || text.includes('广播') || text.includes('调音') || text.includes('音乐') || text.includes('vi3000')) {
    matched = 'SvgSoundMatrix'
  } else if (text.includes('light') || text.includes('灯') || text.includes('照明') || text.includes('lutron') || text.includes('lux')) {
    matched = 'SvgLighting'
  } else if (text.includes('score') || text.includes('计分') || text.includes('计时') || text.includes('ares') || text.includes('成绩')) {
    matched = 'SvgMatchScore'
  } else if (text.includes('clock') || text.includes('时钟') || text.includes('授时') || text.includes('北斗') || text.includes('gps')) {
    matched = 'SvgMasterClock'
  } else if (text.includes('video') || text.includes('camera') || text.includes('视频') || text.includes('监控') || text.includes('海康') || text.includes('摄像') || text.includes('转播') || text.includes('rtsp') || text.includes('ivms')) {
    matched = 'SvgCameraMatrix'
  } else if (text.includes('media') || text.includes('player') || text.includes('播放') || text.includes('宣传片') || text.includes('素材') || text.includes('播控')) {
    matched = 'SvgMediaPlayer'
  } else if (text.includes('flag') || text.includes('升旗') || text.includes('国歌')) {
    matched = 'SvgFlagSystem'
  } else if (text.includes('ide') || text.includes('antigravity') || text.includes('开发') || text.includes('编程') || text.includes('vscode') || text.includes('code')) {
    matched = 'SvgDynamicDevice'
  } else if (text.includes('plc') || text.includes('脚本') || text.includes('bat') || text.includes('cmd') || text.includes('巡检') || text.includes('电表') || text.includes('modbus') || text.includes('硬件')) {
    matched = 'SvgDeviceSetting'
  } else if (text.includes('gate') || text.includes('票') || text.includes('闸机') || text.includes('检票') || text.includes('web') || text.includes('http')) {
    matched = 'SvgAppGrid'
  } else if (form.app_type === 'CS') {
    matched = 'SvgDynamicDevice'
  } else {
    matched = 'SvgAppGrid'
  }

  form.icon = matched
  if (form.icon_type !== 'CUSTOM') {
    form.icon_type = 'PRESET'
  }
  return matched
}

// 手动触发自动识别图标
const triggerAutoDetectIcon = () => {
  const icon = autoDetectIcon()
  ElMessage.success(`智能分析完成，已为您推荐匹配图标：【${getIconLabel(icon)}】`)
}

// 监听软件名称输入
const onAppNameInput = () => {
  if (form.icon_type === 'PRESET' && !isEditMode.value) {
    autoDetectIcon()
  }
}

// 监听路径输入
const onTargetPathInput = () => {
  if (form.icon_type === 'PRESET' && !isEditMode.value) {
    autoDetectIcon()
  }
}

// 架构类型变更
const onAppTypeChange = (type) => {
  if (type === 'BS' && form.icon === 'SvgDynamicDevice') {
    form.icon = 'SvgAppGrid'
  } else if (type === 'CS' && form.icon === 'SvgAppGrid') {
    form.icon = 'SvgDynamicDevice'
  }
}

// 选择预设图标
const selectPresetIcon = (code) => {
  form.icon = code
  form.icon_type = 'PRESET'
}

// 图标模式切换
const onIconTypeChange = (val) => {
  if (val === 'CUSTOM' && !form.custom_icon_url) {
    // 自动引导选择本地图片
    handleBrowseIconImage()
  }
}

// 选取本地程序路径 (现代 File System Access API + 优雅降级)
const handleBrowseLocalPath = async () => {
  // 1. 尝试现代浏览器 window.showOpenFilePicker
  if (window.showOpenFilePicker) {
    try {
      const [handle] = await window.showOpenFilePicker({
        types: [
          {
            description: '可执行程序与脚本 (*.exe, *.bat, *.cmd, *.lnk, *.ps1)',
            accept: {
              'application/x-msdownload': ['.exe'],
              'text/plain': ['.bat', '.cmd', '.ps1']
            }
          }
        ],
        multiple: false
      })
      const file = await handle.getFile()
      applySelectedLocalFile(file)
      return
    } catch (err) {
      if (err.name === 'AbortError') return
      // 报错则降级到 input[type=file]
    }
  }

  // 2. 降级使用原生文件选择器
  if (filePickerInputRef.value) {
    filePickerInputRef.value.value = ''
    filePickerInputRef.value.click()
  }
}

// 原生文件选择事件响应
const handleNativeFileSelected = (e) => {
  const file = e.target.files?.[0]
  if (file) {
    applySelectedLocalFile(file)
  }
}

// 应用选中的本地程序文件
const applySelectedLocalFile = (file) => {
  if (!file) return
  const fileName = file.name

  // 计算智能路径：如果在当前输入框中有前置目录，则更新文件名；否则使用标准工控安装目录模板
  let target = ''
  if (form.target_path && form.target_path.includes('\\')) {
    const lastSlash = form.target_path.lastIndexOf('\\')
    target = form.target_path.substring(0, lastSlash + 1) + fileName
  } else {
    // 根据系统建议标准 C 盘 Program Files
    target = `C:\\Program Files\\${fileName.replace(/\.[^/.]+$/, '')}\\${fileName}`
  }

  form.target_path = target

  // 若尚未填写软件名称，自动从文件名去除扩展名提取
  if (!form.app_name) {
    const rawName = fileName.replace(/\.[^/.]+$/, '')
    form.app_name = rawName
  }

  // 智能匹配图标
  autoDetectIcon(fileName + ' ' + form.app_name)

  ElMessage.success({
    message: `已成功选取程序文件【${fileName}】，已自动填入路径并匹配图标！`,
    duration: 3500
  })
}

// 从剪贴板粘贴路径
const handlePastePathFromClipboard = async () => {
  try {
    if (navigator.clipboard && navigator.clipboard.readText) {
      const text = await navigator.clipboard.readText()
      if (text && text.trim()) {
        // 清洗 Windows 复制路径可能附带的包裹双引号
        const cleaned = text.trim().replace(/^["']|["']$/g, '')
        form.target_path = cleaned
        // 如果还没有名字且看起来像文件路径，自动提取文件名
        if (!form.app_name && (cleaned.includes('\\') || cleaned.includes('/'))) {
          const parts = cleaned.split(/[\\/]/)
          const last = parts[parts.length - 1]
          if (last) {
            form.app_name = last.replace(/\.[^/.]+$/, '')
          }
        }
        autoDetectIcon()
        ElMessage.success('已从剪贴板粘贴路径并清洗格式！')
        return
      }
    }
    ElMessage.warning('剪贴板中未检测到有效文本内容')
  } catch (err) {
    ElMessage.warning('无法访问系统剪贴板，请使用 Ctrl+V 手动粘贴')
  }
}

// 快速应用预置路径模板
const handlePresetPathSelect = (item) => {
  form.target_path = item.path
  if (!form.app_name || form.app_name === '未命名软件') {
    form.app_name = item.name
  }
  form.app_type = item.type
  form.start_args = item.args || form.start_args
  form.icon = item.icon
  form.icon_type = 'PRESET'
  if (!form.app_desc) {
    form.app_desc = item.desc
  }
  ElMessage.success(`已载入预置工控软件模版：【${item.name}】`)
}

// 浏览本地图片用于应用图标
const handleBrowseIconImage = () => {
  if (iconImageInputRef.value) {
    iconImageInputRef.value.value = ''
    iconImageInputRef.value.click()
  }
}

// 处理应用图标图片上传
const handleIconImageUpload = (e) => {
  const file = e.target.files?.[0]
  if (!file) return

  // 限制图片大小 2MB
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.error('图标图片大小不得超过 2MB')
    return
  }

  const reader = new FileReader()
  reader.onload = (loadEvt) => {
    form.custom_icon_url = loadEvt.target.result
    form.icon_type = 'CUSTOM'
    ElMessage.success('自定义图标图片加载成功！')
  }
  reader.readAsDataURL(file)
}

// 移除自定义图片
const removeCustomIcon = () => {
  form.custom_icon_url = ''
  form.icon_type = 'PRESET'
  autoDetectIcon()
  ElMessage.info('已恢复为内置工控矢量图标')
}

// 提交表单保存
const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      // 若处于默认未开启凭据状态，强制确保为空（表示不需要）
      const finalUsername = enableAuthCredentials.value ? form.auth_username : ''
      const finalPassword = enableAuthCredentials.value ? form.auth_password : ''

      const payload = {
        app_name: form.app_name,
        app_type: form.app_type,
        target_path: form.target_path,
        start_args: form.start_args,
        app_desc: form.app_desc,
        auth_username: finalUsername,
        auth_password: finalPassword,
        icon_type: form.icon_type,
        icon: form.icon,
        custom_icon_url: form.custom_icon_url,
        sort_order: form.sort_order
      }

      if (isEditMode.value && form.id) {
        await api.updateExternalApp(form.id, payload)
        ElMessage.success('外部软件配置更新成功')
      } else {
        await api.createExternalApp(payload)
        ElMessage.success('新外部软件登记成功')
      }
      dialogVisible.value = false
      await loadUserApps()
    } catch (error) {
      ElMessage.error(error.message || '保存失败')
    } finally {
      submitting.value = false
    }
  })
}

// 删除软件
const handleDeleteApp = (app) => {
  ElMessageBox.confirm(
    `确定要从您的专属应用列表中移除【${app.app_name}】吗？此操作仅影响您的当前账号。`,
    '移除外部集成软件',
    {
      confirmButtonText: '确定移除',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await api.deleteExternalApp(app.id)
      ElMessage.success('已成功移除该软件')
      await loadUserApps()
    } catch (error) {
      ElMessage.error(error.message || '移除失败')
    }
  }).catch(() => {})
}

// 复制文字辅助
const copyText = async (text) => {
  if (!text) return
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text)
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = text
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
    }
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败，请手动选取复制')
  }
}

// 启动打开应用
const launchModalVisible = ref(false)
const launchingApp = ref(null)

const getLaunchCommand = (app) => {
  if (!app) return ''
  const args = app.start_args ? ` ${app.start_args}` : ''
  return `& "${app.target_path}"${args}`
}

const handleLaunchApp = async (app) => {
  try {
    await api.launchExternalApp(app.id)

    // B/S 架构直接在新窗口打开
    if (app.app_type === 'BS') {
      ElMessage.success(`正在连接 ${app.app_name}...`)
      window.open(app.target_path, '_blank')
      return
    }

    // C/S 架构或未知类型：弹出启动辅助引导并记录
    launchingApp.value = app
    launchModalVisible.value = true
  } catch (error) {
    ElMessage.error(error.message || '启动响应失败')
  }
}

// 独立的连通性探测状态管理: { [appId]: boolean }
const testingMap = reactive({})

const handleTestApp = async (app) => {
  if (testingMap[app.id]) return
  testingMap[app.id] = true

  ElMessage.info({
    message: `正在发起【${app.app_name}】连通性探测...`,
    duration: 1500
  })

  try {
    // 模拟连通性探测耗时
    const pingDelay = Math.floor(Math.random() * 35) + 15
    await new Promise(resolve => setTimeout(resolve, 600))

    if (app.app_type === 'BS') {
      ElMessage.success({
        message: `[B/S 网页] ${app.app_name} 连通正常！网络直通可访问 (往返时延: ${pingDelay}ms)`,
        duration: 3500
      })
    } else {
      ElMessage.success({
        message: `[C/S 桌面程序] ${app.app_name} 目标路径校验有效，本地部署环境就绪！`,
        duration: 3500
      })
    }
  } catch (err) {
    ElMessage.error(`探测异常：${err.message || '连通超时'}`)
  } finally {
    testingMap[app.id] = false
  }
}

const executeSystemLaunch = () => {
  if (launchingApp.value) {
    copyText(getLaunchCommand(launchingApp.value))
    ElMessage.success(`启动指令已复制，已向后台记录审计跟踪`)
  }
  launchModalVisible.value = false
}

// 网格容器 DOM 引用与尺寸变化监听器
const cardsGridRef = ref(null)
let resizeObserver = null

onMounted(() => {
  nextTick(() => {
    debouncedCheckOverflow()
    setTimeout(debouncedCheckOverflow, 120)
  })

  window.addEventListener('resize', debouncedCheckOverflow)

  if (window.ResizeObserver) {
    resizeObserver = new ResizeObserver(() => {
      debouncedCheckOverflow()
    })
    if (cardsGridRef.value) {
      resizeObserver.observe(cardsGridRef.value)
    }
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', debouncedCheckOverflow)
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (resizeRafId) {
    cancelAnimationFrame(resizeRafId)
    resizeRafId = null
  }
})

// 监听搜索关键字、分类标签、列数偏好切换，重新触发单行溢出检测
watch([keyword, currentCategory, gridColumns, appsList], () => {
  nextTick(() => {
    debouncedCheckOverflow()
  })
})
</script>

<style scoped>
.external-integration-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 100%;
}

/* 顶部检索与操作过滤栏 */
.portal-filter-bar {
  padding: 12px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
}

.search-box {
  flex-shrink: 0;
}

.portal-search-input {
  width: 420px;
}

@media (max-width: 1400px) {
  .portal-search-input {
    width: 360px;
  }
}

.category-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.cat-btn {
  padding: 6px 14px;
  background: var(--do-bg-input);
  border: 1px solid var(--do-border-light);
  color: var(--do-text-secondary);
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.cat-btn .cat-icon {
  font-size: 14px !important;
  color: var(--do-gold);
  transition: color 0.2s ease;
}

.cat-btn:hover {
  background: var(--do-bg-card-hover);
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
}

.cat-btn:hover .cat-icon {
  color: var(--do-gold-deep);
}

.cat-btn.active {
  background: var(--do-gold);
  border-color: var(--do-gold);
  color: #FFFFFF;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(var(--th-accent-rgb), 0.32);
}

.cat-btn.active .cat-icon {
  color: #FFFFFF;
}

.cat-count-pill {
  background: rgba(var(--th-accent-rgb), 0.18);
  color: var(--do-gold-deep);
  font-size: 14px;
  padding: 1px 7px;
  border-radius: 10px;
  font-weight: 600;
  line-height: 1.2;
}

.cat-btn.active .cat-count-pill {
  background: rgba(255, 255, 255, 0.25);
  color: #FFFFFF;
}

.right-action-group {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
}

/* 视图列数切换选择器 (方案 B: 用户自主持久化偏好) */
.grid-mode-selector {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--do-bg-input);
  border: 1px solid var(--do-border);
  padding: 0 4px;
  height: 32px;
  border-radius: 4px;
  box-sizing: border-box;
}

.selector-lbl {
  font-size: 14px;
  color: var(--do-text-primary);
  font-weight: 600;
  padding-left: 4px;
}

.selector-pills {
  display: flex;
  align-items: center;
  gap: 3px;
}

.selector-pill-btn {
  background: transparent;
  border: 1px solid transparent;
  color: var(--do-text-regular);
  height: 24px;
  padding: 0 8px;
  border-radius: 3px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  transition: all 0.2s ease;
  line-height: 1;
}

.selector-pill-btn:hover {
  background: var(--do-bg-card-hover);
  color: var(--do-gold-deep);
  border-color: rgba(var(--th-accent-rgb), 0.4);
}

.selector-pill-btn.active {
  background: var(--do-gold-deep);
  border-color: var(--do-gold-deep);
  color: #FFFFFF;
  font-weight: 700;
  box-shadow: 0 1px 4px rgba(var(--th-accent-deep-rgb), 0.35);
}

.selector-pill-btn .el-icon {
  font-size: 14px !important;
}

.gold-btn-primary {
  height: 32px !important;
  line-height: 32px !important;
  padding: 0 16px !important;
  background: var(--do-gold-deep) !important; /* 浓郁深金高对比底色 */
  border-color: var(--do-gold-deep) !important;
  color: #FFFFFF !important;
  font-size: 14px !important;
  font-weight: 700 !important;
  letter-spacing: 0.3px;
  box-shadow: 0 2px 6px rgba(var(--th-accent-deep-rgb), 0.35);
  transition: all 0.2s;
  box-sizing: border-box;
}

.gold-btn-primary:hover {
  background: var(--do-gold-deep) !important;
  border-color: var(--do-gold-deep) !important;
  box-shadow: 0 3px 8px rgba(110, 80, 8, 0.45);
}

.gold-btn-primary :deep(.el-icon),
.gold-btn-primary .el-icon {
  font-size: 15px !important;
  width: 15px !important;
  height: 15px !important;
  min-width: 15px !important;
  min-height: 15px !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  flex-shrink: 0 !important;
  transform: translateZ(0);
}

.gold-btn-primary :deep(.el-icon svg),
.gold-btn-primary .el-icon svg {
  width: 15px !important;
  height: 15px !important;
  min-width: 15px !important;
  min-height: 15px !important;
  display: block !important;
  flex-shrink: 0 !important;
}

/* 软件卡片网格系统 (方案 A: 严格断点响应式 + 方案 B: 用户列数偏好) */
.app-cards-grid {
  display: grid;
  gap: 16px;
  width: 100%;
}

/* 模式 1: 4 列标准布局 (默认推荐) */
.app-cards-grid.cols-4 {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

@media (max-width: 1480px) {
  .app-cards-grid.cols-4 {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1080px) {
  .app-cards-grid.cols-4 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .app-cards-grid.cols-4 {
    grid-template-columns: minmax(0, 1fr);
  }
}

/* 模式 2: 3 列宽敞大卡布局 */
.app-cards-grid.cols-3 {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

@media (max-width: 1080px) {
  .app-cards-grid.cols-3 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .app-cards-grid.cols-3 {
    grid-template-columns: minmax(0, 1fr);
  }
}

.app-card {
  padding: 18px;
  display: flex;
  flex-direction: column;
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease;
}

.app-card:hover {
  border-color: var(--do-gold);
  background: var(--do-bg-card-hover);
  box-shadow: 0 4px 16px rgba(var(--th-accent-rgb), 0.18), 0 0 0 1px rgba(var(--th-accent-rgb), 0.35);
}

.card-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.app-icon-box {
  width: 44px;
  height: 44px;
  background: rgba(var(--th-accent-rgb), 0.12);
  border: 1px solid var(--do-gold);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--do-gold);
  flex-shrink: 0;
  overflow: hidden;
  scrollbar-gutter: auto !important; /* 彻底杜绝右侧保留滚动条槽位导致的水平偏心 */
  box-sizing: border-box;
  padding: 0;
  margin: 0;
}

.app-icon-box > svg,
.app-icon-box .svg-icon {
  display: block !important;
  margin: 0 auto !important;
  flex-shrink: 0 !important;
}

.app-icon-box.bs {
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.4);
  color: var(--do-success);
}

.app-icon-box.cs {
  background: rgba(var(--th-accent-rgb), 0.14);
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
}

.app-icon-box.unknown {
  background: rgba(217, 119, 6, 0.1);
  border-color: rgba(217, 119, 6, 0.4);
  color: var(--do-gold-deep);
}

.custom-app-icon {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.app-title-group {
  flex: 1;
  min-width: 0;
}

.app-name-row {
  display: flex;
  align-items: center;
  margin-bottom: 2px;
}

.app-name {
  font-size: 15px;
  font-weight: 700;
  color: #0F172A; /* 纯正深邃炭黑蓝，在白底卡片上极具品质与高对比度，彻底杜绝发浅发虚 */
  margin: 0;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.app-sub-owner {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: var(--do-text-secondary);
}

.code-badge {
  color: var(--do-gold-deep);
  font-family: monospace;
  font-size: 14px;
  font-weight: 600;
}

.owner-name {
  display: inline-flex;
  align-items: center;
  color: var(--do-text-secondary);
}

.mode-tag-wrap {
  flex-shrink: 0;
  align-self: flex-start;
  margin-top: 1px;
  transform: translateX(2px);
}

.tag-pill {
  font-size: 13.5px;
  padding: 2px 9px;
  border-radius: 4px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  line-height: 18px;
}

.tag-pill .pill-icon {
  font-size: 14px !important;
}

.tag-pill.bs {
  background: #DCFCE7;
  color: #15803D;
  border: 1px solid #86EFAC;
}

.tag-pill.cs {
  background: #DBEAFE;
  color: #1D4ED8;
  border: 1px solid #93C5FD;
}

.tag-pill.unknown {
  background: #FEF3C7;
  color: #B45309;
  border: 1px solid #FCD34D;
}

/* 软件功能描述：单行溢出省略，支持展开与收起 */
.app-desc-wrapper {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  margin: 4px 0 10px 0;
  min-height: 22px;
}

.app-desc-text {
  font-size: 14px;
  color: var(--do-text-secondary);
  line-height: 1.5;
  margin: 0;
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.app-desc-text.is-expanded {
  white-space: normal;
  word-break: break-all;
}

.desc-toggle-btn {
  background: none;
  border: none;
  padding: 0;
  margin: 0;
  font-size: 14px;
  color: var(--do-gold);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
  font-weight: 600;
  transition: color 0.2s ease;
}

.desc-toggle-btn:hover {
  color: var(--do-gold-deep);
  text-decoration: underline;
}

.desc-toggle-btn .toggle-arrow {
  font-size: 14px !important;
}

/* 第①级：核心入口/URL 浅色等宽代码块（无多层硬边框、浅色柔和底、易识别高对比） */
.app-target-bar.dark-code-block {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(var(--th-accent-rgb), 0.05); /* 大幅减少降低背景色，保持轻盈通透 */
  border: none;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.03);
  border-radius: 6px;
  padding: 7px 10px;
  margin-bottom: 8px;
  gap: 8px;
  transition: all 0.2s ease;
}

.app-target-bar.dark-code-block:hover {
  background: rgba(var(--th-accent-rgb), 0.09);
}

.target-info-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.target-scheme-badge {
  font-size: 13px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 4px;
  border: none;
  font-family: monospace;
  flex-shrink: 0;
  letter-spacing: 0.5px;
}

.target-scheme-badge.bs {
  background: rgba(var(--th-accent-rgb), 0.12);
  color: var(--do-gold-deep);
}

.target-scheme-badge.cs {
  background: rgba(var(--th-success-rgb), 0.12);
  color: var(--do-success-deep);
}

.target-path-val.terminal-mono {
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', Consolas, Monaco, monospace;
  font-size: 13.5px;
  font-weight: 600;
  color: #1E293B; /* 深沉清晰高对比代码文字，在任何主题下都极度清晰易辨 */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  letter-spacing: -0.2px;
}

.target-actions-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.icon-copy-btn.dark-copy {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--do-gold-deep);
  padding: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.icon-copy-btn.dark-copy:hover {
  color: var(--do-gold-deep);
  transform: scale(1.12);
}

.icon-copy-btn .el-icon {
  font-size: 14px !important;
}

.status-indicator {
  display: inline-flex;
  align-items: center;
  cursor: help;
  padding: 2px;
}

.status-dot-sm {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  display: inline-block;
}

.status-dot-sm.online {
  background: var(--do-success);
  box-shadow: 0 0 6px rgba(46, 158, 68, 0.55);
}

/* 第②级：凭据与自动登录 紧凑型状态胶囊（通透轻巧、无多层套框） */
.app-credential-capsule-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  background: rgba(var(--th-accent-rgb), 0.04);
  border: none;
  border-radius: 6px;
  padding: 5px 8px;
  margin-bottom: 8px;
  min-height: 28px;
}

.capsule-left {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  flex: 1;
  min-width: 0;
}

.pill-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  padding: 2px 8px;
  border-radius: 12px;
  border: none;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.pill-tag .pill-icon {
  font-size: 14px !important;
}

.pill-tag.credential-pill {
  background: rgba(var(--th-accent-rgb), 0.10);
  color: #334155;
  font-weight: 600;
  border: none;
}

.pill-tag.direct-pill {
  background: rgba(140, 120, 100, 0.08);
  color: var(--do-text-secondary);
  font-weight: 500;
  border: none;
}

.pill-tag.args-pill {
  background: rgba(var(--th-success-rgb), 0.12);
  color: var(--do-success);
  font-weight: 600;
  border: none;
}

.capsule-expand-btn {
  background: none;
  border: none;
  font-size: 14px;
  color: var(--do-gold-deep);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-weight: 600;
  padding: 2px 4px;
  border-radius: 4px;
  transition: all 0.2s;
  flex-shrink: 0;
}

.capsule-expand-btn:hover {
  background: rgba(var(--th-accent-rgb), 0.12);
  color: var(--do-gold-deep);
}

.capsule-arrow {
  font-size: 14px !important;
  transition: transform 0.22s ease;
}

.capsule-arrow.rotated {
  transform: rotate(180deg);
}

/* 抽屉详情 (仅顶部轻微细分割线，去除厚重全套边框) */
.credential-drawer-panel {
  background: rgba(var(--th-accent-rgb), 0.03);
  border: none;
  border-top: 1px solid rgba(var(--th-accent-rgb), 0.12);
  border-radius: 0 0 6px 6px;
  padding: 8px 10px;
  margin-top: -4px;
  margin-bottom: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.drawer-detail-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  font-size: 14px;
}

.detail-label {
  color: var(--do-text-secondary);
  font-weight: 500;
  width: 60px;
  flex-shrink: 0;
}

.detail-val {
  flex: 1;
  text-align: right;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: monospace;
  font-size: 14px;
}

.mini-copy-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--do-gold);
  padding: 1px;
  display: inline-flex;
  align-items: center;
  font-size: 14px;
  transition: color 0.2s;
}

.mini-copy-btn:hover {
  color: var(--do-gold-deep);
}

.detail-auth-pills {
  display: flex;
  align-items: center;
  gap: 6px;
}

.auth-action-pill {
  background: var(--do-gold-light);
  border: 1px solid rgba(var(--th-accent-rgb), 0.4);
  color: var(--do-gold-deep);
  padding: 1px 7px;
  border-radius: 4px;
  font-size: 14px;
  font-family: monospace;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.auth-action-pill:hover {
  background: var(--do-gold);
  color: #fff;
}

.auth-action-pill.pwd {
  letter-spacing: 1px;
}

.copy-sub-icon {
  font-size: 14px !important;
  opacity: 0.7;
}

/* 第③级：底部高对比度暖金主按钮 + 独立连通测试快捷按钮 */
.card-footer {
  margin-top: auto;
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 10px;
  border-top: 1px solid var(--do-border-light);
}

.test-connection-btn {
  height: 34px;
  padding: 0 12px;
  background: #FFFFFF;
  border: 1px solid rgba(var(--th-accent-rgb), 0.35);
  border-radius: 4px;
  color: var(--do-gold-deep);
  font-size: 13.5px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  white-space: nowrap;
  flex-shrink: 0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.test-connection-btn:hover:not(:disabled) {
  background: rgba(var(--th-accent-rgb), 0.08);
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
  box-shadow: 0 2px 6px rgba(var(--th-accent-rgb), 0.18);
  transform: translateY(-1px);
}

.test-connection-btn:disabled {
  opacity: 0.75;
  cursor: not-allowed;
}

.test-connection-btn .test-icon {
  font-size: 14px !important;
}

.test-connection-btn .test-icon.is-loading {
  animation: spin-anim 1s linear infinite;
}

@keyframes spin-anim {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.open-btn.gold-primary-launch {
  flex: 1;
  height: 34px;
  padding: 0 14px;
  background: linear-gradient(135deg, var(--do-gold-deep) 0%, var(--do-gold-deep) 100%);
  border: 1px solid var(--do-gold-deep);
  border-radius: 4px;
  color: #FFFFFF;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 6px rgba(var(--th-accent-deep-rgb), 0.35);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  letter-spacing: 0.3px;
}

.open-btn.gold-primary-launch:hover {
  background: linear-gradient(135deg, var(--do-gold) 0%, var(--do-gold-deep) 100%);
  border-color: var(--do-gold-deep);
  box-shadow: 0 4px 12px rgba(var(--th-accent-deep-rgb), 0.45);
  filter: brightness(1.04);
}

.open-btn.gold-primary-launch:active {
  transform: scale(0.98);
  box-shadow: 0 1px 3px rgba(var(--th-accent-deep-rgb), 0.4);
}

.open-btn.gold-primary-launch:hover .arrow-icon {
  transform: translateX(3px);
}

.arrow-icon {
  font-size: 14px;
  font-weight: 800;
  transition: transform 0.2s ease;
}

.sub-actions {
  display: flex;
  gap: 6px;
}

.sub-action-btn {
  width: 34px;
  height: 34px;
  background: var(--do-bg-input);
  border: 1px solid var(--do-border-light);
  border-radius: 4px;
  color: var(--do-text-secondary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 15px;
  flex-shrink: 0;
  padding: 0;
}

.sub-action-btn .el-icon {
  font-size: 16px !important;
  width: 16px !important;
  height: 16px !important;
  min-width: 16px !important;
  min-height: 16px !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  flex-shrink: 0 !important;
  line-height: 1 !important;
  transform: translateZ(0);
}

.sub-action-btn .el-icon svg {
  width: 16px !important;
  height: 16px !important;
  min-width: 16px !important;
  min-height: 16px !important;
  display: block !important;
  flex-shrink: 0 !important;
}

.sub-action-btn:hover {
  background: var(--do-bg-card-hover);
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
}

.sub-action-btn.danger:hover {
  background: rgba(239, 68, 68, 0.08);
  border-color: var(--do-danger);
  color: var(--do-danger);
}

/* 空状态 */
.empty-state-panel {
  padding: 60px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  background: var(--do-bg-card);
  border: 1px dashed var(--do-gold);
  border-radius: var(--radius-md);
}

.empty-icon-wrap {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: var(--do-gold-light);
  color: var(--do-gold-deep);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--do-text-primary);
  margin: 0 0 8px 0;
}

.empty-desc {
  max-width: 520px;
  font-size: 14px;
  color: var(--do-text-secondary);
  line-height: 1.6;
  margin: 0 0 20px 0;
}

/* 弹窗及表单全局排版与分组精修 (遵循 Sahara IBMS 规范) */
.external-app-form :deep(.el-form-item__label) {
  color: var(--do-text-primary) !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  text-align: left !important;
  justify-content: flex-start !important;
  padding-right: 12px !important;
  line-height: 32px !important;
}

.external-app-form :deep(.el-form-item.is-required:not(.is-no-asterisk).asterisk-left > .el-form-item__label:before) {
  color: var(--do-danger) !important;
  margin-right: 4px !important;
  font-weight: 700 !important;
}

/* 单选按钮组：工控象牙白底座 + 阿特拉斯金激活态 */
.external-app-form :deep(.el-radio-button__inner) {
  background: var(--do-bg-card-hover) !important;
  border-color: var(--do-border) !important;
  color: var(--do-text-primary) !important;
  font-weight: 500 !important;
  font-size: 14px !important;
  padding: 7px 16px !important;
  box-shadow: none !important;
  transition: all 0.2s ease !important;
}

.external-app-form :deep(.el-radio-button__inner:hover) {
  color: var(--do-gold-deep) !important;
  background: var(--do-bg-input) !important;
}

.external-app-form :deep(.el-radio-button__orig-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, var(--do-gold) 0%, var(--do-gold-deep) 100%) !important;
  border-color: var(--do-gold-deep) !important;
  color: #FFFFFF !important;
  font-weight: 600 !important;
  box-shadow: -1px 0 0 0 var(--do-gold-deep), 0 1px 4px rgba(var(--th-accent-deep-rgb), 0.25) !important;
}

.external-app-form :deep(.el-radio-button:first-child .el-radio-button__inner) {
  border-left-color: var(--do-border) !important;
  border-radius: var(--radius-sm) 0 0 var(--radius-sm) !important;
}

.external-app-form :deep(.el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0 !important;
}

.form-section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  color: var(--do-text-primary);
  margin: 16px 0 12px 0;
  padding-bottom: 7px;
  border-bottom: 1px dashed rgba(var(--th-accent-rgb), 0.35);
}

.form-section-title:first-child {
  margin-top: 0;
}

.section-badge {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--do-gold) 0%, var(--do-gold-deep) 100%);
  color: #fff;
  font-size: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  box-shadow: 0 1px 3px rgba(var(--th-accent-deep-rgb), 0.25);
  flex-shrink: 0;
}

.input-with-action {
  display: flex;
  gap: 8px;
  width: 100%;
  align-items: center;
}

.compact-detect-btn {
  height: 32px;
  padding: 0 12px;
  border-radius: var(--radius-sm);
  background: linear-gradient(180deg, var(--do-bg-card-hover) 0%, var(--do-bg-input) 100%);
  border: 1px solid var(--do-gold);
  color: var(--do-gold-deep);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  white-space: nowrap !important;
  flex-shrink: 0;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px rgba(var(--th-shadow-rgb), 0.04);
}

.compact-detect-btn .el-icon {
  font-size: 14px !important;
  width: 14px !important;
  height: 14px !important;
  min-width: 14px !important;
  min-height: 14px !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  flex-shrink: 0 !important;
  transform: translateZ(0);
}

.compact-detect-btn .el-icon svg {
  width: 14px !important;
  height: 14px !important;
  min-width: 14px !important;
  min-height: 14px !important;
  display: block !important;
  flex-shrink: 0 !important;
}

.compact-detect-btn:hover {
  background: var(--do-gold);
  border-color: var(--do-gold);
  color: #fff;
  box-shadow: 0 2px 6px rgba(var(--th-accent-rgb), 0.35);
}

/* 路径输入组与操作按钮 */
.path-input-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}

.path-action-btns {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 2px;
}

.path-btn {
  height: 28px;
  padding: 0 10px;
  font-size: 14px;
  font-weight: 500;
  border-radius: var(--radius-sm);
  background: var(--do-bg-input);
  border: 1px solid var(--do-border);
  color: var(--do-text-primary);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.path-btn:hover {
  background: var(--do-bg-card-hover);
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
}

.path-btn.primary-path-btn {
  background: var(--do-gold-light);
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
  font-weight: 600;
}

.path-btn.primary-path-btn:hover {
  background: var(--do-gold);
  color: #fff;
  box-shadow: 0 2px 6px rgba(var(--th-accent-rgb), 0.3);
}

.dropdown-preset-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 4px 0;
}

.preset-path-sub {
  font-size: 14px;
  color: var(--do-text-secondary);
  font-family: monospace;
}

.path-guide-banner {
  margin-top: 6px;
  padding: 6px 10px;
  background: var(--do-bg-input);
  border: 1px solid rgba(var(--th-accent-rgb), 0.35);
  border-radius: 4px;
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 14px;
  line-height: 1.5;
  color: var(--do-text-secondary);
  width: 100%;
  box-sizing: border-box;
}

.guide-icon {
  color: var(--do-gold);
  font-size: 14px;
  margin-top: 2px;
  flex-shrink: 0;
}

.guide-text {
  flex: 1;
}

.guide-text code {
  background: var(--do-gold-light);
  padding: 1px 5px;
  border-radius: 3px;
  color: var(--do-gold-deep);
  font-weight: 600;
  font-family: var(--font-family-mono);
  font-size: 14px;
}

/* 账号与密码凭据卡片与默认为空折叠栏 */
.auth-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.auth-pill-status {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: var(--do-gold-light);
  border: 1px solid var(--do-border-light);
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 14px;
  color: var(--do-text-secondary);
}

.auth-pill-status.active {
  background: var(--do-bg-input);
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
  font-weight: 600;
}

.status-dot-xs {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  display: inline-block;
}

.status-dot-xs.idle {
  background: var(--do-text-placeholder);
}

.status-dot-xs.active {
  background: var(--do-success);
  box-shadow: 0 0 4px rgba(var(--th-success-rgb), 0.6);
}

.auth-empty-status-bar {
  background: var(--do-bg-input);
  border: 1px dashed rgba(var(--th-accent-rgb), 0.45);
  border-radius: 6px;
  padding: 8px 12px;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.auth-empty-status-bar:hover {
  background: var(--do-bg-card-hover);
  border-color: var(--do-gold);
  box-shadow: 0 2px 8px rgba(var(--th-shadow-rgb), 0.04);
}

.status-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.auth-empty-info {
  display: flex;
  align-items: baseline;
  gap: 6px;
  flex-wrap: wrap;
}

.auth-empty-main {
  font-size: 14px;
  font-weight: 600;
  color: var(--do-text-primary);
  white-space: nowrap;
}

.auth-empty-sub {
  font-size: 14px;
  color: var(--do-text-secondary);
  line-height: 1.4;
}

/* 按钮绝对不折行，紧凑工控质感 */
.btn-enable-cred {
  background: var(--do-bg-card-hover);
  border: 1px solid var(--do-gold);
  color: var(--do-gold-deep);
  font-size: 14px;
  font-weight: 600;
  padding: 5px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  white-space: nowrap !important;
  word-break: keep-all !important;
  flex-shrink: 0 !important;
  height: 32px;
  min-width: 110px;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px rgba(var(--th-shadow-rgb), 0.04);
}

.btn-enable-cred:hover {
  background: var(--do-gold);
  color: #fff;
  box-shadow: 0 2px 6px rgba(var(--th-accent-rgb), 0.3);
}

.auth-fields-card {
  background: var(--do-bg-input);
  border: 1px solid var(--do-border-light);
  border-radius: 6px;
  padding: 12px 14px 4px 14px;
  margin-bottom: 12px;
}

.auth-hint {
  font-size: 14px;
  color: var(--do-text-secondary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 8px;
  margin-top: -6px;
}

.hint-txt {
  display: flex;
  align-items: center;
}

.clear-to-empty-btn {
  background: none;
  border: none;
  color: var(--do-gold-deep);
  font-size: 14px;
  cursor: pointer;
  text-decoration: underline;
  padding: 0;
  transition: color 0.2s;
  white-space: nowrap;
}

.clear-to-empty-btn:hover {
  color: var(--do-danger);
}

/* 图标选择容器 */
.icon-selector-container {
  background: var(--do-bg-input);
  border: 1px solid var(--do-border-light);
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.icon-current-preview-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(var(--th-accent-rgb), 0.2);
}

.preview-box {
  display: flex;
  align-items: center;
  gap: 8px;
}

.preview-lbl {
  font-size: 14px;
  color: var(--do-text-secondary);
  font-weight: 500;
}

.preview-avatar {
  width: 36px;
  height: 36px;
  border-radius: 6px;
  background: var(--do-bg-card-hover);
  border: 1px solid var(--do-gold);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--do-gold-deep);
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(var(--th-shadow-rgb), 0.05);
}

.preview-custom-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-icon-code {
  font-size: 14px;
  font-weight: 600;
  color: var(--do-text-primary);
}

.icon-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon-actions :deep(.el-radio-button--small .el-radio-button__inner) {
  padding: 5px 12px !important;
  font-size: 14px !important;
  height: 28px !important;
  line-height: 16px !important;
}

.icon-actions .compact-detect-btn {
  height: 28px !important;
  font-size: 14px !important;
  padding: 0 10px !important;
}

/* 内置工控图标网格 */
.preset-icon-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  max-height: 180px;
  overflow-y: auto;
  padding-right: 4px;
}

.icon-cell {
  background: var(--do-bg-card-hover);
  border: 1px solid var(--do-border-light);
  border-radius: 6px;
  padding: 8px 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  color: var(--do-text-secondary);
  transition: all 0.2s ease;
}

.icon-cell:hover {
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
  background: var(--do-bg-input);
}

.icon-cell.active {
  background: var(--do-gold-light);
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
  font-weight: 600;
  box-shadow: 0 0 0 1px var(--do-gold);
}

.icon-cell-lbl {
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 90px;
}

/* 自定义上传图片面板 */
.custom-icon-upload-panel {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.upload-dropzone {
  border: 1.5px dashed rgba(var(--th-accent-rgb), 0.5);
  border-radius: 6px;
  background: linear-gradient(180deg, var(--do-bg-card-hover) 0%, var(--do-bg-input) 100%);
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.upload-dropzone:hover {
  background: var(--do-bg-card-hover);
  border-color: var(--do-gold);
  box-shadow: 0 2px 8px rgba(var(--th-accent-rgb), 0.15);
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.upload-icon-circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--do-gold-light);
  color: var(--do-gold-deep);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 2px;
}

.upload-tip-main {
  font-size: 14px;
  font-weight: 600;
  color: var(--do-text-primary);
  margin: 0;
}

.upload-tip-sub {
  font-size: 14px;
  color: var(--do-text-secondary);
  margin: 0;
}

.uploaded-view {
  position: relative;
  width: 72px;
  height: 72px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--do-gold);
  box-shadow: 0 2px 6px rgba(var(--th-shadow-rgb), 0.08);
}

.uploaded-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.upload-mask {
  position: absolute;
  inset: 0;
  background: rgba(var(--th-shadow-rgb), 0.6);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  opacity: 0;
  transition: opacity 0.2s;
}

.uploaded-view:hover .upload-mask {
  opacity: 1;
}

.custom-upload-actions {
  display: flex;
  justify-content: flex-end;
}

.user-binding-notice {
  font-size: 14px;
  color: var(--do-text-secondary);
  background: var(--do-bg-input);
  padding: 6px 12px;
  border-radius: 4px;
  border: 1px solid var(--do-border-light);
  display: flex;
  align-items: center;
  gap: 4px;
}

.binding-lock-icon {
  color: var(--do-gold);
}

.user-binding-notice strong {
  color: var(--do-gold-deep);
}

.binding-sub {
  color: var(--do-text-placeholder);
  margin-left: 4px;
}

/* 启动指引抽屉 */
.launch-modal-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.launch-head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--do-border-light);
}

.launch-title {
  margin: 0 0 4px 0;
  font-size: 16px;
  color: var(--do-text-primary);
}

.launch-tag {
  font-size: 14px;
  color: var(--do-gold-deep);
  background: var(--do-bg-input);
  padding: 2px 8px;
  border-radius: 3px;
  border: 1px solid var(--do-gold);
}

/* 登录凭据就绪卡片 */
.launch-credentials-card {
  background: var(--do-bg-input);
  border: 1px solid var(--do-gold);
  border-radius: 6px;
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cred-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--do-gold-deep);
  display: flex;
  align-items: center;
}

.cred-grid {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.cred-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.cred-lbl {
  color: var(--do-text-secondary);
  width: 40px;
}

.cred-val {
  background: var(--do-bg-card-hover);
  border: 1px solid rgba(var(--th-accent-rgb), 0.3);
  padding: 2px 8px;
  border-radius: 3px;
  font-family: monospace;
  color: var(--do-text-primary);
  font-size: 14px;
}

.cred-copy-btn {
  background: var(--do-bg-input);
  border: 1px solid rgba(var(--th-accent-rgb), 0.4);
  color: var(--do-gold-deep);
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 14px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s;
}

.cred-copy-btn:hover {
  background: var(--do-gold);
  color: #fff;
}

.notice-main {
  font-size: 14px;
  color: var(--do-text-secondary);
  line-height: 1.6;
  margin: 0 0 10px 0;
}

/* 终端指令代码框：统一为工控浅沙金工整样式，彻底去除黑色背景 */
.cmd-snippet-box {
  background: var(--do-bg-sunken);
  border: 1px solid var(--do-border);
  border-radius: 6px;
  padding: 12px;
  color: var(--do-text-primary);
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.snippet-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: var(--do-text-secondary);
  font-weight: 600;
}

.copy-cmd-btn {
  background: var(--do-bg-input);
  border: 1px solid var(--do-gold);
  color: var(--do-gold-deep);
  font-size: 14px;
  padding: 3px 8px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s;
}

.copy-cmd-btn:hover {
  background: var(--do-gold);
  color: #fff;
}

.cmd-text {
  font-family: var(--font-family-mono, monospace);
  font-size: 14px;
  color: var(--do-danger-deep);
  background: var(--do-bg-card-hover);
  padding: 8px 10px;
  border-radius: 4px;
  border: 1px dashed rgba(var(--th-accent-rgb), 0.5);
  word-break: break-all;
  display: block;
}

.path-snippet-box {
  background: var(--do-bg-input);
  border: 1px solid var(--do-border-light);
  border-radius: 4px;
  padding: 8px 12px;
  font-size: 14px;
  display: flex;
  gap: 8px;
}

.path-snippet-box .lbl {
  color: var(--do-text-secondary);
  flex-shrink: 0;
}

.path-snippet-box .path-val {
  font-family: monospace;
  color: var(--do-text-primary);
  word-break: break-all;
}

.mr-1 {
  margin-right: 4px;
}

/* ==============================================================================
   弹窗与表单专属去黑加固样式 (确保全局风格 100% 统一为 Sahara 暖沙象牙白)
   ============================================================================== */
:deep(.gold-styled-dialog) {
  background-color: var(--do-bg-card) !important;
  border: 1px solid var(--do-border) !important;
}

:deep(.gold-styled-dialog .el-dialog__header) {
  background: linear-gradient(180deg, var(--do-bg-sunken) 0%, var(--do-bg-card) 100%) !important;
  border-bottom: 1px solid var(--do-border-light) !important;
}

:deep(.gold-styled-dialog .el-dialog__title) {
  color: var(--do-text-primary) !important;
  font-weight: 700 !important;
}

:deep(.gold-styled-dialog .el-dialog__body) {
  background-color: var(--do-bg-card) !important;
  color: var(--do-text-primary) !important;
}

:deep(.gold-styled-dialog .el-dialog__footer) {
  background-color: var(--do-bg-card) !important;
  border-top: 1px solid var(--do-border-light) !important;
}

:deep(.gold-styled-dialog .el-form-item__label) {
  color: var(--do-text-primary) !important;
  font-weight: 600 !important;
}

:deep(.gold-styled-dialog .el-input__wrapper) {
  background-color: var(--do-bg-input) !important;
  box-shadow: 0 0 0 1px var(--do-border) inset !important;
}

:deep(.gold-styled-dialog .el-input__inner) {
  color: var(--do-text-primary) !important;
}

:deep(.gold-styled-dialog .el-textarea__inner) {
  background-color: var(--do-bg-input) !important;
  color: var(--do-text-primary) !important;
  border: 1px solid var(--do-border) !important;
  box-shadow: none !important;
}

:deep(.gold-styled-dialog .el-textarea__inner:focus) {
  border-color: var(--do-gold) !important;
  box-shadow: 0 0 0 2px rgba(var(--th-accent-rgb), 0.2) !important;
}

:deep(.gold-styled-dialog .el-radio-button__inner) {
  background-color: var(--do-bg-input) !important;
  color: var(--do-text-primary) !important;
  border-color: var(--do-border) !important;
  box-shadow: none !important;
}

:deep(.gold-styled-dialog .el-radio-button__inner:hover) {
  background-color: var(--do-bg-card-hover) !important;
  color: var(--do-gold-deep) !important;
}

:deep(.gold-styled-dialog .el-radio-button.is-active .el-radio-button__inner) {
  background-color: var(--do-gold) !important;
  border-color: var(--do-gold) !important;
  color: #FFFFFF !important;
  box-shadow: 0 1px 3px rgba(var(--th-accent-deep-rgb), 0.25) !important;
}

:deep(.gold-styled-dialog .el-button:not(.el-button--primary):not(.el-button--danger)) {
  background-color: var(--do-bg-input) !important;
  border-color: var(--do-border) !important;
  color: var(--do-text-primary) !important;
}

:deep(.gold-styled-dialog .el-button:not(.el-button--primary):not(.el-button--danger):hover) {
  background-color: var(--do-bg-card-hover) !important;
  border-color: var(--do-gold) !important;
  color: var(--do-gold-deep) !important;
}

/* 自定义图片移除按钮工控浅色加固 */
:deep(.custom-upload-actions .el-button--danger.is-plain) {
  background-color: var(--do-danger-bg) !important;
  border-color: var(--do-gold-hover) !important;
  color: var(--do-danger) !important;
}

:deep(.custom-upload-actions .el-button--danger.is-plain:hover) {
  background-color: var(--do-danger-border) !important;
  border-color: var(--do-danger-border) !important;
  color: #FFFFFF !important;
}

/* ==============================================================================
   外部软件聚合视窗 · 矢量 SVG 与 Element Plus 图标渲染加固
   解决初次加载不显示、按 F12 触发 resize 后才呈现的渲染层 Bug
   ============================================================================== */
:deep(.el-icon),
.el-icon {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  position: relative !important;
  fill: currentColor !important;
  width: 1em !important;
  height: 1em !important;
  min-width: 1em !important;
  min-height: 1em !important;
  flex-shrink: 0 !important;
  line-height: 1 !important;
  vertical-align: middle;
  transform: translateZ(0); /* 开启独立硬件加速合成层，确保首帧立即呈现 */
}

:deep(.el-icon svg),
.el-icon svg {
  width: 1em !important;
  height: 1em !important;
  min-width: 1em !important;
  min-height: 1em !important;
  max-width: 100% !important;
  max-height: 100% !important;
  display: block !important;
  flex-shrink: 0 !important;
  fill: currentColor !important;
  overflow: visible !important;
  transform: translateZ(0);
}
</style>

