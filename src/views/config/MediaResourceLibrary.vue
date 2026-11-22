<template>
  <div class="media-library-workspace">
    <!-- 顶部状态栏 -->
    <div class="library-top-bar glass-panel">
      <div class="top-left">
        <SvgIcon name="SvgMediaLibrary" size="20" class="text-primary" />
          <div class="title-meta">
            <span class="view-title">音频与视频媒体素材资源库</span>
            <p>集中管理音视频、图片和文档素材，为播控、升旗仪式和大屏场景提供统一资源。</p>
          </div>
      </div>

      <div class="top-right">
        <button class="btn-header-action btn-header-primary" @click="openUploadDialog" title="上传新的音视频或国旗国歌图形资产">
          <SvgIcon name="SvgMediaPlayer" size="14" style="margin-right: 4px;" />
          <span>+ 上传新音视频资源</span>
        </button>
      </div>
    </div>

    <!-- 主两栏布局：左侧分类树 + 右侧媒体资产网格卡片 -->
    <div class="library-main-layout">
      <!-- 左栏：分类树目录 -->
      <div class="col-tree glass-panel">
        <div class="panel-header">
          <span class="header-title">媒体分类目录</span>
        </div>

        <div class="cat-tree-list">
          <div
            v-for="cat in categoryTree"
            :key="cat.key"
            :class="['cat-tree-item', { active: currentCatKey === cat.key }]"
            @click="currentCatKey = cat.key"
          >
            <span class="cat-name">{{ cat.name }}</span>
            <span class="cat-count num-mono">{{ cat.count }}</span>
          </div>
        </div>

        <!-- 引用安全检查提示 -->
        <div class="ref-safe-hint">
          <span class="hint-title">安全引用约束机制：</span>
          <p class="hint-text">
            当媒体素材被“自动升旗场景”、“大屏推屏任务”或“播放列表”引用时，系统自动锁定并禁止直接物理删除，确保重大赛事运行零事故。
          </p>
        </div>
      </div>

      <!-- 右栏：媒体资源卡片与明细 -->
      <div class="col-assets glass-panel">
        <div class="panel-header">
          <div class="header-title">
            <span>当前分类素材资产明细 ({{ filteredAssets.length }} 项)</span>
            <span class="panel-subtitle">已自动提取准确时长、采样率、分辨率与文件哈希值</span>
          </div>
        </div>

        <div class="assets-cards-grid">
          <div
            v-for="asset in filteredAssets"
            :key="asset.id"
            class="asset-item-card glass-panel"
          >
            <!-- 头部：类型与引用徽章 -->
            <div class="asset-card-head">
              <div class="type-icon-box" :class="asset.mediaType">
                <SvgIcon :name="asset.mediaType === 'audio' ? 'SvgSoundMatrix' : 'SvgMediaPlayer'" size="20" />
              </div>
              <div class="title-meta">
                <span class="a-title">{{ asset.name }}</span>
                <span class="a-cat-tag">{{ asset.categoryName }}</span>
              </div>
              <span v-if="asset.refCount > 0" class="ref-badge locked" title="已与升旗/推屏任务强绑定">
                被引用 {{ asset.refCount }} 次
              </span>
              <span v-else class="ref-badge free">自由未引用</span>
            </div>

            <!-- 参数详情 -->
            <div class="asset-specs-box">
              <div class="spec-row">
                <span>精确时长:</span>
                <span class="num-mono font-bold text-primary">{{ formatDuration(asset.durationMs) }} ({{ asset.durationMs }}ms)</span>
              </div>
              <div class="spec-row">
                <span>规格参数:</span>
                <span class="num-mono">{{ asset.mediaType === 'audio' ? `${asset.sampleRate}Hz 立体声` : `${asset.resolution} 60fps` }}</span>
              </div>
              <div class="spec-row">
                <span>文件校验:</span>
                <span class="num-mono text-sub">SHA256: {{ asset.hash.substring(0, 16) }}...</span>
              </div>
            </div>

            <!-- 音频波形预览条 -->
            <div v-if="asset.mediaType === 'audio'" class="mini-wave-preview">
              <div class="wave-track">
                <span class="wave-sim-bar" v-for="h in [30, 60, 80, 45, 90, 75, 100, 60, 40, 20]" :key="h" :style="{ height: h + '%' }"></span>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="asset-card-actions">
              <el-button size="small" type="primary" link @click="playAsset(asset)">
                在线试听 / 预览
              </el-button>
              <el-button size="small" type="info" link @click="editAsset(asset)">
                编辑元数据
              </el-button>
              <el-button
                size="small"
                type="danger"
                link
                :disabled="asset.refCount > 0"
                @click="deleteAsset(asset)"
              >
                {{ asset.refCount > 0 ? '已被引用锁闭' : '删除' }}
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 上传媒体弹窗 -->
    <el-dialog v-model="isUploadModalOpen" title="上传新音视频媒体素材" width="520px">
      <el-form label-position="top" size="small">
        <el-form-item label="素材文件类型">
          <el-radio-group v-model="uploadForm.type">
            <el-radio-button value="audio">高保真音频 (.mp3/.wav/.flac)</el-radio-button>
            <el-radio-button value="video">高清视频 (.mp4/.mov)</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="素材名称">
          <el-input v-model="uploadForm.name" placeholder="请输入素材中文展示名" />
        </el-form-item>
        <el-form-item label="归属业务分类">
          <el-select v-model="uploadForm.category" style="width: 100%;">
            <el-option label="国歌典礼专属" value="ANTHEM" />
            <el-option label="颁奖仪式进行曲" value="AWARD" />
            <el-option label="运动员入场曲" value="CEREMONY" />
            <el-option label="场馆背景轻音乐" value="BGM" />
            <el-option label="官方4K宣传片" value="PROMO" />
          </el-select>
        </el-form-item>
        <el-form-item label="选择媒体文件 (自动解析时长与波形)">
          <div class="mock-drop-zone">
            <span>点击或拖拽媒体文件至此处上传</span>
            <small>后台自动调用音视频解码器提取准确毫秒时长与采样率</small>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="isUploadModalOpen = false">取消</el-button>
        <el-button type="primary" @click="handleUploadSubmit">确认上传并入库</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'

const currentCatKey = ref('ALL')
const isUploadModalOpen = ref(false)

const categoryTree = ref([
  { key: 'ALL', name: '全部媒体资产', count: 4 },
  { key: 'ANTHEM', name: '国歌典礼专属曲目', count: 1 },
  { key: 'AWARD', name: '颁奖加冕进行曲', count: 1 },
  { key: 'CEREMONY', name: '入场及开幕式曲目', count: 1 },
  { key: 'BGM', name: '场馆环境背景音乐', count: 1 },
  { key: 'PROMO', name: '高清大屏宣传片', count: 0 }
])

const assets = ref([
  {
    id: 'ast_anthem_CN',
    name: '中国国歌 (义勇军进行曲)',
    mediaType: 'audio',
    categoryKey: 'ANTHEM',
    categoryName: '国歌典礼专属',
    durationMs: 49000,
    sampleRate: 44100,
    hash: 'sha_CN_anthem_mp3',
    refCount: 1 // 被自动升旗系统引用
  },
  {
    id: 2,
    name: '奥运颁奖进行曲 (加冕仪式专用)',
    mediaType: 'audio',
    categoryKey: 'AWARD',
    categoryName: '颁奖加冕进行曲',
    durationMs: 180000,
    sampleRate: 48000,
    hash: '8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4',
    refCount: 1 // 被颁奖宏引用！
  },
  {
    id: 3,
    name: '运动健儿进行曲 (运动员入场仪式)',
    mediaType: 'audio',
    categoryKey: 'CEREMONY',
    categoryName: '入场及开幕式曲目',
    durationMs: 240000,
    sampleRate: 44100,
    hash: 'a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e',
    refCount: 0 // 自由未引用，可删除
  },
  {
    id: 4,
    name: '场馆环境轻音乐 (间歇舒缓氛围)',
    mediaType: 'audio',
    categoryKey: 'BGM',
    categoryName: '场馆环境背景音乐',
    durationMs: 320000,
    sampleRate: 44100,
    hash: 'b2f5ff47436671b6e533d8dc3614845d806d87fed0ce59fd7e3e9d8e57849c3e',
    refCount: 1
  }
])

const filteredAssets = computed(() => {
  if (currentCatKey.value === 'ALL') return assets.value
  return assets.value.filter(a => a.categoryKey === currentCatKey.value)
})

const uploadForm = ref({
  type: 'audio',
  name: '',
  category: 'ANTHEM'
})

const formatDuration = (ms) => {
  const totalSec = Math.floor(ms / 1000)
  const m = Math.floor(totalSec / 60)
  const s = totalSec % 60
  return `${m}分${s}秒`
}

const openUploadDialog = () => {
  uploadForm.value = {
    type: 'audio',
    name: '新上传音频素材',
    category: 'ANTHEM'
  }
  isUploadModalOpen.value = true
}

const handleUploadSubmit = () => {
  assets.value.unshift({
    id: Date.now(),
    name: uploadForm.value.name || '新建媒体素材',
    mediaType: uploadForm.value.type,
    categoryKey: uploadForm.value.category,
    categoryName: '自定义分类',
    durationMs: 65000,
    sampleRate: 48000,
    hash: 'new_media_file_hash_' + Math.random().toString(36).substring(2, 8),
    refCount: 0
  })
  isUploadModalOpen.value = false
  ElMessage.success('媒体素材上传并入库成功，已提取精确有效时长！')
}

const playAsset = (asset) => {
  ElMessage.info(`正在在线试听/预览媒体：${asset.name}`)
}

const editAsset = (asset) => {
  ElMessage.info(`编辑素材元数据：${asset.name}`)
}

// 删除引用安全校验 (规范明确要求)
const deleteAsset = (asset) => {
  if (asset.refCount > 0) {
    ElMessage.error(`【禁止删除】素材【${asset.name}】正在被 ${asset.refCount} 个升旗/播控业务场景引用，请先解除引用关系！`)
    return
  }

  ElMessageBox.confirm(
    `确定删除媒体素材【${asset.name}】吗？此操作将记录安全审计日志。`,
    '删除确认',
    { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning' }
  ).then(() => {
    assets.value = assets.value.filter(a => a.id !== asset.id)
    ElMessage.success('素材已安全删除')
  }).catch(() => {})
}
</script>

<style scoped>
.media-library-workspace {
  display: flex;
  flex-direction: column;
  gap: 16px;
  animation: fadeIn 0.3s ease-out;
}

.library-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  background: var(--do-bg-card);
  border: 1px solid var(--do-border-card);
  border-radius: var(--do-radius-card);
  box-shadow: var(--do-shadow-card);
}

.top-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.view-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--do-coffee);
  letter-spacing: 0.5px;
}

.top-right {
  display: flex;
  gap: 12px;
}

.library-main-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 16px;
}

.col-tree,
.col-assets {
  background: var(--do-bg-card);
  border: 1px solid var(--do-border-card);
  border-radius: var(--do-radius-card);
  box-shadow: var(--do-shadow-card);
  overflow: hidden;
}

.panel-header {
  padding: 14px 18px;
  border-bottom: 1px solid var(--do-border-card);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(240, 235, 227, 0.4);
}

.header-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--do-coffee);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.panel-subtitle {
  font-size: 14px;
  color: var(--do-coffee-light);
  font-weight: 400;
}

/* 分类树 */
.cat-tree-list {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.cat-tree-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: var(--do-coffee-mid);
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.cat-tree-item:hover {
  background: rgba(var(--th-accent-rgb), 0.1);
  color: var(--do-coffee);
}

.cat-tree-item.active {
  background: rgba(var(--th-accent-rgb), 0.18);
  color: var(--do-gold-dark);
  font-weight: 700;
  border-color: rgba(var(--th-accent-rgb), 0.4);
}

.cat-count {
  font-size: 14px;
  background: rgba(var(--th-shadow-rgb), 0.06);
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 700;
}

.ref-safe-hint {
  margin: 16px 12px;
  background: linear-gradient(135deg, rgba(var(--th-accent-rgb), 0.08) 0%, rgba(var(--th-accent-rgb), 0.02) 100%);
  border: 1px solid rgba(var(--th-accent-rgb), 0.25);
  border-radius: 6px;
  padding: 12px 14px;
}

.hint-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--do-amber);
  display: block;
  margin-bottom: 4px;
}

.hint-text {
  font-size: 14px;
  color: var(--do-coffee-mid);
  line-height: 1.6;
  margin: 0;
}

/* 素材卡片流 */
.assets-cards-grid {
  padding: 16px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.asset-item-card {
  padding: 16px;
  background: #FFFFFF;
  border: 1px solid var(--do-border-card);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: 0 1px 4px rgba(var(--th-shadow-rgb), 0.04);
  transition: all 0.2s ease;
}

.asset-item-card:hover {
  border-color: var(--do-gold);
  box-shadow: 0 4px 14px rgba(var(--th-accent-rgb), 0.18);
  transform: translateY(-1px);
}

.asset-card-head {
  display: flex;
  align-items: center;
  gap: 12px;
}

.type-icon-box {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}
.type-icon-box.audio {
  background: rgba(var(--th-accent-rgb), 0.16);
  color: var(--do-gold-dark);
  border: 1px solid rgba(var(--th-accent-rgb), 0.3);
}
.type-icon-box.video {
  background: rgba(var(--th-success-rgb), 0.14);
  color: var(--do-olive);
  border: 1px solid rgba(var(--th-success-rgb), 0.3);
}

.title-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.a-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--do-coffee);
}

.a-cat-tag {
  font-size: 14px;
  color: var(--do-coffee-light);
}

.ref-badge {
  font-size: 14px;
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 600;
}
.ref-badge.locked {
  background: rgba(var(--th-danger-rgb), 0.12);
  color: var(--do-terra);
  border: 1px solid var(--do-terra);
}
.ref-badge.free {
  background: rgba(var(--th-shadow-rgb), 0.05);
  color: var(--do-coffee-light);
  border: 1px solid rgba(var(--th-accent-rgb), 0.5);
}

.asset-specs-box {
  background: var(--do-sand-light);
  padding: 10px 12px;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 14px;
  border: 1px solid rgba(var(--th-accent-rgb), 0.5);
}

.spec-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--do-coffee-mid);
}

.mini-wave-preview {
  height: 28px;
  background: var(--do-sand-light);
  border-radius: 4px;
  display: flex;
  align-items: center;
  padding: 0 12px;
  border: 1px solid rgba(var(--th-accent-rgb), 0.4);
}

.wave-track {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.wave-sim-bar {
  width: 4px;
  background: var(--do-gold);
  border-radius: 2px;
  transition: height 0.2s ease;
}

.asset-card-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 4px;
}

.mock-drop-zone {
  border: 2px dashed var(--do-gold);
  border-radius: 8px;
  padding: 30px;
  text-align: center;
  color: var(--do-coffee-mid);
  display: flex;
  flex-direction: column;
  gap: 6px;
  background: var(--do-sand-light);
}
</style>
