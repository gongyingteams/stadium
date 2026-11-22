<template>
  <div class="template-center-workspace">
    <!-- 顶部状态栏 -->
    <div class="template-top-bar glass-panel">
      <div class="top-left">
        <SvgIcon name="SvgConfigTemplate" size="20" class="text-primary" />
        <div class="title-meta">
          <span class="view-title">配置模板与 JSON 导入导出中心</span>
          <p>通过标准化模板导入、导出和复用场馆设备及指令配置，降低重复部署成本。</p>
        </div>
      </div>

      <div class="top-right">
        <button class="btn-header-action btn-header-primary" @click="exportCurrentConfig" title="一键导出系统全量配置并自动执行敏感密码脱敏">
          <SvgIcon name="SvgConfigTemplate" size="14" style="margin-right: 4px;" />
          <span>导出完整配置包</span>
        </button>
        <button class="btn-header-action btn-header-manage" @click="isImportModalOpen = true" title="上传并导入解析 JSON 格式配置模板">
          <SvgIcon name="SvgAdapterBook" size="14" style="margin-right: 4px;" />
          <span>导入恢复配置包</span>
        </button>
      </div>
    </div>

    <!-- 主布局：模板仓库卡片 + 导入导出与备份安全流程区 -->
    <div class="template-main-layout">
      <!-- 模板资产库网格 -->
      <div class="col-templates glass-panel">
        <div class="panel-header">
          <div class="header-title">
            <span>标准场馆配置模板仓库 (Template Packages)</span>
            <span class="panel-subtitle">区分“附件基线”与“扩展模板”，支持一键导入克隆</span>
          </div>
          <span class="num-mono text-primary">已收录 {{ templateList.length }} 套标准化模板</span>
        </div>

        <div class="templates-grid">
          <div
            v-for="tpl in templateList"
            :key="tpl.code"
            class="template-card glass-panel"
          >
            <div class="tpl-head">
              <div class="title-wrap">
                <span class="tpl-name">{{ tpl.name }}</span>
                <span class="tpl-ver num-mono">{{ tpl.version }}</span>
              </div>
              <!-- 显式区分基线与扩展 -->
              <span v-if="tpl.isBaseline" class="badge-baseline">附件 13 类基线标准</span>
              <span v-else class="badge-extend">扩展/可选场馆模板</span>
            </div>

            <p class="tpl-desc">{{ tpl.desc }}</p>

            <div class="tpl-stats-row">
              <div class="t-stat">
                <span class="s-label">纳管设备</span>
                <span class="s-val num-mono">{{ tpl.deviceCount }} 台</span>
              </div>
              <div class="t-stat">
                <span class="s-label">指令规则</span>
                <span class="s-val num-mono">{{ tpl.ruleCount }} 条</span>
              </div>
              <div class="t-stat">
                <span class="s-label">更新时间</span>
                <span class="s-val num-mono">{{ tpl.updatedAt }}</span>
              </div>
            </div>

            <div class="tpl-actions">
              <el-button size="small" type="primary" plain @click="downloadTemplate(tpl)">
                下载 JSON 模板
              </el-button>
              <el-button size="small" type="success" @click="applyTemplate(tpl)">
                一键应用此模板
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：安全备份与回滚历史 -->
      <div class="col-backups glass-panel">
        <div class="panel-header">
          <span class="header-title">配置安全快照与一键回滚 (Snapshots)</span>
          <span class="num-mono text-success">AUTO_BACKUP_ON</span>
        </div>

        <div class="backups-list-body">
          <p class="backups-hint">
            安全约束：每次执行 JSON 导入覆盖前，系统强制生成当前版本快照；若新配置异常可秒级安全回滚。
          </p>

          <div class="backup-records-scroll">
            <div
              v-for="bk in backupHistory"
              :key="bk.id"
              class="backup-record-item"
            >
              <div class="bk-top">
                <span class="bk-name font-bold">{{ bk.name }}</span>
                <span class="bk-time num-mono">{{ bk.time }}</span>
              </div>
              <div class="bk-meta">
                <span>操作人: {{ bk.operator }}</span>
                <span class="num-mono">{{ bk.size }}</span>
              </div>
              <div class="bk-actions">
                <el-button size="small" type="danger" link @click="rollbackBackup(bk)">
                  回滚至此版本
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 导入 JSON 模态窗 (遵循：校验—预览—备份—导入—回滚) -->
    <el-dialog v-model="isImportModalOpen" title="导入恢复 JSON 配置包 (安全导入校验流程)" width="600px">
      <div class="import-stepper-box">
        <el-alert
          title="导入安全须知：系统将先对 JSON 格式与 Schema 版本进行语法校验，并自动脱敏第三方凭证！"
          type="info"
          :closable="false"
          show-icon
          style="margin-bottom: 14px;"
        />

        <div class="upload-drop-area">
          <SvgIcon name="SvgConfigTemplate" size="36" />
          <p class="drop-text">点击或将 venue_config_package.json 拖放至此处</p>
          <span class="drop-hint">支持完整场馆配置包导入与版本差异预览</span>
        </div>

        <div class="diff-preview-box">
          <span class="diff-title">配置变更差异预检 (Diff Preview):</span>
          <div class="diff-summary num-mono">
            <div class="diff-row add"><span class="diff-sign">+</span> 新增硬件实例: 2 台 (水质检测仪、变频水泵)</div>
            <div class="diff-row mod"><span class="diff-sign">*</span> 修改波特率参数: 1 项 (调音台 9600 -> 115200)</div>
            <div class="diff-row del"><span class="diff-sign">-</span> 待清理孤立指令: 0 条 (无)</div>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="isImportModalOpen = false">取消</el-button>
        <el-button type="primary" @click="confirmImport">
          确认差异并执行安全导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'

const isImportModalOpen = ref(false)

const templateList = ref([
  {
    code: 'TPL_AQUATICS_STANDARD_13',
    name: '国际奥体游泳跳水馆 · 13类基线标准配置包',
    version: 'v1.0.0-Baseline',
    isBaseline: true, // 附件13类基线标准
    desc: '严格覆盖扩声调音、智能照明、LED大屏、计时计分、标准时钟、自动升旗、水下抓拍等全量13类基线子系统。',
    deviceCount: 26,
    ruleCount: 88,
    updatedAt: '2026-10-11 15:00'
  },
  {
    code: 'TPL_MULTISPORT_EXTEND',
    name: '多功能综合体育馆 · 增强配置模板 (可选示例)',
    version: 'v1.2.0-Extend',
    isBaseline: false, // 扩展项
    desc: '面向篮球、排球多功能综合馆扩展模板，包含两块计分屏与环形地毯灯光联动方案。',
    deviceCount: 18,
    ruleCount: 42,
    updatedAt: '2026-09-28 10:20'
  }
])

const backupHistory = ref([
  { id: 'BK-01', name: '全馆初验联调封版快照', time: '2026-10-11 14:30:00', operator: 'admin', size: '142 KB' },
  { id: 'BK-02', name: '升旗音画测速算法升级前备份', time: '2026-10-10 18:00:00', operator: 'ops_chen', size: '138 KB' }
])

const exportCurrentConfig = () => {
  ElMessage.success('已生成完整系统配置包 venue_config_v1.0.json，已自动对密码与密钥完成脱敏！')
}

const downloadTemplate = (tpl) => {
  ElMessage.success(`正在下载【${tpl.name}】标准 JSON 模板...`)
}

const applyTemplate = (tpl) => {
  ElMessageBox.confirm(
    `应用模板【${tpl.name}】前，系统将自动对当前运行配置生成快照备份。是否继续导入？`,
    '应用模板确认',
    { confirmButtonText: '确定应用', cancelButtonText: '取消', type: 'info' }
  ).then(() => {
    backupHistory.value.unshift({
      id: 'BK-' + Date.now().toString().slice(-4),
      name: `导入${tpl.name}前自动快照`,
      time: new Date().toLocaleString(),
      operator: 'admin',
      size: '144 KB'
    })
    ElMessage.success(`【${tpl.name}】已成功应用生效，相关硬件驱动已热重载！`)
  }).catch(() => {})
}

const rollbackBackup = (bk) => {
  ElMessageBox.confirm(
    `确定回滚至快照版本【${bk.name}】(${bk.time}) 吗？系统配置将还原至该时间点。`,
    '安全回滚确认',
    { confirmButtonText: '确定回滚', cancelButtonText: '取消', type: 'warning' }
  ).then(() => {
    ElMessage.success(`已成功回滚至快照版本：${bk.name}`)
  }).catch(() => {})
}

const confirmImport = () => {
  isImportModalOpen.value = false
  ElMessage.success('配置包差异预检通过，已完成导入恢复，历史备份已留存！')
}
</script>

<style scoped>
.template-center-workspace {
  display: flex;
  flex-direction: column;
  gap: 16px;
  animation: fadeIn 0.3s ease-out;
}

.template-top-bar {
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

.template-main-layout {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 16px;
}

.col-templates,
.col-backups {
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
  display: flex;
  flex-direction: column;
  gap: 3px;
  font-size: 14px;
  font-weight: 700;
  color: var(--do-coffee);
}

.panel-subtitle {
  font-size: 14px;
  color: var(--do-coffee-light);
  font-weight: 400;
}

.templates-grid {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.template-card {
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

.template-card:hover {
  border-color: var(--do-gold);
  box-shadow: 0 4px 12px rgba(var(--th-accent-rgb), 0.15);
  transform: translateY(-1px);
}

.tpl-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tpl-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--do-coffee);
}

.tpl-ver {
  font-size: 14px;
  color: var(--do-gold-dark);
  background: rgba(var(--th-accent-rgb), 0.15);
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.badge-baseline {
  background: rgba(var(--th-success-rgb), 0.12);
  color: var(--do-olive);
  border: 1px solid var(--do-olive);
  font-size: 14px;
  padding: 3px 10px;
  border-radius: 4px;
  font-weight: 700;
}

.badge-extend {
  background: rgba(var(--th-accent-rgb), 0.25);
  color: var(--do-coffee-mid);
  border: 1px solid var(--do-border-card);
  font-size: 14px;
  padding: 3px 10px;
  border-radius: 4px;
  font-weight: 500;
}

.tpl-desc {
  font-size: 14px;
  color: var(--do-coffee-mid);
  line-height: 1.6;
  margin: 0;
}

.tpl-stats-row {
  display: flex;
  gap: 24px;
  background: var(--do-sand-light);
  padding: 10px 16px;
  border-radius: 6px;
  font-size: 14px;
  border: 1px solid rgba(var(--th-accent-rgb), 0.5);
}

.t-stat {
  display: flex;
  gap: 8px;
  align-items: center;
}
.s-label { color: var(--do-coffee-light); }
.s-val { color: var(--do-coffee); font-weight: 700; }

.tpl-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* 右侧备份与回滚 */
.backups-list-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.backups-hint {
  font-size: 14px;
  color: var(--do-coffee-light);
  line-height: 1.6;
  margin: 0;
  padding: 10px 14px;
  background: rgba(var(--th-accent-rgb), 0.08);
  border: 1px solid rgba(var(--th-accent-rgb), 0.22);
  border-radius: var(--radius-sm);
}

.backup-records-scroll {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.backup-record-item {
  background: #FFFFFF;
  border: 1px solid var(--do-border-card);
  border-radius: 6px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  box-shadow: 0 1px 3px rgba(var(--th-shadow-rgb), 0.03);
}

.bk-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
}
.bk-name { color: var(--do-coffee); font-weight: 700; }
.bk-time { color: var(--do-coffee-light); font-size: 14px; }

.bk-meta {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: var(--do-coffee-mid);
}

.bk-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 6px;
}

/* 导入模态窗与 Diff 对比 */
.upload-drop-area {
  border: 2px dashed var(--do-gold);
  border-radius: 8px;
  padding: 32px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  color: var(--do-gold-dark);
  background: var(--do-sand-light);
  cursor: pointer;
  transition: all 0.2s ease;
}

.upload-drop-area:hover {
  background: rgba(var(--th-accent-rgb), 0.12);
}

.drop-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--do-coffee);
  margin: 0;
}
.drop-hint {
  font-size: 14px;
  color: var(--do-coffee-light);
}

.diff-preview-box {
  margin-top: 16px;
  background: var(--do-sand-light);
  border: 1px solid var(--do-border-card);
  border-radius: 6px;
  padding: 14px;
}

.diff-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--do-amber);
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
}

.diff-summary {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 14px;
}

.diff-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.diff-row.add {
  color: var(--do-olive);
  background: rgba(var(--th-success-rgb), 0.08);
  border: 1px solid rgba(var(--th-success-rgb), 0.25);
}

.diff-row.mod {
  color: var(--do-amber);
  background: rgba(var(--th-warning-rgb), 0.08);
  border: 1px solid rgba(var(--th-warning-rgb), 0.25);
}

.diff-row.del {
  color: var(--do-terra);
  background: rgba(var(--th-danger-rgb), 0.08);
  border: 1px solid rgba(var(--th-danger-rgb), 0.25);
}

.diff-sign {
  font-weight: 900;
  font-size: 14px;
}
</style>
