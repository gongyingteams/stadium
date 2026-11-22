<template>
  <div class="flag-workspace country-library">
    <!-- 顶部状态栏 -->
    <div class="flag-top-bar glass-panel">
      <div class="top-left">
        <div class="title-cluster">
          <SvgIcon name="SvgAdapterBook" size="22" class="text-gold" />
          <div class="title-meta">
            <h2 class="view-title">国家资料库 · 录入与编辑</h2>
            <p>维护参赛国家、国旗资源与国歌资料，为升旗仪式席位绑定和音画同步提供基础数据。</p>
          </div>
        </div>
        <div class="top-badges">
          <span class="info-badge highlight">
            在库国家: <span class="num-mono">{{ countries.length }}</span>
          </span>
          <span class="info-badge">全球 200 国及地区</span>
          <span class="info-badge muted">素材库深度联动</span>
        </div>
      </div>

      <div class="top-right">
        <button class="btn-header-action btn-top-reset" @click="handleResetStandard197" title="一键重置恢复全球官方标准资料库">
          <SvgIcon name="SvgAdapterBook" size="14" style="margin-right: 4px;" />
          <span>恢复标准库</span>
        </button>
        <button class="btn-header-action btn-top-manage" @click="goBack" title="返回自动升旗仪式与音画同步仿真控制台">
          <SvgIcon name="SvgFlagSystem" size="14" style="margin-right: 4px;" />
          <span>返回升旗控制台</span>
        </button>
      </div>
    </div>

    <!-- 平铺双栏: 左侧国家台账 + 右侧录入/编辑表单 -->
    <div class="cl-layout">
      <!-- 1. 左栏: 国家台账 (占据主要浏览宽度) -->
      <div class="cl-list glass-panel">
        <div class="panel-header">
          <div class="header-title-box">
            <span class="header-accent-bar"></span>
            <span class="header-title">国家台账</span>
            <span class="header-badge num-mono">{{ filteredCountries.length }} / {{ countries.length }}</span>
          </div>

          <div class="cl-filter">
            <el-select
              v-model="regionFilter"
              class="cl-region-select"
            >
              <el-option label="全部区域" value="全部" />
              <el-option v-for="r in REGIONS" :key="r" :label="r" :value="r" />
            </el-select>
            <el-input
              v-model="searchKeyword"
              clearable
              prefix-icon="Search"
              placeholder="搜索缩写 / 中英文 / 国歌..."
              class="cl-search-input"
            />
          </div>
        </div>

        <div class="cl-table-wrap">
          <div class="cm-table">
            <div class="cm-row cm-row-head">
              <span class="col-flag">国旗</span>
              <span class="col-code">代码</span>
              <span class="col-name-cn">中文名称</span>
              <span class="col-name-en">英文名称</span>
              <span class="col-region">所属区域</span>
              <span class="col-anthem">绑定国歌</span>
              <span class="col-ops">操作</span>
            </div>

            <div v-for="c in filteredCountries" :key="c.id" class="cm-row" :class="{ 'is-editing': editingId === c.id }">
              <div class="col-flag">
                <span class="cm-swatch" :style="flagStyle(c)" :title="`${c.nameCn} 国旗`"></span>
              </div>
              <div class="col-code">
                <span class="code-pill num-mono" :title="`ISO Alpha-2: ${c.code}`">{{ c.code }}</span>
                <span v-if="c.codeAlpha3 && c.codeAlpha3 !== c.code" class="code-alpha3-chip num-mono" :title="`ISO Alpha-3: ${c.codeAlpha3}`">{{ c.codeAlpha3 }}</span>
              </div>
              <div class="col-name-cn">
                <span class="name-cn-text" :title="c.nameCn">{{ c.nameCn }}</span>
              </div>
              <div class="col-name-en">
                <span class="name-en-text" :title="c.nameEn">{{ c.nameEn }}</span>
              </div>
              <div class="col-region">
                <el-tag size="small" :type="getRegionTagType(c.region)" effect="light" class="region-tag">
                  {{ c.region }}
                </el-tag>
              </div>
              <div class="col-anthem">
                <div class="anthem-cell" :title="`${c.anthemName} (${c.anthemDuration}秒)`">
                  <button
                    type="button"
                    class="anthem-row-play-btn"
                    :class="{ 'is-playing': playingRowCode === c.code }"
                    :title="playingRowCode === c.code ? '停止试听' : '点击试听国歌'"
                    @click.stop="togglePlayRowAnthem(c)"
                  >
                    <span v-if="playingRowCode === c.code">⏹</span>
                    <span v-else>▶</span>
                  </button>
                  <span class="anthem-name-txt">{{ c.anthemName }}</span>
                  <span class="anthem-duration-chip num-mono">{{ c.anthemDuration }}s</span>
                </div>
              </div>
              <div class="col-ops">
                <button type="button" class="op-link-btn edit" @click="editCountry(c)">编辑</button>
                <button type="button" class="op-link-btn del" @click="deleteCountry(c)">删除</button>
              </div>
            </div>

            <div v-if="!filteredCountries.length" class="cl-empty">
              <p>暂无符合筛选条件的国家信息</p>
              <span class="empty-sub">可尝试清空搜索关键词，或直接在右侧录入新国家</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 2. 右栏: 录入 / 编辑表单 -->
      <div class="cl-form glass-panel">
        <div class="panel-header">
          <div class="header-title-box">
            <span class="header-accent-bar gold"></span>
            <span class="header-title">
              {{ editingId ? `编辑国家 · ${cForm.nameCn || cForm.code || '编辑中'}` : '录入新国家' }}
            </span>
          </div>
          <span class="panel-subtitle">带 <i class="req-star">*</i> 为必填项</span>
        </div>

        <div class="cl-form-body">
          <!-- 分组 1: 国家基础识别信息 -->
          <div class="form-section">
            <div class="section-label">国家基础信息</div>
            <div class="cm-grid">
              <div class="cm-field">
                <label>二字代码 (ISO-2) <i class="req-star">*</i></label>
                <el-input
                  v-model="cForm.code"
                  maxlength="4"
                  placeholder="如 CN、US"
                  @input="cForm.code = (cForm.code || '').toUpperCase()"
                />
              </div>
              <div class="cm-field">
                <label>三字代码 (ISO-3 / IOC)</label>
                <el-input
                  v-model="cForm.codeAlpha3"
                  maxlength="6"
                  placeholder="如 CHN、USA"
                  @input="cForm.codeAlpha3 = (cForm.codeAlpha3 || '').toUpperCase()"
                />
              </div>
              <div class="cm-field">
                <label>中文全称 <i class="req-star">*</i></label>
                <el-input v-model="cForm.nameCn" placeholder="如 中华人民共和国" />
              </div>
              <div class="cm-field">
                <label>英文全称</label>
                <el-input v-model="cForm.nameEn" placeholder="如 China" />
              </div>
              <div class="cm-field" style="grid-column: span 2;">
                <label>所属大洲区域</label>
                <el-select v-model="cForm.region" style="width: 100%;">
                  <el-option v-for="r in REGIONS" :key="r" :label="r" :value="r" />
                </el-select>
              </div>
            </div>
          </div>

          <!-- 分组 2: 国旗配置 (支持从素材资源库选择或上传SVG图片) -->
          <div class="form-section asset-bind-section">
            <div class="section-header-row">
              <span class="section-label">国旗图形资产配置</span>
              <div class="section-actions">
                <button type="button" class="btn-picker-action" @click="openAssetPicker('flag')">
                  <SvgIcon name="SvgConfigTemplate" size="14" style="margin-right: 4px;" />
                  从素材库选择 (分类/分组)
                </button>
                <button type="button" class="btn-upload-action" @click="flagFileInput && flagFileInput.click()">
                  <SvgIcon name="SvgAdapterBook" size="14" style="margin-right: 4px;" />
                  上传 SVG / 图片
                </button>
              </div>
            </div>

            <!-- 国旗绑定状态卡片 -->
            <div class="bind-status-card" :class="{ 'has-asset': !!cForm.imageUrl }">
              <template v-if="cForm.imageUrl">
                <div class="bound-asset-item">
                  <div class="flag-stage-box">
                    <img :src="cForm.imageUrl" class="bound-flag-img" alt="国旗预览" />
                  </div>
                  <div class="bound-asset-meta">
                    <div class="meta-tag-line">
                      <span class="source-tag" :class="cForm.flagSourceType === 'asset' ? 'source-library' : 'source-local'">
                        {{ cForm.flagSourceType === 'asset' ? '素材资源库' : '本地上传SVG' }}
                      </span>
                      <span class="format-tag num-mono">
                        {{ getFileExt(cForm.flagAssetName || cForm.imageUrl) || 'SVG' }}
                      </span>
                    </div>
                    <span class="bound-asset-name" :title="cForm.flagAssetName || '国旗图形资产'">
                      {{ cForm.flagAssetName || '国旗标准矢量图形' }}
                    </span>
                  </div>
                  <button type="button" class="btn-unlink-asset" title="解除绑定" @click="clearFlagBinding">
                    移除
                  </button>
                </div>
              </template>
              <template v-else>
                <div class="empty-bind-placeholder">
                  <span class="placeholder-tip">暂未绑定独立国旗图形，可点击右上角从素材库挑选或直接上传 SVG 矢量图</span>
                </div>
              </template>
            </div>
          </div>

          <!-- 分组 3: 国歌演奏设定 (支持从素材库选择音频或本地上传) -->
          <div class="form-section asset-bind-section">
            <div class="section-header-row">
              <span class="section-label">国歌基本设定与音源绑定</span>
              <div class="section-actions">
                <button type="button" class="btn-picker-action" @click="openAssetPicker('anthem')">
                  <SvgIcon name="SvgSoundMatrix" size="14" style="margin-right: 4px;" />
                  从素材库选择 (音频/国歌)
                </button>
                <button type="button" class="btn-upload-action" @click="anthemFileInput && anthemFileInput.click()">
                  <SvgIcon name="SvgMediaPlayer" size="14" style="margin-right: 4px;" />
                  上传国歌音频
                </button>
              </div>
            </div>

            <div class="cm-grid" style="margin-bottom: 10px;">
              <div class="cm-field">
                <label>国歌曲名</label>
                <el-input v-model="cForm.anthemName" placeholder="如 义勇军进行曲" />
              </div>
              <div class="cm-field">
                <label>演奏标准时长 (秒)</label>
                <el-input-number
                  v-model="cForm.anthemDuration"
                  :min="5"
                  :max="300"
                  :step="1"
                  controls-position="right"
                  style="width: 100%;"
                />
              </div>
            </div>

            <!-- 国歌音频绑定状态卡片 -->
            <div class="bind-status-card" :class="{ 'has-asset': !!cForm.anthemUrl }">
              <template v-if="cForm.anthemUrl">
                <div class="bound-asset-item">
                  <div class="audio-stage-icon">
                    🎵
                  </div>
                  <div class="bound-asset-meta">
                    <div class="meta-tag-line">
                      <span class="source-tag" :class="cForm.anthemSourceType === 'asset' ? 'source-library' : 'source-local'">
                        {{ cForm.anthemSourceType === 'asset' ? '素材资源库' : '本地音频文件' }}
                      </span>
                      <span class="format-tag num-mono">
                        {{ cForm.anthemDuration }} 秒
                      </span>
                    </div>
                    <span class="bound-asset-name" :title="cForm.anthemFileName || cForm.anthemName">
                      {{ cForm.anthemFileName || cForm.anthemName || '国歌原声音频' }}
                    </span>
                  </div>
                  <div class="audio-ctrl-btns">
                    <button type="button" class="btn-audio-preview" @click="togglePreviewAnthem">
                      {{ isPlayingAnthem ? '⏸ 暂停' : '▶ 试听' }}
                    </button>
                    <button type="button" class="btn-unlink-asset" title="移除音频绑定" @click="clearAnthemBinding">
                      移除
                    </button>
                  </div>
                </div>
              </template>
              <template v-else>
                <div class="empty-bind-placeholder">
                  <span class="placeholder-tip">暂未绑定实体音频，升旗时将采用系统 WebAudio 仪式合成旋律</span>
                </div>
              </template>
            </div>
          </div>

          <!-- 分组 4: 实时升旗视觉效果看板 (所见即所得) -->
          <div class="cl-live-preview">
            <div class="preview-flag-stage">
              <span class="preview-flag-drape" :style="flagStyle(cForm)"></span>
            </div>
            <div class="preview-meta">
              <div class="pm-title-row">
                <h4 class="pm-name">{{ cForm.nameCn || '未命名国家' }}</h4>
                <span class="pm-code num-mono">{{ cForm.code || '—' }}</span>
                <el-tag size="small" :type="getRegionTagType(cForm.region)" effect="light">{{ cForm.region || '未选区域' }}</el-tag>
              </div>
              <div class="pm-sub-row">
                <span class="pm-en">{{ cForm.nameEn || 'No English Name' }}</span>
                <span class="pm-sep">·</span>
                <span class="pm-anthem">🎵 {{ cForm.anthemName || '未命名国歌' }} ({{ cForm.anthemDuration || 46 }}s)</span>
              </div>
            </div>
          </div>

          <!-- 分组 5: 表单操作按钮组 -->
          <div class="cm-form-actions">
            <button class="btn-submit-gold" @click="saveCountry">
              {{ editingId ? '保存修改并更新台账' : '确认录入新国家' }}
            </button>
            <button class="btn-reset-form" @click="resetCountryForm">
              清空重置
            </button>
            <button v-if="editingId" class="btn-cancel-edit" @click="resetCountryForm">
              退出编辑
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== 素材挑选专属弹窗 (Asset Picker Dialog) ==================== -->
    <el-dialog
      v-model="assetPickerVisible"
      :title="pickerModalTitle"
      width="820px"
      destroy-on-close
      class="asset-picker-dialog"
    >
      <div class="asset-picker-container">
        <!-- 顶部联动检索栏 -->
        <div class="picker-filter-bar">
          <div class="filter-item">
            <span class="filter-lbl">资源分类:</span>
            <el-select
              v-model="pickerCategory"
              style="width: 130px;"
              @change="onPickerCategoryChange"
            >
              <el-option label="全部分类" value="ALL" />
              <el-option v-for="cat in categories" :key="cat.code" :label="cat.name" :value="cat.code" />
            </el-select>
          </div>

          <div class="filter-item">
            <span class="filter-lbl">业务分组:</span>
            <el-select
              v-model="pickerGroup"
              style="width: 140px;"
              @change="refreshPickerAssets"
            >
              <el-option label="全部分组" value="ALL" />
              <el-option v-for="grp in groups" :key="grp.code" :label="grp.name" :value="grp.code" />
            </el-select>
          </div>

          <div class="filter-item search-item">
            <el-input
              v-model="pickerKeyword"
              clearable
              prefix-icon="Search"
              placeholder="按素材名称、格式、备注搜索..."
              style="width: 240px;"
              @input="refreshPickerAssets"
            />
          </div>
        </div>

        <!-- 素材卡片列表 -->
        <div class="picker-assets-scroll">
          <div v-if="availableAssets.length > 0" class="picker-assets-grid">
            <div
              v-for="item in availableAssets"
              :key="item.id"
              class="asset-choice-card"
              :class="{ 'is-selected': selectedAsset && selectedAsset.id === item.id }"
              @click="selectedAsset = item"
              @dblclick="confirmPickAsset"
            >
              <div class="acc-badge-col">
                <span class="acc-format-badge" :class="item.categoryCode">
                  {{ (item.fileType || 'FILE').toUpperCase() }}
                </span>
              </div>
              <div class="acc-body">
                <div class="acc-title-line">
                  <span class="acc-name" :title="item.name">{{ item.name }}</span>
                </div>
                <div class="acc-meta-line">
                  <span class="acc-pill cat-pill">{{ getCategoryName(item.categoryCode) }}</span>
                  <span class="acc-pill grp-pill">{{ getGroupName(item.categoryCode, item.groupCode) }}</span>
                  <span class="acc-spec num-mono">{{ item.fileSizeFormatted }}</span>
                  <span v-if="item.durationSec > 0" class="acc-spec num-mono">{{ item.durationFormatted }}</span>
                </div>
                <span class="acc-remark" :title="item.remark">{{ item.remark || '无备注信息' }}</span>
              </div>
              <div class="acc-select-col">
                <span v-if="selectedAsset && selectedAsset.id === item.id" class="selected-checkmark">✓ 已选</span>
                <span v-else class="select-hint-txt">点击选择</span>
              </div>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-else class="picker-empty-box">
            <p>当前分类/分组下暂无素材资源</p>
            <span class="pe-sub">可尝试切换分类、清空关键词，或直接在媒体播控台上传素材</span>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="picker-dialog-footer">
          <span class="pdf-selected-tip">
            当前选中: <strong v-if="selectedAsset">{{ selectedAsset.name }}</strong><span v-else>未选择</span>
          </span>
          <div class="pdf-btns">
            <el-button @click="assetPickerVisible = false">取消</el-button>
            <el-button type="primary" :disabled="!selectedAsset" @click="confirmPickAsset">
              确认绑定此素材
            </el-button>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- 隐藏真实文件输入 -->
    <input ref="flagFileInput" type="file" accept=".svg,image/svg+xml,image/*" hidden @change="onFlagFile" />
    <input ref="anthemFileInput" type="file" accept="audio/*,.mp3,.wav,.ogg,.m4a,.aac" hidden @change="onAnthemFile" />
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useFlagCountriesStore, REGIONS, PATTERN_OPTIONS, flagStyle } from '@/stores/flagCountries'
import { mediaAssetService } from '@/services/mediaAssetService'

const router = useRouter()
const store = useFlagCountriesStore()
const countries = computed(() => store.countries)

const editingId = ref(null)
const flagFileInput = ref(null)
const anthemFileInput = ref(null)

// 试听国歌
const isPlayingAnthem = ref(false)
let audioPlayerInstance = null

function togglePreviewAnthem() {
  if (!cForm.value.anthemUrl) {
    ElMessage.info('暂无可播放的国歌音频地址')
    return
  }
  if (isPlayingAnthem.value) {
    if (audioPlayerInstance) {
      audioPlayerInstance.pause()
      audioPlayerInstance = null
    }
    isPlayingAnthem.value = false
  } else {
    try {
      if (audioPlayerInstance) audioPlayerInstance.pause()
      audioPlayerInstance = new Audio(cForm.value.anthemUrl)
      audioPlayerInstance.play().catch(() => {
        isPlayingAnthem.value = false
        ElMessage.warning('音频资源加载失败或地址失效')
      })
      isPlayingAnthem.value = true
      audioPlayerInstance.onended = () => {
        isPlayingAnthem.value = false
      }
      audioPlayerInstance.onerror = () => {
        isPlayingAnthem.value = false
        ElMessage.warning('音频资源加载失败')
      }
    } catch (e) {
      isPlayingAnthem.value = false
    }
  }
}

function clearFlagBinding() {
  cForm.value.imageUrl = null
  cForm.value.flagAssetId = null
  cForm.value.flagAssetName = ''
  cForm.value.flagSourceType = 'none'
  ElMessage.info('已清除国旗图形资产绑定')
}

function clearAnthemBinding() {
  if (audioPlayerInstance) {
    audioPlayerInstance.pause()
    audioPlayerInstance = null
  }
  isPlayingAnthem.value = false
  cForm.value.anthemUrl = null
  cForm.value.anthemAssetId = null
  cForm.value.anthemAssetName = ''
  cForm.value.anthemFileName = ''
  cForm.value.anthemSourceType = 'none'
  ElMessage.info('已清除国歌音频绑定')
}

function blankCountryForm() {
  return {
    code: '',
    codeAlpha3: '',
    nameCn: '',
    nameEn: '',
    region: '亚洲',
    pattern: 'solid',
    c1: '#2563EB',
    c2: '#FFFFFF',
    c3: '#0F172A',
    // 国旗资产
    imageUrl: null,
    flagAssetId: null,
    flagAssetName: '',
    flagSourceType: 'none', // 'asset' | 'upload' | 'none'
    // 国歌资产
    anthemName: '',
    anthemEn: '',
    anthemDuration: 46,
    anthemUrl: null,
    anthemAssetId: null,
    anthemAssetName: '',
    anthemFileName: '',
    anthemSourceType: 'none' // 'asset' | 'upload' | 'none'
  }
}

const cForm = ref(blankCountryForm())

function resetCountryForm() {
  if (audioPlayerInstance) {
    audioPlayerInstance.pause()
    audioPlayerInstance = null
  }
  isPlayingAnthem.value = false
  cForm.value = blankCountryForm()
  editingId.value = null
}

function editCountry(c) {
  if (audioPlayerInstance) {
    audioPlayerInstance.pause()
    audioPlayerInstance = null
  }
  isPlayingAnthem.value = false
  editingId.value = c.id
  cForm.value = {
    code: c.code,
    codeAlpha3: c.codeAlpha3 || c.code,
    nameCn: c.nameCn,
    nameEn: c.nameEn,
    region: c.region,
    pattern: c.pattern || 'solid',
    c1: c.c1 || '#2563EB',
    c2: c.c2 || '#FFFFFF',
    c3: c.c3 || '#0F172A',
    // 国旗绑定
    imageUrl: c.imageUrl || null,
    flagAssetId: c.flagAssetId || null,
    flagAssetName: c.flagAssetName || (c.imageUrl ? '已配置国旗' : ''),
    flagSourceType: c.flagSourceType || (c.imageUrl ? 'asset' : 'none'),
    // 国歌绑定
    anthemName: c.anthemName || '',
    anthemEn: c.anthemEn || '',
    anthemDuration: c.anthemDuration || 46,
    anthemUrl: c.anthemUrl || null,
    anthemAssetId: c.anthemAssetId || null,
    anthemAssetName: c.anthemAssetName || '',
    anthemFileName: c.anthemFileName || '',
    anthemSourceType: c.anthemSourceType || (c.anthemUrl ? 'asset' : 'none')
  }
  ElMessage.info(`正在编辑「${c.nameCn}」`)
  nextTick(() => window.scrollTo({ top: 0, behavior: 'smooth' }))
}

function saveCountry() {
  const f = cForm.value
  if (!f.code.trim() || !f.nameCn.trim()) {
    ElMessage.warning('字母缩写与中文名称为必填项')
    return
  }
  const payload = {
    code: f.code.trim().toUpperCase(),
    codeAlpha3: (f.codeAlpha3 ? f.codeAlpha3.trim().toUpperCase() : f.code.trim().toUpperCase()),
    nameCn: f.nameCn.trim(),
    nameEn: (f.nameEn.trim() || f.nameCn.trim()),
    region: f.region,
    pattern: f.pattern,
    c1: f.c1,
    c2: f.c2,
    c3: f.c3,
    // 国旗持久化
    imageUrl: f.imageUrl,
    flagAssetId: f.flagAssetId,
    flagAssetName: f.flagAssetName,
    flagSourceType: f.flagSourceType,
    // 国歌持久化
    anthemName: f.anthemName.trim() || `${f.nameCn.trim()}国歌`,
    anthemEn: f.anthemEn || '',
    anthemDuration: Math.max(5, Math.min(300, Number(f.anthemDuration) || 46)),
    anthemUrl: f.anthemUrl,
    anthemAssetId: f.anthemAssetId,
    anthemAssetName: f.anthemAssetName,
    anthemFileName: f.anthemFileName,
    anthemSourceType: f.anthemSourceType
  }
  const res = store.upsertCountry(payload, editingId.value)
  if (!res.ok) {
    ElMessage.warning(res.error)
    return
  }
  ElMessage.success(editingId.value ? `国家「${payload.nameCn}」资料已更新` : `已录入新国家「${payload.nameCn}」`)
  resetCountryForm()
}

function deleteCountry(c) {
  ElMessageBox.confirm(
    `确认删除国家「${c.nameCn} (${c.code})」？其绑定的旗帜与国歌资料将一并移除。`,
    '删除国家确认',
    { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消', confirmButtonClass: 'el-button--danger' }
  ).then(() => {
    store.removeCountry(c.id)
    if (editingId.value === c.id) resetCountryForm()
    ElMessage.success(`已删除国家「${c.nameCn}」`)
  }).catch(() => {})
}

// 本地 SVG/图片上传
function onFlagFile(e) {
  const file = e.target.files && e.target.files[0]
  if (!file) return
  const isSvg = file.name.toLowerCase().endsWith('.svg') || file.type.includes('svg')
  const reader = new FileReader()
  reader.onload = () => {
    cForm.value.imageUrl = reader.result
    cForm.value.flagAssetName = file.name
    cForm.value.flagAssetId = null
    cForm.value.flagSourceType = 'upload'
    ElMessage.success(isSvg ? `SVG 矢量国旗「${file.name}」已上传绑定` : `国旗图片「${file.name}」已上传绑定`)
  }
  reader.readAsDataURL(file)
  e.target.value = ''
}

// 本地国歌音频上传
function onAnthemFile(e) {
  const file = e.target.files && e.target.files[0]
  if (!file) return
  const url = URL.createObjectURL(file)
  cForm.value.anthemUrl = url
  cForm.value.anthemFileName = file.name
  cForm.value.anthemAssetName = file.name
  cForm.value.anthemAssetId = null
  cForm.value.anthemSourceType = 'upload'
  
  if (!cForm.value.anthemName) {
    cForm.value.anthemName = file.name.replace(/\.[^.]+$/, '')
  }

  // 自动探测真实音频时长
  try {
    const audioTest = new Audio(url)
    audioTest.addEventListener('loadedmetadata', () => {
      if (audioTest.duration && !isNaN(audioTest.duration) && audioTest.duration > 0) {
        cForm.value.anthemDuration = Math.round(audioTest.duration)
        ElMessage.success(`国歌音频「${file.name}」已载入，时长自动检测为 ${cForm.value.anthemDuration} 秒`)
      }
    })
  } catch (err) {
    // 静默回退
  }
  e.target.value = ''
}

function goBack() {
  if (audioPlayerInstance) {
    audioPlayerInstance.pause()
    audioPlayerInstance = null
  }
  router.push('/iot/flag')
}

/* 区域标签色彩映射 */
function getRegionTagType(region) {
  switch (region) {
    case '亚洲': return 'warning'
    case '欧洲': return 'primary'
    case '北美洲':
    case '美洲': return 'success'
    case '南美洲': return 'info'
    case '非洲': return 'danger'
    case '大洋洲': return ''
    case '其他': return 'info'
    default: return 'info'
  }
}

// 列表行国歌试听播放
const playingRowCode = ref(null)
let rowAudioPlayer = null

function togglePlayRowAnthem(c) {
  if (playingRowCode.value === c.code) {
    if (rowAudioPlayer) {
      rowAudioPlayer.pause()
      rowAudioPlayer = null
    }
    playingRowCode.value = null
    return
  }
  if (rowAudioPlayer) {
    rowAudioPlayer.pause()
    rowAudioPlayer = null
  }
  if (audioPlayerInstance) {
    audioPlayerInstance.pause()
    isPlayingAnthem.value = false
  }
  const audioSrc = c.anthemUrl || `/uploads/audio/${c.code}.mp3`
  try {
    rowAudioPlayer = new Audio(audioSrc)
    rowAudioPlayer.play().then(() => {
      playingRowCode.value = c.code
    }).catch(() => {
      playingRowCode.value = null
      ElMessage.warning(`国歌《${c.anthemName}》加载失败`)
    })
    rowAudioPlayer.onended = () => {
      playingRowCode.value = null
    }
    rowAudioPlayer.onerror = () => {
      playingRowCode.value = null
      ElMessage.warning(`国歌《${c.anthemName}》播放异常`)
    }
  } catch (e) {
    playingRowCode.value = null
  }
}

function handleResetStandard197() {
  ElMessageBox.confirm(
    '确定要恢复至官方 200 个国家及地区完整资料库吗？此操作将刷新并对齐所有标准国旗SVG与国歌音频绑定。',
    '恢复官方标准资料库',
    {
      confirmButtonText: '确定恢复',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    store.resetToDefault()
    ElMessage.success('已恢复全球 200 国及地区官方标准资料库')
  }).catch(() => {})
}

function getFileExt(filename) {
  if (!filename) return ''
  const m = String(filename).match(/\.([a-zA-Z0-9]+)(\?|$)/)
  return m ? m[1].toUpperCase() : ''
}

/* ==================== 素材选择弹窗逻辑 ==================== */
const assetPickerVisible = ref(false)
const assetPickerType = ref('flag') // 'flag' | 'anthem'
const pickerCategory = ref('ALL')
const pickerGroup = ref('ALL')
const pickerKeyword = ref('')
const selectedAsset = ref(null)

const categories = ref([])
const groups = ref([])
const availableAssets = ref([])

const pickerModalTitle = computed(() => {
  return assetPickerType.value === 'flag'
    ? '从素材资源库挑选国旗图形 (支持 SVG / 矢量图片)'
    : '从素材资源库挑选国歌曲目 (音频素材)'
})

function openAssetPicker(type) {
  assetPickerType.value = type
  pickerKeyword.value = ''
  selectedAsset.value = null

  // 1. 获取最新分类列表
  categories.value = mediaAssetService.getCategories()

  // 2. 智能预置分类与分组
  if (type === 'flag') {
    // 优先选中 document (文件) 分类，并寻找 flag (国旗) 分组
    const docCat = categories.value.find(c => c.code === 'document')
    pickerCategory.value = docCat ? 'document' : 'ALL'
    groups.value = mediaAssetService.getGroups(pickerCategory.value)
    const flagGrp = groups.value.find(g => g.code === 'flag')
    pickerGroup.value = flagGrp ? 'flag' : 'ALL'
  } else {
    // 优先选中 audio (音频) 分类，并寻找 anthem (国歌) 分组
    const audioCat = categories.value.find(c => c.code === 'audio')
    pickerCategory.value = audioCat ? 'audio' : 'ALL'
    groups.value = mediaAssetService.getGroups(pickerCategory.value)
    const anthemGrp = groups.value.find(g => g.code === 'anthem')
    pickerGroup.value = anthemGrp ? 'anthem' : 'ALL'
  }

  refreshPickerAssets()
  assetPickerVisible.value = true
}

function onPickerCategoryChange(catCode) {
  pickerCategory.value = catCode
  groups.value = mediaAssetService.getGroups(catCode)
  pickerGroup.value = 'ALL'
  refreshPickerAssets()
}

function refreshPickerAssets() {
  availableAssets.value = mediaAssetService.getAssets({
    categoryCode: pickerCategory.value,
    groupCode: pickerGroup.value,
    keyword: pickerKeyword.value
  })
}

function getCategoryName(catCode) {
  const c = categories.value.find(item => item.code === catCode)
  return c ? c.name : catCode
}

function getGroupName(catCode, grpCode) {
  const g = mediaAssetService.getGroup(catCode, grpCode)
  return g ? g.name : grpCode
}

function confirmPickAsset() {
  if (!selectedAsset.value) {
    ElMessage.warning('请先在列表中点击选中一个素材！')
    return
  }
  const item = selectedAsset.value
  if (assetPickerType.value === 'flag') {
    cForm.value.flagAssetId = item.id
    cForm.value.flagAssetName = item.name
    cForm.value.imageUrl = item.accessUrl || item.storagePath
    cForm.value.flagSourceType = 'asset'
    ElMessage.success(`已选中国旗素材「${item.name}」`)
  } else {
    cForm.value.anthemAssetId = item.id
    cForm.value.anthemAssetName = item.name
    cForm.value.anthemName = item.name
    cForm.value.anthemDuration = item.durationSec || 46
    cForm.value.anthemUrl = item.accessUrl || item.storagePath
    cForm.value.anthemSourceType = 'asset'
    ElMessage.success(`已选中国歌素材「${item.name}」，时长已自动设定为 ${cForm.value.anthemDuration} 秒`)
  }
  assetPickerVisible.value = false
}

onBeforeUnmount(() => {
  if (audioPlayerInstance) {
    audioPlayerInstance.pause()
    audioPlayerInstance = null
  }
  if (rowAudioPlayer) {
    rowAudioPlayer.pause()
    rowAudioPlayer = null
  }
})

/* 台账筛选 */
const regionFilter = ref('全部')
const searchKeyword = ref('')
const filteredCountries = computed(() => {
  const kw = searchKeyword.value.trim().toLowerCase()
  return countries.value.filter(c => {
    const okRegion = regionFilter.value === '全部' || c.region === regionFilter.value
    const okKw = !kw ||
      c.code.toLowerCase().includes(kw) ||
      ((c.codeAlpha3 || '').toLowerCase().includes(kw)) ||
      c.nameCn.toLowerCase().includes(kw) ||
      (c.nameEn || '').toLowerCase().includes(kw) ||
      (c.anthemName || '').toLowerCase().includes(kw) ||
      ((c.anthemEn || '').toLowerCase().includes(kw))
    return okRegion && okKw
  })
})
</script>

<style scoped>
.country-library {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--sp-4, 16px);
}

/* ===== 顶部状态栏 ===== */
.flag-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: var(--do-bg-card, #FFFFFF);
  border: 1px solid var(--do-border, #E2E8F0);
  border-radius: var(--radius-md, 8px);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.top-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.title-cluster {
  display: flex;
  align-items: center;
  gap: 8px;
}

.view-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--do-font-primary, #0F172A);
  letter-spacing: 0.3px;
}

.top-badges {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-badge {
  font-size: 13px;
  padding: 3px 10px;
  border-radius: 4px;
  background: var(--do-bg-sunken, #F8FAFC);
  border: 1px solid var(--do-border, #E2E8F0);
  color: var(--do-font-secondary, #64748B);
  font-weight: normal;
}

.info-badge.highlight {
  background: rgba(217, 119, 6, 0.08);
  border-color: rgba(217, 119, 6, 0.25);
  color: #B45309;
}

.info-badge.highlight .num-mono {
  font-weight: normal;
  color: #D97706;
}

.info-badge.muted {
  opacity: 0.8;
}

.btn-return-console {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 14px;
  font-size: 13px;
  font-weight: normal;
  color: #1E40AF;
  background: #EFF6FF;
  border: 1px solid #BFDBFE;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-return-console:hover {
  background: #DBEAFE;
  border-color: #93C5FD;
}

/* ===== 双栏主体布局 ===== */
.cl-layout {
  display: grid;
  grid-template-columns: minmax(0, 7.2fr) minmax(0, 4.8fr);
  gap: var(--gap-grid, 16px);
  align-items: start;
}

/* 公共 Panel Header */
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border-bottom: 1px solid var(--do-border, #E2E8F0);
  background: rgba(var(--th-shadow-rgb, 15, 23, 42), 0.02);
}

.header-title-box {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-accent-bar {
  width: 3px;
  height: 15px;
  border-radius: 2px;
  background: #2563EB;
}

.header-accent-bar.gold {
  background: var(--do-gold, #D97706);
}

.header-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--do-font-primary, #0F172A);
}

.header-badge {
  font-size: 13px;
  font-weight: normal;
  color: #D97706;
  background: rgba(217, 119, 6, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
}

.panel-subtitle {
  font-size: 13px;
  font-weight: normal;
  color: var(--do-font-secondary, #64748B);
}

.req-star {
  color: var(--do-danger, #EF4444);
  font-style: normal;
}

/* ===== 1. 左栏: 国家台账 ===== */
.cl-list {
  display: flex;
  flex-direction: column;
  min-width: 0;
  border-radius: var(--radius-md, 8px);
  background: var(--do-bg-card, #FFFFFF);
  border: 1px solid var(--do-border, #E2E8F0);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.cl-filter {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cl-region-select {
  width: 115px;
}

.cl-search-input {
  width: 240px;
}

.cl-table-wrap {
  overflow-y: auto;
  padding: 12px 16px 16px;
  max-height: calc(100vh - 210px);
}

.cm-table {
  border: 1px solid var(--do-border, #E2E8F0);
  border-radius: 6px;
  overflow: hidden;
  background: var(--do-bg-card, #FFFFFF);
}

.cm-row {
  display: grid;
  grid-template-columns: 50px 64px minmax(100px, 1.3fr) minmax(110px, 1.2fr) 78px minmax(140px, 1.5fr) 96px;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--do-border, #F1F5F9);
  font-size: 13px;
  transition: background 0.15s ease;
}

.cm-row:last-child {
  border-bottom: none;
}

.cm-row:hover {
  background: rgba(248, 250, 252, 0.9);
}

.cm-row.is-editing {
  background: rgba(217, 119, 6, 0.08);
  border-left: 3px solid #D97706;
}

.cm-row-head {
  background: var(--do-bg-sunken, #F8FAFC);
  color: var(--do-font-secondary, #64748B);
  font-weight: normal;
  font-size: 13px;
  letter-spacing: 0.03em;
  position: sticky;
  top: 0;
  z-index: 2;
  border-bottom: 1px solid var(--do-border, #E2E8F0);
}

/* 单元格视觉细节 */
.cm-swatch {
  width: 42px;
  height: 28px;
  display: block;
  border-radius: 3px;
  border: 1px solid rgba(15, 23, 42, 0.15);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}

.col-code {
  display: flex;
  flex-direction: column;
  gap: 2px;
  align-items: flex-start;
}

.code-pill {
  font-size: 13px;
  font-weight: 600;
  color: var(--do-font-primary, #0F172A);
  background: rgba(15, 23, 42, 0.05);
  padding: 1px 5px;
  border-radius: 3px;
  line-height: 1.2;
}

.code-alpha3-chip {
  font-size: 10px;
  font-weight: 500;
  color: #2563EB;
  background: rgba(37, 99, 235, 0.08);
  padding: 0 4px;
  border-radius: 2px;
  line-height: 1.2;
}

.anthem-row-play-btn {
  width: 20px;
  height: 20px;
  min-width: 20px;
  padding: 0;
  border-radius: 50%;
  border: 1px solid var(--do-border, #CBD5E1);
  background: var(--do-bg-sunken, #F8FAFC);
  color: var(--do-font-secondary, #475569);
  font-size: 9px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.anthem-row-play-btn:hover {
  background: #2563EB;
  border-color: #2563EB;
  color: #FFFFFF;
}

.anthem-row-play-btn.is-playing {
  background: #DC2626;
  border-color: #DC2626;
  color: #FFFFFF;
}

.btn-top-reset {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 12px;
  font-size: 13px;
  font-weight: 500;
  color: #047857;
  background: #ECFDF5;
  border: 1px solid #A7F3D0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-right: 8px;
}

.btn-top-reset:hover {
  background: #D1FAE5;
  border-color: #6EE7B7;
}

.name-cn-text {
  font-weight: normal;
  font-size: 13px;
  color: var(--do-font-primary, #0F172A);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
}

.name-en-text {
  font-weight: normal;
  font-size: 13px;
  color: var(--do-font-secondary, #64748B);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
}

.region-tag {
  font-weight: normal;
  font-size: 13px;
}

.anthem-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  overflow: hidden;
  min-width: 0;
}

.anthem-name-txt {
  font-weight: normal;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--do-font-primary, #0F172A);
}

.anthem-duration-chip {
  font-size: 13px;
  font-weight: normal;
  color: var(--do-font-secondary, #64748B);
  background: var(--do-bg-sunken, #F1F5F9);
  padding: 1px 6px;
  border-radius: 3px;
  flex-shrink: 0;
}

.col-ops {
  display: flex;
  align-items: center;
  gap: 6px;
}

.op-link-btn {
  background: transparent;
  border: none;
  outline: none;
  padding: 3px 8px;
  font-size: 13px;
  font-weight: normal;
  line-height: 1.4;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.op-link-btn.edit {
  color: #2563EB;
}

.op-link-btn.edit:hover {
  color: #1D4ED8;
  background: rgba(37, 99, 235, 0.08);
}

.op-link-btn.edit:active {
  background: rgba(37, 99, 235, 0.16);
}

.op-link-btn.del {
  color: #DC2626;
}

.op-link-btn.del:hover {
  color: #B91C1C;
  background: rgba(220, 38, 38, 0.08);
}

.op-link-btn.del:active {
  background: rgba(220, 38, 38, 0.16);
}

.cl-empty {
  padding: 40px 16px;
  text-align: center;
  color: var(--do-font-secondary, #64748B);
}

.cl-empty p {
  margin: 0;
  font-size: 14px;
  font-weight: normal;
}

.empty-sub {
  margin-top: 6px;
  font-size: 13px;
  font-weight: normal;
  color: #94A3B8;
  display: block;
}

/* ===== 2. 右栏: 录入 / 编辑表单 ===== */
.cl-form {
  display: flex;
  flex-direction: column;
  min-width: 0;
  border-radius: var(--radius-md, 8px);
  background: var(--do-bg-card, #FFFFFF);
  border: 1px solid var(--do-border, #E2E8F0);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.cl-form-body {
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-label {
  font-size: 13px;
  font-weight: normal;
  color: var(--do-font-secondary, #64748B);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  display: flex;
  align-items: center;
  gap: 6px;
}

.section-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-picker-action {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  font-size: 13px;
  font-weight: normal;
  color: #2563EB;
  background: #EFF6FF;
  border: 1px solid #BFDBFE;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-picker-action:hover {
  background: #DBEAFE;
}

.btn-upload-action {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  font-size: 13px;
  font-weight: normal;
  color: #334155;
  background: var(--do-bg-sunken, #F1F5F9);
  border: 1px solid var(--do-border, #CBD5E1);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-upload-action:hover {
  background: #E2E8F0;
}

.cm-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 14px;
}

.cm-field {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 0;
}

.cm-field label {
  font-size: 13px;
  font-weight: normal;
  color: var(--do-font-primary, #1E293B);
}

/* 资产绑定状态卡片 */
.bind-status-card {
  border: 1px dashed var(--do-border, #CBD5E1);
  border-radius: 6px;
  background: var(--do-bg-sunken, #F8FAFC);
  padding: 10px 14px;
  transition: all 0.2s ease;
}

.bind-status-card.has-asset {
  border-style: solid;
  border-color: #BFDBFE;
  background: #F8FAFC;
}

.bound-asset-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.flag-stage-box {
  width: 54px;
  height: 36px;
  border-radius: 3px;
  border: 1px solid rgba(15, 23, 42, 0.2);
  overflow: hidden;
  background: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.bound-flag-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.audio-stage-icon {
  width: 44px;
  height: 44px;
  font-size: 20px;
  border-radius: 6px;
  background: #EFF6FF;
  border: 1px solid #BFDBFE;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.bound-asset-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.meta-tag-line {
  display: flex;
  align-items: center;
  gap: 6px;
}

.source-tag {
  font-size: 13px;
  font-weight: normal;
  padding: 1px 6px;
  border-radius: 3px;
}

.source-library {
  color: #1D4ED8;
  background: #EFF6FF;
  border: 1px solid #BFDBFE;
}

.source-local {
  color: #047857;
  background: #ECFDF5;
  border: 1px solid #A7F3D0;
}

.format-tag {
  font-size: 13px;
  font-weight: normal;
  color: var(--do-font-secondary, #64748B);
  background: rgba(15, 23, 42, 0.05);
  padding: 1px 5px;
  border-radius: 3px;
}

.bound-asset-name {
  font-size: 13px;
  font-weight: normal;
  color: var(--do-font-primary, #0F172A);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.audio-ctrl-btns {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-audio-preview {
  padding: 4px 10px;
  font-size: 13px;
  font-weight: normal;
  color: #047857;
  background: #ECFDF5;
  border: 1px solid #A7F3D0;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-audio-preview:hover {
  background: #D1FAE5;
}

.btn-unlink-asset {
  padding: 4px 8px;
  font-size: 13px;
  font-weight: normal;
  color: #DC2626;
  background: #FEF2F2;
  border: 1px solid #FECACA;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-unlink-asset:hover {
  background: #FEE2E2;
}

.empty-bind-placeholder {
  padding: 8px 0;
  text-align: center;
}

.placeholder-tip {
  font-size: 13px;
  font-weight: normal;
  color: #94A3B8;
}

/* 实时效果看板 */
.cl-live-preview {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 16px;
  border-radius: 8px;
  background: var(--do-bg-sunken, #F8FAFC);
  border: 1px solid var(--do-border, #E2E8F0);
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.03);
}

.preview-flag-stage {
  flex-shrink: 0;
}

.preview-flag-drape {
  width: 66px;
  height: 44px;
  display: block;
  border-radius: 4px;
  border: 1px solid rgba(15, 23, 42, 0.15);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.preview-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  flex: 1;
}

.pm-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.pm-name {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--do-font-primary, #0F172A);
}

.pm-code {
  font-size: 13px;
  font-weight: normal;
  color: #1E293B;
  background: #E2E8F0;
  padding: 1px 6px;
  border-radius: 3px;
}

.pm-sub-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: normal;
  color: var(--do-font-secondary, #64748B);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pm-en {
  font-weight: normal;
}

.pm-sep {
  opacity: 0.6;
}

.pm-anthem {
  color: #B45309;
  font-weight: normal;
}

/* 表单操作区 */
.cm-form-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-top: 6px;
  border-top: 1px solid var(--do-border, #E2E8F0);
}

.btn-submit-gold {
  flex: 1;
  height: 36px;
  padding: 0 18px;
  font-size: 14px;
  font-weight: normal;
  color: #FFFFFF;
  background: #D97706;
  border: 1px solid #B45309;
  border-radius: 6px;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(217, 119, 6, 0.2);
  transition: all 0.2s ease;
}

.btn-submit-gold:hover {
  background: #B45309;
}

.btn-reset-form {
  height: 36px;
  padding: 0 16px;
  font-size: 13px;
  font-weight: normal;
  color: var(--do-font-secondary, #64748B);
  background: var(--do-bg-sunken, #F1F5F9);
  border: 1px solid var(--do-border, #CBD5E1);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-reset-form:hover {
  background: #E2E8F0;
  color: var(--do-font-primary, #0F172A);
}

.btn-cancel-edit {
  height: 36px;
  padding: 0 14px;
  font-size: 13px;
  font-weight: normal;
  color: #DC2626;
  background: #FEF2F2;
  border: 1px solid #FECACA;
  border-radius: 6px;
  cursor: pointer;
}

.btn-cancel-edit:hover {
  background: #FEE2E2;
}

/* ==================== 素材挑选专属弹窗样式 ==================== */
.asset-picker-container {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.picker-filter-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px 14px;
  background: var(--do-bg-sunken, #F8FAFC);
  border: 1px solid var(--do-border, #E2E8F0);
  border-radius: 6px;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.filter-lbl {
  font-size: 13px;
  font-weight: normal;
  color: var(--do-font-secondary, #64748B);
}

.search-item {
  margin-left: auto;
}

.picker-assets-scroll {
  max-height: 420px;
  overflow-y: auto;
  border: 1px solid var(--do-border, #E2E8F0);
  border-radius: 6px;
  padding: 8px;
}

.picker-assets-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.asset-choice-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: #FFFFFF;
  border: 1px solid var(--do-border, #E2E8F0);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.asset-choice-card:hover {
  background: #F8FAFC;
  border-color: #93C5FD;
}

.asset-choice-card.is-selected {
  background: #EFF6FF;
  border-color: #2563EB;
  box-shadow: 0 0 0 1px #2563EB;
}

.acc-badge-col {
  flex-shrink: 0;
}

.acc-format-badge {
  display: inline-block;
  font-size: 13px;
  font-weight: normal;
  padding: 3px 8px;
  border-radius: 4px;
  color: #FFFFFF;
  background: #64748B;
  min-width: 44px;
  text-align: center;
}

.acc-format-badge.document {
  background: #D97706;
}

.acc-format-badge.audio {
  background: #2563EB;
}

.acc-format-badge.video {
  background: #059669;
}

.acc-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.acc-title-line {
  display: flex;
  align-items: center;
  gap: 8px;
}

.acc-name {
  font-size: 13px;
  font-weight: normal;
  color: var(--do-font-primary, #0F172A);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.acc-meta-line {
  display: flex;
  align-items: center;
  gap: 8px;
}

.acc-pill {
  font-size: 13px;
  font-weight: normal;
  padding: 1px 6px;
  border-radius: 3px;
}

.cat-pill {
  color: #1D4ED8;
  background: #DBEAFE;
}

.grp-pill {
  color: #B45309;
  background: #FEF3C7;
}

.acc-spec {
  font-size: 13px;
  font-weight: normal;
  color: var(--do-font-secondary, #64748B);
}

.acc-remark {
  font-size: 13px;
  font-weight: normal;
  color: #94A3B8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.acc-select-col {
  flex-shrink: 0;
}

.selected-checkmark {
  font-size: 13px;
  font-weight: normal;
  color: #2563EB;
}

.select-hint-txt {
  font-size: 13px;
  font-weight: normal;
  color: #94A3B8;
}

.picker-empty-box {
  padding: 40px 16px;
  text-align: center;
  color: var(--do-font-secondary, #64748B);
}

.picker-empty-box p {
  margin: 0;
  font-size: 14px;
  font-weight: normal;
}

.pe-sub {
  margin-top: 6px;
  font-size: 13px;
  font-weight: normal;
  color: #94A3B8;
  display: block;
}

.picker-dialog-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.pdf-selected-tip {
  font-size: 13px;
  font-weight: normal;
  color: var(--do-font-secondary, #64748B);
}

.pdf-selected-tip strong {
  color: var(--do-font-primary, #0F172A);
  font-weight: normal;
}

.pdf-btns {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ===== 响应式适配 ===== */
@media (max-width: 1280px) {
  .cl-layout {
    grid-template-columns: minmax(0, 1fr);
  }

  .cl-table-wrap {
    max-height: 500px;
  }
}
</style>
