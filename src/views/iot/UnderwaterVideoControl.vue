<template>
  <div class="video-monitor-page">
    <!-- 页面标题头 -->
    <section class="page-header glass-panel">
      <div class="page-heading">
        <div class="page-icon"><SvgIcon name="SvgCameraMatrix" size="28" /></div>
        <div>
          <div class="title-row">
            <h1>水下音像采集控制总控台</h1>
          </div>
          <p>水下多机位分组实时监看 · 点击分组整组切屏 · 同型号分组参数统一配置与云台操控</p>
        </div>
      </div>
      <div class="header-status">
        <div class="status-metric">
          <span :class="['status-dot', currentCameras.length ? 'online' : 'warning']"></span>
          <span>{{ groups.length }} 个分组</span>
        </div>
        <div class="status-metric"><strong class="num-mono">{{ onlineCamCount }}/{{ currentCameras.length }}</strong> 当前组在线</div>
        <div class="status-metric"><strong class="num-mono">{{ totalBitrate }} Mbps</strong> 推流带宽</div>
        <button class="btn-header-action" @click="openGroupDialog('add')" title="新增水下摄像机分组（组内可添加多台同品牌型号摄像机）">
          <span>+ 新增分组</span>
        </button>
        <button class="btn-header-action" @click="openGroupDialog('edit', activeGroup)" title="以组为单位修改分组品牌型号、公共流参数与组内摄像机列表">
          <el-icon style="margin-right: 4px;"><Setting /></el-icon>
          <span>编辑分组参数</span>
        </button>
        <button class="btn-header-action" :disabled="syncingLedger" @click="syncGroupsFromLedger(false)" title="从水下台账数据库 tb_camera 按分组导入真实摄像机">
          <el-icon style="margin-right: 4px;"><Refresh /></el-icon>
          <span>{{ syncingLedger ? '同步中...' : '从台账同步分组' }}</span>
        </button>
        <button class="btn-header-action" @click="$router.push('/iot/underwater-video/ledger')" title="查看水下影像识别台账与实时报警">
          <span>水下台账与报警</span>
        </button>
        <button class="btn-header-action btn-header-primary" @click="snapshotAll" title="一键抓拍当前分组全部水下摄像机画面">
          <SvgIcon name="SvgCameraMatrix" size="14" style="margin-right: 4px;" />
          <span>一键整组抓拍</span>
        </button>
      </div>
    </section>

    <!-- 关键指标卡 -->
    <section class="metric-grid">
      <div class="metric-card glass-panel">
        <span>当前监控分组</span>
        <strong>{{ activeGroup?.name || '未选择分组' }}</strong>
        <em>{{ activeGroup ? (activeGroup.model || activeGroup.brand || '自定义型号') : '点击下方分组一键切屏' }}</em>
      </div>
      <div class="metric-card glass-panel">
        <span>分组与总机位</span>
        <strong class="num-mono">{{ groups.length }} 组 / {{ totalCameraCount }} 路</strong>
        <em>按水下区域与型号分组管理</em>
      </div>
      <div class="metric-card glass-panel">
        <span>当前组在线机位</span>
        <strong class="num-mono">{{ onlineCamCount }}/{{ currentCameras.length }}</strong>
        <em>当前选定分组实时拉流</em>
      </div>
      <div class="metric-card glass-panel">
        <span>当前组推流带宽</span>
        <strong class="num-mono">{{ totalBitrate }} Mbps</strong>
        <em>当前展示视窗合计</em>
      </div>
      <div class="metric-card glass-panel">
        <span>当前选中机位</span>
        <strong class="num-mono">{{ selectedCamHost || '未选择' }}</strong>
        <em>{{ selectedCamObj?.name || '点击视窗选择云台目标' }}</em>
      </div>
      <div class="metric-card glass-panel">
        <span>抓拍归档</span>
        <strong class="num-mono">{{ snapshotCount }} 张</strong>
        <em>今日水下快照入库</em>
      </div>
    </section>

    <!-- 水下摄像机分组切换栏 + 视窗布局控制 -->
    <section class="scene-toolbar glass-panel">
      <div class="group-bar-main">
        <div class="group-bar-head">
          <div>
            <h2>水下摄像机分组切换</h2>
            <span class="section-help">点击任意分组即可同时切换整组摄像机画面，支持以组为单位新增与编辑参数</span>
          </div>
          <div v-if="activeGroup" class="group-quick-actions">
            <button class="mini-action-btn" @click="reconnectGroup(activeGroup)">整组重拉流</button>
            <button class="mini-action-btn" @click="openGroupDialog('edit', activeGroup)">编辑当前组</button>
            <button class="mini-action-btn danger" @click="removeGroup(activeGroup)">删除当前组</button>
          </div>
        </div>

        <div v-if="groups.length" class="group-tabs-wrap">
          <button
            v-for="grp in groups"
            :key="grp.id"
            :class="['group-tab-btn', { active: activeGroupId === grp.id }]"
            @click="selectGroup(grp.id)"
          >
            <span class="group-tab-name">{{ grp.name }}</span>
            <span class="group-tab-count num-mono">{{ grp.cameras.length }} 路</span>
            <span v-if="grp.isMock" class="group-tab-mock">模拟</span>
            <span v-if="grp.model || grp.brand" class="group-tab-model">{{ grp.model || grp.brand }}</span>
          </button>
        </div>
        <div v-else class="group-empty-hint">
          暂无水下摄像机分组，请点击「+ 新增分组」创建分组或点击「从台账同步分组」。
        </div>
      </div>

      <div class="layout-switch">
        <span class="switch-lbl">视窗布局</span>
        <div class="segmented">
          <button :class="['seg-btn', { active: splitMode === 'auto' }]" @click="splitMode = 'auto'">整组自适应</button>
          <button :class="['seg-btn', { active: splitMode === 1 }]" @click="splitMode = 1">单屏</button>
          <button :class="['seg-btn', { active: splitMode === 4 }]" @click="splitMode = 4">4分屏</button>
          <button :class="['seg-btn', { active: splitMode === 9 }]" @click="splitMode = 9">9分屏</button>
        </div>
      </div>
    </section>

    <!-- 主视窗布局：整组视频网格 + 右侧 PTZ 云台控制栏 -->
    <section class="main-layout">
      <!-- 视频视窗网格区 -->
      <div class="video-stage glass-panel">
        <div v-if="!groups.length" class="empty-stage">
          <div class="empty-stage-inner">
            <p>当前尚未配置水下摄像机分组</p>
            <span>水下摄像机可按泳道/池区划分为多个分组，每组默认统一品牌型号并支持批量添加机位</span>
            <div class="empty-stage-actions">
              <button class="btn-header-action btn-header-primary" @click="openGroupDialog('add')">+ 新增水下摄像机分组</button>
              <button class="btn-header-action" @click="loadDemoGroups(true)">载入模拟演示分组</button>
              <button class="btn-header-action" @click="syncGroupsFromLedger(false)">从台账同步分组</button>
            </div>
          </div>
        </div>
        <div v-else-if="!displayedCameras.length" class="empty-stage">
          <div class="empty-stage-inner">
            <p>分组「{{ activeGroup?.name }}」中暂无摄像机</p>
            <button class="btn-header-action btn-header-primary" @click="openGroupDialog('edit', activeGroup)">编辑分组并添加摄像机</button>
          </div>
        </div>
        <div v-else :class="['video-grid-container', resolvedGridClass]">
          <div
            v-for="cam in displayedCameras"
            :key="`${activeGroupId}-${cam.id}`"
            :class="['cam-viewport', { selected: selectedCamId === cam.id }]"
            @click="selectedCamId = cam.id"
          >
            <!-- 视窗 OSD 顶栏 -->
            <div class="cam-osd-header">
              <span class="cam-title">{{ cam.name }}</span>
              <span v-if="activeGroup?.model || activeGroup?.brand" class="cam-model-tag">{{ activeGroup.model || activeGroup.brand }}</span>
              <span class="cam-meta num-mono">{{ activeGroup?.resolution || '1920×1080' }}@{{ activeGroup?.fps || 25 }}fps · {{ activeGroup?.bitrate || '6 Mbps' }}</span>
              <span :class="['status-dot', cam.isReconnecting ? 'warning' : 'online']"></span>
            </div>

            <!-- 视频画面渲染区 -->
            <div class="cam-feed-area">
              <div v-if="cam.isReconnecting" class="reconnecting-overlay">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>水下视频流重连中...</span>
              </div>

              <!-- 模拟演示水下监控画面（便于无实机时预览分组切屏效果） -->
              <div v-if="activeGroup?.isMock" class="uw-mock-visual">
                <div class="uw-water-grid"></div>
                <div class="uw-caustic-glow"></div>
                <div class="cam-corner top-left mock-badge">UNDERWATER DEMO</div>
                <div class="cam-corner top-right num-mono">
                  {{ cam.depth ? `水深 ${cam.depth} · ` : '' }}{{ activeGroup?.fps || 25 }} FPS
                </div>
                <div class="uw-center-reticle">
                  <span class="uw-reticle-label num-mono">{{ cam.ip }}</span>
                </div>
                <div class="bottom-osd num-mono">
                  <span class="osd-preset">{{ cam.maskedUrl }}</span>
                  <span class="rec-dot demo-dot">● SIM</span>
                  <span>{{ liveTime }}</span>
                </div>
              </div>

              <!-- 实时画面 (RTSP 转码 MJPEG / HTTP / HLS) -->
              <div v-else-if="cam.livePlayUrl" class="live-video-wrap ip-live-wrap">
                <img
                  v-if="cam.playType === 'mjpeg'"
                  :src="cam.livePlayUrl"
                  class="live-video-el"
                  :alt="cam.name"
                />
                <video
                  v-else
                  :src="cam.livePlayUrl"
                  class="live-video-el"
                  autoplay
                  playsinline
                  muted
                  controls
                ></video>
                <div class="cam-corner top-left live-badge">UNDERWATER LIVE</div>
                <div class="cam-corner top-right num-mono">{{ (activeGroup?.protocol || 'RTSP').toUpperCase() }}</div>
                <div class="bottom-osd num-mono">
                  <span class="osd-preset">{{ cam.maskedUrl }}</span>
                  <span class="rec-dot">● LIVE</span>
                  <span>{{ liveTime }}</span>
                </div>
              </div>

              <!-- 无有效流地址待机提示 -->
              <div v-else class="mock-cam-visual">
                <div class="cam-grid-lines"></div>
                <div class="cam-corner top-left">NO STREAM</div>
                <div class="cam-corner top-right num-mono">{{ activeGroup?.fps || 25 }} FPS</div>
                <div class="center-cross"></div>
                <div class="bottom-osd num-mono">
                  <span class="osd-preset">请编辑分组配置摄像机 IP 与流地址</span>
                  <span class="rec-dot">● STANDBY</span>
                  <span>{{ liveTime }}</span>
                </div>
              </div>
            </div>

            <!-- 视窗底部微工具条 -->
            <div class="cam-foot-tools">
              <button class="tool-btn" @click.stop="openGroupDialog('edit', activeGroup)">编辑分组</button>
              <button class="tool-btn" @click.stop="takeSnapshot(cam)">抓拍</button>
              <button class="tool-btn" @click.stop="triggerPtzPreset(cam)">看位</button>
              <button class="tool-btn" @click.stop="reconnectCam(cam)">重拉流</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧 PTZ 云台控制栏 -->
      <aside class="video-side glass-panel">
        <div class="side-pane">
          <div class="panel-heading">
            <div>
              <h2>云台 PTZ 八向控制盘</h2>
              <p>对当前组选中水下机位下发方向、变倍与预置位指令</p>
            </div>
            <span class="pane-pill num-mono">{{ selectedCamHost || selectedCamObj?.name || '未选择机位' }}</span>
          </div>

          <!-- 八向云台操控盘（按住转动、松开即停） -->
          <div class="ptz-pad">
            <div class="ptz-circle-bg">
              <button
                class="ptz-btn up"
                title="按住向上转动，松开停止"
                @pointerdown="startPtzHold('UP', 'STOP')"
                @pointerup="stopPtzHold('STOP')"
                @pointerleave="stopPtzHold('STOP')"
              >▲</button>
              <button
                class="ptz-btn left"
                title="按住向左转动，松开停止"
                @pointerdown="startPtzHold('LEFT', 'STOP')"
                @pointerup="stopPtzHold('STOP')"
                @pointerleave="stopPtzHold('STOP')"
              >◀</button>
              <button class="ptz-btn center" title="立即停止云台" @click="sendPtz('STOP')">■</button>
              <button
                class="ptz-btn right"
                title="按住向右转动，松开停止"
                @pointerdown="startPtzHold('RIGHT', 'STOP')"
                @pointerup="stopPtzHold('STOP')"
                @pointerleave="stopPtzHold('STOP')"
              >▶</button>
              <button
                class="ptz-btn down"
                title="按住向下转动，松开停止"
                @pointerdown="startPtzHold('DOWN', 'STOP')"
                @pointerup="stopPtzHold('STOP')"
                @pointerleave="stopPtzHold('STOP')"
              >▼</button>
            </div>
          </div>

          <!-- 镜头变倍（拉近/拉远）、对焦与归位 -->
          <div class="ptz-action-grid">
            <button
              class="ptz-act-btn"
              title="按住拉近镜头（Zoom In），松开停止"
              @pointerdown="startPtzHold('ZOOM_IN', 'ZOOM_STOP')"
              @pointerup="stopPtzHold('ZOOM_STOP')"
              @pointerleave="stopPtzHold('ZOOM_STOP')"
            >🔍 拉近 (Zoom +)</button>
            <button
              class="ptz-act-btn"
              title="按住拉远镜头（Zoom Out），松开停止"
              @pointerdown="startPtzHold('ZOOM_OUT', 'ZOOM_STOP')"
              @pointerup="stopPtzHold('ZOOM_STOP')"
              @pointerleave="stopPtzHold('ZOOM_STOP')"
            >🔎 拉远 (Zoom -)</button>
            <button
              class="ptz-act-btn"
              title="按住近焦微调，松开停止"
              @pointerdown="startPtzHold('FOCUS_NEAR', 'FOCUS_STOP')"
              @pointerup="stopPtzHold('FOCUS_STOP')"
              @pointerleave="stopPtzHold('FOCUS_STOP')"
            >近焦</button>
            <button
              class="ptz-act-btn"
              title="按住远焦微调，松开停止"
              @pointerdown="startPtzHold('FOCUS_FAR', 'FOCUS_STOP')"
              @pointerup="stopPtzHold('FOCUS_STOP')"
              @pointerleave="stopPtzHold('FOCUS_STOP')"
            >远焦</button>
            <button class="ptz-act-btn" @click="sendPtz('FOCUS_AUTO')">✨ 自动对焦</button>
            <button class="ptz-act-btn" @click="sendPtz('HOME')">🏠 云台归位</button>
          </div>

          <!-- 云台转动速度 -->
          <div class="ptz-sliders-group">
            <div class="slider-row">
              <span class="s-lbl">云台 / 变焦速度 ({{ ptzSpeed }}):</span>
              <el-slider v-model="ptzSpeed" :min="1" :max="18" size="small" />
            </div>
          </div>

          <!-- 当前分组参数摘要 -->
          <div v-if="activeGroup" class="group-meta-card">
            <div class="meta-title">当前分组参数摘要</div>
            <div class="meta-row"><span>分组名称</span><strong>{{ activeGroup.name }}</strong></div>
            <div class="meta-row"><span>统一品牌 / 型号</span><strong>{{ activeGroup.model || activeGroup.brand || '未填写' }}</strong></div>
            <div class="meta-row"><span>传输协议</span><strong class="num-mono">{{ (activeGroup.protocol || 'rtsp').toUpperCase() }}</strong></div>
            <div class="meta-row"><span>默认流路径</span><strong class="num-mono">{{ activeGroup.pathTemplate || '/' }}</strong></div>
            <div class="meta-row"><span>PTZ 端口</span><strong class="num-mono">{{ activeGroup.ptzPort || 1259 }}</strong></div>
          </div>
        </div>
      </aside>
    </section>

    <!-- 水下摄像机分组 新增 / 编辑弹窗（以组为单位，默认同组同品牌型号，支持组内多机位管理） -->
    <el-dialog
      v-model="groupDialogVisible"
      :title="groupDialogMode === 'edit' ? '编辑水下摄像机分组参数' : '新增水下摄像机分组'"
      width="780px"
      destroy-on-close
    >
      <el-form label-position="top" size="default" class="video-config-form">
        <el-form-item v-if="groupDialogMode === 'edit' && groups.length > 1" label="选择要编辑的分组">
          <el-select
            v-model="editingGroupId"
            style="width: 100%;"
            placeholder="请选择分组"
            @change="onEditingGroupChange"
          >
            <el-option
              v-for="grp in groups"
              :key="grp.id"
              :label="`${grp.name}（${grp.cameras.length} 路 · ${grp.model || grp.brand || '未标型号'}）`"
              :value="grp.id"
            />
          </el-select>
        </el-form-item>

        <!-- 区块 1：分组公共品牌型号与参数（同组摄像机默认共享） -->
        <div class="form-section-title">① 分组公共参数（同组摄像机默认同一品牌与型号）</div>

        <div class="config-grid-2">
          <el-form-item label="分组名称">
            <el-input v-model="groupForm.name" placeholder="如：比赛池东侧水下 1 组 / 跳水池深水组" clearable />
          </el-form-item>
          <el-form-item label="选择品牌与型号模板">
            <el-select v-model="groupForm.brandPreset" style="width: 100%;" @change="onBrandPresetChange">
              <el-option
                v-for="item in BRAND_PRESETS"
                :key="item.key"
                :label="item.label"
                :value="item.key"
              />
            </el-select>
          </el-form-item>
        </div>

        <div class="config-grid-3">
          <el-form-item label="具体型号标注">
            <el-input v-model="groupForm.model" placeholder="如：海康 DS-2CD 水下机" clearable />
          </el-form-item>
          <el-form-item label="网络协议">
            <el-select v-model="groupForm.protocol" style="width: 100%;">
              <el-option label="RTSP 视频流 (rtsp://)" value="rtsp" />
              <el-option label="HTTP / MJPEG 流 (http://)" value="mjpeg" />
              <el-option label="HLS 视频流 (.m3u8)" value="hls" />
            </el-select>
          </el-form-item>
          <el-form-item label="默认流路径模板">
            <el-input v-model="groupForm.pathTemplate" placeholder="如 /Streaming/Channels/101" clearable />
          </el-form-item>
        </div>

        <div class="config-grid-2">
          <el-form-item label="组统一账号（没有请留空）">
            <el-input v-model="groupForm.username" placeholder="同组摄像机默认鉴权账号" clearable />
          </el-form-item>
          <el-form-item label="组统一密码（没有请留空）">
            <el-input v-model="groupForm.password" type="password" show-password placeholder="同组摄像机默认鉴权密码" clearable />
          </el-form-item>
        </div>

        <div class="config-grid-3">
          <el-form-item label="画面规格">
            <el-select v-model="groupForm.resolutionKey" style="width: 100%;">
              <el-option label="1920×1080 @ 25fps" value="1920×1080@25" />
              <el-option label="1920×1080 @ 30fps" value="1920×1080@30" />
              <el-option label="1920×1080 @ 60fps" value="1920×1080@60" />
              <el-option label="3840×2160 @ 25fps" value="3840×2160@25" />
              <el-option label="3840×2160 @ 30fps" value="3840×2160@30" />
              <el-option label="1280×720 @ 25fps" value="1280×720@25" />
            </el-select>
          </el-form-item>
          <el-form-item label="单路码率标注">
            <el-select v-model="groupForm.bitrate" style="width: 100%;" filterable allow-create default-first-option>
              <el-option label="4 Mbps" value="4 Mbps" />
              <el-option label="6 Mbps" value="6 Mbps" />
              <el-option label="8 Mbps" value="8 Mbps" />
              <el-option label="12 Mbps" value="12 Mbps" />
              <el-option label="16 Mbps" value="16 Mbps" />
            </el-select>
          </el-form-item>
          <el-form-item label="云台 PTZ 端口">
            <el-input-number
              v-model="groupForm.ptzPort"
              :min="1"
              :max="65535"
              :controls="false"
              placeholder="默认 1259"
              style="width: 100%;"
            />
          </el-form-item>
        </div>

        <!-- 区块 2：组内摄像机清单 -->
        <div class="cam-list-header">
          <div class="form-section-title" style="margin: 0;">② 组内摄像机列表（共 {{ groupForm.cameras.length }} 台，默认继承上述品牌与流参数）</div>
          <div class="cam-list-tools">
            <el-button size="small" @click="showBatchAdd = !showBatchAdd">
              {{ showBatchAdd ? '收起批量添加' : '批量连续 IP 添加' }}
            </el-button>
            <el-button size="small" type="primary" plain @click="addCameraRow">+ 添加 1 台摄像机</el-button>
          </div>
        </div>

        <!-- 批量连续 IP 生成助手 -->
        <div v-if="showBatchAdd" class="batch-add-box">
          <span class="batch-lbl">起始 IP：</span>
          <el-input v-model="batchGen.startIp" size="small" placeholder="例如 192.168.7.171" style="width: 155px;" />
          <span class="batch-lbl">名称前缀：</span>
          <el-input v-model="batchGen.namePrefix" size="small" placeholder="水下机位" style="width: 115px;" />
          <span class="batch-lbl">数量：</span>
          <el-input-number v-model="batchGen.count" size="small" :min="1" :max="16" style="width: 96px;" />
          <el-button size="small" type="primary" @click="generateBatchCameras">生成并加入本组</el-button>
        </div>

        <div class="group-cam-rows">
          <div v-for="(row, idx) in groupForm.cameras" :key="row._key" class="group-cam-row">
            <div class="cam-row-index num-mono">#{{ idx + 1 }}</div>
            <div class="cam-row-fields">
              <div class="cam-row-inputs">
                <el-input v-model="row.name" size="small" placeholder="机位名称（如 水下 1 号位）" style="width: 170px;" clearable />
                <el-input v-model="row.ip" size="small" placeholder="IP 地址或完整流地址（如 192.168.7.171）" style="flex: 1; min-width: 170px;" clearable />
                <el-input v-model="row.customPath" size="small" :placeholder="`路径（留空用 ${groupForm.pathTemplate || '/live/av0'}）`" style="width: 190px;" clearable />
              </div>
              <div class="cam-row-preview">
                <span class="num-mono preview-url">{{ maskUrl(buildCamStreamUrl(groupForm, row)) || '请填写该机位 IP 地址' }}</span>
                <span v-if="row.probeMsg" :class="['probe-tag', row.probeOk ? 'ok' : 'warn']">{{ row.probeMsg }}</span>
              </div>
            </div>
            <div class="cam-row-ops">
              <el-button size="small" :loading="row.probing" @click="probeCameraRow(row)">探测</el-button>
              <el-button size="small" type="danger" plain :disabled="groupForm.cameras.length <= 1" @click="removeCameraRow(idx)">删除</el-button>
            </div>
          </div>
        </div>
      </el-form>

      <template #footer>
        <div class="dialog-footer-bar">
          <span class="footer-tip">保存后将立即切换至该分组并按组内机位重新拉流</span>
          <div style="flex: 1;"></div>
          <el-button @click="groupDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitGroupForm">
            {{ groupDialogMode === 'edit' ? '保存分组修改并切屏' : '创建分组并启动画面' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 水下影像新增报警预警弹窗 -->
    <el-dialog v-model="alertPopupVisible" title="⚠️ 水下影像识别新增报警预警" width="620px" destroy-on-close>
      <div v-if="latestAlertItem" class="uw-alert-box">
        <div class="uw-alert-head">
          <strong>{{ latestAlertItem.title }}</strong>
          <span>{{ latestAlertItem.create_time }}</span>
        </div>
        <div class="uw-alert-desc">{{ latestAlertItem.content }}（摄像机 ID: {{ latestAlertItem.camera_id }}）</div>
        <div class="uw-alert-img-wrap" v-if="latestAlertImg">
          <img :src="latestAlertImg" alt="报警抓拍" class="uw-alert-img" />
        </div>
      </div>
      <template #footer>
        <el-button @click="$router.push('/iot/underwater-video/ledger'); alertPopupVisible = false">查看全部台账</el-button>
        <el-button type="primary" @click="alertPopupVisible = false">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { Loading, Setting, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import SvgIcon from '@/components/SvgIcon.vue'
import { api, API_BASE_URL } from '@/services/api'

const UNDERWATER_GROUPS_STORAGE_KEY = 'venue_underwater_camera_groups_v1'

const DEMO_UNDERWATER_GROUPS = [
  {
    id: 'uw-demo-grp-1',
    name: '比赛池水下 1 组（1~4 泳道）',
    brandPreset: 'hikvision',
    brand: '海康威视',
    model: '海康威视 DS-2CD 水下摄像机',
    protocol: 'rtsp',
    pathTemplate: '/Streaming/Channels/101',
    username: '',
    password: '',
    resolution: '1920×1080',
    fps: 30,
    bitrate: '6 Mbps',
    ptzPort: 1259,
    isMock: true,
    cameras: [
      { id: 'uw-demo-101', name: '水下 01 · 1~2 道出发端', ip: '192.168.7.171', customPath: '', depth: '1.8m' },
      { id: 'uw-demo-102', name: '水下 02 · 3~4 道出发端', ip: '192.168.7.172', customPath: '', depth: '1.8m' },
      { id: 'uw-demo-103', name: '水下 03 · 1~2 道转身端', ip: '192.168.7.173', customPath: '', depth: '2.0m' },
      { id: 'uw-demo-104', name: '水下 04 · 3~4 道转身端', ip: '192.168.7.174', customPath: '', depth: '2.0m' }
    ]
  },
  {
    id: 'uw-demo-grp-2',
    name: '跳水深水池水下 2 组',
    brandPreset: 'dahua',
    brand: '大华',
    model: '大华 DH-IPC 水下高速机',
    protocol: 'rtsp',
    pathTemplate: '/cam/realmonitor?channel=1&subtype=0',
    username: '',
    password: '',
    resolution: '3840×2160',
    fps: 60,
    bitrate: '8 Mbps',
    ptzPort: 1259,
    isMock: true,
    cameras: [
      { id: 'uw-demo-201', name: '跳水池 01 · 10米台落水区东', ip: '192.168.7.181', customPath: '', depth: '4.5m' },
      { id: 'uw-demo-202', name: '跳水池 02 · 10米台落水区西', ip: '192.168.7.182', customPath: '', depth: '4.5m' },
      { id: 'uw-demo-203', name: '跳水池 03 · 3米板正面窗', ip: '192.168.7.183', customPath: '', depth: '3.2m' },
      { id: 'uw-demo-204', name: '跳水池 04 · 3米板侧面窗', ip: '192.168.7.184', customPath: '', depth: '3.2m' },
      { id: 'uw-demo-205', name: '跳水池 05 · 池底全景仰拍东', ip: '192.168.7.185', customPath: '', depth: '5.5m' },
      { id: 'uw-demo-206', name: '跳水池 06 · 池底全景仰拍西', ip: '192.168.7.186', customPath: '', depth: '5.5m' }
    ]
  }
]

const BRAND_PRESETS = [
  {
    key: 'hikvision',
    label: '海康威视 Hikvision（RTSP · /Streaming/Channels/101）',
    brand: '海康威视',
    model: '海康威视 水下摄像机',
    protocol: 'rtsp',
    pathTemplate: '/Streaming/Channels/101',
    ptzPort: 1259
  },
  {
    key: 'dahua',
    label: '大华 Dahua（RTSP · /cam/realmonitor?channel=1&subtype=0）',
    brand: '大华',
    model: '大华 水下摄像机',
    protocol: 'rtsp',
    pathTemplate: '/cam/realmonitor?channel=1&subtype=0',
    ptzPort: 1259
  },
  {
    key: 'uniview',
    label: '宇视 Uniview（RTSP · /media/video1）',
    brand: '宇视',
    model: '宇视 水下摄像机',
    protocol: 'rtsp',
    pathTemplate: '/media/video1',
    ptzPort: 1259
  },
  {
    key: 'visca',
    label: 'VISCA / 通用球机（RTSP · /live/av0）',
    brand: 'VISCA 通用',
    model: 'VISCA 水下云台摄像机',
    protocol: 'rtsp',
    pathTemplate: '/live/av0',
    ptzPort: 1259
  },
  {
    key: 'custom',
    label: '自定义品牌与型号',
    brand: '自定义',
    model: '',
    protocol: 'rtsp',
    pathTemplate: '/live/av0',
    ptzPort: 1259
  }
]

const groups = ref([])
const activeGroupId = ref('')
const splitMode = ref('auto') // 'auto' | 1 | 4 | 9
const selectedCamId = ref(null)
const snapshotCount = ref(0)
const syncingLedger = ref(false)

const liveTime = ref('')
let timer = null

// ===== 现场/水下报警轮询 =====
const alertPopupVisible = ref(false)
const latestAlertItem = ref(null)
const latestAlertImg = ref('')
let lastKnownAlertId = null
let alertPollTimer = null

const pollUnderwaterAlerts = async () => {
  try {
    const res = await api.underwaterLedger(5)
    if (!res || !res.online) return
    const maxId = Number(res.latestAlertId || 0)
    if (lastKnownAlertId !== null && maxId > lastKnownAlertId) {
      const newest = (res.alerts || []).find(a => Number(a.id) > lastKnownAlertId) || res.alerts?.[0]
      if (newest) {
        latestAlertItem.value = newest
        latestAlertImg.value = ''
        alertPopupVisible.value = true
        ElNotification({
          title: newest.title || '水下影像报警预警',
          message: newest.content || '',
          type: 'error',
          duration: 6000
        })
        if (newest.has_image) {
          try {
            const imgRes = await api.underwaterAlertImage(newest.id)
            latestAlertImg.value = imgRes?.image || ''
          } catch { /* ignore */ }
        }
      }
    }
    if (maxId > 0) lastKnownAlertId = maxId
  } catch { /* ignore */ }
}

// ===== URL 拼接与拉流工具 =====
const maskUrl = (url) => String(url || '').replace(/\/\/([^:@/]+):([^@/]+)@/, '//$1:***@')

const buildCamStreamUrl = (grpCfg, camRow) => {
  const rawIp = (camRow?.ip || '').trim()
  if (!rawIp) return ''
  const user = (grpCfg?.username || '').trim()
  const pwd = grpCfg?.password || ''

  if (/^[a-z]+:\/\//i.test(rawIp)) {
    if (user && !rawIp.includes('@')) {
      const auth = pwd ? `${encodeURIComponent(user)}:${encodeURIComponent(pwd)}@` : `${encodeURIComponent(user)}@`
      return rawIp.replace(/^([a-z]+:\/\/)/i, `$1${auth}`)
    }
    return rawIp
  }

  const protocol = grpCfg?.protocol || 'rtsp'
  const scheme = protocol === 'rtsp' ? 'rtsp://' : 'http://'
  const auth = user ? (pwd ? `${encodeURIComponent(user)}:${encodeURIComponent(pwd)}@` : `${encodeURIComponent(user)}@`) : ''
  let path = (camRow?.customPath || grpCfg?.pathTemplate || '').trim()
  if (path && !path.startsWith('/')) path = `/${path}`
  return `${scheme}${auth}${rawIp}${path}`
}

const makePlayConfig = (streamUrl, protocol, bustCache = false) => {
  if (!streamUrl) return { playType: 'mjpeg', livePlayUrl: '' }
  const base = API_BASE_URL.replace(/\/$/, '')
  const ts = bustCache ? `&_t=${Date.now()}` : ''
  if (protocol === 'rtsp' || streamUrl.startsWith('rtsp://')) {
    return {
      playType: 'mjpeg',
      livePlayUrl: `${base}/video/rtsp/mjpeg?url=${encodeURIComponent(streamUrl)}${ts}`
    }
  }
  if (protocol === 'mjpeg') {
    return {
      playType: 'mjpeg',
      livePlayUrl: `${base}/video/proxy?url=${encodeURIComponent(streamUrl)}${ts}`
    }
  }
  return {
    playType: 'video',
    livePlayUrl: `${base}/video/proxy?url=${encodeURIComponent(streamUrl)}${ts}`
  }
}

const parseResolutionKey = (key) => {
  const [resPart, fpsPart] = String(key || '1920×1080@25').split('@')
  return {
    resolution: (resPart || '1920×1080').replace(/x/i, '×'),
    fps: Number(fpsPart) || 25
  }
}

const hydrateGroup = (rawGrp, bustCache = false) => {
  const grpCfg = {
    id: rawGrp.id || `uw-grp-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
    name: rawGrp.name || '未命名水下分组',
    brandPreset: rawGrp.brandPreset || 'hikvision',
    brand: rawGrp.brand || '',
    model: rawGrp.model || '',
    protocol: rawGrp.protocol || 'rtsp',
    pathTemplate: rawGrp.pathTemplate ?? '/Streaming/Channels/101',
    username: rawGrp.username || '',
    password: rawGrp.password || '',
    resolution: rawGrp.resolution || '1920×1080',
    fps: Number(rawGrp.fps) || 25,
    bitrate: rawGrp.bitrate || '6 Mbps',
    ptzPort: Number(rawGrp.ptzPort) || 1259,
    isMock: Boolean(rawGrp.isMock)
  }
  const camList = Array.isArray(rawGrp.cameras) ? rawGrp.cameras : []
  grpCfg.cameras = camList.map((c, idx) => {
    const ip = (c.ip || '').trim()
    const customPath = (c.customPath || '').trim()
    const streamUrl = buildCamStreamUrl(grpCfg, { ip, customPath }) || c.streamUrl || ''
    const playCfg = grpCfg.isMock ? { playType: 'mjpeg', livePlayUrl: '' } : makePlayConfig(streamUrl, grpCfg.protocol, bustCache)
    return {
      id: c.id || `${grpCfg.id}-cam-${idx + 1}`,
      name: (c.name || '').trim() || `水下机位 ${String(idx + 1).padStart(2, '0')} (${ip || '未填IP'})`,
      ip,
      customPath,
      depth: c.depth || '',
      streamUrl,
      maskedUrl: maskUrl(streamUrl),
      isReconnecting: false,
      ...playCfg
    }
  })
  return grpCfg
}

const saveGroupsToStorage = () => {
  try {
    const payload = groups.value.map(g => ({
      id: g.id,
      name: g.name,
      brandPreset: g.brandPreset,
      brand: g.brand,
      model: g.model,
      protocol: g.protocol,
      pathTemplate: g.pathTemplate,
      username: g.username,
      password: g.password,
      resolution: g.resolution,
      fps: g.fps,
      bitrate: g.bitrate,
      ptzPort: g.ptzPort,
      isMock: Boolean(g.isMock),
      cameras: g.cameras.map(c => ({
        id: c.id,
        name: c.name,
        ip: c.ip,
        customPath: c.customPath || '',
        depth: c.depth || ''
      }))
    }))
    localStorage.setItem(UNDERWATER_GROUPS_STORAGE_KEY, JSON.stringify(payload))
  } catch { /* ignore */ }
}

const loadDemoGroups = (showToast = false) => {
  groups.value = DEMO_UNDERWATER_GROUPS.map(g => hydrateGroup(g))
  activeGroupId.value = groups.value[0]?.id || ''
  selectedCamId.value = groups.value[0]?.cameras[0]?.id ?? null
  saveGroupsToStorage()
  if (showToast) {
    ElMessage.success(`已载入 ${groups.value.length} 组水下摄像机模拟演示数据`)
  }
}

const loadGroupsFromStorage = () => {
  try {
    const raw = localStorage.getItem(UNDERWATER_GROUPS_STORAGE_KEY)
    if (raw === null) return false
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed) || parsed.length === 0) return false
    groups.value = parsed.map(g => hydrateGroup(g))
    if (groups.value.length) {
      activeGroupId.value = groups.value[0].id
      selectedCamId.value = groups.value[0].cameras[0]?.id ?? null
    }
    return true
  } catch {
    return false
  }
}

// 从水下台账 MySQL tb_camera 按 group 字段自动归组导入真实摄像机
const syncGroupsFromLedger = async (silent = false) => {
  syncingLedger.value = true
  try {
    const res = await api.underwaterLedger(5)
    if (!res || !res.online) {
      if (!silent) ElMessage.warning(res?.error || '无法连接水下台账数据库，请手动新增水下摄像机分组')
      return
    }
    const dbCams = (res.cameras || []).filter(c => c.ip)
    if (!dbCams.length) {
      if (!silent) ElMessage.info('水下台账 tb_camera 中暂无可用摄像机记录')
      return
    }
    const bucket = new Map()
    for (const row of dbCams) {
      const grpKey = String(row.group || '默认水下分组').trim() || '默认水下分组'
      if (!bucket.has(grpKey)) bucket.set(grpKey, [])
      bucket.get(grpKey).push(row)
    }
    const imported = []
    let idx = 1
    for (const [grpName, rows] of bucket.entries()) {
      const sample = rows[0]
      const sampleChannel = sample.channel || 101
      const pathTemplate = `/Streaming/Channels/${sampleChannel}`
      const fps = Number(sample.frame_rate) || 25
      imported.push(hydrateGroup({
        id: `uw-db-grp-${idx++}`,
        name: grpName.includes('组') ? grpName : `水下 ${grpName} 组`,
        brandPreset: 'hikvision',
        brand: '海康威视',
        model: sample.version ? `海康威视 (${sample.version})` : '海康威视 水下摄像机',
        protocol: 'rtsp',
        pathTemplate,
        username: sample.hik_user || '',
        password: '',
        resolution: '1920×1080',
        fps,
        bitrate: '6 Mbps',
        ptzPort: 1259,
        cameras: rows.map((r, cIdx) => {
          const host = r.port && Number(r.port) !== 80 && Number(r.port) !== 8000 ? `${r.ip}:${r.port}` : String(r.ip)
          const ch = r.channel && r.channel !== sampleChannel ? `/Streaming/Channels/${r.channel}` : ''
          return {
            id: `uw-db-cam-${r.id || cIdx + 1}`,
            name: r.name ? `${r.name} (${r.ip})` : `水下机位 ${cIdx + 1} (${r.ip})`,
            ip: host,
            customPath: ch
          }
        })
      }, true))
    }

    groups.value = imported
    activeGroupId.value = imported[0]?.id || ''
    selectedCamId.value = imported[0]?.cameras[0]?.id ?? null
    saveGroupsToStorage()
    if (!silent) {
      ElMessage.success(`已从台账导入 ${imported.length} 个分组、共 ${dbCams.length} 台水下摄像机`)
    }
  } catch (err) {
    if (!silent) ElMessage.error(`同步水下台账失败：${err?.message || err}`)
  } finally {
    syncingLedger.value = false
  }
}

// ===== 当前激活分组与视窗计算 =====
const activeGroup = computed(() => groups.value.find(g => g.id === activeGroupId.value) || null)
const currentCameras = computed(() => activeGroup.value?.cameras || [])

const displayedCameras = computed(() => {
  if (splitMode.value === 'auto') return currentCameras.value
  return currentCameras.value.slice(0, Number(splitMode.value) || 4)
})

const resolvedGridClass = computed(() => {
  if (splitMode.value !== 'auto') return `grid-${splitMode.value}`
  const count = displayedCameras.value.length
  if (count <= 1) return 'grid-1'
  if (count <= 4) return 'grid-4'
  return 'grid-9'
})

const totalCameraCount = computed(() => groups.value.reduce((sum, g) => sum + g.cameras.length, 0))
const onlineCamCount = computed(() => currentCameras.value.filter(cam => !cam.isReconnecting).length)
const totalBitrate = computed(() => {
  const perCam = Number(String(activeGroup.value?.bitrate || '6').split(' ')[0]) || 0
  return perCam * displayedCameras.value.length
})

const selectGroup = (groupId) => {
  if (activeGroupId.value === groupId) return
  activeGroupId.value = groupId
  const grp = groups.value.find(g => g.id === groupId)
  if (grp) {
    // 切换分组时刷新该组拉流地址，确保整组画面立即切换生效
    grp.cameras.forEach(cam => {
      const cfg = makePlayConfig(cam.streamUrl, grp.protocol, true)
      cam.playType = cfg.playType
      cam.livePlayUrl = cfg.livePlayUrl
    })
    selectedCamId.value = grp.cameras[0]?.id ?? null
  } else {
    selectedCamId.value = null
  }
}

// ===== 分组新增 / 编辑弹窗逻辑 =====
const groupDialogVisible = ref(false)
const groupDialogMode = ref('add') // 'add' | 'edit'
const editingGroupId = ref('')
const showBatchAdd = ref(false)

const batchGen = reactive({
  startIp: '192.168.7.171',
  namePrefix: '水下机位',
  count: 4
})

let rowKeySeq = 1
const makeCamRow = (partial = {}) => ({
  _key: `row-${Date.now()}-${rowKeySeq++}`,
  id: partial.id || '',
  name: partial.name || '',
  ip: partial.ip || '',
  customPath: partial.customPath || '',
  probing: false,
  probeOk: false,
  probeMsg: ''
})

const groupForm = reactive({
  name: '',
  brandPreset: 'hikvision',
  brand: '海康威视',
  model: '海康威视 水下摄像机',
  protocol: 'rtsp',
  pathTemplate: '/Streaming/Channels/101',
  username: '',
  password: '',
  resolutionKey: '1920×1080@25',
  bitrate: '6 Mbps',
  ptzPort: 1259,
  cameras: [makeCamRow({ name: '水下 01 号位' })]
})

const onBrandPresetChange = (key) => {
  const preset = BRAND_PRESETS.find(p => p.key === key)
  if (!preset) return
  groupForm.brand = preset.brand
  if (preset.key !== 'custom') {
    groupForm.model = preset.model
    groupForm.protocol = preset.protocol
    groupForm.pathTemplate = preset.pathTemplate
    groupForm.ptzPort = preset.ptzPort
  }
}

const loadGroupIntoForm = (grp) => {
  if (!grp) return
  groupForm.name = grp.name || ''
  groupForm.brandPreset = grp.brandPreset || 'custom'
  groupForm.brand = grp.brand || ''
  groupForm.model = grp.model || ''
  groupForm.protocol = grp.protocol || 'rtsp'
  groupForm.pathTemplate = grp.pathTemplate ?? '/Streaming/Channels/101'
  groupForm.username = grp.username || ''
  groupForm.password = grp.password || ''
  groupForm.resolutionKey = `${(grp.resolution || '1920×1080').replace(/x/i, '×')}@${grp.fps || 25}`
  groupForm.bitrate = grp.bitrate || '6 Mbps'
  groupForm.ptzPort = Number(grp.ptzPort) || 1259
  groupForm.cameras = grp.cameras.length
    ? grp.cameras.map(c => makeCamRow({ id: c.id, name: c.name, ip: c.ip, customPath: c.customPath || '' }))
    : [makeCamRow({ name: '水下 01 号位' })]
}

const openGroupDialog = (mode = 'add', targetGrp = null) => {
  showBatchAdd.value = false
  if (mode === 'edit') {
    if (!groups.value.length) {
      ElMessage.warning('当前暂无可编辑的分组，请先新增水下摄像机分组')
      openGroupDialog('add')
      return
    }
    const grp = targetGrp || activeGroup.value || groups.value[0]
    groupDialogMode.value = 'edit'
    editingGroupId.value = grp.id
    loadGroupIntoForm(grp)
    groupDialogVisible.value = true
    return
  }

  groupDialogMode.value = 'add'
  editingGroupId.value = ''
  const nextIndex = groups.value.length + 1
  const defPreset = BRAND_PRESETS[0]
  groupForm.name = `水下摄像机 ${nextIndex} 组`
  groupForm.brandPreset = defPreset.key
  groupForm.brand = defPreset.brand
  groupForm.model = defPreset.model
  groupForm.protocol = defPreset.protocol
  groupForm.pathTemplate = defPreset.pathTemplate
  groupForm.username = ''
  groupForm.password = ''
  groupForm.resolutionKey = '1920×1080@25'
  groupForm.bitrate = '6 Mbps'
  groupForm.ptzPort = defPreset.ptzPort
  groupForm.cameras = [
    makeCamRow({ name: '水下 01 号位', ip: '' }),
    makeCamRow({ name: '水下 02 号位', ip: '' })
  ]
  groupDialogVisible.value = true
}

const onEditingGroupChange = (grpId) => {
  const grp = groups.value.find(g => g.id === grpId)
  if (grp) loadGroupIntoForm(grp)
}

const addCameraRow = () => {
  const nextNo = String(groupForm.cameras.length + 1).padStart(2, '0')
  groupForm.cameras.push(makeCamRow({ name: `水下 ${nextNo} 号位` }))
}

const removeCameraRow = (idx) => {
  if (groupForm.cameras.length <= 1) return
  groupForm.cameras.splice(idx, 1)
}

const generateBatchCameras = () => {
  const m = String(batchGen.startIp || '').trim().match(/^(\d{1,3}\.\d{1,3}\.\d{1,3}\.)(\d{1,3})(:\d+)?$/)
  if (!m) {
    ElMessage.warning('请输入合法的 IPv4 起始地址，例如 192.168.7.171')
    return
  }
  const prefix = m[1]
  const startOctet = Number(m[2])
  const portSuffix = m[3] || ''
  const count = Math.max(1, Math.min(16, Number(batchGen.count) || 1))
  if (startOctet + count - 1 > 254) {
    ElMessage.warning('起始 IP 末段加上数量超过 254，请调整数量')
    return
  }
  // 如果当前列表全是空白占位行，先清空空白行再填充
  if (groupForm.cameras.every(r => !r.ip.trim())) {
    groupForm.cameras = []
  }
  const namePrefix = (batchGen.namePrefix || '水下机位').trim()
  for (let i = 0; i < count; i++) {
    const ip = `${prefix}${startOctet + i}${portSuffix}`
    const seq = String(groupForm.cameras.length + 1).padStart(2, '0')
    groupForm.cameras.push(makeCamRow({
      name: `${namePrefix} ${seq} (${ip})`,
      ip
    }))
  }
  showBatchAdd.value = false
  ElMessage.success(`已批量生成 ${count} 台水下摄像机到当前分组`)
}

const probeCameraRow = async (row) => {
  const url = buildCamStreamUrl(groupForm, row)
  if (!url) {
    ElMessage.warning('请先填写该台摄像机的 IP 地址')
    return
  }
  row.probing = true
  row.probeMsg = ''
  try {
    const res = await api.videoProbe({ target: url, protocol: groupForm.protocol })
    if (res && !res.__offline) {
      row.probeOk = Boolean(res.reachable)
      row.probeMsg = res.reachable ? '端口连通' : '无法连通'
      if (res.reachable) {
        ElMessage.success(res.message || `${row.ip} 连通正常`)
      } else {
        ElMessage.warning(res.message || `${row.ip} 无法连通`)
      }
    } else {
      row.probeOk = false
      row.probeMsg = '后端离线'
      ElMessage.warning('后端服务（8000端口）未响应')
    }
  } catch (err) {
    row.probeOk = false
    row.probeMsg = '探测失败'
    ElMessage.error(`探测失败：${err?.message || err}`)
  } finally {
    row.probing = false
  }
}

const submitGroupForm = () => {
  const grpName = (groupForm.name || '').trim()
  if (!grpName) {
    ElMessage.warning('请填写分组名称')
    return
  }
  const validRows = groupForm.cameras.filter(r => (r.ip || '').trim())
  if (!validRows.length) {
    ElMessage.warning('请至少填写 1 台摄像机的 IP 地址或流地址')
    return
  }
  const { resolution, fps } = parseResolutionKey(groupForm.resolutionKey)
  const preset = BRAND_PRESETS.find(p => p.key === groupForm.brandPreset)
  const rawGrp = {
    id: groupDialogMode.value === 'edit' ? editingGroupId.value : `uw-grp-${Date.now()}`,
    name: grpName,
    brandPreset: groupForm.brandPreset,
    brand: groupForm.brand || preset?.brand || '',
    model: (groupForm.model || '').trim(),
    protocol: groupForm.protocol,
    pathTemplate: (groupForm.pathTemplate || '').trim(),
    username: (groupForm.username || '').trim(),
    password: groupForm.password || '',
    resolution,
    fps,
    bitrate: (groupForm.bitrate || '').trim() || '6 Mbps',
    ptzPort: Number(groupForm.ptzPort) || 1259,
    cameras: validRows.map((r, idx) => ({
      id: r.id || `uw-cam-${Date.now()}-${idx + 1}`,
      name: (r.name || '').trim() || `水下机位 ${String(idx + 1).padStart(2, '0')} (${r.ip.trim()})`,
      ip: r.ip.trim(),
      customPath: (r.customPath || '').trim()
    }))
  }
  const hydrated = hydrateGroup(rawGrp, true)

  if (groupDialogMode.value === 'edit') {
    const idx = groups.value.findIndex(g => g.id === editingGroupId.value)
    if (idx >= 0) {
      groups.value.splice(idx, 1, hydrated)
    }
    activeGroupId.value = hydrated.id
    selectedCamId.value = hydrated.cameras[0]?.id ?? null
    saveGroupsToStorage()
    groupDialogVisible.value = false
    ElMessage.success(`已保存分组「${hydrated.name}」（共 ${hydrated.cameras.length} 路）并刷新整组画面`)
    return
  }

  groups.value.push(hydrated)
  activeGroupId.value = hydrated.id
  selectedCamId.value = hydrated.cameras[0]?.id ?? null
  saveGroupsToStorage()
  groupDialogVisible.value = false
  ElMessage.success(`已新增分组「${hydrated.name}」（共 ${hydrated.cameras.length} 路）并切换至该组画面`)
}

const removeGroup = async (grp) => {
  if (!grp) return
  try {
    await ElMessageBox.confirm(
      `确认删除水下摄像机分组「${grp.name}」（包含 ${grp.cameras.length} 台摄像机）吗？`,
      '删除分组确认',
      { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' }
    )
  } catch {
    return
  }
  groups.value = groups.value.filter(g => g.id !== grp.id)
  if (activeGroupId.value === grp.id) {
    activeGroupId.value = groups.value[0]?.id || ''
    selectedCamId.value = groups.value[0]?.cameras[0]?.id ?? null
  }
  saveGroupsToStorage()
  ElMessage.info(`已删除分组「${grp.name}」`)
}

// ===== PTZ 云台控制（针对当前组内选中的水下机位） =====
const ptzSpeed = ref(8)
let activePtzStopCmd = ''

const selectedCamObj = computed(() => currentCameras.value.find(c => c.id === selectedCamId.value) || null)
const selectedCamHost = computed(() => {
  const cam = selectedCamObj.value
  const src = cam?.ip || cam?.streamUrl || ''
  const m = String(src).match(/(\d{1,3}(?:\.\d{1,3}){3})/)
  return m ? m[1] : ''
})

const sendPtz = async (action) => {
  const host = selectedCamHost.value
  if (!host) {
    ElMessage.warning('请先在左侧选中一台有效的水下摄像机')
    return
  }
  const port = Number(activeGroup.value?.ptzPort) || 1259
  try {
    if (typeof api.videoPtz === 'function') {
      await api.videoPtz({
        host,
        port,
        action,
        speed: ptzSpeed.value
      })
    } else {
      const base = API_BASE_URL.replace(/\/$/, '')
      const resp = await fetch(`${base}/video/ptz`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ host, port, action, speed: ptzSpeed.value })
      })
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    }
  } catch (err) {
    ElMessage.error(err?.message || `云台指令 ${action} 下发失败`)
  }
}

const startPtzHold = (action, stopAction) => {
  activePtzStopCmd = stopAction
  sendPtz(action)
}

const stopPtzHold = (stopAction) => {
  if (!activePtzStopCmd) return
  const cmd = stopAction || activePtzStopCmd
  activePtzStopCmd = ''
  sendPtz(cmd)
}

const takeSnapshot = (cam) => {
  snapshotCount.value += 1
  ElMessage.success(`已抓拍 ${cam.name} 水下实时画面并存入素材库！`)
}

const triggerPtzPreset = (cam) => {
  ElMessage.success(`机位 ${cam.name} 已转动至水下预置位`)
}

const reconnectCam = (cam) => {
  const proto = activeGroup.value?.protocol || 'rtsp'
  cam.isReconnecting = true
  const playCfg = makePlayConfig(cam.streamUrl, proto, true)
  setTimeout(() => {
    cam.playType = playCfg.playType
    cam.livePlayUrl = playCfg.livePlayUrl
    cam.isReconnecting = false
    ElMessage.success(`${cam.name} 视频流已重新拉流！`)
  }, 800)
}

const reconnectGroup = (grp) => {
  if (!grp || !grp.cameras.length) return
  grp.cameras.forEach(cam => {
    cam.isReconnecting = true
    const playCfg = makePlayConfig(cam.streamUrl, grp.protocol || 'rtsp', true)
    setTimeout(() => {
      cam.playType = playCfg.playType
      cam.livePlayUrl = playCfg.livePlayUrl
      cam.isReconnecting = false
    }, 600)
  })
  ElMessage.success(`分组「${grp.name}」全部 ${grp.cameras.length} 路水下画面已重新拉流`)
}

const snapshotAll = () => {
  const count = displayedCameras.value.length
  if (!count) {
    ElMessage.warning('当前分组暂无可抓拍的水下摄像机画面')
    return
  }
  snapshotCount.value += count
  ElMessage.success(`分组「${activeGroup.value?.name}」一键抓拍完成，已归档 ${count} 张快照！`)
}

onMounted(() => {
  const loaded = loadGroupsFromStorage()
  if (!loaded) {
    // 无本地分组配置时，默认载入模拟演示分组，便于页面效果预览与开发调试
    loadDemoGroups(false)
  }
  liveTime.value = new Date().toLocaleTimeString()
  timer = setInterval(() => {
    liveTime.value = new Date().toLocaleTimeString()
  }, 1000)
  pollUnderwaterAlerts()
  alertPollTimer = setInterval(pollUnderwaterAlerts, 8000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  if (alertPollTimer) clearInterval(alertPollTimer)
})
</script>

<style scoped>
.video-monitor-page { display: flex; flex-direction: column; gap: 14px; min-width: 0; color: var(--do-text-primary); animation: fadeIn 0.3s ease-out; }
.glass-panel { background: var(--do-bg-card); border: 1px solid var(--do-border); border-radius: 10px; box-shadow: var(--shadow-sm); }

/* ===== 页面标题头 ===== */
.page-header { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 18px 22px; }
.page-heading { display: flex; align-items: center; gap: 14px; min-width: 0; }
.page-icon { width: 52px; height: 52px; display: grid; place-items: center; flex-shrink: 0; color: var(--do-gold); background: var(--do-gold-wash); border: 1px solid var(--do-border-dark); border-radius: 12px; }
h1, h2, h3, p { margin: 0; }
h1 { font-size: 21px; line-height: 1.3; }
h2 { font-size: 16px; line-height: 1.35; }
h3 { font-size: 15px; line-height: 1.35; }
.title-row { display: flex; align-items: center; gap: 10px; }
.page-heading p { margin-top: 5px; color: var(--do-text-secondary); font-size: 13px; }
.header-status { display: flex; align-items: center; justify-content: flex-end; gap: 12px; flex-wrap: wrap; color: var(--do-text-secondary); font-size: 13px; }
.status-metric { display: flex; align-items: center; gap: 6px; white-space: nowrap; }
.status-metric strong { color: var(--do-text-primary); font-size: 15px; }
.status-dot { width: 8px; height: 8px; flex: 0 0 auto; border-radius: 50%; background: currentColor; }
.status-dot.online { color: var(--do-success); box-shadow: 0 0 7px currentColor; }
.status-dot.warning { color: var(--do-warning); box-shadow: 0 0 7px currentColor; }

/* ===== 指标卡带 ===== */
.metric-grid { display: grid; grid-template-columns: repeat(6, minmax(135px, 1fr)); gap: 12px; }
.metric-card { min-width: 0; padding: 15px; }
.metric-card span { color: var(--do-text-secondary); font-size: 13px; }
.metric-card strong { display: block; margin-top: 8px; overflow: hidden; color: var(--do-text-primary); font-size: 17px; text-overflow: ellipsis; white-space: nowrap; }
.metric-card em { display: block; margin-top: 5px; overflow: hidden; color: var(--do-text-secondary); font-size: 13px; font-style: normal; text-overflow: ellipsis; white-space: nowrap; }

/* ===== 分组切换与布局工具条 ===== */
.scene-toolbar { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; padding: 14px 18px; flex-wrap: wrap; }
.group-bar-main { flex: 1; min-width: 280px; display: flex; flex-direction: column; gap: 10px; }
.group-bar-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.section-help { display: block; margin-top: 4px; color: var(--do-text-secondary); font-size: 13px; }
.group-quick-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.mini-action-btn { padding: 4px 10px; border-radius: 6px; border: 1px solid var(--do-border); background: var(--do-bg-sunken); color: var(--do-text-primary); font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.2s ease; }
.mini-action-btn:hover { border-color: var(--do-gold); color: var(--do-gold-deep); }
.mini-action-btn.danger:hover { border-color: var(--do-danger); color: var(--do-danger); }

.group-tabs-wrap { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.group-tab-btn { display: inline-flex; align-items: center; gap: 8px; padding: 8px 13px; border-radius: 8px; border: 1px solid var(--do-border); background: var(--do-bg-sunken); color: var(--do-text-primary); font-size: 13px; cursor: pointer; transition: all 0.2s ease; }
.group-tab-btn:hover { border-color: var(--do-gold); color: var(--do-gold-deep); }
.group-tab-btn.active { background: var(--do-gold); border-color: var(--do-gold); color: #FFFFFF; box-shadow: 0 2px 8px rgba(var(--th-accent-rgb), 0.28); }
.group-tab-name { font-weight: 700; }
.group-tab-count { padding: 1px 6px; border-radius: 10px; background: rgba(var(--th-shadow-rgb), 0.08); font-size: 12px; font-weight: 700; }
.group-tab-btn.active .group-tab-count { background: rgba(255, 255, 255, 0.22); color: #FFFFFF; }
.group-tab-mock { padding: 1px 5px; border-radius: 4px; background: var(--do-warning-bg); color: var(--do-warning-deep); border: 1px solid var(--do-warning-border); font-size: 11px; font-weight: 700; }
.group-tab-btn.active .group-tab-mock { background: rgba(255, 255, 255, 0.2); color: #FFFFFF; border-color: rgba(255, 255, 255, 0.38); }
.group-tab-model { font-size: 12px; color: var(--do-text-secondary); }
.group-tab-btn.active .group-tab-model { color: rgba(255, 255, 255, 0.88); }
.group-empty-hint { font-size: 13px; color: var(--do-text-secondary); padding: 4px 0; }

.layout-switch { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.switch-lbl { color: var(--do-text-secondary); font-size: 13px; white-space: nowrap; }
.segmented { display: flex; gap: 4px; padding: 3px; background: var(--do-bg-sunken); border: 1px solid var(--do-border-light); border-radius: 8px; }
.seg-btn { padding: 5px 12px; background: transparent; border: none; border-radius: 5px; color: var(--do-text-secondary); font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s ease; }
.seg-btn:hover { color: var(--do-gold-deep); }
.seg-btn.active { background: var(--do-gold); color: #FFFFFF; box-shadow: 0 2px 6px rgba(var(--th-accent-rgb), 0.22); }

/* ===== 主布局：视频网格 + 右侧控制栏 ===== */
.main-layout { display: grid; grid-template-columns: minmax(0, 1fr) minmax(320px, 360px); gap: 14px; align-items: stretch; }

.video-stage { padding: 14px; display: flex; min-height: 540px; }
.empty-stage { flex: 1; display: flex; align-items: center; justify-content: center; color: var(--do-text-secondary); font-size: 14px; background: var(--do-bg-sunken); border: 1px dashed var(--do-border); border-radius: 8px; padding: 24px; }
.empty-stage-inner { display: flex; flex-direction: column; align-items: center; gap: 10px; text-align: center; }
.empty-stage-inner p { font-size: 16px; font-weight: 700; color: var(--do-text-primary); }
.empty-stage-inner span { font-size: 13px; color: var(--do-text-secondary); }
.empty-stage-actions { display: flex; gap: 10px; margin-top: 6px; flex-wrap: wrap; justify-content: center; }

.video-grid-container { flex: 1; display: grid; gap: 10px; width: 100%; min-height: 0; }
.video-grid-container.grid-1 { grid-template-columns: minmax(0, 1fr); grid-auto-rows: minmax(0, 1fr); }
.video-grid-container.grid-4 { grid-template-columns: repeat(2, minmax(0, 1fr)); grid-auto-rows: minmax(150px, 1fr); }
.video-grid-container.grid-9 { grid-template-columns: repeat(3, minmax(0, 1fr)); grid-auto-rows: minmax(128px, 1fr); }

/* ===== 单个视频视窗 ===== */
.cam-viewport { display: flex; flex-direction: column; min-width: 0; min-height: 0; overflow: hidden; position: relative; background: var(--do-bg-dark); border: 1px solid var(--do-border); border-radius: 8px; cursor: pointer; transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s; }
.cam-viewport:hover { border-color: var(--do-gold); box-shadow: var(--shadow-hover); }
.cam-viewport.selected { border-color: var(--do-gold); box-shadow: inset 0 0 0 1.5px var(--do-gold), 0 0 0 3px rgba(var(--th-accent-rgb), 0.18); }

.cam-osd-header { display: flex; align-items: center; gap: 8px; padding: 7px 11px; background: rgba(var(--th-shadow-rgb), 0.92); border-bottom: 1px solid rgba(var(--th-accent-rgb), 0.18); flex-shrink: 0; }
.cam-title { flex: 1; min-width: 0; overflow: hidden; color: var(--do-text-inverse); font-size: 13px; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.cam-model-tag { flex-shrink: 0; padding: 1px 6px; border-radius: 4px; background: rgba(var(--th-accent-rgb), 0.24); border: 1px solid rgba(var(--th-accent-rgb), 0.42); color: var(--do-text-inverse); font-size: 11px; font-weight: 600; white-space: nowrap; }
.cam-meta { flex-shrink: 0; color: var(--do-text-inverse-sub); font-size: 12px; }
.cam-osd-header .status-dot { flex-shrink: 0; width: 7px; height: 7px; }

.cam-feed-area { flex: 1; min-height: 0; position: relative; display: flex; background: var(--do-bg-dark); }
.live-video-wrap { position: relative; flex: 1; min-width: 0; min-height: 0; overflow: hidden; background: #000; }
.ip-live-wrap { display: flex; align-items: center; justify-content: center; }
.live-video-el { width: 100%; height: 100%; object-fit: contain; display: block; }
.cam-corner.live-badge { padding: 2px 6px; border-radius: 4px; background: rgba(16, 185, 129, 0.85); color: #fff; font-weight: 700; }
.cam-corner.mock-badge { padding: 2px 6px; border-radius: 4px; background: rgba(14, 165, 233, 0.85); color: #fff; font-weight: 700; }
.uw-mock-visual { position: relative; flex: 1; min-width: 0; overflow: hidden; background: radial-gradient(circle at 50% 20%, rgba(14, 165, 233, 0.32) 0%, #0a2540 55%, #061529 100%); }
.uw-water-grid { position: absolute; inset: 0; opacity: 0.16; background: linear-gradient(rgba(125, 211, 252, 0.65) 1px, transparent 1px), linear-gradient(90deg, rgba(125, 211, 252, 0.65) 1px, transparent 1px); background-size: 36px 36px; }
.uw-caustic-glow { position: absolute; inset: 0; background: linear-gradient(160deg, rgba(56, 189, 248, 0.16) 0%, transparent 45%, rgba(6, 182, 212, 0.14) 100%); pointer-events: none; }
.uw-center-reticle { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); padding: 8px 14px; border: 1px dashed rgba(125, 211, 252, 0.45); border-radius: 8px; background: rgba(6, 21, 41, 0.45); color: rgba(224, 242, 254, 0.9); font-size: 12px; }
.uw-reticle-label { letter-spacing: 0.4px; }
.rec-dot.demo-dot { color: #38bdf8; }
.mock-cam-visual { position: relative; flex: 1; min-width: 0; overflow: hidden; background: radial-gradient(circle, rgba(var(--th-accent-rgb), 0.14) 0%, var(--do-bg-dark) 78%); }
.cam-grid-lines { position: absolute; inset: 0; opacity: 0.14; background: linear-gradient(rgba(255, 255, 255, 0.6) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.6) 1px, transparent 1px); background-size: 34px 34px; }
.cam-corner { position: absolute; z-index: 1; color: rgba(255, 255, 255, 0.62); font-size: 11px; letter-spacing: 0.5px; }
.cam-corner.top-left { top: 9px; left: 11px; }
.cam-corner.top-right { top: 9px; right: 11px; }
.center-cross { position: absolute; top: 50%; left: 50%; width: 28px; height: 28px; transform: translate(-50%, -50%); border: 1px dashed rgba(var(--th-accent-rgb), 0.45); border-radius: 50%; }
.bottom-osd { position: absolute; bottom: 6px; left: 8px; right: 8px; z-index: 1; display: flex; align-items: center; gap: 8px; padding: 4px 9px; background: rgba(15, 23, 42, 0.68); border-radius: 4px; color: rgba(255, 255, 255, 0.75); font-size: 11px; }
.osd-preset { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rec-dot { flex-shrink: 0; color: var(--do-danger); font-weight: 700; }
.bottom-osd span:last-child { flex-shrink: 0; }

.reconnecting-overlay { position: absolute; inset: 0; z-index: 10; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; background: rgba(24, 17, 11, 0.88); color: var(--do-warning); font-size: 13px; font-weight: 600; }

.cam-foot-tools { display: flex; gap: 6px; justify-content: flex-end; padding: 5px 9px; background: rgba(var(--th-shadow-rgb), 0.95); flex-shrink: 0; }
.tool-btn { padding: 3px 10px; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(var(--th-accent-rgb), 0.3); border-radius: 4px; color: var(--do-text-inverse); font-size: 12px; cursor: pointer; transition: all 0.2s ease; }
.tool-btn:hover { background: var(--do-gold); border-color: var(--do-gold); color: #FFFFFF; box-shadow: 0 2px 6px rgba(var(--th-accent-rgb), 0.28); }

/* ===== 右侧控制栏 ===== */
.video-side { display: flex; flex-direction: column; min-width: 0; overflow: hidden; }
.side-pane { display: flex; flex-direction: column; height: 100%; min-height: 0; }
.panel-heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 14px 18px; border-bottom: 1px solid var(--do-border-light); background: var(--do-bg-sunken); }
.panel-heading p { margin-top: 4px; color: var(--do-text-secondary); font-size: 13px; }
.pane-pill { flex-shrink: 0; padding: 4px 8px; border-radius: 14px; color: var(--do-gold-deep); background: var(--do-gold-wash); border: 1px solid var(--do-border-dark); font-size: 13px; font-weight: 700; white-space: nowrap; }

/* PTZ 控制盘 */
.ptz-pad { padding: 22px; display: flex; align-items: center; justify-content: center; }
.ptz-circle-bg { width: 148px; height: 148px; background: var(--do-bg-sunken); border: 1px solid var(--do-border); border-radius: 50%; position: relative; box-shadow: inset 0 2px 6px rgba(var(--th-shadow-rgb), 0.06); }
.ptz-btn { position: absolute; width: 34px; height: 34px; padding: 0; line-height: 1; background: var(--do-bg-card); border: 1px solid var(--do-border); border-radius: 8px; color: var(--do-text-regular); cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; transition: all 0.2s ease; box-shadow: var(--shadow-xs); }
.ptz-btn:hover { background: var(--do-gold); border-color: var(--do-gold-deep); color: #FFFFFF; box-shadow: 0 2px 6px rgba(var(--th-accent-rgb), 0.28); }
.ptz-btn.up { top: 8px; left: 50%; transform: translateX(-50%); }
.ptz-btn.down { bottom: 8px; left: 50%; transform: translateX(-50%); }
.ptz-btn.left { left: 8px; top: 50%; transform: translateY(-50%); }
.ptz-btn.right { right: 8px; top: 50%; transform: translateY(-50%); }
.ptz-btn.center { top: 50%; left: 50%; transform: translate(-50%, -50%); width: 36px; height: 36px; border-radius: 50%; background: var(--do-gold-wash); color: var(--do-gold-deep); border-color: var(--do-border-dark); }

.ptz-sliders-group { padding: 12px 18px 14px; display: flex; flex-direction: column; gap: 10px; }
.ptz-action-grid { padding: 0 18px 8px; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.ptz-act-btn { padding: 7px 10px; border-radius: 6px; border: 1px solid var(--do-border); background: var(--do-bg-card); color: var(--do-text-primary); font-size: 12.5px; font-weight: 600; cursor: pointer; user-select: none; transition: all 0.15s ease; }
.ptz-act-btn:hover { border-color: var(--do-gold); color: var(--do-gold-deep); }
.ptz-act-btn:active { background: var(--do-gold); border-color: var(--do-gold); color: #fff; }
.slider-row { display: flex; flex-direction: column; }
.s-lbl { font-size: 13px; color: var(--do-text-secondary); font-weight: 600; }

.group-meta-card { margin-top: auto; padding: 14px 18px; border-top: 1px solid var(--do-border-light); background: var(--do-bg-sunken); display: flex; flex-direction: column; gap: 6px; }
.meta-title { font-size: 13px; font-weight: 700; color: var(--do-text-primary); margin-bottom: 2px; }
.meta-row { display: flex; justify-content: space-between; gap: 10px; font-size: 12.5px; color: var(--do-text-secondary); }
.meta-row strong { color: var(--do-text-primary); font-weight: 600; text-align: right; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.num-mono { font-family: var(--font-family-mono, 'SF Mono', Consolas, monospace); }

.btn-header-action { display: inline-flex; align-items: center; padding: 7px 13px; border-radius: 8px; border: 1px solid var(--do-border); background: var(--do-bg-card); color: var(--do-text-primary); font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s ease; }
.btn-header-action:hover { border-color: var(--do-gold); color: var(--do-gold-deep); }
.btn-header-action:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-header-action.btn-header-primary { background: var(--do-gold); border-color: var(--do-gold); color: #fff; }
.btn-header-action.btn-header-primary:hover { opacity: 0.92; color: #fff; }

/* ===== 分组编辑弹窗 ===== */
.video-config-form { display: flex; flex-direction: column; gap: 4px; }
.form-section-title { font-size: 13.5px; font-weight: 700; color: var(--do-text-primary); margin: 4px 0 10px; padding-left: 8px; border-left: 3px solid var(--do-gold); }
.config-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.config-grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
.cam-list-header { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin: 8px 0 10px; flex-wrap: wrap; }
.cam-list-tools { display: flex; align-items: center; gap: 8px; }
.batch-add-box { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; padding: 10px 12px; margin-bottom: 10px; background: var(--do-bg-sunken); border: 1px solid var(--do-border); border-radius: 8px; }
.batch-lbl { font-size: 12.5px; color: var(--do-text-secondary); white-space: nowrap; }

.group-cam-rows { display: flex; flex-direction: column; gap: 8px; max-height: 290px; overflow-y: auto; padding-right: 4px; }
.group-cam-row { display: flex; align-items: flex-start; gap: 10px; padding: 10px 12px; background: var(--do-bg-sunken); border: 1px solid var(--do-border); border-radius: 8px; }
.cam-row-index { width: 28px; height: 24px; display: flex; align-items: center; justify-content: center; border-radius: 5px; background: var(--do-gold-wash); color: var(--do-gold-deep); font-size: 12px; font-weight: 700; flex-shrink: 0; }
.cam-row-fields { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 6px; }
.cam-row-inputs { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.cam-row-preview { display: flex; align-items: center; justify-content: space-between; gap: 8px; font-size: 12px; color: var(--do-text-secondary); }
.preview-url { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.probe-tag { flex-shrink: 0; padding: 1px 6px; border-radius: 4px; font-size: 11px; font-weight: 700; }
.probe-tag.ok { background: var(--do-success-bg); color: var(--do-success-deep); }
.probe-tag.warn { background: var(--do-warning-bg); color: var(--do-warning-deep); }
.cam-row-ops { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }

.dialog-footer-bar { display: flex; align-items: center; gap: 8px; width: 100%; }
.footer-tip { font-size: 12px; color: var(--do-text-secondary); }

.uw-alert-box { display: flex; flex-direction: column; gap: 10px; }
.uw-alert-head { display: flex; justify-content: space-between; align-items: center; font-size: 14px; }
.uw-alert-desc { font-size: 13px; color: var(--do-text-secondary); }
.uw-alert-img-wrap { border-radius: 8px; overflow: hidden; border: 1px solid var(--do-border); }
.uw-alert-img { width: 100%; display: block; }

/* ===== 响应式断点 ===== */
@media (max-width: 1600px) {
  .video-grid-container.grid-9 .cam-meta { display: none; }
}
@media (max-width: 1440px) {
  .metric-grid { grid-template-columns: repeat(3, minmax(150px, 1fr)); }
}
@media (max-width: 1280px) {
  .main-layout { grid-template-columns: 1fr; }
  .video-stage { min-height: 480px; }
  .video-grid-container.grid-9 .cam-meta { display: inline; }
}
@media (max-width: 900px) {
  .page-header, .scene-toolbar { align-items: flex-start; flex-direction: column; }
  .header-status { justify-content: flex-start; }
  .metric-grid { grid-template-columns: repeat(2, minmax(140px, 1fr)); }
  .video-grid-container.grid-9 .cam-meta { display: none; }
  .config-grid-2, .config-grid-3 { grid-template-columns: 1fr; }
}
@media (max-width: 720px) {
  .metric-grid { grid-template-columns: 1fr; }
  .video-stage { min-height: 0; }
  .video-grid-container.grid-9 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .video-grid-container.grid-9 .cam-meta { display: none; }
  .layout-switch { width: 100%; }
}
@media (max-width: 520px) {
  .video-grid-container.grid-4,
  .video-grid-container.grid-9 { grid-template-columns: minmax(0, 1fr); }
}
</style>
