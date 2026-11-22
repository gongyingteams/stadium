<template>
  <div class="video-monitor-page">
    <!-- 页面标题头：与 大屏调度 / 计时计分 页面保持一致的图标块 + 标题 + 状态指标体系 -->
    <section class="page-header glass-panel">
      <div class="page-heading">
        <div class="page-icon"><SvgIcon name="SvgCameraMatrix" size="28" /></div>
        <div>
          <div class="title-row">
            <h1>现场影像监看与转播监视总控台</h1>
            <span class="simulation-badge">演示数据</span>
          </div>
          <p>现场影像采集回放 · 现场影像识别与台账 · 电视转播专线监测</p>
        </div>
      </div>
      <div class="header-status">
        <div class="status-metric">
          <span :class="['status-dot', activeStream || ipStreamState.connected ? 'online' : 'warning']"></span>
          <span>{{ inputModeLabel }}</span>
        </div>
        <div class="status-metric"><strong class="num-mono">{{ onlineCamCount }}/{{ cameras.length }}</strong> 机位在线</div>
        <div class="status-metric"><strong class="num-mono">{{ totalBitrate }} Mbps</strong> 推流带宽</div>
        <button class="btn-header-action" @click="openAddCameraModal" title="新增现场网络摄像机（支持 RTSP / HTTP / HLS，可选账号密码）">
          <span>+ 新增摄像机</span>
        </button>
        <button class="btn-header-action" @click="$router.push('/iot/video/ledger')" title="查看现场影像采集识别数据库全部台账与实时报警">
          <span>现场台账与报警</span>
        </button>
        <button class="btn-header-action" @click="openConfigDialog" title="配置摄像机 HDMI 直连或 HDMI 转 USB 采集卡接入参数">
          <el-icon style="margin-right: 4px;"><Setting /></el-icon>
          <span>接入参数配置</span>
        </button>
        <button class="btn-header-action btn-header-primary" @click="snapshotAll" title="一键抓拍当前所有现场视频路画面的即时快照">
          <SvgIcon name="SvgCameraMatrix" size="14" style="margin-right: 4px;" />
          <span>一键全机位抓拍</span>
        </button>
      </div>
    </section>

    <!-- 关键指标卡：与计时计分页同构的 6 格指标带 -->
    <section class="metric-grid">
      <div class="metric-card glass-panel"><span>当前业务场景</span><strong>{{ subTabLabel }}</strong><em>三合一监看模式</em></div>
      <div class="metric-card glass-panel"><span>视窗布局</span><strong class="num-mono">{{ splitMode }} 分屏</strong><em>点击视窗可选中机位</em></div>
      <div class="metric-card glass-panel"><span>在线机位</span><strong class="num-mono">{{ onlineCamCount }}/{{ cameras.length }}</strong><em>RTSP 链路健康</em></div>
      <div class="metric-card glass-panel"><span>推流带宽</span><strong class="num-mono">{{ totalBitrate }} Mbps</strong><em>当前展示视窗合计</em></div>
      <div class="metric-card glass-panel"><span>断流自愈</span><strong class="num-mono">{{ reconnectingCount }} 路</strong><em>自动重连守护中</em></div>
      <div class="metric-card glass-panel"><span>抓拍归档</span><strong class="num-mono">9 张</strong><em>今日快照入库</em></div>
    </section>

    <!-- 业务子场景切换 + 视窗布局选择工具条 -->
    <section class="scene-toolbar glass-panel">
      <div class="section-heading">
        <div>
          <h2>业务监看场景</h2>
          <span class="section-help">切换现场影像、水下识别与电视转播三类专业监视视角</span>
        </div>
        <el-radio-group v-model="currentSubTab" size="small">
          <el-radio-button value="FIELD">现场影像采集回放</el-radio-button>
          <el-radio-button value="UNDERWATER">水下影像识别</el-radio-button>
          <el-radio-button value="BROADCAST">电视转播监测</el-radio-button>
        </el-radio-group>
      </div>
      <div class="layout-switch">
        <span class="switch-lbl">视窗布局</span>
        <div class="segmented">
          <button :class="['seg-btn', { active: splitMode === 1 }]" @click="splitMode = 1">单屏</button>
          <button :class="['seg-btn', { active: splitMode === 4 }]" @click="splitMode = 4">4分屏</button>
          <button :class="['seg-btn', { active: splitMode === 9 }]" @click="splitMode = 9">9分屏</button>
        </div>
      </div>
    </section>

    <!-- 主视窗布局：视频网格 + 右侧 PTZ 云台 / 水下参数 / 转播板卡监视抽屉 -->
    <section class="main-layout">
      <!-- 视频视窗网格区 -->
      <div class="video-stage glass-panel">
        <div :class="['video-grid-container', `grid-${splitMode}`]">
          <div
            v-for="cam in displayedCameras"
            :key="cam.id"
            :class="['cam-viewport', { selected: selectedCamId === cam.id }]"
            @click="selectedCamId = cam.id"
          >
            <!-- 视窗 OSD 顶栏 -->
            <div class="cam-osd-header">
              <span class="cam-title">{{ cam.name }}</span>
              <span class="cam-meta num-mono">{{ cam.resolution }}@{{ cam.fps }}fps · {{ cam.bitrate }}</span>
              <span :class="['status-dot', cam.isReconnecting ? 'warning' : 'online']"></span>
            </div>

            <!-- 视频画面渲染区 -->
            <div class="cam-feed-area">
              <div v-if="cam.isReconnecting" class="reconnecting-overlay">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>网络断流自愈重连中 (1/3)...</span>
              </div>

              <!-- 真实视频流画面（当当前机位已绑定本地采集流时展示） -->
              <div v-if="isCamLiveBound(cam.id)" class="live-video-wrap">
                <video
                  :ref="(el) => setVideoElRef(cam.id, el)"
                  class="live-video-el"
                  autoplay
                  playsinline
                  muted
                ></video>
                <div class="cam-corner top-left live-badge">LIVE INPUT</div>
                <div class="cam-corner top-right num-mono">{{ cam.fps }} FPS</div>
                <div class="bottom-osd num-mono">
                  <span class="osd-preset">{{ activeDeviceLabel || cam.ptzPreset }}</span>
                  <span class="rec-dot">● LIVE</span>
                  <span>{{ liveTime }}</span>
                </div>
              </div>

              <!-- IP 网络流 / vMix 服务绑定视窗 -->
              <div v-else-if="isCamIpBound(cam.id)" class="live-video-wrap ip-live-wrap">
                <img
                  v-if="ipStreamState.playType === 'mjpeg' && ipStreamState.playUrl"
                  :src="ipStreamState.playUrl"
                  class="live-video-el"
                  alt="IP Camera Live"
                />
                <video
                  v-else-if="ipStreamState.playType === 'video' && ipStreamState.playUrl"
                  :src="ipStreamState.playUrl"
                  class="live-video-el"
                  autoplay
                  playsinline
                  muted
                  controls
                ></video>
                <div v-else class="ip-standby-panel">
                  <div class="ip-standby-title">IP 网络接入已绑定 · {{ ipStreamState.host || videoConfig.ipAddress }}</div>
                  <div class="ip-standby-msg">{{ ipStreamState.statusText }}</div>
                  <div v-if="ipStreamState.vmixInputs.length" class="vmix-switch-row">
                    <span class="vmix-lbl">vMix 采集机位切换：</span>
                    <button
                      v-for="inp in ipStreamState.vmixInputs"
                      :key="inp.number"
                      :class="['vmix-cut-btn', { active: ipStreamState.vmixActive === inp.number }]"
                      @click.stop="cutVmixInput(inp.number)"
                    >
                      #{{ inp.number }} {{ inp.title }}
                    </button>
                  </div>
                </div>
                <div class="cam-corner top-left live-badge">IP SOURCE</div>
                <div class="cam-corner top-right num-mono">{{ videoConfig.ipProtocol.toUpperCase() }}</div>
                <div class="bottom-osd num-mono">
                  <span class="osd-preset">{{ videoConfig.ipAddress }}</span>
                  <span class="rec-dot">{{ ipStreamState.playUrl ? '● LIVE' : '● LINK' }}</span>
                  <span>{{ liveTime }}</span>
                </div>
              </div>

              <!-- 已新增/绑定的网络摄像机实时画面 (RTSP 转码 MJPEG / HTTP / HLS) -->
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
                <div class="cam-corner top-left live-badge">LIVE STREAM</div>
                <div class="cam-corner top-right num-mono">{{ (cam.protocol || 'RTSP').toUpperCase() }}</div>
                <div class="bottom-osd num-mono">
                  <span class="osd-preset">{{ cam.ptzPreset }}</span>
                  <span class="rec-dot">● LIVE</span>
                  <span>{{ liveTime }}</span>
                </div>
              </div>

              <!-- 模拟视频监控画面 -->
              <div v-else class="mock-cam-visual">
                <div class="cam-grid-lines"></div>
                <div class="cam-corner top-left">CAMERA LIVE</div>
                <div class="cam-corner top-right num-mono">{{ cam.fps }} FPS</div>
                <div class="center-cross"></div>
                <div class="bottom-osd num-mono">
                  <span class="osd-preset">{{ cam.ptzPreset }}</span>
                  <span class="rec-dot">● REC</span>
                  <span>{{ liveTime }}</span>
                </div>
              </div>
            </div>

            <!-- 视窗底部微工具条 -->
            <div class="cam-foot-tools">
              <button v-if="cam.isCustom" class="tool-btn" @click.stop="removeCustomCamera(cam)">移除</button>
              <button class="tool-btn" @click.stop="takeSnapshot(cam)">抓拍</button>
              <button class="tool-btn" @click.stop="triggerPtzPreset(cam)">看位</button>
              <button class="tool-btn" @click.stop="reconnectCam(cam)">重拉流</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧控制侧边栏 (根据子 Tab 动态展示) -->
      <aside class="video-side glass-panel">
        <!-- 侧边栏A：现场影像 PTZ 云台与录像回放检索 -->
        <div v-if="currentSubTab === 'FIELD'" class="side-pane">
          <div class="panel-heading">
            <div>
              <h2>云台 PTZ 八向控制盘</h2>
              <p>对当前选中机位下发方向、变倍与预置位指令</p>
            </div>
            <span class="pane-pill num-mono">{{ selectedCamHost || `CAM-0${selectedCamId}` }}</span>
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

          <!-- 录像回放检索 -->
          <div class="playback-search-box">
            <div class="search-title">比赛关键录像检索回放</div>
            <el-date-picker
              v-model="playbackDate"
              type="date"
              placeholder="选择检索日期"
              size="small"
              style="width: 100%; margin-bottom: 8px;"
            />
            <div class="event-tags-list">
              <span class="e-tag" @click="seekRecording('15:30:00')"><span>15:30:00 鸣枪出发</span><em class="num-mono">回放</em></span>
              <span class="e-tag" @click="seekRecording('15:30:46')"><span>15:30:46 触壁完赛</span><em class="num-mono">回放</em></span>
              <span class="e-tag" @click="seekRecording('15:35:00')"><span>15:35:00 仲裁慢动作</span><em class="num-mono">回放</em></span>
            </div>
          </div>
        </div>

        <!-- 侧边栏B：水下识别特种参数 -->
        <div v-else-if="currentSubTab === 'UNDERWATER'" class="side-pane">
          <div class="panel-heading">
            <div>
              <h2>水下高速视窗控制参数</h2>
              <p>补光、触壁联动与抗水纹算法特种调节</p>
            </div>
            <span class="pane-pill success num-mono">4K 120FPS</span>
          </div>

          <div class="underwater-params">
            <el-form label-position="top" size="small">
              <el-form-item label="水下高速补光灯照度 (0~100%)">
                <el-slider v-model="underwaterLight" />
              </el-form-item>
              <el-form-item label="触壁传感器联动抓拍灵敏度">
                <el-radio-group v-model="touchSensitivity">
                  <el-radio-button value="高灵敏">高灵敏</el-radio-button>
                  <el-radio-button value="标准">标准</el-radio-button>
                  <el-radio-button value="防溅水">防溅水</el-radio-button>
                </el-radio-group>
              </el-form-item>
              <el-form-item label="水下特种除雾与抗水纹算法">
                <el-switch v-model="defogEnabled" active-text="已启用图像自适应去散射" />
              </el-form-item>
            </el-form>
          </div>
        </div>

        <!-- 侧边栏C：电视转播采集源与板卡监测 -->
        <div v-else class="side-pane">
          <div class="panel-heading">
            <div>
              <h2>转播采集板卡状态监视</h2>
              <p>采集链路物理接口与板卡健康遥测</p>
            </div>
            <span class="pane-pill num-mono">SDI 12G</span>
          </div>

          <div class="broadcast-inspect">
            <div class="b-row"><span>采集板卡型号</span><strong class="num-mono">DeckLink 8K Pro</strong></div>
            <div class="b-row"><span>物理输入接口</span><strong class="num-mono">BNC 12G-SDI 输入 1</strong></div>
            <div class="b-row"><span>输入色彩空间</span><strong class="num-mono">YUV 4:2:2 10-bit</strong></div>
            <div class="b-row"><span>嵌入式音频通道</span><strong class="num-mono">16ch 24-bit 48kHz</strong></div>
            <div class="b-row"><span>板卡温度与风扇</span><strong class="num-mono ok">48°C / 2400 RPM</strong></div>
          </div>
        </div>
      </aside>
    </section>

    <!-- 视频接入参数配置弹窗 -->
    <el-dialog
      v-model="configDialogVisible"
      title="摄像机视频接入参数配置"
      width="560px"
      destroy-on-close
    >
      <el-form label-position="top" size="default" class="video-config-form">
        <el-form-item label="① 视频接入方式">
          <el-radio-group v-model="draftConfig.inputMode" class="mode-radio-group">
            <el-radio-button value="ip_network">IP 网络接入</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <div class="mode-tip-box info">
          <strong>IP 网络接入说明：</strong>
          <p>适用于现场网络摄像机（如 <code>rtsp://192.168.7.163/live/av0</code>、<code>rtsp://192.168.7.164/live/av0</code>）或局域网导播/推流服务器（如 <code>http://192.168.0.33:8088</code>）。支持端口探测、机位切换及 RTSP/HTTP/MJPEG/HLS 实时拉流。</p>
        </div>

        <div class="config-grid-2">
          <el-form-item label="② IP 接入协议类型">
            <el-select v-model="draftConfig.ipProtocol" style="width: 100%;">
              <el-option label="RTSP 网络摄像机流 (554)" value="rtsp" />
              <el-option label="TClIVE SP / vMix 服务 (8088)" value="vmix" />
              <el-option label="HTTP / MJPEG 实时流" value="mjpeg" />
              <el-option label="HLS (.m3u8) 视频流" value="hls" />
            </el-select>
          </el-form-item>
          <el-form-item label="快捷模板填充">
            <div class="preset-btn-row">
              <el-button size="small" @click="applyIpPreset('cam163')">192.168.7.163</el-button>
              <el-button size="small" @click="applyIpPreset('cam164')">192.168.7.164</el-button>
              <el-button size="small" @click="applyIpPreset('vmix')">192.168.0.33:8088</el-button>
            </div>
          </el-form-item>
        </div>

        <el-form-item label="③ 摄像机 IP 或流地址">
          <div class="device-select-row">
            <el-input
              v-model="draftConfig.ipAddress"
              placeholder="例如 rtsp://192.168.7.164/live/av0 或 192.168.0.33:8088"
              style="flex: 1;"
              clearable
            />
            <el-button :loading="probingIp" @click="probeIpSource">
              <el-icon style="margin-right: 4px;"><Refresh /></el-icon>
              探测连通性
            </el-button>
          </div>
          <div v-if="ipProbeMessage" class="detect-result-text">{{ ipProbeMessage }}</div>
        </el-form-item>

        <div class="config-grid-2">
          <el-form-item label="④ 绑定展示机位">
            <el-select v-model="draftConfig.targetCamId" style="width: 100%;">
              <el-option
                v-for="cam in cameras"
                :key="cam.id"
                :label="cam.name"
                :value="cam.id"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="⑤ 预期画面规格">
            <el-select v-model="draftConfig.resolutionKey" style="width: 100%;">
              <el-option label="1920×1080 @ 25fps" value="1920x1080@25" />
              <el-option label="1920×1080 @ 60fps" value="1920x1080@60" />
              <el-option label="1280×720 @ 60fps" value="1280x720@60" />
            </el-select>
          </el-form-item>
        </div>
      </el-form>

      <template #footer>
        <div class="dialog-footer-bar">
          <el-button v-if="activeStream || ipStreamState.connected" type="danger" plain @click="stopAllLive">
            断开实时采集
          </el-button>
          <div style="flex: 1;"></div>
          <el-button @click="configDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="startingStream" @click="saveAndStartConfig">
            保存配置并启动画面
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 新增现场摄像机弹窗 -->
    <el-dialog v-model="addCameraVisible" title="新增现场网络摄像机" width="560px" destroy-on-close>
      <el-form label-position="top" size="default" class="video-config-form">
        <div class="config-grid-2">
          <el-form-item label="摄像机名称">
            <el-input v-model="newCamForm.name" placeholder="如：现场主摄像机 192.168.7.164" clearable />
          </el-form-item>
          <el-form-item label="网络协议">
            <el-select v-model="newCamForm.protocol" style="width: 100%;" @change="onProtocolChange">
              <el-option label="RTSP 视频流 (rtsp://)" value="rtsp" />
              <el-option label="HTTP / MJPEG 流 (http://)" value="mjpeg" />
              <el-option label="HLS 视频流 (.m3u8)" value="hls" />
            </el-select>
          </el-form-item>
        </div>

        <div class="config-grid-2">
          <el-form-item label="摄像机 IP 地址（或完整流地址）">
            <el-input v-model="newCamForm.ip" placeholder="例如 192.168.7.164" clearable />
          </el-form-item>
          <el-form-item label="流路径 / 端口路径">
            <el-input v-model="newCamForm.path" placeholder="例如 /live/av0" clearable />
          </el-form-item>
        </div>

        <div class="config-grid-2">
          <el-form-item label="账号（没有请留空）">
            <el-input v-model="newCamForm.username" placeholder="留空表示无鉴权" clearable />
          </el-form-item>
          <el-form-item label="密码（没有请留空）">
            <el-input v-model="newCamForm.password" type="password" show-password placeholder="留空表示无密码" clearable />
          </el-form-item>
        </div>

        <el-form-item label="展示位置">
          <el-select v-model="newCamForm.slotMode" style="width: 100%;">
            <el-option label="新增为第 1 号机位（立即置顶展示）" value="prepend" />
            <el-option label="追加到机位列表末尾" value="append" />
          </el-select>
        </el-form-item>

        <div class="mode-tip-box info" style="margin-bottom: 0;">
          <strong>生成流地址预览：</strong>
          <div class="num-mono" style="margin-top: 4px; word-break: break-all;">{{ builtStreamUrl || '请填写 IP 地址' }}</div>
        </div>
      </el-form>

      <template #footer>
        <div class="dialog-footer-bar">
          <el-button @click="probeNewCamera" :loading="probingNewCam">探测连通性</el-button>
          <div style="flex: 1;"></div>
          <el-button @click="addCameraVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmAddCamera">保存并接入画面</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 现场影像新增报警预警弹窗 -->
    <el-dialog v-model="alertPopupVisible" title="⚠️ 现场影像识别新增报警预警" width="620px" destroy-on-close>
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
        <el-button @click="$router.push('/iot/video/ledger'); alertPopupVisible = false">查看全部台账</el-button>
        <el-button type="primary" @click="alertPopupVisible = false">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { Loading, Setting, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElNotification } from 'element-plus'
import SvgIcon from '@/components/SvgIcon.vue'
import { api, API_BASE_URL } from '@/services/api'

const VIDEO_CONFIG_STORAGE_KEY = 'venue_video_input_config_v1'

const currentSubTab = ref('FIELD') // FIELD / UNDERWATER / BROADCAST
const splitMode = ref(4) // 1, 4, 9
const selectedCamId = ref(1)

const ptzZoom = ref(12)
const ptzFocus = ref(50)
const playbackDate = ref(new Date())
const underwaterLight = ref(80)
const touchSensitivity = ref('标准')
const defogEnabled = ref(true)

const liveTime = ref('')
let timer = null

// ===== 接入参数配置与本机/IP视频采集状态 =====
const configDialogVisible = ref(false)
const detectingDevices = ref(false)
const probingIp = ref(false)
const startingStream = ref(false)
const deviceDetectMessage = ref('')
const ipProbeMessage = ref('')
const videoInputDevices = ref([])
const activeStream = ref(null)
const activeDeviceLabel = ref('')
const videoElMap = new Map()

const ipStreamState = reactive({
  connected: false,
  host: '',
  playType: '', // 'mjpeg' | 'video' | ''
  playUrl: '',
  statusText: '',
  vmixBaseUrl: '',
  vmixActive: 0,
  vmixInputs: []
})

const loadStoredConfig = () => {
  try {
    const raw = localStorage.getItem(VIDEO_CONFIG_STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      const mode = ['ip_network', 'hdmi_usb', 'hdmi_direct'].includes(parsed.inputMode)
        ? parsed.inputMode
        : 'ip_network'
      return {
        inputMode: mode,
        ipProtocol: parsed.ipProtocol || 'vmix',
        ipAddress: parsed.ipAddress || 'http://192.168.0.33:8088',
        deviceId: parsed.deviceId || '',
        targetCamId: Number(parsed.targetCamId) || 1,
        resolutionKey: parsed.resolutionKey || '1920x1080@60'
      }
    }
  } catch { /* ignore */ }
  return {
    inputMode: 'ip_network',
    ipProtocol: 'vmix',
    ipAddress: 'http://192.168.0.33:8088',
    deviceId: '',
    targetCamId: 1,
    resolutionKey: '1920x1080@60'
  }
}

const videoConfig = reactive(loadStoredConfig())
const draftConfig = reactive({ ...videoConfig })

const inputModeLabel = computed(() => {
  if (videoConfig.inputMode === 'ip_network') return 'IP 网络接入'
  if (videoConfig.inputMode === 'hdmi_usb') return 'HDMI 转 USB 采集'
  return 'HDMI 直连模式'
})

const isCamLiveBound = (camId) => Boolean(activeStream.value && videoConfig.inputMode !== 'ip_network' && videoConfig.targetCamId === camId)
const isCamIpBound = (camId) => Boolean(ipStreamState.connected && videoConfig.inputMode === 'ip_network' && videoConfig.targetCamId === camId)

const setVideoElRef = (camId, el) => {
  if (el) {
    videoElMap.set(camId, el)
    if (isCamLiveBound(camId) && el.srcObject !== activeStream.value) {
      el.srcObject = activeStream.value
    }
  } else {
    videoElMap.delete(camId)
  }
}

const stopLiveStream = () => {
  if (activeStream.value) {
    activeStream.value.getTracks().forEach(track => track.stop())
    activeStream.value = null
  }
  activeDeviceLabel.value = ''
  videoElMap.forEach(el => {
    if (el) el.srcObject = null
  })
}

const detectVideoDevices = async () => {
  if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
    deviceDetectMessage.value = '当前浏览器不支持媒体设备枚举，请在 localhost 或 HTTPS 环境下使用。'
    return
  }
  detectingDevices.value = true
  deviceDetectMessage.value = ''
  try {
    // 先请求一次临时权限，才能拿到完整设备名称（如 USB Video / 采集卡型号）
    let tempStream = null
    try {
      tempStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
    } catch {
      // 用户未授权或无摄像头时仍继续 enumerateDevices
    } finally {
      if (tempStream) tempStream.getTracks().forEach(t => t.stop())
    }

    const allDevices = await navigator.mediaDevices.enumerateDevices()
    const inputs = allDevices
      .filter(d => d.kind === 'videoinput')
      .map((d, idx) => ({
        deviceId: d.deviceId,
        label: d.label || `视频输入设备 #${idx + 1}`
      }))

    videoInputDevices.value = inputs
    if (inputs.length === 0) {
      deviceDetectMessage.value = '未检测到任何可用视频输入设备。'
      return
    }

    if (!draftConfig.deviceId || !inputs.some(d => d.deviceId === draftConfig.deviceId)) {
      draftConfig.deviceId = inputs[0].deviceId
    }

    const hasUsbCaptureHint = inputs.some(d => /usb|capture|hdmi|uvc|cam\s*link|magewell|avermedia|elgato/i.test(d.label))
    if (draftConfig.inputMode === 'hdmi_direct' && !hasUsbCaptureHint) {
      deviceDetectMessage.value = `共检测到 ${inputs.length} 个设备（${inputs.map(d => d.label).join('、')}），未发现 HDMI-IN 采集设备；普通电脑 HDMI 口为输出口，无法直连采集。`
    } else {
      deviceDetectMessage.value = `共检测到 ${inputs.length} 个视频输入设备，请在上方下拉框选择目标设备。`
    }
  } catch (err) {
    deviceDetectMessage.value = `检测失败：${err?.message || err}`
  } finally {
    detectingDevices.value = false
  }
}

const stopIpStream = () => {
  ipStreamState.connected = false
  ipStreamState.host = ''
  ipStreamState.playType = ''
  ipStreamState.playUrl = ''
  ipStreamState.statusText = ''
  ipStreamState.vmixBaseUrl = ''
  ipStreamState.vmixActive = 0
  ipStreamState.vmixInputs = []
}

const stopAllLive = () => {
  stopLiveStream()
  stopIpStream()
  ElMessage.info('已断开当前视频采集/IP接入流')
}

const applyIpPreset = (type) => {
  if (type === 'vmix') {
    draftConfig.ipProtocol = 'vmix'
    draftConfig.ipAddress = 'http://192.168.0.33:8088'
  } else if (type === 'cam163') {
    draftConfig.ipProtocol = 'rtsp'
    draftConfig.ipAddress = 'rtsp://192.168.7.163/live/av0'
  } else {
    draftConfig.ipProtocol = 'rtsp'
    draftConfig.ipAddress = 'rtsp://192.168.7.164/live/av0'
  }
}

const probeIpSource = async () => {
  const target = (draftConfig.ipAddress || '').trim()
  if (!target) {
    ipProbeMessage.value = '请先输入摄像机 IP 或流地址'
    return null
  }
  probingIp.value = true
  ipProbeMessage.value = ''
  try {
    const res = await api.videoProbe({ target, protocol: draftConfig.ipProtocol })
    if (res && !res.__offline) {
      ipProbeMessage.value = res.message || (res.reachable ? '探测成功' : '无法连通目标地址')
      return res
    }
    ipProbeMessage.value = '后端接口未响应，请确认后端服务（8000端口）已启动。'
    return null
  } catch (err) {
    ipProbeMessage.value = `探测失败：${err?.message || err}`
    return null
  } finally {
    probingIp.value = false
  }
}

const cutVmixInput = async (inputNumber) => {
  if (!ipStreamState.vmixBaseUrl) return
  try {
    const res = await api.videoVmixCut({
      baseUrl: ipStreamState.vmixBaseUrl,
      inputNumber
    })
    if (res?.vmix) {
      ipStreamState.vmixActive = res.vmix.active || inputNumber
      ipStreamState.vmixInputs = res.vmix.inputs || ipStreamState.vmixInputs
    }
    ElMessage.success(`已切换 vMix 主输出至采集机位 #${inputNumber}`)
  } catch (err) {
    ElMessage.error(`切换机位失败：${err?.message || err}`)
  }
}

const openConfigDialog = () => {
  Object.assign(draftConfig, videoConfig)
  ipProbeMessage.value = ''
  configDialogVisible.value = true
  if (draftConfig.inputMode !== 'ip_network') {
    detectVideoDevices()
  }
}

const parseResolution = (key) => {
  const [wh, fpsStr] = String(key || '1920x1080@60').split('@')
  const [w, h] = (wh || '1920x1080').split('x').map(Number)
  return {
    width: w || 1920,
    height: h || 1080,
    frameRate: Number(fpsStr) || 60
  }
}

const saveAndStartConfig = async () => {
  Object.assign(videoConfig, draftConfig)
  try {
    localStorage.setItem(VIDEO_CONFIG_STORAGE_KEY, JSON.stringify(videoConfig))
  } catch { /* ignore */ }

  if (draftConfig.inputMode === 'ip_network') {
    stopLiveStream()
    stopIpStream()
    const target = (draftConfig.ipAddress || '').trim()
    if (!target) {
      ElMessage.warning('请输入摄像机 IP 或流地址')
      return
    }
    startingStream.value = true
    try {
      const res = await probeIpSource()
      ipStreamState.connected = true
      ipStreamState.host = res?.host || target
      selectedCamId.value = draftConfig.targetCamId

      const normalizedHttp = target.startsWith('http://') || target.startsWith('https://')
        ? target
        : `http://${target}`
      const proxyBase = API_BASE_URL.replace(/\/$/, '')

      if (res?.isVmix && res.vmix) {
        ipStreamState.vmixBaseUrl = normalizedHttp.replace(/\/$/, '')
        ipStreamState.vmixActive = res.vmix.active || 0
        ipStreamState.vmixInputs = (res.vmix.inputs || []).filter(i => i.type !== 'Blank')
        if (res.vmix.liveLanReady && res.vmix.liveLanUrl) {
          ipStreamState.playType = 'video'
          ipStreamState.playUrl = `${proxyBase}/video/proxy?url=${encodeURIComponent(res.vmix.liveLanUrl)}`
          ipStreamState.statusText = 'vMix LiveLAN 视频流已连接'
        } else {
          ipStreamState.playType = ''
          ipStreamState.playUrl = ''
          ipStreamState.statusText = '已连通 vMix 控制服务（可在下方直接切换采集卡机位；若需本页同步画面，请在 vMix 中开启 LiveLAN）'
        }
      } else if (draftConfig.ipProtocol === 'mjpeg') {
        ipStreamState.playType = 'mjpeg'
        ipStreamState.playUrl = `${proxyBase}/video/proxy?url=${encodeURIComponent(normalizedHttp)}`
        ipStreamState.statusText = 'MJPEG 视频流已接入'
      } else if (draftConfig.ipProtocol === 'hls' || normalizedHttp.toLowerCase().includes('.m3u8')) {
        ipStreamState.playType = 'video'
        ipStreamState.playUrl = `${proxyBase}/video/proxy?url=${encodeURIComponent(normalizedHttp)}`
        ipStreamState.statusText = 'HLS 视频流已接入'
      } else {
        ipStreamState.playType = ''
        ipStreamState.playUrl = ''
        ipStreamState.statusText = res?.message || '已保存 IP 地址并完成端口探测（RTSP 流需配合流媒体转码网关推送到网页播放）'
      }

      configDialogVisible.value = false
      ElMessage.success(`已绑定 IP 接入源到 CAM-0${draftConfig.targetCamId}`)
    } finally {
      startingStream.value = false
    }
    return
  }

  stopIpStream()
  if (!draftConfig.deviceId) {
    stopLiveStream()
    configDialogVisible.value = false
    ElMessage.warning('已保存接入方式，但尚未选择有效视频输入设备，当前保持演示占位画面。')
    return
  }

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    ElMessage.error('当前浏览器环境不支持本地视频采集（需 localhost 或 HTTPS）。')
    return
  }

  startingStream.value = true
  try {
    stopLiveStream()
    const { width, height, frameRate } = parseResolution(draftConfig.resolutionKey)
    const stream = await navigator.mediaDevices.getUserMedia({
      video: {
        deviceId: { exact: draftConfig.deviceId },
        width: { ideal: width },
        height: { ideal: height },
        frameRate: { ideal: frameRate }
      },
      audio: false
    })
    activeStream.value = stream
    const matchedDev = videoInputDevices.value.find(d => d.deviceId === draftConfig.deviceId)
    activeDeviceLabel.value = matchedDev ? matchedDev.label : '本地视频输入'
    selectedCamId.value = draftConfig.targetCamId

    await nextTick()
    const el = videoElMap.get(draftConfig.targetCamId)
    if (el) el.srcObject = stream

    configDialogVisible.value = false
    ElMessage.success(`已接入「${activeDeviceLabel.value}」并绑定到 CAM-0${draftConfig.targetCamId}`)
  } catch (err) {
    ElMessage.error(`启动采集画面失败：${err?.message || err}`)
  } finally {
    startingStream.value = false
  }
}

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
          title: newest.title || '现场影像报警预警',
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

const CUSTOM_CAMERAS_STORAGE_KEY = 'venue_custom_cameras_v1'
const addCameraVisible = ref(false)
const probingNewCam = ref(false)
const newCamForm = reactive({
  name: '',
  protocol: 'rtsp',
  ip: '192.168.7.164',
  path: '/live/av0',
  username: '',
  password: '',
  slotMode: 'prepend'
})

const onProtocolChange = (proto) => {
  if (proto === 'rtsp' && !newCamForm.path) {
    newCamForm.path = '/live/av0'
  }
}

const builtStreamUrl = computed(() => {
  const rawIp = (newCamForm.ip || '').trim()
  if (!rawIp) return ''
  // 如果用户直接粘贴了完整协议地址（如 rtsp://192.168.7.164/live/av0）
  if (/^[a-z]+:\/\//i.test(rawIp)) {
    const user = (newCamForm.username || '').trim()
    const pwd = newCamForm.password || ''
    if (user && !rawIp.includes('@')) {
      const auth = pwd ? `${encodeURIComponent(user)}:${encodeURIComponent(pwd)}@` : `${encodeURIComponent(user)}@`
      return rawIp.replace(/^([a-z]+:\/\/)/i, `$1${auth}`)
    }
    return rawIp
  }
  const scheme = newCamForm.protocol === 'rtsp' ? 'rtsp://' : 'http://'
  const user = (newCamForm.username || '').trim()
  const pwd = newCamForm.password || ''
  const auth = user ? (pwd ? `${encodeURIComponent(user)}:${encodeURIComponent(pwd)}@` : `${encodeURIComponent(user)}@`) : ''
  let p = (newCamForm.path || '').trim()
  if (p && !p.startsWith('/')) p = `/${p}`
  return `${scheme}${auth}${rawIp}${p}`
})

const openAddCameraModal = () => {
  addCameraVisible.value = true
}

const probeNewCamera = async () => {
  const url = builtStreamUrl.value
  if (!url) {
    ElMessage.warning('请先填写摄像机 IP 地址')
    return
  }
  probingNewCam.value = true
  try {
    const res = await api.videoProbe({ target: url, protocol: newCamForm.protocol })
    if (res?.reachable) {
      ElMessage.success(res.message || '摄像机端口连通正常')
    } else {
      ElMessage.warning(res?.message || '无法连通目标摄像机端口')
    }
  } catch (err) {
    ElMessage.error(`探测失败：${err?.message || err}`)
  } finally {
    probingNewCam.value = false
  }
}

const makePlayConfig = (streamUrl, protocol) => {
  const base = API_BASE_URL.replace(/\/$/, '')
  if (protocol === 'rtsp' || streamUrl.startsWith('rtsp://')) {
    return {
      playType: 'mjpeg',
      livePlayUrl: `${base}/video/rtsp/mjpeg?url=${encodeURIComponent(streamUrl)}`
    }
  }
  if (protocol === 'mjpeg') {
    return {
      playType: 'mjpeg',
      livePlayUrl: `${base}/video/proxy?url=${encodeURIComponent(streamUrl)}`
    }
  }
  return {
    playType: 'video',
    livePlayUrl: `${base}/video/proxy?url=${encodeURIComponent(streamUrl)}`
  }
}

const saveCustomCamerasToStorage = () => {
  try {
    const customList = cameras.value
      .filter(c => c.isCustom)
      .map(c => ({
        id: c.id,
        name: c.name,
        protocol: c.protocol,
        streamUrl: c.streamUrl,
        slotMode: c.slotMode || 'prepend'
      }))
    localStorage.setItem(CUSTOM_CAMERAS_STORAGE_KEY, JSON.stringify(customList))
  } catch { /* ignore */ }
}

const loadCustomCamerasFromStorage = () => {
  try {
    const raw = localStorage.getItem(CUSTOM_CAMERAS_STORAGE_KEY)
    if (!raw) return
    const list = JSON.parse(raw)
    if (!Array.isArray(list)) return
    for (const item of list.slice().reverse()) {
      if (!item?.streamUrl) continue
      const playCfg = makePlayConfig(item.streamUrl, item.protocol || 'rtsp')
      const camObj = {
        id: item.id || Date.now(),
        name: item.name || item.streamUrl,
        resolution: '1920×1080',
        fps: 25,
        bitrate: '6 Mbps',
        ptzPreset: item.streamUrl.replace(/\/\/.*@/, '//***@'),
        isReconnecting: false,
        isCustom: true,
        protocol: item.protocol || 'rtsp',
        streamUrl: item.streamUrl,
        slotMode: item.slotMode || 'prepend',
        ...playCfg
      }
      if (camObj.slotMode === 'append') {
        cameras.value.push(camObj)
      } else {
        cameras.value.unshift(camObj)
      }
    }
  } catch { /* ignore */ }
}

const confirmAddCamera = () => {
  const url = builtStreamUrl.value
  if (!url) {
    ElMessage.warning('请先填写摄像机 IP 地址')
    return
  }
  const playCfg = makePlayConfig(url, newCamForm.protocol)
  const camId = Date.now()
  const displayName = (newCamForm.name || '').trim() || `现场摄像机 (${newCamForm.ip.trim()})`
  const newCam = {
    id: camId,
    name: displayName,
    resolution: '1920×1080',
    fps: 25,
    bitrate: '6 Mbps',
    ptzPreset: url.replace(/\/\/.*@/, '//***@'),
    isReconnecting: false,
    isCustom: true,
    protocol: newCamForm.protocol,
    streamUrl: url,
    slotMode: newCamForm.slotMode,
    ...playCfg
  }
  if (newCamForm.slotMode === 'append') {
    cameras.value.push(newCam)
  } else {
    cameras.value.unshift(newCam)
  }
  selectedCamId.value = camId
  saveCustomCamerasToStorage()
  addCameraVisible.value = false
  ElMessage.success(`已新增摄像机「${displayName}」并开始拉流`)
}

const removeCustomCamera = (cam) => {
  cameras.value = cameras.value.filter(c => c.id !== cam.id)
  if (selectedCamId.value === cam.id && cameras.value.length) {
    selectedCamId.value = cameras.value[0].id
  }
  saveCustomCamerasToStorage()
  ElMessage.info(`已移除摄像机「${cam.name}」`)
}

const ensureDefaultFieldCameras = () => {
  const defaults = [
    { id: 10163, name: '现场摄像机 01 (192.168.7.163)', streamUrl: 'rtsp://192.168.7.163/live/av0' },
    { id: 10164, name: '现场摄像机 02 (192.168.7.164)', streamUrl: 'rtsp://192.168.7.164/live/av0' }
  ]
  for (const d of defaults.slice().reverse()) {
    const exists = cameras.value.some(c => c.streamUrl === d.streamUrl)
    if (!exists) {
      const playCfg = makePlayConfig(d.streamUrl, 'rtsp')
      cameras.value.unshift({
        id: d.id,
        name: d.name,
        resolution: '1920×1080',
        fps: 25,
        bitrate: '6 Mbps',
        ptzPreset: d.streamUrl,
        isReconnecting: false,
        isCustom: true,
        protocol: 'rtsp',
        streamUrl: d.streamUrl,
        slotMode: 'prepend',
        ...playCfg
      })
    }
  }
  if (cameras.value.length) selectedCamId.value = cameras.value[0].id
}

onMounted(() => {
  loadCustomCamerasFromStorage()
  ensureDefaultFieldCameras()
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
  stopLiveStream()
})

const cameras = ref([
  { id: 1, name: 'CAM-01 比赛泳池全景枪机 (东看台俯视角)', resolution: '3840×2160', fps: 50, bitrate: '16 Mbps', ptzPreset: '预置位 01 (泳池全貌)', isReconnecting: false },
  { id: 2, name: 'CAM-02 总裁判长席特写机位 (起跳台正面)', resolution: '3840×2160', fps: 50, bitrate: '14 Mbps', ptzPreset: '预置位 02 (1~8道出发台)', isReconnecting: false },
  { id: 3, name: 'CAM-03 跳水深水池 10米跳台高速机位', resolution: '1920×1080', fps: 60, bitrate: '8 Mbps', ptzPreset: '预置位 03 (跳水起跳高台)', isReconnecting: false },
  { id: 4, name: 'CAM-04 水下4号道触壁特写 (深水池特种视窗)', resolution: '3840×2160', fps: 120, bitrate: '24 Mbps', ptzPreset: '预置位 04 (水下触壁板)', isReconnecting: false },
  { id: 5, name: 'CAM-05 主席台贵宾席微动云台', resolution: '1920×1080', fps: 30, bitrate: '6 Mbps', ptzPreset: '预置位 05 (主席台全貌)', isReconnecting: false },
  { id: 6, name: 'CAM-06 运动员更衣检录通道枪机', resolution: '1920×1080', fps: 25, bitrate: '4 Mbps', ptzPreset: '预置位 06 (检录通道)', isReconnecting: false },
  { id: 7, name: 'CAM-07 电视转播主车 SDI 监视源', resolution: '3840×2160', fps: 50, bitrate: '45 Mbps', ptzPreset: '广播级 SDI 12G 直连', isReconnecting: false },
  { id: 8, name: 'CAM-08 观众安检大厅全景', resolution: '1920×1080', fps: 25, bitrate: '4 Mbps', ptzPreset: '预置位 08 (安检通道)', isReconnecting: false },
  { id: 9, name: 'CAM-09 场馆东外围广场巡检球机', resolution: '1920×1080', fps: 25, bitrate: '4 Mbps', ptzPreset: '巡航扫描中', isReconnecting: false }
])

const displayedCameras = computed(() => {
  return cameras.value.slice(0, splitMode.value)
})

const onlineCamCount = computed(() => cameras.value.filter(cam => !cam.isReconnecting).length)
const reconnectingCount = computed(() => cameras.value.filter(cam => cam.isReconnecting).length)
const totalBitrate = computed(() =>
  displayedCameras.value.reduce((sum, cam) => sum + (Number(String(cam.bitrate).split(' ')[0]) || 0), 0)
)
const subTabLabel = computed(() => ({
  FIELD: '现场影像采集回放',
  UNDERWATER: '水下影像识别',
  BROADCAST: '电视转播监测'
})[currentSubTab.value])

const ptzSpeed = ref(8)
let activePtzStopCmd = ''

const selectedCamObj = computed(() => cameras.value.find(c => c.id === selectedCamId.value) || null)
const selectedCamHost = computed(() => {
  const cam = selectedCamObj.value
  const src = cam?.streamUrl || cam?.ptzPreset || ''
  const m = String(src).match(/(\d{1,3}(?:\.\d{1,3}){3})/)
  return m ? m[1] : ''
})

const sendPtz = async (action) => {
  const host = selectedCamHost.value
  if (!host) {
    ElMessage.warning('当前选中机位未绑定有效 IP 地址，无法下发云台控制')
    return
  }
  try {
    if (typeof api.videoPtz === 'function') {
      await api.videoPtz({
        host,
        port: 1259,
        action,
        speed: ptzSpeed.value
      })
    } else {
      const base = API_BASE_URL.replace(/\/$/, '')
      const resp = await fetch(`${base}/video/ptz`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ host, port: 1259, action, speed: ptzSpeed.value })
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
  const el = videoElMap.get(cam.id)
  if (isCamLiveBound(cam.id) && el && el.videoWidth > 0) {
    const canvas = document.createElement('canvas')
    canvas.width = el.videoWidth
    canvas.height = el.videoHeight
    const ctx = canvas.getContext('2d')
    ctx.drawImage(el, 0, 0, canvas.width, canvas.height)
    const link = document.createElement('a')
    link.href = canvas.toDataURL('image/png')
    link.download = `cam-${cam.id}-${Date.now()}.png`
    link.click()
    ElMessage.success(`已抓拍 ${cam.name} 真实画面（${canvas.width}×${canvas.height}）并下载！`)
    return
  }
  ElMessage.success(`已抓拍 ${cam.name} 4K 高清截图并存入素材库！`)
}

const triggerPtzPreset = (cam) => {
  ElMessage.success(`机位 ${cam.name} 已转动至预置位`)
}

const reconnectCam = (cam) => {
  cam.isReconnecting = true
  setTimeout(() => {
    cam.isReconnecting = false
    ElMessage.success(`${cam.name} RTSP 视频流已自愈重拉成功！`)
  }, 1200)
}

const snapshotAll = () => {
  ElMessage.success('全场视窗一键抓拍完成，已归档 9 张快照！')
}

const seekRecording = (t) => {
  ElMessage.info(`正在加载录像时间轴定位于：${t}`)
}
</script>

<style scoped>
.video-monitor-page { display: flex; flex-direction: column; gap: 14px; min-width: 0; color: var(--do-text-primary); animation: fadeIn 0.3s ease-out; }
.glass-panel { background: var(--do-bg-card); border: 1px solid var(--do-border); border-radius: 10px; box-shadow: var(--shadow-sm); }

/* ===== 页面标题头 (与 大屏调度/计时计分 完全同构) ===== */
.page-header { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 18px 22px; }
.page-heading { display: flex; align-items: center; gap: 14px; min-width: 0; }
.page-icon { width: 52px; height: 52px; display: grid; place-items: center; flex-shrink: 0; color: var(--do-gold); background: var(--do-gold-wash); border: 1px solid var(--do-border-dark); border-radius: 12px; }
h1, h2, h3, p { margin: 0; }
h1 { font-size: 21px; line-height: 1.3; }
h2 { font-size: 16px; line-height: 1.35; }
h3 { font-size: 15px; line-height: 1.35; }
.title-row { display: flex; align-items: center; gap: 10px; }
.page-heading p { margin-top: 5px; color: var(--do-text-secondary); font-size: 13px; }
.simulation-badge { padding: 4px 8px; color: var(--do-warning-deep); background: var(--do-warning-bg); border: 1px solid var(--do-warning-border); border-radius: 5px; font-size: 13px; font-weight: 700; white-space: nowrap; }
.header-status { display: flex; align-items: center; justify-content: flex-end; gap: 16px; flex-wrap: wrap; color: var(--do-text-secondary); font-size: 13px; }
.status-metric { display: flex; align-items: center; gap: 6px; white-space: nowrap; }
.status-metric strong { color: var(--do-text-primary); font-size: 15px; }
.status-dot { width: 8px; height: 8px; flex: 0 0 auto; border-radius: 50%; background: currentColor; }
.status-dot.online { color: var(--do-success); box-shadow: 0 0 7px currentColor; }
.status-dot.warning { color: var(--do-warning); box-shadow: 0 0 7px currentColor; }

/* ===== 指标卡带 (与计时计分页同构) ===== */
.metric-grid { display: grid; grid-template-columns: repeat(6, minmax(135px, 1fr)); gap: 12px; }
.metric-card { min-width: 0; padding: 15px; }
.metric-card span { color: var(--do-text-secondary); font-size: 13px; }
.metric-card strong { display: block; margin-top: 8px; overflow: hidden; color: var(--do-text-primary); font-size: 17px; text-overflow: ellipsis; white-space: nowrap; }
.metric-card em { display: block; margin-top: 5px; overflow: hidden; color: var(--do-text-secondary); font-size: 13px; font-style: normal; text-overflow: ellipsis; white-space: nowrap; }

/* ===== 业务场景与布局工具条 ===== */
.scene-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 14px 18px; flex-wrap: wrap; }
.section-heading { display: flex; align-items: center; justify-content: space-between; gap: 14px; min-width: 0; flex: 1; flex-wrap: wrap; }
.section-help { display: block; margin-top: 4px; color: var(--do-text-secondary); font-size: 13px; }
.layout-switch { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.switch-lbl { color: var(--do-text-secondary); font-size: 13px; white-space: nowrap; }
.segmented { display: flex; gap: 4px; padding: 3px; background: var(--do-bg-sunken); border: 1px solid var(--do-border-light); border-radius: 8px; }
.seg-btn { padding: 5px 13px; background: transparent; border: none; border-radius: 5px; color: var(--do-text-secondary); font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s ease; }
.seg-btn:hover { color: var(--do-gold-deep); }
.seg-btn.active { background: var(--do-gold); color: #FFFFFF; box-shadow: 0 2px 6px rgba(var(--th-accent-rgb), 0.22); }

/* ===== 主布局：视频网格 + 右侧控制栏 ===== */
.main-layout { display: grid; grid-template-columns: minmax(0, 1fr) minmax(320px, 360px); gap: 14px; align-items: stretch; }

.video-stage { padding: 14px; display: flex; min-height: 540px; }
.video-grid-container { flex: 1; display: grid; gap: 10px; width: 100%; min-height: 0; }
.video-grid-container.grid-1 { grid-template-columns: minmax(0, 1fr); grid-auto-rows: minmax(0, 1fr); }
.video-grid-container.grid-4 { grid-template-columns: repeat(2, minmax(0, 1fr)); grid-auto-rows: minmax(150px, 1fr); }
.video-grid-container.grid-9 { grid-template-columns: repeat(3, minmax(0, 1fr)); grid-auto-rows: minmax(128px, 1fr); }

/* ===== 单个视频视窗 (采用大屏调度预览框的监视器语言) ===== */
.cam-viewport { display: flex; flex-direction: column; min-width: 0; min-height: 0; overflow: hidden; position: relative; background: var(--do-bg-dark); border: 1px solid var(--do-border); border-radius: 8px; cursor: pointer; transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s; }
.cam-viewport:hover { border-color: var(--do-gold); box-shadow: var(--shadow-hover); }
.cam-viewport.selected { border-color: var(--do-gold); box-shadow: inset 0 0 0 1.5px var(--do-gold), 0 0 0 3px rgba(var(--th-accent-rgb), 0.18); }

.cam-osd-header { display: flex; align-items: center; gap: 8px; padding: 7px 11px; background: rgba(var(--th-shadow-rgb), 0.92); border-bottom: 1px solid rgba(var(--th-accent-rgb), 0.18); flex-shrink: 0; }
.cam-title { flex: 1; min-width: 0; overflow: hidden; color: var(--do-text-inverse); font-size: 13px; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.cam-meta { flex-shrink: 0; color: var(--do-text-inverse-sub); font-size: 12px; }
.cam-osd-header .status-dot { flex-shrink: 0; width: 7px; height: 7px; }

.cam-feed-area { flex: 1; min-height: 0; position: relative; display: flex; background: var(--do-bg-dark); }
.live-video-wrap { position: relative; flex: 1; min-width: 0; min-height: 0; overflow: hidden; background: #000; }
.live-video-el { width: 100%; height: 100%; object-fit: contain; display: block; }
.cam-corner.live-badge { padding: 2px 6px; border-radius: 4px; background: rgba(16, 185, 129, 0.85); color: #fff; font-weight: 700; }
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
.pane-pill.success { color: var(--do-success-deep); background: var(--do-success-bg); border-color: var(--do-success-border); }

/* PTZ 控制盘 */
.ptz-pad { padding: 22px; display: flex; align-items: center; justify-content: center; }
.ptz-circle-bg { width: 148px; height: 148px; background: var(--do-bg-sunken); border: 1px solid var(--do-border); border-radius: 50%; position: relative; box-shadow: inset 0 2px 6px rgba(var(--th-shadow-rgb), 0.06); }
.ptz-btn { position: absolute; width: 34px; height: 34px; background: var(--do-bg-card); border: 1px solid var(--do-border); border-radius: 8px; color: var(--do-text-regular); cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; transition: all 0.2s ease; box-shadow: var(--shadow-xs); }
.ptz-btn:hover { background: var(--do-gold); border-color: var(--do-gold-deep); color: #FFFFFF; box-shadow: 0 2px 6px rgba(var(--th-accent-rgb), 0.28); }
.ptz-btn.up { top: 6px; left: calc(50% - 17px); }
.ptz-btn.down { bottom: 6px; left: calc(50% - 17px); }
.ptz-btn.left { left: 6px; top: calc(50% - 17px); }
.ptz-btn.right { right: 6px; top: calc(50% - 17px); }
.ptz-btn.center { width: 36px; height: 36px; border-radius: 50%; background: var(--do-gold-wash); color: var(--do-gold-deep); border-color: var(--do-border-dark); }

.ptz-sliders-group { padding: 12px 18px; display: flex; flex-direction: column; gap: 10px; }
.ptz-action-grid { padding: 0 18px 8px; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.ptz-act-btn { padding: 7px 10px; border-radius: 6px; border: 1px solid var(--do-border); background: var(--do-bg-card); color: var(--do-text-primary); font-size: 12.5px; font-weight: 600; cursor: pointer; user-select: none; transition: all 0.15s ease; }
.ptz-act-btn:hover { border-color: var(--do-gold); color: var(--do-gold-deep); }
.ptz-act-btn:active { background: var(--do-gold); border-color: var(--do-gold); color: #fff; }
.slider-row { display: flex; flex-direction: column; }
.s-lbl { font-size: 13px; color: var(--do-text-secondary); font-weight: 600; }

.playback-search-box { margin-top: auto; padding: 15px 18px; border-top: 1px solid var(--do-border-light); background: var(--do-bg-sunken); }
.search-title { margin-bottom: 8px; color: var(--do-text-primary); font-size: 14px; font-weight: 700; }
.event-tags-list { display: flex; flex-direction: column; gap: 6px; }
.e-tag { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 7px 10px; background: var(--do-bg-card); border: 1px solid var(--do-border); border-radius: 6px; color: var(--do-text-primary); font-size: 13px; cursor: pointer; transition: all 0.2s ease; }
.e-tag span { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.e-tag em { flex-shrink: 0; color: var(--do-gold-deep); font-size: 12px; font-style: normal; font-weight: 700; }
.e-tag:hover { border-color: var(--do-gold); box-shadow: var(--shadow-hover); }

/* 水下与转播参数 */
.underwater-params { padding: 16px 18px; }
.broadcast-inspect { padding: 8px 18px 16px; display: flex; flex-direction: column; }
.b-row { display: flex; justify-content: space-between; gap: 12px; padding: 10px 0; border-bottom: 1px solid var(--do-border-light); color: var(--do-text-secondary); font-size: 13px; }
.b-row:last-child { border-bottom: none; }
.b-row strong { flex-shrink: 0; color: var(--do-text-primary); font-size: 13px; font-weight: 600; text-align: right; }
.b-row strong.ok { color: var(--do-success-deep); }

.num-mono { font-family: var(--font-family-mono, 'SF Mono', Consolas, monospace); }

.btn-header-action { display: inline-flex; align-items: center; padding: 7px 13px; border-radius: 8px; border: 1px solid var(--do-border); background: var(--do-bg-card); color: var(--do-text-primary); font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s ease; }
.btn-header-action:hover { border-color: var(--do-gold); color: var(--do-gold-deep); }
.btn-header-action.btn-header-primary { background: var(--do-gold); border-color: var(--do-gold); color: #fff; }
.btn-header-action.btn-header-primary:hover { opacity: 0.92; color: #fff; }

.video-config-form { display: flex; flex-direction: column; gap: 4px; }
.mode-tip-box { margin-bottom: 16px; padding: 10px 12px; border-radius: 8px; font-size: 13px; line-height: 1.55; }
.mode-tip-box p { margin-top: 4px; }
.mode-tip-box.warn { background: var(--do-warning-bg); border: 1px solid var(--do-warning-border); color: var(--do-warning-deep); }
.mode-tip-box.info { background: var(--do-bg-sunken); border: 1px solid var(--do-border); color: var(--do-text-secondary); }
.device-select-row { display: flex; align-items: center; gap: 8px; width: 100%; }
.detect-result-text { margin-top: 6px; font-size: 12px; color: var(--do-text-secondary); line-height: 1.45; }
.config-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.preset-btn-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; height: 32px; }
.ip-live-wrap { display: flex; align-items: center; justify-content: center; }
.ip-standby-panel { padding: 18px; text-align: center; color: #e2e8f0; max-width: 92%; }
.ip-standby-title { font-size: 14px; font-weight: 700; color: #fff; margin-bottom: 6px; }
.ip-standby-msg { font-size: 12px; color: #94a3b8; line-height: 1.5; margin-bottom: 12px; }
.vmix-switch-row { display: flex; flex-wrap: wrap; gap: 6px; justify-content: center; align-items: center; }
.vmix-lbl { font-size: 12px; color: #cbd5e1; }
.vmix-cut-btn { padding: 4px 10px; border-radius: 5px; border: 1px solid rgba(255,255,255,0.25); background: rgba(255,255,255,0.08); color: #fff; font-size: 12px; cursor: pointer; }
.vmix-cut-btn.active, .vmix-cut-btn:hover { background: var(--do-gold); border-color: var(--do-gold); }
.dialog-footer-bar { display: flex; align-items: center; gap: 8px; width: 100%; }

/* ===== 响应式断点：与 大屏调度 页同级阶梯，任意分辨率不变形、不撑破主容器 ===== */
@media (max-width: 1600px) {
  /* 9 分屏在中等宽度下隐藏分辨率元信息，防止 OSD 顶栏拥挤 */
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
  .section-heading { align-items: flex-start; flex-direction: column; }
  .metric-grid { grid-template-columns: repeat(2, minmax(140px, 1fr)); }
  .video-grid-container.grid-9 .cam-meta { display: none; }
}
@media (max-width: 720px) {
  .metric-grid { grid-template-columns: 1fr; }
  .video-stage { min-height: 0; }
  .video-grid-container.grid-9 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .video-grid-container.grid-9 .cam-meta { display: none; }
  .layout-switch { width: 100%; }
}
@media (max-width: 520px) {
  /* 极窄视口(含应用外壳侧边栏占用后)视窗退化为单列，保证机位画面始终可用 */
  .video-grid-container.grid-4,
  .video-grid-container.grid-9 { grid-template-columns: minmax(0, 1fr); }
}
</style>
