<template>
  <div class="media-console-workspace">
    <!-- 页面级标题区：与大屏调度、计时计分页面保持一致 -->
    <section class="page-header media-page-header glass-panel">
      <div class="page-heading">
        <div class="page-icon"><SvgIcon name="SvgMediaPlayer" size="28" /></div>
        <div>
          <div class="title-row">
            <h1>媒体播控台</h1>
            <span class="media-status-badge">素材库已加载</span>
          </div>
          <p>背景音乐与视频素材管理 · HTML5 播放 · 存储驱动与业务分组统一维护</p>
        </div>
      </div>
      <div class="header-status media-header-status">
        <div class="status-metric">
          <span class="status-dot online"></span>
          <span>素材库同步正常</span>
        </div>
        <div class="status-metric"><strong class="num-mono">{{ totalAssetsCount }}</strong> 项素材</div>
        <div class="status-metric"><strong class="num-mono">{{ categories.length }}</strong> 个分类</div>
      </div>
    </section>

    <!-- 1. 双维度分类与分组管理选择面板 -->
    <div class="filter-matrix-panel glass-panel">
      <!-- 维度 1：资源分类栏 (Category) -->
      <div class="filter-row category-row">
        <div class="row-label">
          <SvgIcon name="SvgAppGrid" size="20" />
          <span>资源分类:</span>
        </div>
        <div class="chips-container">
          <div :class="['matrix-chip', { active: currentCategory === 'ALL' }]" @click="handleCategoryChange('ALL')">
            <span class="chip-name">全部分类</span>
            <span class="chip-count num-mono">{{ totalAssetsCount }}</span>
          </div>
          <div v-for="cat in categories" :key="cat.code"
            :class="['matrix-chip', { active: currentCategory === cat.code }]" @click="handleCategoryChange(cat.code)">
            <SvgIcon :name="cat.icon || 'SvgAppGrid'" size="20" />
            <span class="chip-name">{{ cat.name }}</span>
            <span class="chip-count num-mono">{{ getCategoryCount(cat.code) }}</span>
          </div>
        </div>
      </div>

      <!-- 维度 2：资源分组栏 (Group，隶属于分类，需先选定分类) -->
      <div class="filter-row group-row" :class="{ disabled: currentCategory === 'ALL' }">
        <div class="row-label">
          <SvgIcon name="SvgFlagSystem" size="20" />
          <span>业务分组:</span>
        </div>
        <div class="chips-container">
          <template v-if="currentCategory === 'ALL'">
            <div class="matrix-chip placeholder-chip">
              <SvgIcon name="SvgAppGrid" size="20" />
              <span class="chip-name">请先选择分类</span>
            </div>
          </template>
          <template v-else>
            <div :class="['matrix-chip group-chip', { active: currentGroup === 'ALL' }]" @click="currentGroup = 'ALL'">
              <span class="chip-name">全部分组</span>
              <span class="chip-count num-mono">{{ getCategoryCount(currentCategory) }}</span>
            </div>
            <div v-for="grp in currentCategoryGroups" :key="grp.code"
              :class="['matrix-chip group-chip', { active: currentGroup === grp.code }]"
              @click="currentGroup = grp.code">
              <span class="chip-dot"></span>
              <span class="chip-name">{{ grp.name }}</span>
              <span class="chip-count num-mono">{{ getGroupCount(currentCategory, grp.code) }}</span>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- 3. 素材操作与检索工具栏 -->
    <div class="assets-toolbar glass-panel">
      <div class="toolbar-left">
        <div class="filter-summary">
          <span class="fs-text">当前检索范围:</span>
          <span class="fs-tag fs-tag-primary">
            分类: {{ currentCategoryName }}
          </span>
          <span class="fs-divider">×</span>
          <span class="fs-tag fs-tag-warning">
            分组: {{ currentGroupName }}
          </span>
        </div>
      </div>

      <div class="toolbar-right">
        <!-- 搜索框 -->
        <el-input v-model="searchKeyword" placeholder="按素材名称、格式、备注搜索..." clearable size="small"
          class="toolbar-search-input" prefix-icon="Search" />

        <!-- 分类 / 分组管理 -->
        <el-button size="small" plain @click="openCategoryManageDialog">
          <SvgIcon name="SvgDeviceSetting" size="15" style="margin-right: 4px;" />
          管理分类 ({{ categories.length }})
        </el-button>
        <el-button size="small" plain @click="openGroupManageDialog">
          <SvgIcon name="SvgDeviceSetting" size="15" style="margin-right: 4px;" />
          管理分组 ({{ groups.length }})
        </el-button>

        <!-- 核心上传主按钮 -->
        <el-button size="small" type="primary" class="btn-main-upload" @click="openUploadDialog">
          <SvgIcon name="SvgDynamicDevice" size="16" style="margin-right: 4px;" />
          + 上传素材到当前分组
        </el-button>
      </div>
    </div>

    <!-- 4. 素材呈现区域 (卡片网格 or 表格) -->
    <div class="assets-display-area">
      <!-- 空状态提示 -->
      <div v-if="filteredAssets.length === 0" class="empty-assets-card glass-panel">
        <SvgIcon name="SvgMediaPlayer" size="48" class="text-sub" />
        <h4 class="empty-title">当前分类【{{ currentCategoryName }}】× 分组【{{ currentGroupName }}】暂无素材</h4>
        <p class="empty-sub">点击下方按钮，文件将按【系统设置】中生效的存储策略自动落盘入库！</p>
        <el-button type="primary" size="small" @click="openUploadDialog">
          立即上传第一份素材
        </el-button>
      </div>

      <!-- A. 单列常规列表视图 -->
      <div v-else class="asset-list-panel glass-panel">
        <div class="asset-list-head">
          <span class="alh-title">素材列表</span>
          <span class="alh-count num-mono">共 {{ filteredAssets.length }} 项</span>
        </div>

        <div class="asset-table-head" role="row">
          <span class="ath-type">类型</span>
          <span class="ath-name">名称</span>
          <span class="ath-spec">时长 / 大小</span>
          <span class="ath-play">播放资源 / 预览</span>
          <span class="ath-actions">操作</span>
        </div>

        <div class="asset-list">
          <div v-for="asset in filteredAssets" :key="asset.id" class="asset-row"
            :class="{ 'is-active': isActiveTrack(asset) }">
            <!-- 类型 -->
            <div class="ar-type">
              <span class="type-badge" :class="asset.categoryCode">
                {{ (asset.fileType || 'file').toUpperCase() }}
              </span>
            </div>

            <!-- 名称 -->
            <div class="ar-main">
              <div class="ar-titles">
                <h4 class="asset-name" :title="asset.name">{{ asset.name }}</h4>
                <div class="tag-row">
                  <span class="pill-tag cat-pill">{{ getCategoryNameByCode(asset.categoryCode) }}</span>
                  <span class="pill-tag grp-pill">{{ getGroupNameByCode(asset.categoryCode, asset.groupCode) }}</span>
                </div>
              </div>
            </div>

            <!-- 时长 / 大小 -->
            <div class="ar-spec">
              <span v-if="asset.durationSec > 0" class="spec-chip num-mono">{{ asset.durationFormatted }}</span>
              <span class="spec-chip num-mono">{{ asset.fileSizeFormatted }}</span>
              <span v-if="asset.resolution" class="spec-chip spec-text">{{ asset.resolution }}</span>
            </div>

            <!-- 播放资源 / 预览：独立成列 -->
            <div class="ar-play">
              <el-button v-if="isPlayable(asset)" size="small" type="primary" class="btn-play-preview"
                @click="playResource(asset)">
                <span class="play-glyph">▶</span>
                播放 / 预览
              </el-button>
              <span v-else class="play-unavailable" title="该素材类型不支持在线播放，请下载后查看">—</span>
            </div>

            <!-- 操作列：下载 / 详情 / 删除 -->
            <div class="ar-actions">
              <el-button size="small" plain class="btn-asset-action" :loading="downloadingId === asset.id"
                @click="downloadAsset(asset)">
                ⤓ 下载
              </el-button>

              <el-button size="small" type="info" link @click="viewAssetDetail(asset)">
                详情
              </el-button>

              <el-button size="small" type="danger" link :disabled="asset.refCount > 0"
                :title="asset.refCount > 0 ? `当前被引用 ${asset.refCount} 次，已锁定` : '删除素材'"
                @click="handleDeleteAsset(asset)">
                {{ asset.refCount > 0 ? '已锁定' : '删除' }}
              </el-button>
            </div>
          </div>
        </div>
      </div>

    </div>

    <!-- ==================== 模态弹窗系统 ==================== -->

    <!-- 0. 音视频资源统一弹窗播放 (真实 HTML5 播放) -->
    <el-dialog v-model="playDialogVisible" :title="`播放资源：${playingAsset?.name || ''}`" width="min(900px, calc(100vw - 24px))" destroy-on-close
      @closed="handlePlayerClosed">
      <div class="player-box">
        <!-- 视频播放器 -->
        <video v-if="isVideoAsset(playingAsset)" ref="playerVideoEl" class="player-media player-video" controls
          preload="metadata" :src="playingAsset?.accessUrl || ''" @playing="handlePlayerPlaying"
          @waiting="handlePlayerWaiting" @ended="handlePlayerEnded" @error="handlePlayerError"></video>

        <!-- 音频播放器 -->
        <audio v-else ref="playerAudioEl" class="player-media player-audio" controls preload="metadata"
          :src="playingAsset?.accessUrl || ''" @playing="handlePlayerPlaying" @waiting="handlePlayerWaiting"
          @ended="handlePlayerEnded" @error="handlePlayerError"></audio>

        <!-- 播放状态与错误回执 -->
        <div class="player-status" :class="playerStatus.state">
          <span class="ps-text">{{ playerStatus.text }}</span>
          <span v-if="playerStatus.message" class="ps-msg">{{ playerStatus.message }}</span>
        </div>

        <!-- 资源信息 -->
        <div class="player-meta">
          <div class="pm-row">
            <span class="pm-k">资源分类:</span>
            <span class="pm-v">{{ getCategoryNameByCode(playingAsset?.categoryCode) }}</span>
          </div>
          <div class="pm-row">
            <span class="pm-k">业务分组:</span>
            <span class="pm-v">{{ getGroupNameByCode(playingAsset?.categoryCode, playingAsset?.groupCode) }}</span>
          </div>
          <div class="pm-row">
            <span class="pm-k">规格大小:</span>
            <span class="pm-v num-mono">{{ playingAsset?.fileSizeFormatted || '—' }}</span>
          </div>
          <div class="pm-row pm-row-url">
            <span class="pm-k">播放地址:</span>
            <span class="pm-v num-mono">{{ playingAsset?.accessUrl || '—' }}</span>
          </div>
        </div>

        <!-- 连播同组其他素材 -->
        <div class="player-options">
          <el-checkbox v-model="loopPlaylist">播放结束后连播同组其他素材</el-checkbox>
        </div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="playDialogVisible = false">关闭</el-button>
          <el-button type="info" link @click="copyAccessUrl(playingAsset)">复制链接</el-button>
          <el-button type="primary" @click="downloadAsset(playingAsset)">下载该资源</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 1. 素材上传入库对话框 (严格读取系统设置的存储驱动) -->
    <el-dialog v-model="uploadDialogVisible" title="上传新素材并落盘入库 (自动同步系统存储配置)" width="min(600px, calc(100vw - 24px))" destroy-on-close>
      <div class="upload-dialog-content">
        <el-form label-position="top" size="small" class="upload-form">
          <!-- 联动分类 -->
          <el-form-item label="所属资源分类 *" required>
            <el-select v-model="uploadForm.categoryCode" style="width: 100%;" @change="handleUploadCategoryChange">
              <el-option v-for="cat in categories" :key="cat.code" :label="cat.name" :value="cat.code" />
            </el-select>
          </el-form-item>

          <!-- 联动分组 (分组隶属于分类，仅列出所选分类下的分组) -->
          <el-form-item label="所属业务分组 *" required>
            <el-select v-model="uploadForm.groupCode" placeholder="请先选择分类..." style="width: 100%;">
              <el-option v-for="grp in uploadCategoryGroups" :key="grp.code" :label="grp.name" :value="grp.code" />
            </el-select>
            <div class="form-hint">
              分组隶属于「{{ getCategoryNameByCode(uploadForm.categoryCode) }}」分类，分类内分组编码唯一。
            </div>
          </el-form-item>

          <!-- 文件选取 -->
          <el-form-item label="选择素材文件 *" required>
            <div class="file-picker-box">
              <input type="file" ref="fileInputRef" class="hidden-file-input" @change="handleFileSelected" />
              <div class="picker-trigger" @click="$refs.fileInputRef?.click()">
                <SvgIcon name="SvgMediaPlayer" size="28" class="text-sub" />
                <span v-if="!selectedFile" class="picker-tip">点击浏览本地文件或拖拽至此处</span>
                <div v-else class="selected-file-meta">
                  <span class="sf-name font-bold">{{ selectedFile.name }}</span>
                  <span class="sf-size num-mono text-sub">({{ formatBytes(selectedFile.size) }})</span>
                </div>
              </div>
            </div>
          </el-form-item>

          <!-- 素材名称 -->
          <el-form-item label="素材显示名称 *" required>
            <el-input v-model="uploadForm.name" placeholder="例如: 2026 赛事仪式专用国歌 (军乐团完整版)" />
          </el-form-item>

          <!-- 规格参数：仅音视频需要，均由文件自动探测，用户不可填写 -->
          <div v-if="isMediaCategory(uploadForm.categoryCode)" class="form-row-two">
            <el-form-item label="时长 (自动探测)" style="flex: 1;">
              <div class="auto-field">
                <span class="af-value num-mono">
                  {{ detectedDuration > 0 ? formatDuration(detectedDuration) : '--:--' }}
                </span>
                <span class="af-hint">{{ detectStatus }}</span>
              </div>
            </el-form-item>
            <el-form-item label="采样率/分辨率规格 (自动探测)" style="flex: 1.5;">
              <div class="auto-field">
                <span class="af-value">{{ detectedResolution || '—' }}</span>
                <span class="af-hint">{{ detectStatus }}</span>
              </div>
            </el-form-item>
          </div>
          <div v-else class="form-hint">
            仅音频 / 视频素材需要时长与规格参数，选择文件后由系统自动探测，无需填写。
          </div>

          <!-- 备注说明 -->
          <el-form-item label="备注说明">
            <el-input v-model="uploadForm.remark" type="textarea" :rows="2" placeholder="填写素材版本来源、用途等备忘信息..." />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="uploadDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="isSubmitting" @click="submitUpload">
            确认存储入库
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 2. 分类管理对话框 (增减编辑分类) -->
    <el-dialog v-model="categoryDialogVisible" title="资源分类管理 (支持增减编辑)" width="min(580px, calc(100vw - 24px))" destroy-on-close>
      <div class="mgmt-dialog-content">
        <!-- 现有分类列表 -->
        <div class="mgmt-list">
          <div v-for="cat in categories" :key="cat.code" class="mgmt-item">
            <div class="mi-left">
              <span class="mi-code num-mono font-bold">[{{ cat.code }}]</span>
              <span class="mi-name">{{ cat.name }}</span>
              <span v-if="cat.isBuiltin" class="mi-builtin-tag">内置默认</span>
              <span class="mi-count num-mono">{{ getCategoryGroupCount(cat.code) }} 个分组 · {{ getCategoryCount(cat.code)
              }}
                个素材</span>
            </div>
            <div class="mi-right">
              <el-button size="small" type="primary" link @click="editCategory(cat)">
                编辑名称
              </el-button>
              <el-button size="small" type="danger" link @click="handleDeleteCategory(cat)">
                删除
              </el-button>
            </div>
          </div>
        </div>

        <el-divider style="margin: 16px 0;" />

        <!-- 添加新分类表单 -->
        <div class="mgmt-add-form">
          <h4 class="form-sub-title">+ 添加新资源分类</h4>
          <div class="add-row">
            <el-input v-model="newCategoryForm.code" placeholder="分类编码 (英文/数字, 如: animation)" size="small"
              style="width: 180px;" />
            <el-input v-model="newCategoryForm.name" placeholder="分类名称 (如: 动画/三维)" size="small" style="width: 180px;" />
            <el-button size="small" type="primary" @click="submitAddCategory">
              添加分类
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 3. 分组管理对话框 (按分类分节，级联删除) -->
    <el-dialog v-model="groupDialogVisible" title="业务分组管理 (分组隶属于分类 · 支持增减编辑)" width="min(720px, calc(100vw - 24px))" destroy-on-close>
      <div class="mgmt-dialog-content">
        <div class="mgmt-hint">
          分组隶属于分类，分类内分组编码唯一。删除分组会<strong>级联删除</strong>该分组下的全部素材。
        </div>

        <!-- 按分类分节展示现有分组 -->
        <div class="mgmt-list">
          <div v-for="cat in categories" :key="cat.code" class="mgmt-section">
            <div class="ms-header">
              <SvgIcon :name="cat.icon || 'SvgAppGrid'" size="18" />
              <span class="ms-title">{{ cat.name }}</span>
              <span class="ms-code num-mono">[{{ cat.code }}]</span>
              <span class="ms-count num-mono">{{ groupsOfCategory(cat.code).length }} 个分组</span>
            </div>

            <div v-if="groupsOfCategory(cat.code).length === 0" class="ms-empty">
              该分类下暂无分组，请从下方添加。
            </div>

            <div v-for="grp in groupsOfCategory(cat.code)" :key="`${cat.code}-${grp.code}`" class="mgmt-item">
              <div class="mi-left">
                <span class="mi-code num-mono font-bold">[{{ grp.code }}]</span>
                <span class="mi-name">{{ grp.name }}</span>
                <span v-if="grp.isBuiltin" class="mi-builtin-tag">内置默认</span>
                <span class="mi-count num-mono">{{ getGroupCount(cat.code, grp.code) }} 个素材</span>
              </div>
              <div class="mi-right">
                <el-button size="small" type="primary" link @click="editGroup(grp)">
                  编辑
                </el-button>
                <el-button size="small" type="danger" link @click="handleDeleteGroup(grp)">
                  删除
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <el-divider style="margin: 16px 0;" />

        <!-- 添加新分组表单 -->
        <div class="mgmt-add-form">
          <h4 class="form-sub-title">+ 添加新业务分组</h4>
          <div class="add-row">
            <el-select v-model="newGroupForm.categoryCode" placeholder="所属分类..." size="small" style="width: 160px;">
              <el-option v-for="cat in categories" :key="cat.code" :label="cat.name" :value="cat.code" />
            </el-select>
            <el-input v-model="newGroupForm.code" placeholder="分组编码 (英文, 如: sponsor)" size="small"
              style="width: 150px;" />
            <el-input v-model="newGroupForm.name" placeholder="分组名称 (如: 赞助商物料)" size="small" style="width: 150px;" />
            <el-input v-model="newGroupForm.desc" placeholder="业务描述说明" size="small" style="flex: 1;" />
            <el-button size="small" type="primary" @click="submitAddGroup">
              添加分组
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { mediaAssetService } from '@/services/mediaAssetService'

// 1. 基础状态
const categories = ref([])
const groups = ref([])
const allAssets = ref([])
const currentCategory = ref('ALL') // 'ALL' | code
const currentGroup = ref('ALL') // 'ALL' | code
const searchKeyword = ref('')

// 2. 真实播放状态（由 HTML5 媒体元素事件驱动，弹窗内播放）
const playerVideoEl = ref(null)
const playerAudioEl = ref(null)
const playDialogVisible = ref(false)
const playingAsset = ref(null)
const downloadingId = ref('')
const loopPlaylist = ref(false)
const playerStatus = ref({ state: 'idle', text: '待机中', message: '' })

// 媒体类型判定：优先按分类，其次按扩展名兜底
const AUDIO_EXTENSIONS = ['mp3', 'wav', 'aac', 'ogg', 'flac', 'm4a', 'wma', 'amr', 'ape']
const VIDEO_EXTENSIONS = ['mp4', 'mkv', 'mov', 'avi', 'flv', 'webm', 'm4v', 'ts', 'rmvb']

const isAudioAsset = (asset) => {
  if (!asset) return false
  const ext = (asset.fileType || '').toLowerCase()
  return asset.categoryCode === 'audio' || AUDIO_EXTENSIONS.includes(ext)
}

const isVideoAsset = (asset) => {
  if (!asset) return false
  const ext = (asset.fileType || '').toLowerCase()
  return asset.categoryCode === 'video' || VIDEO_EXTENSIONS.includes(ext)
}

const isPlayable = (asset) => isAudioAsset(asset) || isVideoAsset(asset)

// 正在弹窗播放的素材行高亮
const isActiveTrack = (asset) => playingAsset.value?.id === asset?.id

const driverLabel = (driver) => {
  const map = { LOCAL: '本地落盘', ALIYUN: '阿里云 OSS', TENCENT: '腾讯云 COS' }
  return map[driver] || driver || '未知驱动'
}

const MEDIA_ERROR_TEXT = {
  1: '播放被中止',
  2: '网络错误：无法连接媒体地址（资源不可达或被浏览器跨域策略拦截）',
  3: '解码错误：媒体文件已损坏或格式不受当前浏览器支持',
  4: '源不支持：媒体地址不存在、不可访问或格式无法解码'
}

// 加载核心数据
const reloadData = () => {
  categories.value = mediaAssetService.getCategories()
  groups.value = mediaAssetService.getGroups()
  allAssets.value = mediaAssetService.getAssets()

  // 若正在播放的素材已被删除，则同步关闭播放弹窗
  if (playingAsset.value?.id && !allAssets.value.some(a => a.id === playingAsset.value.id)) {
    playDialogVisible.value = false
    playingAsset.value = null
    playerStatus.value = { state: 'idle', text: '待机中', message: '' }
  }
}

// 统计
const totalAssetsCount = computed(() => allAssets.value.length)

// 当前分类下的分组（分组隶属于分类，先选分类才能选分组）
const currentCategoryGroups = computed(() => {
  if (currentCategory.value === 'ALL') return []
  return groups.value.filter(g => g.categoryCode === currentCategory.value)
})

const getCategoryCount = (code) => {
  return allAssets.value.filter(a => a.categoryCode === code).length
}

// 分组计数按 (分类, 分组) 二元统计
const getGroupCount = (categoryCode, groupCode) => {
  return allAssets.value.filter(a => a.categoryCode === categoryCode && a.groupCode === groupCode).length
}

// 某分类下的分组列表
const groupsOfCategory = (categoryCode) => {
  return groups.value.filter(g => g.categoryCode === categoryCode)
}

// 某分类下的分组数量
const getCategoryGroupCount = (categoryCode) => {
  return groups.value.filter(g => g.categoryCode === categoryCode).length
}

// 切换分类时重置分组选择（分组隶属于分类）
const handleCategoryChange = (code) => {
  currentCategory.value = code
  currentGroup.value = 'ALL'
}

const currentCategoryName = computed(() => {
  if (currentCategory.value === 'ALL') return '全部分类'
  const found = categories.value.find(c => c.code === currentCategory.value)
  return found ? found.name : currentCategory.value
})

const currentGroupName = computed(() => {
  if (currentGroup.value === 'ALL') return '全部分组'
  const found = groups.value.find(g => g.categoryCode === currentCategory.value && g.code === currentGroup.value)
  return found ? found.name : currentGroup.value
})

const getCategoryNameByCode = (code) => {
  const c = categories.value.find(item => item.code === code)
  return c ? c.name : code
}

const getGroupNameByCode = (categoryCode, groupCode) => {
  const g = groups.value.find(item => item.categoryCode === categoryCode && item.code === groupCode)
  return g ? g.name : groupCode
}

// 筛选后的列表
const filteredAssets = computed(() => {
  return mediaAssetService.getAssets({
    categoryCode: currentCategory.value,
    groupCode: currentGroup.value,
    keyword: searchKeyword.value
  })
})

// 格式化辅助
const formatBytes = (bytes) => {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

// ==================== 真实播放引擎 (HTML5 Media Element) ====================

// ==================== 真实播放引擎 (弹窗 HTML5 Media Element) ====================

// 当前活动的媒体元素（音频 / 视频）
const activePlayerEl = () => {
  if (!playingAsset.value) return null
  return isVideoAsset(playingAsset.value) ? playerVideoEl.value : playerAudioEl.value
}

// 播放请求序号：用于忽略「关闭弹窗 / 切换资源」造成的 AbortError
let playSeq = 0
let playTimeoutTimer = null

const clearPlayTimeout = () => {
  if (playTimeoutTimer) {
    clearTimeout(playTimeoutTimer)
    playTimeoutTimer = null
  }
}

// 资源地址不可达时 play() 会长期挂起，用超时兜底并给出明确提示
const startPlayTimeout = (seq) => {
  clearPlayTimeout()
  playTimeoutTimer = setTimeout(() => {
    playTimeoutTimer = null
    if (seq !== playSeq || !playDialogVisible.value) return
    const el = activePlayerEl()
    // 已经进入播放 / 已拿到足够数据 / 用户主动暂停则无需报错
    if (!el || el.readyState >= 3 || el.networkState !== 2 || el.paused) return
    el.pause()
    playerStatus.value = {
      state: 'error',
      text: '加载超时',
      message: `资源地址无法访问或响应超时，请检查存储服务是否启动、访问地址是否可直连｜播放地址：${playingAsset.value?.accessUrl || '—'}`
    }
    ElMessage.error('音频加载超时：资源地址无法访问，请检查存储服务与素材访问地址。')
  }, 8000)
}

// 统一播放入口：音视频均以弹窗方式真实播放
const playResource = async (asset) => {
  if (!asset) return
  if (!isPlayable(asset)) {
    ElMessage.info('该资源不是音视频格式，无法在页面内播放，请使用「下载」获取原始文件。')
    return
  }
  if (!asset.accessUrl) {
    ElMessage.warning('该素材尚未生成可访问地址，请检查存储配置或重新上传。')
    return
  }

  const seq = ++playSeq
  playingAsset.value = asset
  playerStatus.value = { state: 'loading', text: '加载中', message: '' }
  playDialogVisible.value = true

  await nextTick()
  const el = activePlayerEl()
  if (!el) return

  startPlayTimeout(seq)

  try {
    await el.play()
  } catch (err) {
    // 已被新的播放请求取代，或弹窗已关闭：属于主动取消，不当作播放失败
    if (seq !== playSeq || !playDialogVisible.value) return
    clearPlayTimeout()

    const errName = err?.name || 'UnknownError'
    if (errName === 'NotAllowedError') {
      // 浏览器自动播放策略拦截，可由用户点击播放器内播放键手动开始
      playerStatus.value = {
        state: 'blocked',
        text: '待播放',
        message: '浏览器阻止了自动播放，请点击播放器下方的播放键手动开始。'
      }
      ElMessage.warning('浏览器阻止了自动播放，请点击播放器下方的播放键手动开始。')
    } else {
      const reason = errName === 'AbortError'
        ? '播放被中断：资源加载超时或请求被取消，请重试'
        : (errName === 'NotSupportedError'
          ? MEDIA_ERROR_TEXT[4]
          : `媒体播放被拒绝（${errName}）`)
      playerStatus.value = {
        state: 'error',
        text: '播放失败',
        message: `${reason}｜播放地址：${asset.accessUrl}`
      }
      ElMessage.error(`播放失败：${reason}`)
    }
  }
}

// ---------- 播放器事件回调 ----------

const handlePlayerPlaying = () => {
  clearPlayTimeout()
  playerStatus.value = { state: 'playing', text: '播放中', message: '' }
}

const handlePlayerWaiting = () => {
  if (['error', 'blocked'].includes(playerStatus.value.state)) return
  playerStatus.value = { state: 'loading', text: '缓冲中', message: '' }
}

const handlePlayerError = () => {
  clearPlayTimeout()
  const el = activePlayerEl()
  const code = el?.error?.code
  const reason = MEDIA_ERROR_TEXT[code] || '未知媒体错误'
  // 初始加载失败由 play() 的 catch 统一提示，这里只处理播放过程中的中断，避免重复弹窗
  const shouldToast = playerStatus.value.state === 'playing'
  playerStatus.value = {
    state: 'error',
    text: '播放失败',
    message: `${reason}｜播放地址：${playingAsset.value?.accessUrl || '—'}`
  }
  if (shouldToast) ElMessage.error(`播放失败：${reason}`)
}

// 播放结束：可选连播同组其他素材
const handlePlayerEnded = async () => {
  clearPlayTimeout()
  if (!loopPlaylist.value) {
    playerStatus.value = { state: 'paused', text: '播放结束', message: '' }
    return
  }
  const next = getNextInGroup(playingAsset.value)
  if (!next) {
    playerStatus.value = { state: 'paused', text: '播放结束', message: '同组已无其他可连播素材。' }
    return
  }
  playingAsset.value = next
  playerStatus.value = { state: 'loading', text: '连播中', message: `正在播放：${next.name}` }
  await nextTick()
  activePlayerEl()?.play().catch(() => { })
}

// 同组（同一分类 + 同一分组）内可连播的下一个素材
const getNextInGroup = (asset) => {
  if (!asset) return null
  const siblings = allAssets.value.filter(
    a => a.categoryCode === asset.categoryCode && a.groupCode === asset.groupCode && isPlayable(a)
  )
  if (siblings.length <= 1) return null
  const idx = siblings.findIndex(a => a.id === asset.id)
  return siblings[(idx + 1) % siblings.length]
}

// 关闭弹窗：停止播放并释放资源
const handlePlayerClosed = () => {
  playSeq += 1
  clearPlayTimeout()
  const el = activePlayerEl()
  if (el) {
    el.pause()
    el.removeAttribute('src')
    el.load()
  }
  playingAsset.value = null
  playerStatus.value = { state: 'idle', text: '待机中', message: '' }
}

// ---------- 下载 ----------

const downloadAsset = async (asset) => {
  if (!asset) return
  if (!asset.accessUrl) {
    ElMessage.warning('该素材尚未生成可下载地址，请先确认存储配置或重新上传。')
    return
  }

  const fileName = `${asset.name}.${asset.fileType || 'bin'}`
  downloadingId.value = asset.id

  // 媒体地址可能不可达，设置超时避免长时间无反馈
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 10000)

  try {
    const res = await fetch(asset.accessUrl, { mode: 'cors', signal: controller.signal })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const blob = await res.blob()
    const href = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = href
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(href)
    ElMessage.success(`已开始下载：${fileName}`)
  } catch (err) {
    const reason = err?.name === 'AbortError'
      ? '请求超时（10 秒内无响应）'
      : (err?.message || '未知原因')
    ElMessage({
      type: 'warning',
      duration: 6000,
      showClose: true,
      message: `直连下载未成功（${reason}）。浏览器跨域安全策略禁止直接拉取二进制文件，请使用「详情 → 复制访问地址」获取地址后手动下载。`
    })
  } finally {
    clearTimeout(timer)
    downloadingId.value = ''
  }
}

// 复制外链
const copyAccessUrl = (asset) => {
  if (!asset?.accessUrl) {
    ElMessage.warning('该素材尚未生成访问地址。')
    return
  }
  if (navigator.clipboard) {
    navigator.clipboard.writeText(asset.accessUrl).then(
      () => ElMessage.success(`已复制资源外链：${asset.accessUrl}`),
      () => ElMessage.info(`资源外链：${asset.accessUrl}`)
    )
  } else {
    ElMessage.info(`资源外链：${asset.accessUrl}`)
  }
}

// HTML 转义，避免素材名称/备注等用户输入注入弹窗 DOM
const escapeHtml = (value) => {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

// 素材详情（不展示存储路径）
const viewAssetDetail = (asset) => {
  if (!asset) return
  const rows = [
    ['素材名称', asset.name],
    ['文件类型', (asset.fileType || 'file').toUpperCase()],
    ['规格大小', asset.fileSizeFormatted],
    ['时长', asset.durationSec > 0 ? `${asset.durationFormatted} (${asset.durationSec}s)` : '—'],
    ['参数描述', asset.resolution || '—'],
    ['资源分类', getCategoryNameByCode(asset.categoryCode)],
    ['业务分组', getGroupNameByCode(asset.categoryCode, asset.groupCode)],
    ['存储驱动', driverLabel(asset.storageDriver)],
    ['存储桶/目录', asset.storageBucket || '—'],
    ['访问地址', asset.accessUrl || '—'],
    ['上传时间', asset.createdAt || '—']
  ]
  if (asset.remark) rows.push(['备注说明', asset.remark])

  const html = rows.map(([label, value]) => `
    <p style="margin:0 0 8px 0;">
      <strong style="display:inline-block;min-width:88px;color:#1E293B;">${escapeHtml(label)}：</strong>
      <span style="color:#334155;word-break:break-all;">${escapeHtml(value)}</span>
    </p>`).join('')

  ElMessageBox.confirm(
    `<div style="font-size:14px;line-height:1.7;text-align:left;">${html}</div>`,
    '素材详情',
    {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '复制访问地址',
      cancelButtonText: '关闭'
    }
  ).then(() => {
    copyAccessUrl(asset)
  }).catch(() => { })
}

// 删除素材
const handleDeleteAsset = (asset) => {
  ElMessageBox.confirm(
    `确定要从素材库中彻底删除【${asset.name}】吗？删除后将同时清理其在【${asset.storageDriver}】的存储引用记录！`,
    '删除素材安全确认',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    const res = mediaAssetService.deleteAsset(asset.id)
    if (res.success) {
      ElMessage.success(res.message)
      reloadData()
    } else {
      ElMessage.error(res.message)
    }
  }).catch(() => { })
}

// ==================== 上传逻辑 ====================
const uploadDialogVisible = ref(false)
const isSubmitting = ref(false)
const selectedFile = ref(null)

// 自动探测结果（时长 / 采样率·分辨率），用户不可填写
const detectedDuration = ref(0)
const detectedResolution = ref('')
const detectStatus = ref('请选择素材文件')

const uploadForm = ref({
  name: '',
  categoryCode: 'audio',
  groupCode: 'anthem',
  durationSec: 0,
  resolution: '',
  remark: ''
})

// 仅音频 / 视频需要时长与规格参数
const isMediaCategory = (code) => code === 'audio' || code === 'video'

// 格式化时长 (秒 -> mm:ss)
const formatDuration = (sec) => {
  const m = Math.floor(sec / 60).toString().padStart(2, '0')
  const s = Math.floor(sec % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

// 上传表单当前分类下的可选分组
const uploadCategoryGroups = computed(() => {
  if (!uploadForm.value.categoryCode) return []
  return groups.value.filter(g => g.categoryCode === uploadForm.value.categoryCode)
})

// 依据分类挑一个默认分组（优先当前筛选的分组，否则取该分类第一个）
const pickDefaultGroup = (categoryCode) => {
  const list = groups.value.filter(g => g.categoryCode === categoryCode)
  if (!list.length) return ''
  const preferred = list.find(g => g.code === currentGroup.value)
  return preferred ? preferred.code : list[0].code
}

/**
 * 自动探测音视频文件的时长与采样率/分辨率
 * - 视频：<video> metadata -> duration + videoWidth×videoHeight
 * - 音频：AudioContext.decodeAudioData -> duration + sampleRate + 声道数
 *          （解码失败时回退到 <audio> metadata 只取时长）
 */
const detectMediaMeta = async (file) => {
  const ext = (file.name.split('.').pop() || '').toLowerCase()
  const url = URL.createObjectURL(file)

  try {
    if (VIDEO_EXTENSIONS.includes(ext)) {
      const v = document.createElement('video')
      v.preload = 'metadata'
      v.muted = true
      v.src = url
      await new Promise((resolve, reject) => {
        v.onloadedmetadata = resolve
        v.onerror = () => reject(new Error('无法读取视频元数据'))
      })
      detectedDuration.value = Number.isFinite(v.duration) ? Math.round(v.duration) : 0
      detectedResolution.value = v.videoWidth && v.videoHeight
        ? `${v.videoWidth}×${v.videoHeight}`
        : ''
      v.removeAttribute('src')
      v.load()
      return
    }

    // 音频：优先用 Web Audio 解码，可同时拿到采样率与声道数
    const AudioCtx = window.AudioContext || window.webkitAudioContext
    if (AudioCtx) {
      const ctx = new AudioCtx()
      try {
        const buffer = await ctx.decodeAudioData(await file.arrayBuffer())
        detectedDuration.value = Math.round(buffer.duration)
        const ch = buffer.numberOfChannels
        detectedResolution.value =
          `${(buffer.sampleRate / 1000).toFixed(1)}kHz ${ch === 1 ? '单声道' : ch === 2 ? '立体声' : `${ch} 声道`}`
        return
      } catch (e) {
        // 解码失败，继续走 <audio> 回退
      } finally {
        ctx.close().catch(() => { })
      }
    }

    const a = document.createElement('audio')
    a.preload = 'metadata'
    a.src = url
    await new Promise((resolve, reject) => {
      a.onloadedmetadata = resolve
      a.onerror = () => reject(new Error('无法读取音频元数据'))
    })
    detectedDuration.value = Number.isFinite(a.duration) ? Math.round(a.duration) : 0
    if (!detectedResolution.value) detectedResolution.value = '未知采样率'
    a.removeAttribute('src')
    a.load()
  } finally {
    URL.revokeObjectURL(url)
  }
}

// 执行探测并回填表单
const runDetect = async (file) => {
  detectedDuration.value = 0
  detectedResolution.value = ''
  detectStatus.value = '检测中…'
  uploadForm.value.durationSec = 0
  uploadForm.value.resolution = ''

  try {
    await detectMediaMeta(file)
    uploadForm.value.durationSec = detectedDuration.value
    uploadForm.value.resolution = detectedResolution.value
    detectStatus.value = '已从文件自动读取'
  } catch (err) {
    detectStatus.value = '未能自动读取该文件元数据'
    ElMessage.warning('未能自动读取该文件的时长与规格，请确认文件可被浏览器正常解码。')
  }
}

// 上传弹窗中切换分类时，分组必须重置为新分类下的分组
const handleUploadCategoryChange = async (code) => {
  const changed = uploadForm.value.categoryCode !== code
  uploadForm.value.categoryCode = code
  uploadForm.value.groupCode = pickDefaultGroup(code)

  // 分类切换后重新探测（音视频才有时长与规格）
  if (changed && selectedFile.value) {
    if (isMediaCategory(code)) {
      await runDetect(selectedFile.value)
    } else {
      detectedDuration.value = 0
      detectedResolution.value = ''
      detectStatus.value = '不适用'
      uploadForm.value.durationSec = 0
      uploadForm.value.resolution = '标准文档规格'
    }
  }
}

const openUploadDialog = () => {
  const categoryCode = currentCategory.value !== 'ALL' ? currentCategory.value : 'audio'
  uploadForm.value = {
    name: '',
    categoryCode,
    groupCode: currentCategory.value !== 'ALL' && currentGroup.value !== 'ALL'
      ? currentGroup.value
      : pickDefaultGroup(categoryCode),
    durationSec: 0,
    resolution: '',
    remark: ''
  }
  selectedFile.value = null
  detectedDuration.value = 0
  detectedResolution.value = ''
  detectStatus.value = '请选择素材文件'
  uploadDialogVisible.value = true
}

const handleFileSelected = async (e) => {
  const file = e.target.files?.[0]
  if (!file) return

  selectedFile.value = file
  // 自动回填文件名
  if (!uploadForm.value.name) {
    const baseName = file.name.substring(0, file.name.lastIndexOf('.')) || file.name
    uploadForm.value.name = baseName
  }

  // 依据扩展名推断分类（分组随之重置）
  const ext = file.name.split('.').pop()?.toLowerCase() || ''
  let guessed = uploadForm.value.categoryCode
  if (AUDIO_EXTENSIONS.includes(ext)) guessed = 'audio'
  else if (VIDEO_EXTENSIONS.includes(ext)) guessed = 'video'
  else if (['pdf', 'doc', 'docx', 'svg', 'png', 'jpg', 'txt', 'xls', 'xlsx'].includes(ext)) guessed = 'document'

  uploadForm.value.categoryCode = guessed
  uploadForm.value.groupCode = pickDefaultGroup(guessed)

  // 音视频：自动探测时长与规格；其他类型不需要
  if (isMediaCategory(guessed)) {
    await runDetect(file)
  } else {
    detectedDuration.value = 0
    detectedResolution.value = ''
    detectStatus.value = '不适用（该分类无需时长与规格）'
    uploadForm.value.durationSec = 0
    uploadForm.value.resolution = '标准文档规格'
  }
}

const submitUpload = () => {
  if (!uploadForm.value.name.trim()) {
    return ElMessage.warning('请输入素材资源名称！')
  }
  isSubmitting.value = true

  const ext = selectedFile.value
    ? selectedFile.value.name.split('.').pop()
    : (uploadForm.value.categoryCode === 'audio' ? 'mp3' : (uploadForm.value.categoryCode === 'video' ? 'mp4' : 'pdf'))

  const res = mediaAssetService.uploadAsset({
    name: uploadForm.value.name,
    categoryCode: uploadForm.value.categoryCode,
    groupCode: uploadForm.value.groupCode,
    fileName: selectedFile.value?.name || `${uploadForm.value.name}.${ext}`,
    fileSize: selectedFile.value?.size || 1024 * 1024 * 4,
    fileType: ext,
    durationSec: uploadForm.value.durationSec,
    resolution: uploadForm.value.resolution,
    remark: uploadForm.value.remark
  })

  isSubmitting.value = false
  if (res.success) {
    ElMessage.success(res.message)
    uploadDialogVisible.value = false
    reloadData()
  } else {
    ElMessage.error(res.message)
  }
}

// ==================== 分类管理 ====================
const categoryDialogVisible = ref(false)
const newCategoryForm = ref({ code: '', name: '' })

const openCategoryManageDialog = () => {
  newCategoryForm.value = { code: '', name: '' }
  categoryDialogVisible.value = true
}

const submitAddCategory = () => {
  const res = mediaAssetService.addCategory({
    code: newCategoryForm.value.code,
    name: newCategoryForm.value.name
  })
  if (res.success) {
    ElMessage.success(`新分类【${newCategoryForm.value.name}】添加成功！`)
    newCategoryForm.value = { code: '', name: '' }
    reloadData()
  } else {
    ElMessage.error(res.message)
  }
}

const editCategory = (cat) => {
  ElMessageBox.prompt('请输入新的分类显示名称：', '编辑分类', {
    confirmButtonText: '保存',
    cancelButtonText: '取消',
    inputValue: cat.name
  }).then(({ value }) => {
    if (value && value.trim()) {
      mediaAssetService.updateCategory(cat.code, { name: value.trim() })
      ElMessage.success('分类名称更新成功！')
      reloadData()
    }
  }).catch(() => { })
}

// ==================== 级联删除：两步二次确认 ====================

// 生成「将被删除的素材」清单 HTML（被引用素材标红警示）
const buildCascadeAssetList = (assets) => {
  if (!assets.length) {
    return '<p style="margin:0;color:#64748B;">该范围内当前没有素材资源。</p>'
  }
  const rows = assets.map(a => {
    const locked = (a.refCount || 0) > 0
    return `<li style="margin:0 0 6px 0;">
      <span style="color:#1E293B;">${escapeHtml(a.name)}</span>
      <span style="color:#64748B;font-size:13px;">（${escapeHtml((a.fileType || 'file').toUpperCase())} · ${escapeHtml(a.fileSizeFormatted || '-')}）</span>
      ${locked ? `<span style="color:#DC2626;font-weight:700;"> ⚠ 已被升旗/推屏引用 ${a.refCount} 次，删除后相关编排将失效</span>` : ''}
    </li>`
  }).join('')
  return `<ul style="margin:8px 0 0 0;padding-left:18px;max-height:220px;overflow:auto;">${rows}</ul>`
}

const handleDeleteCategory = (cat) => {
  const preview = mediaAssetService.previewDeleteCategory(cat.code)
  if (!preview.success) {
    ElMessage.error(preview.message)
    return
  }

  // 第一次确认：说明影响范围
  ElMessageBox.confirm(
    `确定要删除分类【${cat.name}】吗？<br/>` +
    `该分类下有 <strong>${preview.groupCount}</strong> 个业务分组、<strong>${preview.assetCount}</strong> 个素材资源，` +
    `将<strong style="color:#DC2626;">随分类一并永久删除</strong>。`,
    '删除分类 · 第一次确认',
    {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '继续删除',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    // 第二次确认：逐条列出将被删除的分组与素材
    const groupList = preview.groups.length
      ? `<p style="margin:8px 0 0 0;">将同时删除以下 <strong>${preview.groupCount}</strong> 个分组：</p>
         <p style="margin:4px 0 0 0;color:#64748B;">${preview.groups.map(g => escapeHtml(g.name)).join('、')}</p>`
      : '<p style="margin:8px 0 0 0;color:#64748B;">该分类下没有业务分组。</p>'

    const referencedTip = preview.referencedCount > 0
      ? `<p style="margin:10px 0 0 0;color:#DC2626;font-weight:700;">⚠ 其中 ${preview.referencedCount} 个素材正被升旗仪式/大屏推屏引用，删除后相关编排将立即失效！</p>`
      : ''

    ElMessageBox.confirm(
      `<div style="text-align:left;">
        <p style="margin:0;font-weight:700;color:#DC2626;">此操作不可恢复，请再次确认。</p>
        ${groupList}
        <p style="margin:8px 0 0 0;">以下 <strong>${preview.assetCount}</strong> 个素材将被永久删除：</p>
        ${buildCascadeAssetList(preview.assets)}
        ${referencedTip}
      </div>`,
      '删除分类 · 最终确认',
      {
        dangerouslyUseHTMLString: true,
        confirmButtonText: '确认永久删除',
        cancelButtonText: '我再想想',
        type: 'error',
        confirmButtonClass: 'el-button--danger'
      }
    ).then(() => {
      const res = mediaAssetService.deleteCategory(cat.code, true)
      if (res.success) {
        ElMessage.success(res.message)
        if (currentCategory.value === cat.code) {
          currentCategory.value = 'ALL'
          currentGroup.value = 'ALL'
        }
        reloadData()
      } else {
        ElMessage.error(res.message)
      }
    }).catch(() => { })
  }).catch(() => { })
}

// ==================== 分组管理 ====================
const groupDialogVisible = ref(false)
const newGroupForm = ref({ categoryCode: '', code: '', name: '', desc: '' })

const openGroupManageDialog = () => {
  newGroupForm.value = {
    categoryCode: currentCategory.value !== 'ALL' ? currentCategory.value : (categories.value[0]?.code || ''),
    code: '',
    name: '',
    desc: ''
  }
  groupDialogVisible.value = true
}

const submitAddGroup = () => {
  const res = mediaAssetService.addGroup({
    categoryCode: newGroupForm.value.categoryCode,
    code: newGroupForm.value.code,
    name: newGroupForm.value.name,
    desc: newGroupForm.value.desc
  })
  if (res.success) {
    ElMessage.success(`新分组【${newGroupForm.value.name}】已添加到分类【${getCategoryNameByCode(newGroupForm.value.categoryCode)}】下！`)
    newGroupForm.value = { ...newGroupForm.value, code: '', name: '', desc: '' }
    reloadData()
  } else {
    ElMessage.error(res.message)
  }
}

const editGroup = (grp) => {
  ElMessageBox.prompt('请输入新的业务分组名称：', '编辑业务分组', {
    confirmButtonText: '保存',
    cancelButtonText: '取消',
    inputValue: grp.name
  }).then(({ value }) => {
    if (value && value.trim()) {
      mediaAssetService.updateGroup(grp.categoryCode, grp.code, { name: value.trim() })
      ElMessage.success('分组更新成功！')
      reloadData()
    }
  }).catch(() => { })
}

const handleDeleteGroup = (grp) => {
  const preview = mediaAssetService.previewDeleteGroup(grp.categoryCode, grp.code)
  if (!preview.success) {
    ElMessage.error(preview.message)
    return
  }
  const catName = getCategoryNameByCode(grp.categoryCode)

  // 第一次确认：说明影响范围
  ElMessageBox.confirm(
    `确定要删除分组【${grp.name}】（所属分类：${catName}）吗？<br/>` +
    `该分组下的 <strong style="color:#DC2626;">${preview.assetCount}</strong> 个素材资源将一并永久删除。`,
    '删除分组 · 第一次确认',
    {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '继续删除',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    // 第二次确认：逐条列出将被删除的素材
    const referencedTip = preview.referencedCount > 0
      ? `<p style="margin:10px 0 0 0;color:#DC2626;font-weight:700;">⚠ 其中 ${preview.referencedCount} 个素材正被升旗仪式/大屏推屏引用，删除后相关编排将立即失效！</p>`
      : ''

    ElMessageBox.confirm(
      `<div style="text-align:left;">
        <p style="margin:0;font-weight:700;color:#DC2626;">此操作不可恢复，请再次确认。</p>
        <p style="margin:8px 0 0 0;">以下 <strong>${preview.assetCount}</strong> 个素材将被永久删除：</p>
        ${buildCascadeAssetList(preview.assets)}
        ${referencedTip}
      </div>`,
      '删除分组 · 最终确认',
      {
        dangerouslyUseHTMLString: true,
        confirmButtonText: '确认永久删除',
        cancelButtonText: '我再想想',
        type: 'error',
        confirmButtonClass: 'el-button--danger'
      }
    ).then(() => {
      const res = mediaAssetService.deleteGroup(grp.categoryCode, grp.code, true)
      if (res.success) {
        ElMessage.success(res.message)
        if (currentGroup.value === grp.code) currentGroup.value = 'ALL'
        reloadData()
      } else {
        ElMessage.error(res.message)
      }
    }).catch(() => { })
  }).catch(() => { })
}

onMounted(() => {
  reloadData()
  if (typeof window !== 'undefined') {
    window.addEventListener('ibms-media-assets-changed', reloadData)
  }
})

onUnmounted(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('ibms-media-assets-changed', reloadData)
  }
  // 释放真实媒体资源，避免离开页面后仍在后台播放
  const el = activePlayerEl()
  if (el) {
    el.pause()
    el.removeAttribute('src')
    el.load()
  }
})
</script>

<style scoped>
.media-console-workspace {
  display: flex;
  flex-direction: column;
  gap: 14px;
  animation: fadeIn 0.3s ease-out;
}

/* 2. 双维度矩阵面板 */
.filter-matrix-panel {
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  border-radius: var(--radius-md);
  padding: 12px 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-shadow: var(--shadow-card);
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.row-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 700;
  color: var(--do-text-secondary);
  min-width: 108px;
}

.chips-container {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  flex: 1;
}

.matrix-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  min-height: 42px;
  border-radius: 8px;
  background: rgba(var(--th-shadow-rgb), 0.04);
  border: 1px solid var(--do-border);
  font-size: 16px;
  color: var(--do-text-primary);
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.matrix-chip:hover {
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
  background: rgba(var(--th-accent-rgb), 0.06);
}

.matrix-chip.active {
  background: rgba(var(--th-accent-rgb), 0.16);
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
}

.chip-count {
  font-size: 13px;
  font-weight: 700;
  background: rgba(var(--th-shadow-rgb), 0.08);
  padding: 2px 9px;
  border-radius: 10px;
  color: var(--do-text-secondary);
}

.matrix-chip.active .chip-count {
  background: var(--do-gold);
  color: #FFFFFF;
}

.group-chip .chip-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--do-gold);
  flex-shrink: 0;
}

/* 未选分类时的分组行占位 */
.group-row.disabled .row-label {
  opacity: 0.55;
}

.placeholder-chip {
  cursor: default;
  opacity: 0.6;
  border-style: dashed;
  background: transparent;
}

.placeholder-chip:hover {
  border-color: var(--do-border);
  color: var(--do-text-primary);
  background: transparent;
}

/* 3. 工具条 */
.assets-toolbar {
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  border-radius: var(--radius-md);
  padding: 10px 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px 16px;
}

.toolbar-left {
  flex: 0 0 auto;
  white-space: nowrap;
}

.filter-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  flex-wrap: nowrap;
  white-space: nowrap;
}

.fs-text {
  color: var(--do-text-secondary);
}

/* 当前检索范围标签：用原生元素实现，字号/字重完全可控 */
.fs-tag {
  font-size: 14px;
  line-height: 1.4;
  padding: 3px 10px;
  border-radius: 5px;
  white-space: nowrap;
  border: 1px solid transparent;
}

.fs-tag-primary {
  color: #2563eb;
  background: #eff6ff;
  border-color: #93c5fd;
}

.fs-tag-warning {
  color: #d97706;
  background: #fffbeb;
  border-color: #fcd34d;
}

.fs-divider {
  color: var(--do-text-secondary);
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 0 0 auto;
  padding: 8px 10px;
}

/* 搜索框尺寸优化：宽度拓宽至 320px，高度统一为 30px 与按钮对齐 */
.toolbar-search-input {
  width: 320px;
  height: 30px;
  --el-input-height: 30px;
}

.toolbar-search-input :deep(.el-input__wrapper) {
  height: 30px;
}

/* 统一工具栏右侧所有按钮高度，保持与上传按钮及搜索框一致 (30px) */
.toolbar-right .el-button {
  height: 30px;
}

/* Element Plus 默认给相邻按钮加 margin-left，与 flex gap 叠加会让工具栏超宽换行 */
.toolbar-right .el-button+.el-button {
  margin-left: 0;
}

.btn-main-upload {
  font-weight: 700;
  padding: 6px 10px;
  height: 30px;
}

/* 4. 素材呈现区域 */
.empty-assets-card {
  padding: 40px 20px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  background: var(--do-bg-card);
  border: 1px dashed var(--do-border);
  border-radius: var(--radius-md);
}

.empty-title {
  margin: 0;
  font-size: 16px;
  color: var(--do-text-primary);
}

.empty-sub {
  margin: 0;
  font-size: 14px;
  color: var(--do-text-secondary);
  max-width: 560px;
}

/* ===== 单列常规列表 (非卡片) ===== */
.asset-list-panel {
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.asset-list-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 18px;
  border-bottom: 1px solid var(--do-border);
  background: rgba(var(--th-shadow-rgb), 0.03);
}

.alh-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.alh-count {
  font-size: 13px;
  font-weight: 700;
  color: var(--do-gold-deep);
}

.asset-list {
  display: flex;
  flex-direction: column;
}

.asset-table-head,
.asset-row {
  display: grid;
  grid-template-columns: 86px minmax(240px, 1fr) minmax(150px, 200px) minmax(132px, 156px) minmax(210px, 260px);
  align-items: center;
  gap: 14px;
  padding: 0 18px;
}

.asset-table-head {
  min-height: 40px;
  color: var(--do-text-secondary);
  background: var(--do-bg-sunken);
  border-bottom: 1px solid var(--do-border);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.asset-table-head > span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ath-actions {
  text-align: right;
}

.asset-row {
  padding-top: 14px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--do-border-light, var(--do-border));
  transition: background 0.2s ease;
}

.asset-row:nth-child(even) {
  background: rgba(var(--th-shadow-rgb), 0.018);
}

.ar-type {
  display: flex;
  align-items: center;
}

.asset-row:last-child {
  border-bottom: none;
}

.asset-row:hover {
  background: rgba(var(--th-accent-rgb), 0.04);
}

.asset-row.is-active {
  background: rgba(16, 185, 129, 0.06);
  box-shadow: inset 3px 0 0 var(--do-success);
}

.ar-main {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.ar-titles {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.type-badge {
  font-size: 13px;
  font-weight: 800;
  padding: 5px 10px;
  border-radius: 5px;
  letter-spacing: 0.5px;
  color: #FFFFFF;
  background: #64748B;
  flex-shrink: 0;
}

.type-badge.audio {
  background: #3b82f6;
}

.type-badge.video {
  background: #10b981;
}

.type-badge.document {
  background: #f59e0b;
}

.type-badge.other {
  background: #6b7280;
}

.asset-name {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--do-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tag-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pill-tag {
  font-size: 13px;
  padding: 2px 9px;
  border-radius: 5px;
  font-weight: 600;
  white-space: nowrap;
}

.cat-pill {
  background: rgba(59, 130, 246, 0.1);
  color: #2563eb;
}

.grp-pill {
  background: rgba(245, 158, 11, 0.12);
  color: #d97706;
}

/* 规格参数列：不允许被压缩挤压，保证文字完整可读 */
.ar-spec {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex-wrap: wrap;
}

.spec-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 28px;
  box-sizing: border-box;
  font-size: 13px;
  color: var(--do-text-secondary);
  background: var(--do-bg-sunken);
  border: 1px solid var(--do-border-light, var(--do-border));
  border-radius: 5px;
  padding: 0 10px;
  white-space: nowrap;
}

.spec-chip.num-mono {
  color: var(--do-text-primary);
  font-weight: 700;
}

.spec-text {
  max-width: 170px;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 播放资源 / 预览列 */
.ar-play {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  min-width: 0;
}

.btn-play-preview {
  height: 28px;
  padding: 0 12px;
  font-size: 13px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  box-sizing: border-box;
  font-weight: 600;
}

.play-glyph {
  font-size: 11px;
  line-height: 1;
  transform: translateY(-0.5px);
}

.play-unavailable {
  color: var(--do-text-placeholder);
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.08em;
  user-select: none;
}

/* 操作按钮列 */
.ar-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}

/* 播放/下载按钮高度与 class="spec-chip num-mono" 完全一致 (28px) */
.ar-play .btn-play-preview,
.ar-actions .btn-asset-action,
.ar-actions .el-button:not(.is-link) {
  height: 28px;
  padding: 0 12px;
  font-size: 13px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.file-picker-box {
  width: 100%;
}

.hidden-file-input {
  display: none;
}

.picker-trigger {
  border: 1px dashed var(--do-border);
  border-radius: 6px;
  padding: 16px;
  text-align: center;
  background: var(--do-bg-sunken);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
}

.picker-trigger:hover {
  border-color: var(--do-gold);
  background: rgba(var(--th-accent-rgb), 0.05);
}

.picker-tip {
  font-size: 14px;
  color: var(--do-text-secondary);
}

.selected-file-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--do-text-primary);
}

.form-row-two {
  display: flex;
  gap: 12px;
}

.form-hint {
  font-size: 13px;
  line-height: 1.6;
  color: var(--do-text-secondary);
  margin-top: 4px;
}

/* 自动探测字段（只读，不可填写） */
.auto-field {
  display: flex;
  align-items: baseline;
  gap: 10px;
  width: 100%;
  min-height: 32px;
  padding: 0 11px;
  border: 1px solid var(--do-border);
  border-radius: var(--radius-sm, 4px);
  background: var(--do-bg-sunken);
}

.af-value {
  font-size: 14px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.af-hint {
  font-size: 13px;
  color: var(--do-text-secondary);
  margin-left: auto;
  white-space: nowrap;
}

/* 分类/分组管理对话框列表 */
.mgmt-dialog-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mgmt-hint {
  font-size: 13px;
  line-height: 1.6;
  color: var(--do-text-secondary);
  background: var(--do-bg-sunken);
  border: 1px solid var(--do-border);
  border-radius: 6px;
  padding: 8px 12px;
}

.mgmt-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-height: 340px;
  overflow-y: auto;
}

/* 分组按分类分节 */
.mgmt-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ms-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  color: var(--do-text-primary);
  padding-bottom: 6px;
  border-bottom: 1px solid var(--do-border);
}

.ms-title {
  font-size: 15px;
}

.ms-code {
  font-size: 13px;
  color: var(--do-gold-deep);
  font-weight: 600;
}

.ms-count {
  font-size: 13px;
  color: var(--do-text-secondary);
  font-weight: 600;
  margin-left: auto;
}

.ms-empty {
  font-size: 13px;
  color: var(--do-text-secondary);
  padding: 8px 12px;
  background: var(--do-bg-sunken);
  border: 1px dashed var(--do-border);
  border-radius: 6px;
}

.mgmt-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: var(--do-bg-sunken);
  border: 1px solid var(--do-border);
  border-radius: 6px;
}

.mi-left {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}

.mi-code {
  color: var(--do-gold-deep);
}

.mi-name {
  font-weight: 700;
  color: var(--do-text-primary);
}

.mi-builtin-tag {
  font-size: 13px;
  background: rgba(var(--th-shadow-rgb), 0.08);
  padding: 2px 8px;
  border-radius: 4px;
  color: var(--do-text-secondary);
}

.mi-count {
  font-size: 13px;
  color: var(--do-text-secondary);
}

.mgmt-add-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.form-sub-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.add-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ===== 真实播放器相关 ===== */
/* ===== 弹窗内真实播放器 ===== */
.player-box {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.player-media {
  width: 100%;
  border-radius: 8px;
  outline: none;
}

.player-video {
  max-height: 520px;
  background: #0F172A;
  border: 1px solid var(--do-border);
}

.player-audio {
  background: var(--do-bg-sunken);
  border: 1px solid var(--do-border);
  padding: 8px;
}

/* 播放状态与错误回执 */
.player-status {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 13px;
  line-height: 1.6;
  padding: 8px 12px;
  border-radius: 6px;
  background: var(--do-bg-sunken);
  border: 1px solid var(--do-border);
  color: var(--do-text-secondary);
}

.player-status .ps-text {
  font-weight: 700;
  white-space: nowrap;
}

.player-status .ps-msg {
  word-break: break-all;
}

.player-status.playing {
  color: var(--do-success);
  background: rgba(16, 185, 129, 0.08);
  border-color: rgba(16, 185, 129, 0.28);
}

.player-status.loading {
  color: #b45309;
  background: rgba(245, 158, 11, 0.08);
  border-color: rgba(245, 158, 11, 0.3);
}

.player-status.blocked {
  color: #b45309;
  background: rgba(245, 158, 11, 0.08);
  border-color: rgba(245, 158, 11, 0.3);
}

.player-status.error {
  color: var(--do-danger);
  background: rgba(220, 38, 38, 0.07);
  border-color: rgba(220, 38, 38, 0.22);
}

/* 资源信息 */
.player-meta {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px 16px;
  padding: 10px 12px;
  background: var(--do-bg-sunken);
  border: 1px solid var(--do-border);
  border-radius: 6px;
}

.pm-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
  font-size: 13px;
  min-width: 0;
}

.pm-row-url {
  grid-column: 1 / -1;
}

.pm-k {
  color: var(--do-text-secondary);
  white-space: nowrap;
}

.pm-v {
  color: var(--do-text-primary);
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.player-options {
  display: flex;
  align-items: center;
}

/* ===== 设计系统中不存在的工具类：本文件内补齐 ===== */
.font-bold {
  font-weight: 700;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(4px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 1100px) {
  .player-meta {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

/* ============================================================================
 * 统一控制台视觉与响应式增强
 * 对齐“大屏调度”和“计时计分”页面，保留素材服务与全部操作入口
 * ============================================================================ */
.media-console-workspace {
  width: 100%;
  min-width: 0;
  color: var(--do-text-primary);
}

.glass-panel {
  border-radius: 10px;
  box-shadow: var(--shadow-sm, var(--shadow-card));
}

.media-page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  min-width: 0;
  padding: 18px 22px;
}

.media-page-header .page-heading,
.media-page-header .title-row,
.media-page-header .header-status,
.media-page-header .status-metric {
  display: flex;
  align-items: center;
}

.media-page-header .page-heading {
  min-width: 0;
  flex: 1 1 420px;
  gap: 14px;
}

.media-page-header .page-heading > div:last-child {
  min-width: 0;
}

.media-page-header .page-icon {
  display: grid;
  place-items: center;
  width: 52px;
  height: 52px;
  flex: 0 0 auto;
  color: var(--do-gold);
  background: var(--do-gold-wash);
  border: 1px solid var(--do-border-dark);
  border-radius: 12px;
}

.media-page-header h1 {
  margin: 0;
  color: var(--do-text-primary);
  font-size: 21px;
  line-height: 1.3;
}

.media-page-header .title-row {
  min-width: 0;
  gap: 10px;
}

.media-page-header p {
  margin: 5px 0 0;
  color: var(--do-text-secondary);
  font-size: 13px;
}

.media-status-badge {
  flex: 0 0 auto;
  padding: 4px 8px;
  color: var(--do-success-deep);
  background: var(--do-success-bg);
  border: 1px solid var(--do-success-border);
  border-radius: 5px;
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
}

.media-header-status {
  justify-content: flex-end;
  flex: 0 1 auto;
  gap: 16px;
  flex-wrap: wrap;
  color: var(--do-text-secondary);
  font-size: 13px;
}

.media-header-status .status-metric {
  gap: 6px;
  white-space: nowrap;
}

.media-header-status .status-metric strong {
  color: var(--do-text-primary);
  font-size: 15px;
}

.media-header-status .status-dot {
  width: 8px;
  height: 8px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: currentColor;
}

.media-header-status .status-dot.online {
  color: var(--do-success);
  box-shadow: 0 0 7px currentColor;
}

.filter-matrix-panel {
  min-width: 0;
  padding: 14px 18px;
  border-radius: 10px;
  box-shadow: var(--shadow-sm, var(--shadow-card));
}

.filter-row {
  min-width: 0;
  align-items: flex-start;
  gap: 14px;
  flex-wrap: wrap;
}

.filter-row + .filter-row {
  padding-top: 12px;
  border-top: 1px solid var(--do-border-light);
}

.row-label {
  flex: 0 0 108px;
  min-width: 108px;
  padding-top: 7px;
  font-size: 14px;
}

.chips-container {
  min-width: 0;
  flex: 1 1 300px;
  gap: 8px;
}

.matrix-chip {
  min-width: 0;
  min-height: 34px;
  padding: 7px 12px;
  border-radius: 7px;
  font-size: 14px;
}

.matrix-chip .chip-name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.assets-toolbar {
  min-width: 0;
  padding: 14px 18px;
  border-radius: 10px;
  box-shadow: var(--shadow-sm, var(--shadow-card));
}

.toolbar-left {
  min-width: 0;
  flex: 1 1 260px;
}

.filter-summary {
  min-width: 0;
  flex-wrap: wrap;
  white-space: normal;
}

.fs-text,
.fs-tag {
  min-width: 0;
}

.fs-tag {
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 240px;
}

.toolbar-right {
  min-width: 0;
  flex: 1 1 560px;
  justify-content: flex-end;
  flex-wrap: wrap;
  padding: 0;
}

.toolbar-search-input {
  min-width: 0;
  width: min(320px, 100%);
  flex: 1 1 240px;
}

.toolbar-right .el-button {
  flex: 0 1 auto;
  margin-left: 0;
  white-space: nowrap;
}

.btn-main-upload {
  flex: 0 1 auto !important;
}

.assets-display-area,
.asset-list-panel,
.asset-list,
.empty-assets-card {
  min-width: 0;
}

.asset-list-panel {
  border-radius: 10px;
  box-shadow: var(--shadow-sm, var(--shadow-card));
}

.asset-list-head {
  padding: 14px 18px;
  background: var(--do-bg-card);
}

.asset-row {
  display: grid;
  grid-template-columns: 86px minmax(240px, 1fr) minmax(150px, 200px) minmax(132px, 156px) minmax(210px, 260px);
  align-items: center;
  min-width: 0;
  gap: 14px;
  padding: 14px 18px;
}

.ar-main,
.ar-type,
.ar-spec,
.ar-play,
.ar-actions,
.ar-titles {
  min-width: 0;
}

.ar-main {
  width: auto;
}

.ar-type {
  display: flex;
  align-items: center;
}

.ar-spec {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.spec-chip,
.driver-tag {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ar-actions {
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 6px;
}

.ar-actions .el-button {
  margin-left: 0;
}

.asset-name {
  max-width: 100%;
}

.tag-row {
  min-width: 0;
  flex-wrap: wrap;
}

.pill-tag {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}

.empty-assets-card {
  min-height: 260px;
  padding: 48px 20px;
  border-radius: 10px;
  box-shadow: var(--shadow-sm, var(--shadow-card));
}

.empty-title,
.empty-sub {
  max-width: min(680px, 100%);
  overflow-wrap: anywhere;
}

.form-row-two {
  min-width: 0;
  flex-wrap: wrap;
}

.form-row-two > .el-form-item {
  min-width: 0;
  flex: 1 1 220px !important;
}

.auto-field {
  min-width: 0;
  flex-wrap: wrap;
}

.af-value,
.af-hint {
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}

.af-hint {
  white-space: normal;
}

.mgmt-dialog-content,
.mgmt-list,
.mgmt-section,
.mgmt-item,
.mi-left,
.mi-right,
.add-row {
  min-width: 0;
}

.mgmt-item {
  align-items: flex-start;
  gap: 10px;
  flex-wrap: wrap;
}

.mi-left {
  flex: 1 1 260px;
  flex-wrap: wrap;
  gap: 7px 10px;
}

.mi-name,
.mi-count,
.mi-builtin-tag,
.mi-code {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mi-right {
  flex: 0 0 auto;
  display: flex;
  flex-wrap: wrap;
}

.add-row {
  align-items: stretch;
  flex-wrap: wrap;
}

.add-row :deep(.el-input),
.add-row :deep(.el-select) {
  min-width: 0;
  width: auto !important;
  flex: 1 1 150px;
}

.add-row :deep(.el-button) {
  flex: 0 0 auto;
}

.player-box,
.player-meta,
.player-status,
.player-options {
  min-width: 0;
}

.player-meta {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.pm-row,
.pm-v,
.ps-msg {
  min-width: 0;
}

.pm-v,
.ps-msg {
  overflow-wrap: anywhere;
}

@media (max-width: 1280px) {

  .asset-table-head,
  .asset-row {
    grid-template-columns: 78px minmax(200px, 1fr) minmax(140px, 180px) minmax(122px, 142px) minmax(186px, 224px);
    gap: 12px;
  }

  .ar-actions .el-button {
    margin-left: 0;
  }
}

/* 中等宽度（含侧边栏后内容区不足 810px）改为带字段标签的卡片行，避免表格横向溢出 */
@media (max-width: 1100px) {
  .asset-table-head {
    display: none;
  }

  .asset-row {
    grid-template-columns: minmax(0, 1fr);
    gap: 10px;
  }

  .ar-main,
  .ar-type,
  .ar-spec,
  .ar-play,
  .ar-actions {
    grid-column: auto;
    width: 100%;
  }

  .ar-actions {
    justify-content: flex-start;
  }

  .ar-type::before,
  .ar-main::before,
  .ar-spec::before,
  .ar-play::before,
  .ar-actions::before {
    display: block;
    flex: 0 0 84px;
    color: var(--do-text-placeholder);
    font-size: 11px;
    font-weight: 700;
  }

  .ar-type::before { content: '类型'; }
  .ar-main::before { content: '名称'; }
  .ar-spec::before { content: '时长 / 大小'; }
  .ar-play::before { content: '播放资源 / 预览'; }
  .ar-actions::before { content: '操作'; }
}

@media (max-width: 900px) {
  .media-page-header {
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .media-page-header .page-heading,
  .media-page-header .header-status {
    flex-basis: 100%;
  }

  .media-header-status {
    justify-content: flex-start;
  }

  .filter-row {
    align-items: flex-start;
  }

  .row-label {
    flex-basis: 100%;
    min-width: 0;
    padding-top: 0;
  }

  .chips-container {
    flex-basis: 100%;
  }

  .toolbar-right {
    flex-basis: 100%;
    justify-content: flex-start;
  }

  .toolbar-search-input {
    flex-basis: 260px;
  }

  .player-meta {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .media-page-header,
  .filter-matrix-panel,
  .assets-toolbar {
    padding: 14px;
  }

  .media-page-header .page-heading {
    align-items: flex-start;
  }

  .media-page-header .page-icon {
    width: 44px;
    height: 44px;
  }

  .media-page-header .title-row {
    align-items: flex-start;
    flex-direction: column;
    gap: 6px;
  }

  .media-page-header h1 {
    font-size: 18px;
  }

  .media-page-header p {
    line-height: 1.5;
  }

  .toolbar-left,
  .toolbar-right {
    flex-basis: 100%;
  }

  .toolbar-search-input,
  .toolbar-right .el-button,
  .btn-main-upload {
    flex: 1 1 100% !important;
    width: 100%;
  }

  .ar-actions .el-button {
    flex: 1 1 auto;
  }

  .form-row-two {
    flex-direction: column;
  }

  .form-row-two > .el-form-item {
    flex-basis: auto !important;
  }

  .player-meta {
    grid-template-columns: minmax(0, 1fr);
  }

  .pm-row-url {
    grid-column: auto;
  }

  .add-row :deep(.el-input),
  .add-row :deep(.el-select),
  .add-row :deep(.el-button) {
    width: 100% !important;
    flex-basis: 100%;
  }
}

@media (max-width: 480px) {
  .media-page-header .page-heading {
    flex-direction: column;
  }

  .media-header-status {
    align-items: flex-start;
    flex-direction: column;
    gap: 8px;
  }

  .matrix-chip {
    max-width: 100%;
  }

  .fs-tag {
    max-width: 100%;
  }

  .ar-actions .el-button {
    flex-basis: 100%;
  }
}
</style>
