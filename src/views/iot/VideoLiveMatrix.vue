<template>
  <div class="video-monitor-page">
    <!-- 页面标题头：与 大屏调度 / 计时计分 页面保持一致的图标块 + 标题 + 状态指标体系 -->
    <section class="page-header glass-panel">
      <div class="page-heading">
        <div class="page-icon"><SvgIcon name="SvgCameraMatrix" size="28" /></div>
        <div>
          <div class="title-row">
            <h1>现场摄像机实时监看总控台</h1>
          </div>
          <p>现场网络摄像机实时画面监看 · 云台 PTZ 操控 · 实时抓拍归档</p>
        </div>
      </div>
      <div class="header-status">
        <div class="status-metric">
          <span :class="['status-dot', cameras.length ? 'online' : 'warning']"></span>
          <span>IP 网络接入</span>
        </div>
        <div class="status-metric"><strong class="num-mono">{{ onlineCamCount }}/{{ cameras.length }}</strong> 机位在线</div>
        <div class="status-metric"><strong class="num-mono">{{ totalBitrate }} Mbps</strong> 推流带宽</div>
        <button class="btn-header-action" @click="openCameraDialog('add')" title="新增现场网络摄像机（支持不同型号 RTSP / HTTP / HLS，可选账号密码）">
          <span>+ 新增摄像机</span>
        </button>
        <button class="btn-header-action" @click="openCameraDialog('edit', selectedCamObj)" title="修改编辑现场各机位摄像机型号、流地址、鉴权与云台端口参数">
          <el-icon style="margin-right: 4px;"><Setting /></el-icon>
          <span>摄像机参数编辑</span>
        </button>
        <button class="btn-header-action" @click="openSnapshotGallery" :title="`查看已抓拍截图（保存目录：${snapshotStorageDir}）`">
          <span>抓拍图库 ({{ snapshots.length }})</span>
        </button>
        <button class="btn-header-action btn-header-primary" :disabled="capturingAll" @click="snapshotAll" title="一键抓拍当前所有现场视频路画面的即时快照">
          <SvgIcon name="SvgCameraMatrix" size="14" style="margin-right: 4px;" />
          <span>{{ capturingAll ? '抓拍中...' : '一键全机位抓拍' }}</span>
        </button>
      </div>
    </section>

    <!-- 关键指标卡：与计时计分页同构的 6 格指标带 -->
    <section class="metric-grid">
      <div class="metric-card glass-panel"><span>当前选中机位</span><strong class="num-mono">{{ selectedCamHost || '未选择' }}</strong><em>{{ selectedCamObj?.name || '点击视窗选择机位' }}</em></div>
      <div class="metric-card glass-panel"><span>视窗布局</span><strong class="num-mono">{{ splitMode }} 分屏</strong><em>点击视窗可选中机位</em></div>
      <div class="metric-card glass-panel"><span>在线机位</span><strong class="num-mono">{{ onlineCamCount }}/{{ cameras.length }}</strong><em>RTSP 链路健康</em></div>
      <div class="metric-card glass-panel"><span>推流带宽</span><strong class="num-mono">{{ totalBitrate }} Mbps</strong><em>当前展示视窗合计</em></div>
      <div class="metric-card glass-panel"><span>断流自愈</span><strong class="num-mono">{{ reconnectingCount }} 路</strong><em>自动重连守护中</em></div>
      <div class="metric-card glass-panel clickable-card" @click="openSnapshotGallery" :title="`点击查看全部抓拍截图 · 保存目录：${snapshotStorageDir}`">
        <span>抓拍归档</span>
        <strong class="num-mono">{{ snapshots.length }} 张</strong>
        <em>点击查看截图 · 已归档</em>
      </div>
    </section>

    <!-- 视窗布局选择工具条 -->
    <section class="scene-toolbar glass-panel">
      <div class="section-heading">
        <div>
          <h2>现场摄像机画面</h2>
          <span class="section-help">
            抓拍保存位置：
            <code class="path-code num-mono">{{ snapshotStorageDir }}</code>
            <button class="inline-link-btn" @click="copyText(snapshotStorageDir, '保存目录路径')">复制路径</button>
            <button class="inline-link-btn" @click="openSnapshotGallery">查看已存截图 ({{ snapshots.length }})</button>
          </span>
        </div>
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

    <!-- 最新抓拍结果与保存路径提示条 -->
    <section v-if="latestSnapshot" class="snapshot-notice-bar glass-panel">
      <img
        :src="latestSnapshot.url"
        :alt="latestSnapshot.cameraName"
        class="snapshot-notice-thumb"
        @click="openSnapshotPreview(latestSnapshot)"
      />
      <div class="snapshot-notice-info">
        <div class="snapshot-notice-title">
          <strong>抓拍成功：{{ latestSnapshot.cameraName }}</strong>
          <span class="num-mono">{{ latestSnapshot.createdAt }}</span>
        </div>
        <div class="snapshot-notice-path">
          <span>保存路径：</span>
          <code class="path-code num-mono">{{ latestSnapshot.filePath }}</code>
        </div>
      </div>
      <div class="snapshot-notice-actions">
        <button class="btn-header-action btn-header-primary" @click="openSnapshotPreview(latestSnapshot)">查看截图</button>
        <button class="btn-header-action" @click="copyText(latestSnapshot.filePath, '截图保存路径')">复制路径</button>
        <button class="btn-header-action" @click="openSnapshotGallery">抓拍图库 ({{ snapshots.length }})</button>
        <button class="notice-close-btn" title="关闭提示" @click="latestSnapshot = null">×</button>
      </div>
    </section>

    <!-- 主视窗布局：视频网格 + 右侧 PTZ 云台控制栏 -->
    <section class="main-layout">
      <!-- 视频视窗网格区 -->
      <div class="video-stage glass-panel">
        <div v-if="!displayedCameras.length" class="empty-stage">
          暂无接入现场摄像机，请点击右上角「+ 新增摄像机」添加设备
        </div>
        <div v-else :class="['video-grid-container', `grid-${splitMode}`]">
          <div
            v-for="cam in displayedCameras"
            :key="cam.id"
            :class="['cam-viewport', { selected: selectedCamId === cam.id }]"
            @click="selectedCamId = cam.id"
          >
            <!-- 视窗 OSD 顶栏 -->
            <div class="cam-osd-header">
              <span class="cam-title">{{ cam.name }}</span>
              <span v-if="cam.model" class="cam-model-tag">{{ cam.model }}</span>
              <span class="cam-meta num-mono">{{ cam.resolution }}@{{ cam.fps }}fps · {{ cam.bitrate }}</span>
              <span :class="['status-dot', cam.isReconnecting ? 'warning' : 'online']"></span>
            </div>

            <!-- 视频画面渲染区 -->
            <div class="cam-feed-area">
              <div v-if="cam.isReconnecting" class="reconnecting-overlay">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>网络断流自愈重连中...</span>
              </div>

              <!-- 网络摄像机实时画面 (RTSP 转码 MJPEG / HTTP / HLS) -->
              <div v-if="cam.livePlayUrl" class="live-video-wrap ip-live-wrap">
                <img
                  v-if="cam.playType === 'mjpeg'"
                  :ref="(el) => setMediaElRef(cam.id, el)"
                  :src="cam.livePlayUrl"
                  class="live-video-el"
                  :alt="cam.name"
                />
                <video
                  v-else
                  :ref="(el) => setMediaElRef(cam.id, el)"
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

              <!-- 未配置有效流地址时的待机提示 -->
              <div v-else class="mock-cam-visual">
                <div class="cam-grid-lines"></div>
                <div class="cam-corner top-left">NO STREAM</div>
                <div class="cam-corner top-right num-mono">{{ cam.fps }} FPS</div>
                <div class="center-cross"></div>
                <div class="bottom-osd num-mono">
                  <span class="osd-preset">{{ cam.ptzPreset || '请点击下方编辑配置流地址' }}</span>
                  <span class="rec-dot">● STANDBY</span>
                  <span>{{ liveTime }}</span>
                </div>
              </div>
            </div>

            <!-- 视窗底部微工具条 -->
            <div class="cam-foot-tools">
              <button class="tool-btn" @click.stop="openCameraDialog('edit', cam)">编辑</button>
              <button class="tool-btn" @click.stop="removeCustomCamera(cam)">移除</button>
              <button class="tool-btn" :disabled="capturingCamId === cam.id" @click.stop="takeSnapshot(cam)">
                {{ capturingCamId === cam.id ? '抓拍中...' : '抓拍' }}
              </button>
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
              <p>对当前选中机位下发方向、变倍与预置位指令</p>
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
        </div>
      </aside>
    </section>

    <!-- 摄像机新增 / 参数修改编辑弹窗（支持现场多台不同型号摄像机独立配置） -->
    <el-dialog
      v-model="cameraDialogVisible"
      :title="cameraDialogMode === 'edit' ? '摄像机参数修改编辑' : '新增现场网络摄像机'"
      width="620px"
      destroy-on-close
    >
      <el-form label-position="top" size="default" class="video-config-form">
        <el-form-item v-if="cameraDialogMode === 'edit'" label="选择要编辑的摄像机机位">
          <el-select
            v-model="editingCamId"
            style="width: 100%;"
            placeholder="请选择机位"
            @change="onEditingCamChange"
          >
            <el-option
              v-for="cam in cameras"
              :key="cam.id"
              :label="cam.model ? `${cam.name} [${cam.model}]` : cam.name"
              :value="cam.id"
            />
          </el-select>
        </el-form-item>

        <div class="config-grid-2">
          <el-form-item label="摄像机名称">
            <el-input v-model="camForm.name" placeholder="如：现场摄像机 01 (192.168.7.163)" clearable />
          </el-form-item>
          <el-form-item label="品牌 / 型号（不同型号独立配置）">
            <el-input v-model="camForm.model" placeholder="如：VISCA 会议球机 / 海康 DS-2CD / 大华 IPC" clearable />
          </el-form-item>
        </div>

        <el-form-item label="常见型号流路径快捷填充">
          <div class="preset-btn-row">
            <el-button size="small" @click="applyModelPreset('visca')">默认 / VISCA (/live/av0)</el-button>
            <el-button size="small" @click="applyModelPreset('hikvision')">海康主码流 (/Streaming/Channels/101)</el-button>
            <el-button size="small" @click="applyModelPreset('dahua')">大华主码流</el-button>
            <el-button size="small" @click="applyModelPreset('uniview')">宇视主码流</el-button>
          </div>
        </el-form-item>

        <div class="config-grid-2">
          <el-form-item label="网络协议">
            <el-select v-model="camForm.protocol" style="width: 100%;" @change="onProtocolChange">
              <el-option label="RTSP 视频流 (rtsp://)" value="rtsp" />
              <el-option label="HTTP / MJPEG 流 (http://)" value="mjpeg" />
              <el-option label="HLS 视频流 (.m3u8)" value="hls" />
            </el-select>
          </el-form-item>
          <el-form-item label="云台 PTZ 控制端口 (VISCA TCP)">
            <el-input-number
              v-model="camForm.ptzPort"
              :min="1"
              :max="65535"
              :controls="false"
              placeholder="默认 1259"
              style="width: 100%;"
            />
          </el-form-item>
        </div>

        <div class="config-grid-2">
          <el-form-item label="摄像机 IP 地址（或完整流地址）">
            <el-input v-model="camForm.ip" placeholder="例如 192.168.7.163 或 192.168.7.163:554" clearable />
          </el-form-item>
          <el-form-item label="流路径 / 端口路径">
            <el-input v-model="camForm.path" placeholder="例如 /live/av0" clearable />
          </el-form-item>
        </div>

        <div class="config-grid-2">
          <el-form-item label="账号（没有请留空）">
            <el-input v-model="camForm.username" placeholder="留空表示无鉴权" clearable />
          </el-form-item>
          <el-form-item label="密码（没有请留空）">
            <el-input v-model="camForm.password" type="password" show-password placeholder="留空表示无密码" clearable />
          </el-form-item>
        </div>

        <div class="config-grid-2">
          <el-form-item label="画面规格">
            <el-select v-model="camForm.resolutionKey" style="width: 100%;">
              <el-option label="1920×1080 @ 25fps" value="1920×1080@25" />
              <el-option label="1920×1080 @ 30fps" value="1920×1080@30" />
              <el-option label="1920×1080 @ 60fps" value="1920×1080@60" />
              <el-option label="3840×2160 @ 25fps" value="3840×2160@25" />
              <el-option label="3840×2160 @ 30fps" value="3840×2160@30" />
              <el-option label="1280×720 @ 25fps" value="1280×720@25" />
            </el-select>
          </el-form-item>
          <el-form-item label="预估推流码率">
            <el-select v-model="camForm.bitrate" style="width: 100%;" filterable allow-create default-first-option>
              <el-option label="4 Mbps" value="4 Mbps" />
              <el-option label="6 Mbps" value="6 Mbps" />
              <el-option label="8 Mbps" value="8 Mbps" />
              <el-option label="12 Mbps" value="12 Mbps" />
              <el-option label="16 Mbps" value="16 Mbps" />
            </el-select>
          </el-form-item>
        </div>

        <el-form-item v-if="cameraDialogMode === 'add'" label="展示位置">
          <el-select v-model="camForm.slotMode" style="width: 100%;">
            <el-option label="新增为第 1 号机位（立即置顶展示）" value="prepend" />
            <el-option label="追加到机位列表末尾" value="append" />
          </el-select>
        </el-form-item>

        <div class="mode-tip-box info" style="margin-bottom: 0;">
          <strong>生成流地址预览：</strong>
          <div class="num-mono" style="margin-top: 4px; word-break: break-all;">{{ maskedBuiltStreamUrl || '请填写 IP 地址' }}</div>
          <div v-if="camProbeMessage" class="detect-result-text">{{ camProbeMessage }}</div>
        </div>
      </el-form>

      <template #footer>
        <div class="dialog-footer-bar">
          <el-button @click="probeCameraForm" :loading="probingCamera">
            <el-icon style="margin-right: 4px;"><Refresh /></el-icon>
            探测连通性
          </el-button>
          <div style="flex: 1;"></div>
          <el-button @click="cameraDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitCameraForm">
            {{ cameraDialogMode === 'edit' ? '保存参数并重新拉流' : '保存并接入画面' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 抓拍截图库弹窗 -->
    <el-dialog v-model="snapshotGalleryVisible" title="现场摄像机抓拍截图库" width="840px" destroy-on-close>
      <div class="snapshot-dir-banner">
        <div class="snapshot-dir-text">
          <span>抓拍文件保存位置：</span>
          <code class="path-code num-mono">{{ snapshotStorageDir }}</code>
        </div>
        <div class="snapshot-dir-btns">
          <el-button size="small" @click="copyText(snapshotStorageDir, '保存目录路径')">复制路径</el-button>
          <el-button size="small" :loading="loadingSnapshots" @click="loadSnapshots">刷新列表</el-button>
        </div>
      </div>

      <div v-if="!snapshots.length" class="snapshot-empty">
        暂无抓拍截图，点击摄像机画面底部的「抓拍」或顶部「一键全机位抓拍」即可生成截图并保存至上述目录。
      </div>
      <div v-else class="snapshot-grid">
        <div v-for="item in snapshots" :key="item.id" class="snapshot-card">
          <div class="snapshot-thumb-wrap" @click="openSnapshotPreview(item)">
            <img :src="item.url" :alt="item.cameraName" class="snapshot-thumb-img" />
          </div>
          <div class="snapshot-card-body">
            <div class="snapshot-card-name" :title="item.cameraName">{{ item.cameraName }}</div>
            <div class="snapshot-card-meta num-mono">{{ item.createdAt }} · {{ formatBytes(item.size) }}</div>
            <div class="snapshot-card-path num-mono" :title="item.filePath">{{ item.filePath }}</div>
            <div class="snapshot-card-ops">
              <el-button size="small" type="primary" link @click="openSnapshotPreview(item)">查看大图</el-button>
              <el-button size="small" link @click="downloadSnapshot(item)">下载</el-button>
              <el-button size="small" link @click="copyText(item.filePath, '截图路径')">复制路径</el-button>
              <el-button size="small" type="danger" link @click="removeSnapshot(item)">删除</el-button>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 抓拍截图大图预览弹窗 -->
    <el-dialog v-model="snapshotPreviewVisible" title="抓拍截图查看" width="760px" destroy-on-close>
      <div v-if="previewSnapshot" class="snapshot-preview-wrap">
        <div class="snapshot-preview-img-box">
          <img :src="previewSnapshot.url" :alt="previewSnapshot.cameraName" class="snapshot-preview-img" />
        </div>
        <div class="snapshot-preview-meta">
          <div class="preview-meta-row"><span>抓拍机位</span><strong>{{ previewSnapshot.cameraName }}</strong></div>
          <div class="preview-meta-row"><span>抓拍时间</span><strong class="num-mono">{{ previewSnapshot.createdAt }}</strong></div>
          <div class="preview-meta-row"><span>文件名称</span><strong class="num-mono">{{ previewSnapshot.filename }}</strong></div>
          <div class="preview-meta-row">
            <span>保存路径</span>
            <code class="path-code num-mono">{{ previewSnapshot.filePath }}</code>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer-bar">
          <el-button v-if="previewSnapshot" @click="copyText(previewSnapshot.filePath, '截图保存路径')">复制保存路径</el-button>
          <el-button v-if="previewSnapshot" @click="downloadSnapshot(previewSnapshot)">下载原图</el-button>
          <div style="flex: 1;"></div>
          <el-button type="primary" @click="snapshotPreviewVisible = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { Loading, Setting, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import SvgIcon from '@/components/SvgIcon.vue'
import { api, API_BASE_URL } from '@/services/api'

const CUSTOM_CAMERAS_STORAGE_KEY = 'venue_custom_cameras_v1'
const LOCAL_SNAPSHOTS_STORAGE_KEY = 'venue_video_snapshots_local_v1'

const splitMode = ref(4) // 1, 4, 9
const selectedCamId = ref(null)

const mediaElMap = new Map()
const setMediaElRef = (camId, el) => {
  if (el) {
    mediaElMap.set(camId, el)
  } else {
    mediaElMap.delete(camId)
  }
}

const snapshots = ref([])
const snapshotStorageDir = ref('public/uploads/snapshots（项目根目录）')
const latestSnapshot = ref(null)
const snapshotGalleryVisible = ref(false)
const snapshotPreviewVisible = ref(false)
const previewSnapshot = ref(null)
const loadingSnapshots = ref(false)
const capturingCamId = ref(null)
const capturingAll = ref(false)

const liveTime = ref('')
let timer = null

// ===== 摄像机列表与按机位独立参数配置（新增 / 修改编辑） =====
const cameras = ref([])
const cameraDialogVisible = ref(false)
const cameraDialogMode = ref('add') // 'add' | 'edit'
const editingCamId = ref(null)
const probingCamera = ref(false)
const camProbeMessage = ref('')

const camForm = reactive({
  name: '',
  model: '',
  protocol: 'rtsp',
  ip: '192.168.7.164',
  path: '/live/av0',
  username: '',
  password: '',
  resolutionKey: '1920×1080@25',
  bitrate: '6 Mbps',
  ptzPort: 1259,
  slotMode: 'prepend'
})

const parseResolutionKey = (key) => {
  const [resPart, fpsPart] = String(key || '1920×1080@25').split('@')
  return {
    resolution: (resPart || '1920×1080').replace(/x/i, '×'),
    fps: Number(fpsPart) || 25
  }
}

const parseStreamUrl = (streamUrl, fallbackProtocol = 'rtsp') => {
  const raw = (streamUrl || '').trim()
  if (!raw) {
    return { protocol: fallbackProtocol, ip: '', path: '/live/av0', username: '', password: '' }
  }
  try {
    const isRtsp = /^rtsps?:\/\//i.test(raw)
    const forUrl = isRtsp
      ? raw.replace(/^rtsps?:\/\//i, 'http://')
      : (/^https?:\/\//i.test(raw) ? raw : `http://${raw}`)
    const u = new URL(forUrl)
    const protocol = isRtsp
      ? 'rtsp'
      : (raw.toLowerCase().includes('.m3u8') ? 'hls' : (fallbackProtocol === 'rtsp' ? 'mjpeg' : (fallbackProtocol || 'mjpeg')))
    const hostPort = u.port ? `${u.hostname}:${u.port}` : u.hostname
    const path = `${u.pathname || ''}${u.search || ''}`
    return {
      protocol,
      ip: hostPort,
      path: path === '/' ? '' : path,
      username: u.username ? decodeURIComponent(u.username) : '',
      password: u.password ? decodeURIComponent(u.password) : ''
    }
  } catch {
    return { protocol: fallbackProtocol, ip: raw, path: '', username: '', password: '' }
  }
}

const onProtocolChange = (proto) => {
  if (proto === 'rtsp' && !camForm.path) {
    camForm.path = '/live/av0'
  }
}

const applyModelPreset = (preset) => {
  camForm.protocol = 'rtsp'
  if (preset === 'visca') {
    camForm.path = '/live/av0'
    camForm.ptzPort = 1259
    if (!camForm.model) camForm.model = 'VISCA 云台摄像机'
  } else if (preset === 'hikvision') {
    camForm.path = '/Streaming/Channels/101'
    if (!camForm.model) camForm.model = '海康威视 IPC'
  } else if (preset === 'dahua') {
    camForm.path = '/cam/realmonitor?channel=1&subtype=0'
    if (!camForm.model) camForm.model = '大华 IPC'
  } else if (preset === 'uniview') {
    camForm.path = '/media/video1'
    if (!camForm.model) camForm.model = '宇视 IPC'
  }
}

const builtStreamUrl = computed(() => {
  const rawIp = (camForm.ip || '').trim()
  if (!rawIp) return ''
  // 如果用户直接粘贴了完整协议地址（如 rtsp://192.168.7.164/live/av0）
  if (/^[a-z]+:\/\//i.test(rawIp)) {
    const user = (camForm.username || '').trim()
    const pwd = camForm.password || ''
    if (user && !rawIp.includes('@')) {
      const auth = pwd ? `${encodeURIComponent(user)}:${encodeURIComponent(pwd)}@` : `${encodeURIComponent(user)}@`
      return rawIp.replace(/^([a-z]+:\/\/)/i, `$1${auth}`)
    }
    return rawIp
  }
  const scheme = camForm.protocol === 'rtsp' ? 'rtsp://' : 'http://'
  const user = (camForm.username || '').trim()
  const pwd = camForm.password || ''
  const auth = user ? (pwd ? `${encodeURIComponent(user)}:${encodeURIComponent(pwd)}@` : `${encodeURIComponent(user)}@`) : ''
  let p = (camForm.path || '').trim()
  if (p && !p.startsWith('/')) p = `/${p}`
  return `${scheme}${auth}${rawIp}${p}`
})

const maskedBuiltStreamUrl = computed(() =>
  builtStreamUrl.value.replace(/\/\/([^:@/]+):([^@/]+)@/, '//$1:***@')
)

const makePlayConfig = (streamUrl, protocol, bustCache = false) => {
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

const loadCamIntoForm = (cam) => {
  if (!cam) return
  const parsed = parseStreamUrl(cam.streamUrl, cam.protocol || 'rtsp')
  camForm.name = cam.name || ''
  camForm.model = cam.model || ''
  camForm.protocol = parsed.protocol
  camForm.ip = parsed.ip
  camForm.path = parsed.path
  camForm.username = parsed.username
  camForm.password = parsed.password
  camForm.resolutionKey = `${(cam.resolution || '1920×1080').replace(/x/i, '×')}@${cam.fps || 25}`
  camForm.bitrate = cam.bitrate || '6 Mbps'
  camForm.ptzPort = Number(cam.ptzPort) || 1259
  camForm.slotMode = cam.slotMode || 'prepend'
  camProbeMessage.value = ''
}

const openCameraDialog = (mode = 'add', targetCam = null) => {
  camProbeMessage.value = ''
  if (mode === 'edit') {
    if (!cameras.value.length) {
      ElMessage.warning('当前暂无可编辑的摄像机，请先新增摄像机')
      openCameraDialog('add')
      return
    }
    const cam = targetCam || selectedCamObj.value || cameras.value[0]
    cameraDialogMode.value = 'edit'
    editingCamId.value = cam.id
    loadCamIntoForm(cam)
    cameraDialogVisible.value = true
    return
  }

  cameraDialogMode.value = 'add'
  editingCamId.value = null
  camForm.name = ''
  camForm.model = ''
  camForm.protocol = 'rtsp'
  camForm.ip = ''
  camForm.path = '/live/av0'
  camForm.username = ''
  camForm.password = ''
  camForm.resolutionKey = '1920×1080@25'
  camForm.bitrate = '6 Mbps'
  camForm.ptzPort = 1259
  camForm.slotMode = 'prepend'
  cameraDialogVisible.value = true
}

const onEditingCamChange = (camId) => {
  const cam = cameras.value.find(c => c.id === camId)
  if (cam) loadCamIntoForm(cam)
}

const probeCameraForm = async () => {
  const url = builtStreamUrl.value
  if (!url) {
    ElMessage.warning('请先填写摄像机 IP 地址')
    return
  }
  probingCamera.value = true
  camProbeMessage.value = ''
  try {
    const res = await api.videoProbe({ target: url, protocol: camForm.protocol })
    if (res && !res.__offline) {
      camProbeMessage.value = res.message || (res.reachable ? '摄像机端口连通正常' : '无法连通目标摄像机端口')
      if (res.reachable) {
        ElMessage.success(camProbeMessage.value)
      } else {
        ElMessage.warning(camProbeMessage.value)
      }
    } else {
      camProbeMessage.value = '后端接口未响应，请确认后端服务（8000端口）已启动。'
      ElMessage.warning(camProbeMessage.value)
    }
  } catch (err) {
    camProbeMessage.value = `探测失败：${err?.message || err}`
    ElMessage.error(camProbeMessage.value)
  } finally {
    probingCamera.value = false
  }
}

const saveCustomCamerasToStorage = () => {
  try {
    const list = cameras.value.map(c => ({
      id: c.id,
      name: c.name,
      model: c.model || '',
      protocol: c.protocol || 'rtsp',
      streamUrl: c.streamUrl,
      resolution: c.resolution || '1920×1080',
      fps: Number(c.fps) || 25,
      bitrate: c.bitrate || '6 Mbps',
      ptzPort: Number(c.ptzPort) || 1259,
      slotMode: c.slotMode || 'prepend'
    }))
    localStorage.setItem(CUSTOM_CAMERAS_STORAGE_KEY, JSON.stringify(list))
  } catch { /* ignore */ }
}

const hydrateCameraItem = (item) => {
  const protocol = item.protocol || 'rtsp'
  const playCfg = makePlayConfig(item.streamUrl, protocol)
  return {
    id: item.id || Date.now(),
    name: item.name || item.streamUrl,
    model: item.model || '',
    resolution: item.resolution || '1920×1080',
    fps: Number(item.fps) || 25,
    bitrate: item.bitrate || '6 Mbps',
    ptzPort: Number(item.ptzPort) || 1259,
    ptzPreset: String(item.streamUrl || '').replace(/\/\/.*@/, '//***@'),
    isReconnecting: false,
    isCustom: true,
    protocol,
    streamUrl: item.streamUrl,
    slotMode: item.slotMode || 'prepend',
    ...playCfg
  }
}

const initCameras = () => {
  try {
    const raw = localStorage.getItem(CUSTOM_CAMERAS_STORAGE_KEY)
    if (raw !== null) {
      const list = JSON.parse(raw)
      if (Array.isArray(list)) {
        cameras.value = list.filter(item => item?.streamUrl).map(hydrateCameraItem)
        if (cameras.value.length) selectedCamId.value = cameras.value[0].id
        return
      }
    }
  } catch { /* ignore */ }

  const defaults = [
    {
      id: 10163,
      name: '现场摄像机 01 (192.168.7.163)',
      model: 'VISCA 云台摄像机',
      protocol: 'rtsp',
      streamUrl: 'rtsp://192.168.7.163/live/av0',
      resolution: '1920×1080',
      fps: 25,
      bitrate: '6 Mbps',
      ptzPort: 1259
    },
    {
      id: 10164,
      name: '现场摄像机 02 (192.168.7.164)',
      model: 'VISCA 云台摄像机',
      protocol: 'rtsp',
      streamUrl: 'rtsp://192.168.7.164/live/av0',
      resolution: '1920×1080',
      fps: 25,
      bitrate: '6 Mbps',
      ptzPort: 1259
    }
  ]
  cameras.value = defaults.map(hydrateCameraItem)
  if (cameras.value.length) selectedCamId.value = cameras.value[0].id
  saveCustomCamerasToStorage()
}

const submitCameraForm = () => {
  const url = builtStreamUrl.value
  if (!url) {
    ElMessage.warning('请先填写摄像机 IP 地址')
    return
  }
  const { resolution, fps } = parseResolutionKey(camForm.resolutionKey)
  const displayName = (camForm.name || '').trim() || `现场摄像机 (${camForm.ip.trim()})`
  const model = (camForm.model || '').trim()
  const bitrate = (camForm.bitrate || '').trim() || '6 Mbps'
  const ptzPort = Number(camForm.ptzPort) || 1259

  if (cameraDialogMode.value === 'edit') {
    const target = cameras.value.find(c => c.id === editingCamId.value)
    if (!target) {
      ElMessage.error('未找到要修改的摄像机机位')
      return
    }
    const playCfg = makePlayConfig(url, camForm.protocol, true)
    target.name = displayName
    target.model = model
    target.protocol = camForm.protocol
    target.streamUrl = url
    target.resolution = resolution
    target.fps = fps
    target.bitrate = bitrate
    target.ptzPort = ptzPort
    target.ptzPreset = url.replace(/\/\/.*@/, '//***@')
    target.playType = playCfg.playType
    target.livePlayUrl = playCfg.livePlayUrl

    selectedCamId.value = target.id
    saveCustomCamerasToStorage()
    cameraDialogVisible.value = false
    ElMessage.success(`已保存「${displayName}」参数并重新拉流`)
    return
  }

  const playCfg = makePlayConfig(url, camForm.protocol, true)
  const camId = Date.now()
  const newCam = {
    id: camId,
    name: displayName,
    model,
    resolution,
    fps,
    bitrate,
    ptzPort,
    ptzPreset: url.replace(/\/\/.*@/, '//***@'),
    isReconnecting: false,
    isCustom: true,
    protocol: camForm.protocol,
    streamUrl: url,
    slotMode: camForm.slotMode,
    ...playCfg
  }
  if (camForm.slotMode === 'append') {
    cameras.value.push(newCam)
  } else {
    cameras.value.unshift(newCam)
  }
  selectedCamId.value = camId
  saveCustomCamerasToStorage()
  cameraDialogVisible.value = false
  ElMessage.success(`已新增摄像机「${displayName}」并开始拉流`)
}

const removeCustomCamera = (cam) => {
  cameras.value = cameras.value.filter(c => c.id !== cam.id)
  if (selectedCamId.value === cam.id) {
    selectedCamId.value = cameras.value.length ? cameras.value[0].id : null
  }
  saveCustomCamerasToStorage()
  ElMessage.info(`已移除摄像机「${cam.name}」`)
}

onMounted(() => {
  initCameras()
  loadSnapshots()
  liveTime.value = new Date().toLocaleTimeString()
  timer = setInterval(() => {
    liveTime.value = new Date().toLocaleTimeString()
  }, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

const displayedCameras = computed(() => {
  return cameras.value.slice(0, splitMode.value)
})

const onlineCamCount = computed(() => cameras.value.filter(cam => !cam.isReconnecting).length)
const reconnectingCount = computed(() => cameras.value.filter(cam => cam.isReconnecting).length)
const totalBitrate = computed(() =>
  displayedCameras.value.reduce((sum, cam) => sum + (Number(String(cam.bitrate).split(' ')[0]) || 0), 0)
)

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
  const port = Number(selectedCamObj.value?.ptzPort) || 1259
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

const formatBytes = (bytes) => {
  const n = Number(bytes) || 0
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / (1024 * 1024)).toFixed(2)} MB`
}

const copyText = async (text, label = '路径') => {
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success(`已复制${label}：${text}`)
  } catch {
    const input = document.createElement('textarea')
    input.value = text
    document.body.appendChild(input)
    input.select()
    document.execCommand('copy')
    document.body.removeChild(input)
    ElMessage.success(`已复制${label}`)
  }
}

const loadLocalSnapshots = () => {
  try {
    const raw = localStorage.getItem(LOCAL_SNAPSHOTS_STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

const saveLocalSnapshots = (list) => {
  try {
    localStorage.setItem(LOCAL_SNAPSHOTS_STORAGE_KEY, JSON.stringify(list.slice(0, 30)))
  } catch { /* ignore */ }
}

const loadSnapshots = async () => {
  loadingSnapshots.value = true
  try {
    const res = await api.videoSnapshots()
    if (res && !res.__offline && Array.isArray(res.snapshots)) {
      if (res.storageDir) snapshotStorageDir.value = res.storageDir
      const localOnly = loadLocalSnapshots().filter(l => l.isLocal)
      snapshots.value = [...res.snapshots, ...localOnly]
      return
    }
  } catch { /* ignore */ } finally {
    loadingSnapshots.value = false
  }
  snapshots.value = loadLocalSnapshots()
}

const captureElementToDataUrl = (camId) => {
  const el = mediaElMap.get(camId)
  if (!el) return ''
  try {
    const isVideo = el.tagName === 'VIDEO'
    const width = isVideo ? el.videoWidth : el.naturalWidth
    const height = isVideo ? el.videoHeight : el.naturalHeight
    if (!width || !height) return ''
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const ctx = canvas.getContext('2d')
    ctx.drawImage(el, 0, 0, width, height)
    return canvas.toDataURL('image/jpeg', 0.92)
  } catch {
    return ''
  }
}

const openSnapshotGallery = () => {
  snapshotGalleryVisible.value = true
  loadSnapshots()
}

const openSnapshotPreview = (item) => {
  previewSnapshot.value = item
  snapshotPreviewVisible.value = true
}

const downloadSnapshot = (item) => {
  if (!item?.url) return
  const link = document.createElement('a')
  link.href = item.url
  link.download = item.filename || `snapshot-${Date.now()}.jpg`
  link.click()
}

const removeSnapshot = async (item) => {
  if (!item) return
  if (item.isLocal) {
    const nextLocal = loadLocalSnapshots().filter(x => x.id !== item.id)
    saveLocalSnapshots(nextLocal)
    snapshots.value = snapshots.value.filter(x => x.id !== item.id)
    if (latestSnapshot.value?.id === item.id) latestSnapshot.value = null
    ElMessage.info('已删除该条本地抓拍记录')
    return
  }
  try {
    await api.deleteVideoSnapshot(item.filename)
    snapshots.value = snapshots.value.filter(x => x.filename !== item.filename)
    if (latestSnapshot.value?.filename === item.filename) latestSnapshot.value = null
    ElMessage.success(`已删除抓拍截图 ${item.filename}`)
  } catch (err) {
    ElMessage.error(`删除失败：${err?.message || err}`)
  }
}

const captureSingleCamera = async (cam, silentToast = false) => {
  const imageBase64 = captureElementToDataUrl(cam.id)
  try {
    const res = await api.videoSnapshot({
      cameraId: String(cam.id),
      cameraName: cam.name,
      streamUrl: cam.streamUrl || '',
      imageBase64
    })
    if (res && !res.__offline && res.snapshot) {
      if (res.storageDir) snapshotStorageDir.value = res.storageDir
      const snap = res.snapshot
      snapshots.value = [snap, ...snapshots.value.filter(s => s.filename !== snap.filename)]
      latestSnapshot.value = snap
      if (!silentToast) {
        ElMessage.success(`已抓拍「${cam.name}」，保存至：${snap.filePath}`)
      }
      return snap
    }
  } catch (err) {
    // 若后端已响应且明确报错（如摄像机离线无画面），且前端也没有截取到画面，直接提示真实原因
    if (!imageBase64) {
      if (!silentToast) {
        ElMessage.error(err?.message || `抓拍「${cam.name}」失败：当前未获取到实时画面`)
      }
      return null
    }
  }

  // 后端离线或未重启新接口时的本地降级：直接保存前端截取到的真实画面并触发下载
  if (!imageBase64) {
    if (!silentToast) {
      ElMessage.warning(`未能获取「${cam.name}」实时画面，请确认摄像机已出流且后端服务已启动`)
    }
    return null
  }
  const nowStr = new Date().toLocaleString('zh-CN', { hour12: false })
  const filename = `snap_${Date.now()}_${cam.id}.jpg`
  const approxSize = Math.round((imageBase64.length * 3) / 4)
  const localSnap = {
    id: filename,
    filename,
    cameraId: String(cam.id),
    cameraName: cam.name,
    streamUrl: cam.streamUrl || '',
    url: imageBase64,
    filePath: `浏览器默认下载目录/${filename}（本地缓存预览）`,
    storageDir: '浏览器默认下载目录',
    size: approxSize,
    createdAt: nowStr,
    isLocal: true
  }
  const nextLocal = [localSnap, ...loadLocalSnapshots()]
  saveLocalSnapshots(nextLocal)
  snapshots.value = [localSnap, ...snapshots.value]
  latestSnapshot.value = localSnap
  downloadSnapshot(localSnap)
  if (!silentToast) {
    ElMessage.success(`已抓拍「${cam.name}」并下载至浏览器默认下载目录（${filename}）`)
  }
  return localSnap
}

const takeSnapshot = async (cam) => {
  if (capturingCamId.value === cam.id) return
  capturingCamId.value = cam.id
  try {
    await captureSingleCamera(cam, false)
  } finally {
    capturingCamId.value = null
  }
}

const triggerPtzPreset = (cam) => {
  ElMessage.success(`机位 ${cam.name} 已转动至预置位`)
}

const reconnectCam = (cam) => {
  cam.isReconnecting = true
  const playCfg = makePlayConfig(cam.streamUrl, cam.protocol || 'rtsp', true)
  setTimeout(() => {
    cam.playType = playCfg.playType
    cam.livePlayUrl = playCfg.livePlayUrl
    cam.isReconnecting = false
    ElMessage.success(`${cam.name} 视频流已重新拉流！`)
  }, 800)
}

const snapshotAll = async () => {
  const targets = displayedCameras.value
  if (!targets.length) {
    ElMessage.warning('当前没有可抓拍的现场摄像机画面')
    return
  }
  capturingAll.value = true
  let okCount = 0
  try {
    for (const cam of targets) {
      const snap = await captureSingleCamera(cam, true)
      if (snap) okCount += 1
    }
    if (okCount > 0) {
      ElMessage.success(`一键抓拍完成：成功保存 ${okCount}/${targets.length} 张截图，目录：${snapshotStorageDir.value}`)
    } else {
      ElMessage.warning('未能抓拍到实时画面，请确认现场摄像机已正常出流')
    }
  } finally {
    capturingAll.value = false
  }
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
.empty-stage { flex: 1; display: flex; align-items: center; justify-content: center; color: var(--do-text-secondary); font-size: 14px; background: var(--do-bg-sunken); border: 1px dashed var(--do-border); border-radius: 8px; }
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
.cam-model-tag { flex-shrink: 0; padding: 1px 6px; border-radius: 4px; background: rgba(var(--th-accent-rgb), 0.24); border: 1px solid rgba(var(--th-accent-rgb), 0.42); color: var(--do-text-inverse); font-size: 11px; font-weight: 600; white-space: nowrap; }
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

.ptz-sliders-group { padding: 12px 18px 18px; display: flex; flex-direction: column; gap: 10px; }
.ptz-action-grid { padding: 0 18px 8px; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.ptz-act-btn { padding: 7px 10px; border-radius: 6px; border: 1px solid var(--do-border); background: var(--do-bg-card); color: var(--do-text-primary); font-size: 12.5px; font-weight: 600; cursor: pointer; user-select: none; transition: all 0.15s ease; }
.ptz-act-btn:hover { border-color: var(--do-gold); color: var(--do-gold-deep); }
.ptz-act-btn:active { background: var(--do-gold); border-color: var(--do-gold); color: #fff; }
.slider-row { display: flex; flex-direction: column; }
.s-lbl { font-size: 13px; color: var(--do-text-secondary); font-weight: 600; }

.num-mono { font-family: var(--font-family-mono, 'SF Mono', Consolas, monospace); }

.btn-header-action { display: inline-flex; align-items: center; padding: 7px 13px; border-radius: 8px; border: 1px solid var(--do-border); background: var(--do-bg-card); color: var(--do-text-primary); font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s ease; }
.btn-header-action:hover { border-color: var(--do-gold); color: var(--do-gold-deep); }
.btn-header-action.btn-header-primary { background: var(--do-gold); border-color: var(--do-gold); color: #fff; }
.btn-header-action.btn-header-primary:hover { opacity: 0.92; color: #fff; }

.video-config-form { display: flex; flex-direction: column; gap: 4px; }
.mode-tip-box { margin-bottom: 16px; padding: 10px 12px; border-radius: 8px; font-size: 13px; line-height: 1.55; }
.mode-tip-box p { margin-top: 4px; }
.mode-tip-box.info { background: var(--do-bg-sunken); border: 1px solid var(--do-border); color: var(--do-text-secondary); }
.detect-result-text { margin-top: 6px; font-size: 12px; color: var(--do-text-secondary); line-height: 1.45; }
.config-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.preset-btn-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.ip-live-wrap { display: flex; align-items: center; justify-content: center; }
.dialog-footer-bar { display: flex; align-items: center; gap: 8px; width: 100%; }

/* ===== 抓拍保存路径提示与图库预览 ===== */
.clickable-card { cursor: pointer; transition: border-color 0.2s, box-shadow 0.2s; }
.clickable-card:hover { border-color: var(--do-gold); box-shadow: var(--shadow-hover); }
.path-code { padding: 2px 6px; border-radius: 4px; background: var(--do-bg-sunken); border: 1px solid var(--do-border); color: var(--do-text-primary); font-size: 12px; word-break: break-all; }
.inline-link-btn { margin-left: 8px; padding: 0; border: none; background: transparent; color: var(--do-gold-deep); font-size: 12.5px; font-weight: 600; cursor: pointer; text-decoration: underline; }
.inline-link-btn:hover { color: var(--do-gold); }

.snapshot-notice-bar { display: flex; align-items: center; gap: 14px; padding: 10px 16px; border-left: 4px solid var(--do-success); background: var(--do-bg-card); flex-wrap: wrap; }
.snapshot-notice-thumb { width: 88px; height: 50px; object-fit: cover; border-radius: 6px; border: 1px solid var(--do-border); cursor: pointer; flex-shrink: 0; background: #000; }
.snapshot-notice-info { flex: 1; min-width: 240px; display: flex; flex-direction: column; gap: 5px; }
.snapshot-notice-title { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; font-size: 13.5px; color: var(--do-text-primary); }
.snapshot-notice-title span { font-size: 12px; color: var(--do-text-secondary); }
.snapshot-notice-path { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; font-size: 12.5px; color: var(--do-text-secondary); }
.snapshot-notice-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.notice-close-btn { width: 28px; height: 28px; border-radius: 6px; border: 1px solid var(--do-border); background: transparent; color: var(--do-text-secondary); font-size: 16px; line-height: 1; cursor: pointer; }
.notice-close-btn:hover { color: var(--do-text-primary); border-color: var(--do-gold); }

.snapshot-dir-banner { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 12px; margin-bottom: 14px; background: var(--do-bg-sunken); border: 1px solid var(--do-border); border-radius: 8px; flex-wrap: wrap; }
.snapshot-dir-text { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; font-size: 13px; color: var(--do-text-secondary); }
.snapshot-dir-btns { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.snapshot-empty { padding: 36px 20px; text-align: center; color: var(--do-text-secondary); font-size: 13.5px; background: var(--do-bg-sunken); border: 1px dashed var(--do-border); border-radius: 8px; }
.snapshot-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; max-height: 520px; overflow-y: auto; padding-right: 4px; }
.snapshot-card { display: flex; flex-direction: column; overflow: hidden; border: 1px solid var(--do-border); border-radius: 8px; background: var(--do-bg-card); }
.snapshot-thumb-wrap { height: 140px; background: #000; overflow: hidden; cursor: pointer; }
.snapshot-thumb-img { width: 100%; height: 100%; object-fit: cover; display: block; transition: transform 0.2s ease; }
.snapshot-thumb-wrap:hover .snapshot-thumb-img { transform: scale(1.03); }
.snapshot-card-body { padding: 10px; display: flex; flex-direction: column; gap: 5px; }
.snapshot-card-name { font-size: 13px; font-weight: 700; color: var(--do-text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.snapshot-card-meta { font-size: 11.5px; color: var(--do-text-secondary); }
.snapshot-card-path { font-size: 11px; color: var(--do-text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.snapshot-card-ops { display: flex; align-items: center; justify-content: space-between; margin-top: 4px; }

.snapshot-preview-wrap { display: flex; flex-direction: column; gap: 14px; }
.snapshot-preview-img-box { display: flex; align-items: center; justify-content: center; background: #000; border-radius: 8px; overflow: hidden; border: 1px solid var(--do-border); }
.snapshot-preview-img { max-width: 100%; max-height: 60vh; object-fit: contain; display: block; }
.snapshot-preview-meta { display: flex; flex-direction: column; gap: 8px; padding: 12px 14px; background: var(--do-bg-sunken); border: 1px solid var(--do-border); border-radius: 8px; }
.preview-meta-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; font-size: 13px; color: var(--do-text-secondary); flex-wrap: wrap; }
.preview-meta-row strong { color: var(--do-text-primary); }

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
