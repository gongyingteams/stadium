<template>
  <div class="user-role-workspace">
    <!-- 1. 顶部状态与安全态势总控栏 -->
    <div class="role-top-bar glass-panel">
      <div class="top-left">
        <div class="icon-cube">
          <SvgIcon name="SvgUserRole" size="22" />
        </div>
        <div class="title-meta">
          <div class="title-main-row">
            <span class="view-title">用户角色管理与细粒度权限配置中心</span>
            <span class="security-level-pill">
              <span class="pulse-dot"></span>
              RBAC 3.0 物理隔离级防御生效中
            </span>
          </div>
          <p class="sub-meta-txt">支持系统菜单、页面组件、业务按钮及底层物联硬件控制指令的细粒度三维隔离授权。</p>
        </div>
      </div>

      <div class="top-right">
        <button class="btn-header-action btn-header-manage" @click="openCreateUserModal" title="新建平台登录工号并分配基础角色">
          <SvgIcon name="SvgUserRole" size="14" style="margin-right: 4px;" />
          <span>新建用户账号</span>
        </button>
        <button class="btn-header-action btn-header-manage" @click="openCreateRoleModal" title="新增业务岗位角色定义">
          <SvgIcon name="SvgSecurityShield" size="14" style="margin-right: 4px;" />
          <span>新建系统角色</span>
        </button>
        <button
          class="btn-header-action btn-header-primary"
          :disabled="isSavingPolicy"
          @click="saveRolePermissions"
          title="固化并保存当前角色对菜单、组件与指令的访问控制策略"
        >
          <el-icon><Check /></el-icon>
          <span>{{ isSavingPolicy ? '正在保存策略...' : '固化并保存权限策略' }}</span>
        </button>
      </div>
    </div>

    <!-- 2. RBAC 安全态势 KPI 指标卡片 -->
    <div class="security-kpi-grid">
      <div class="kpi-card">
        <div class="kpi-icon-box gold">
          <el-icon><UserFilled /></el-icon>
        </div>
        <div class="kpi-content">
          <span class="kpi-label">受控用户总数</span>
          <div class="kpi-val-row">
            <span class="kpi-number num-mono">{{ userList.length }}</span>
            <span class="kpi-unit">人</span>
            <span class="kpi-sub-pill normal">正常活跃: {{ userList.filter(u => u.status === 'NORMAL').length }}</span>
          </div>
        </div>
      </div>

      <div class="kpi-card">
        <div class="kpi-icon-box coffee">
          <el-icon><Key /></el-icon>
        </div>
        <div class="kpi-content">
          <span class="kpi-label">已配置角色</span>
          <div class="kpi-val-row">
            <span class="kpi-number num-mono">{{ roleList.length }}</span>
            <span class="kpi-unit">套</span>
            <span class="kpi-sub-pill builtin">内置: 4 · 自定义: {{ roleList.length - 4 }}</span>
          </div>
        </div>
      </div>

      <div class="kpi-card">
        <div class="kpi-icon-box green">
          <el-icon><Setting /></el-icon>
        </div>
        <div class="kpi-content">
          <span class="kpi-label">细粒度权限节点</span>
          <div class="kpi-val-row">
            <span class="kpi-number num-mono">36</span>
            <span class="kpi-unit">项</span>
            <span class="kpi-sub-pill safe">按钮级指令: 18项</span>
          </div>
        </div>
      </div>

      <div class="kpi-card">
        <div class="kpi-icon-box red">
          <el-icon><Lock /></el-icon>
        </div>
        <div class="kpi-content">
          <span class="kpi-label">操作员防呆隔离率</span>
          <div class="kpi-val-row">
            <span class="kpi-number num-mono text-success">100%</span>
            <span class="kpi-sub-pill danger">通讯配置物理拦截</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 3. 主体标签页导航：角色与权限矩阵 VS 用户账号名录 -->
    <div class="main-tabs-container glass-panel">
      <el-tabs v-model="activeTab" class="sahara-styled-tabs">
        <!-- 标签页 1: 角色权限授权矩阵 -->
        <el-tab-pane label="角色名录与细粒度权限配置" name="roles">
          <div class="role-perm-matrix-layout">
            <!-- 左栏：系统角色名录卡片列表 -->
            <div class="col-role-list">
              <div class="section-card-header">
                <div class="header-title-wrap">
                  <span class="section-title-txt">系统角色清单 ({{ roleList.length }}类)</span>
                  <span class="section-subtitle-txt">选择角色以配置其权限树</span>
                </div>
                <el-button link type="primary" size="small" class="btn-link-gold" @click="openCreateRoleModal">
                  + 新增
                </el-button>
              </div>

              <!-- 角色卡片列表 -->
              <div class="role-cards-scroll">
                <div
                  v-for="r in roleList"
                  :key="r.code"
                  :class="['role-entry-card', { active: selectedRoleCode === r.code }]"
                  @click="selectRole(r)"
                >
                  <div class="role-entry-top">
                    <div class="role-title-row">
                      <span class="role-name-txt">{{ r.name }}</span>
                      <span v-if="r.isBuiltin" class="tag-pill builtin">系统内置</span>
                      <span v-else class="tag-pill custom">自定义</span>
                    </div>
                    <span :class="['sec-level-badge', r.secLevel]">
                      {{ r.secLevelText }}
                    </span>
                  </div>

                  <p class="role-desc-txt">{{ r.desc }}</p>

                  <div class="role-entry-footer">
                    <span class="role-code-badge num-mono">{{ r.code }}</span>
                    <span class="role-user-stat">
                      <el-icon class="mr-1"><User /></el-icon>
                      已分配 <strong>{{ r.userCount }}</strong> 人
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 右栏：菜单与按钮级细粒度权限树配置 -->
            <div class="col-perm-details">
              <div class="section-card-header">
                <div class="header-title-wrap">
                  <div class="current-role-badge-row">
                    <span class="section-title-txt">当前授权对象: 【{{ currentRole.name }}】</span>
                    <span class="current-role-code num-mono">({{ currentRole.code }})</span>
                  </div>
                  <span class="section-subtitle-txt">
                    已勾选 <strong>{{ currentSelectedCount }}</strong> / 36 个控制节点，保存后立即对该角色下全量用户热生效
                  </span>
                </div>

                <div class="tree-quick-actions">
                  <el-button size="small" @click="expandAllTree(true)">全部展开</el-button>
                  <el-button size="small" @click="expandAllTree(false)">全部折叠</el-button>
                  <el-button size="small" @click="checkAllTree(true)">一键全选</el-button>
                  <el-button size="small" @click="checkAllTree(false)">清空勾选</el-button>
                </div>
              </div>

              <!-- 防呆隔离警告横幅 (专为操作员或受限角色) -->
              <transition name="fade">
                <div v-if="selectedRoleCode === 'operator'" class="operator-security-fence">
                  <div class="fence-icon">
                    <el-icon :size="20"><Lock /></el-icon>
                  </div>
                  <div class="fence-content">
                    <span class="fence-title">重大赛事现场操作员防呆与物理安全硬隔离红线</span>
                    <p class="fence-desc">
                      场馆操作员仅限触发日常赛事预设音效、灯光模式及大屏推屏等操作控件；<strong>底层通信协议（串口/波特率/IP端口）、自定义HEX报文编辑、模拟沙箱及急停配置已被底层拦截</strong>，即使勾选亦无法生效。
                    </p>
                  </div>
                </div>
              </transition>

              <!-- 权限树过滤搜索栏 -->
              <div class="tree-filter-bar">
                <el-input
                  v-model="permSearchKeyword"
                  size="small"
                  placeholder="搜索权限名称、控制代码 (例如: 推屏, 波特率, 急停, 音响)"
                  clearable
                  style="width: 320px;"
                  @input="filterPermTree"
                >
                  <template #prefix>
                    <el-icon><Search /></el-icon>
                  </template>
                </el-input>

                <div class="legend-pills">
                  <span class="legend-item"><span class="dot-icon menu"></span>菜单级</span>
                  <span class="legend-item"><span class="dot-icon action"></span>按钮控制</span>
                  <span class="legend-item"><span class="dot-icon risk"></span>高危指令</span>
                  <span class="legend-item"><span class="dot-icon protocol"></span>敏感底层协议</span>
                </div>
              </div>

              <!-- 核心权限树体 -->
              <div class="tree-viewport">
                <el-tree
                  ref="permTreeRef"
                  :data="permTreeData"
                  show-checkbox
                  node-key="id"
                  default-expand-all
                  :filter-node-method="filterNodeMethod"
                  :default-checked-keys="currentCheckedKeys"
                  class="sahara-styled-tree"
                  @check="handleTreeCheck"
                >
                  <template #default="{ node, data }">
                    <div class="custom-tree-node-row">
                      <span class="node-main-label">
                        <el-icon v-if="data.children" class="node-icon folder"><FolderOpened /></el-icon>
                        <el-icon v-else class="node-icon leaf"><Key /></el-icon>
                        <span>{{ node.label }}</span>
                      </span>

                      <div class="node-tags-row">
                        <span v-if="data.code" class="code-tag num-mono">{{ data.code }}</span>
                        <span v-if="data.isHighRisk" class="tag-danger-pill">
                          <el-icon><Warning /></el-icon> 高危硬件指令
                        </span>
                        <span v-if="data.isProtocolConfig" class="tag-protocol-pill">
                          <el-icon><Lock /></el-icon> 敏感通信配置
                        </span>
                        <span v-if="data.isSafeAction" class="tag-safe-pill">常规运行</span>
                      </div>
                    </div>
                  </template>
                </el-tree>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- 标签页 2: 用户账号名录与角色指派 -->
        <el-tab-pane label="用户账号名录与身份管理" name="users">
          <div class="user-management-panel">
            <!-- 顶部过滤与动作栏 -->
            <div class="user-filter-toolbar">
              <div class="filter-inputs">
                <el-input
                  v-model="userSearchKeyword"
                  size="small"
                  placeholder="搜索用户名、姓名、工号或手机号"
                  clearable
                  style="width: 260px;"
                >
                  <template #prefix>
                    <el-icon><Search /></el-icon>
                  </template>
                </el-input>

                <el-select
                  v-model="userRoleFilter"
                  size="small"
                  placeholder="角色筛选"
                  clearable
                  style="width: 150px;"
                >
                  <el-option label="全部系统角色" value="" />
                  <el-option
                    v-for="r in roleList"
                    :key="r.code"
                    :label="r.name"
                    :value="r.code"
                  />
                </el-select>

                <el-select
                  v-model="userDeptFilter"
                  size="small"
                  placeholder="所属部门"
                  clearable
                  style="width: 160px;"
                >
                  <el-option label="全部保障部门" value="" />
                  <el-option label="弱电智能工程处" value="弱电工程处" />
                  <el-option label="赛事技术保障部" value="赛事保障部" />
                  <el-option label="总控运行调度中心" value="总控调度中心" />
                  <el-option label="场馆领导办公室" value="领导办公室" />
                </el-select>

                <el-select
                  v-model="userStatusFilter"
                  size="small"
                  placeholder="账号状态"
                  clearable
                  style="width: 120px;"
                >
                  <el-option label="全部状态" value="" />
                  <el-option label="正常活跃" value="NORMAL" />
                  <el-option label="临时锁定" value="DISABLED" />
                </el-select>
              </div>

              <div class="filter-actions">
                <el-button size="small" type="primary" class="gold-btn-primary" @click="openCreateUserModal">
                  <el-icon class="mr-1"><Plus /></el-icon>
                  新增用户账号
                </el-button>
              </div>
            </div>

            <!-- 用户数据表格：保留固定列与行内操作，外层提供局部横向滚动 -->
            <div class="user-table-scroll">
              <el-table
                :data="filteredUserList"
                stripe
                class="sahara-styled-table user-table"
                style="width: 100%;"
              >
              <el-table-column label="工号" prop="empNo" width="115">
                <template #default="{ row }">
                  <span class="emp-no-pill num-mono">{{ row.empNo }}</span>
                </template>
              </el-table-column>

              <el-table-column label="用户信息" min-width="160">
                <template #default="{ row }">
                  <div class="user-profile-cell">
                    <div class="avatar-circle">
                      {{ row.realName.slice(0, 1) }}
                    </div>
                    <div class="profile-info">
                      <span class="user-real-name">{{ row.realName }}</span>
                      <span class="user-username num-mono">@{{ row.username }}</span>
                    </div>
                  </div>
                </template>
              </el-table-column>

              <el-table-column label="所属部门 / 业务组" prop="dept" min-width="150" />

              <el-table-column label="已绑定角色" min-width="140">
                <template #default="{ row }">
                  <span :class="['role-tag-badge', row.roleCode]">
                    {{ getRoleName(row.roleCode) }}
                  </span>
                </template>
              </el-table-column>

              <el-table-column label="联系电话" prop="phone" width="130">
                <template #default="{ row }">
                  <span class="num-mono">{{ row.phone }}</span>
                </template>
              </el-table-column>

              <el-table-column label="账号状态" width="105" align="center">
                <template #default="{ row }">
                  <el-tag
                    :type="row.status === 'NORMAL' ? 'success' : 'danger'"
                    size="small"
                    class="status-tag"
                  >
                    {{ row.status === 'NORMAL' ? '正常活跃' : '临时停用' }}
                  </el-tag>
                </template>
              </el-table-column>

              <el-table-column label="最后登录时间" prop="lastLogin" width="160">
                <template #default="{ row }">
                  <span class="num-mono text-muted">{{ row.lastLogin }}</span>
                </template>
              </el-table-column>

              <el-table-column label="动作操作" width="220" align="center" fixed="right">
                <template #default="{ row }">
                  <div class="user-row-actions">
                    <el-button link type="primary" size="small" @click="openEditUser(row)">
                      编辑
                    </el-button>
                    <el-button link type="primary" size="small" @click="openAssignRole(row)">
                      改配角色
                    </el-button>
                    <el-button link type="primary" size="small" @click="viewUserEffectivePerms(row)">
                      权限透视
                    </el-button>
                    <el-button
                      link
                      :type="row.status === 'NORMAL' ? 'danger' : 'success'"
                      size="small"
                      @click="toggleUserStatus(row)"
                    >
                      {{ row.status === 'NORMAL' ? '停用' : '启用' }}
                    </el-button>
                  </div>
                </template>
              </el-table-column>
              </el-table>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 弹窗 1: 新建/编辑角色弹窗 -->
    <el-dialog
      v-model="roleModalVisible"
      :title="isEditRole ? '编辑系统角色与安全级别' : '登记新增系统角色'"
      width="min(540px, calc(100vw - 32px))"
      append-to-body
      destroy-on-close
      class="gold-styled-dialog"
    >
      <el-form label-position="top" :model="roleForm" class="dialog-standard-form">
        <el-form-item label="角色名称" required>
          <el-input v-model="roleForm.name" placeholder="例如: 裁判运行高级主管, 现场电力保障员" />
        </el-form-item>

        <el-form-item label="角色英文唯一标识码 (Code)" required>
          <el-input
            v-model="roleForm.code"
            :disabled="isEditRole && currentRoleToEdit?.isBuiltin"
            placeholder="例如: referee_lead, power_guard (英文字母/下划线)"
          />
        </el-form-item>

        <el-form-item label="安全防御防护等级">
          <el-select v-model="roleForm.secLevel" style="width: 100%;">
            <el-option label="Level 1 - 核心最高 (允许底层协议与沙箱)" value="L1" />
            <el-option label="Level 2 - 运维工程师 (允许排查调优与硬件检测)" value="L2" />
            <el-option label="Level 3 - 现场操作员 (严格防呆硬隔离)" value="L3" />
            <el-option label="Level 4 - 观察员只读 (仅大屏与监控态势查看)" value="L4" />
          </el-select>
        </el-form-item>

        <el-form-item label="克隆现有角色权限模板 (快速预设)">
          <el-select v-model="roleForm.cloneFrom" placeholder="可选：继承并克隆现有角色的权限勾选" style="width: 100%;">
            <el-option label="不克隆 (创建空白权限角色)" value="" />
            <el-option
              v-for="r in roleList"
              :key="r.code"
              :label="`继承【${r.name}】(${r.code})`"
              :value="r.code"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="角色职责与授权范围备忘">
          <el-input v-model="roleForm.desc" type="textarea" :rows="3" placeholder="清晰描述该角色允许操作的场馆系统或业务责任边界" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="roleModalVisible = false">取消</el-button>
        <el-button type="primary" class="gold-btn-primary" @click="submitRoleForm">
          确认保存角色
        </el-button>
      </template>
    </el-dialog>

    <!-- 弹窗 2: 新建/编辑用户账号弹窗 -->
    <el-dialog
      v-model="userModalVisible"
      :title="isEditUser ? '编辑用户账号与资料' : '登记新增场馆运行用户账号'"
      width="min(580px, calc(100vw - 32px))"
      append-to-body
      destroy-on-close
      class="gold-styled-dialog"
    >
      <el-form label-position="top" :model="userForm" class="dialog-standard-form">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="真实姓名" required>
              <el-input v-model="userForm.realName" placeholder="例如: 潘展乐, 王建国" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="企业工号" required>
              <el-input v-model="userForm.empNo" placeholder="例如: EMP-1088" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="登录账号 (Username)" required>
              <el-input v-model="userForm.username" :disabled="isEditUser" placeholder="例如: swim_ops_01" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="isEditUser ? '登录密码 (留空保持不变)' : '初始登录密码'" :required="!isEditUser">
              <el-input v-model="userForm.password" type="password" show-password placeholder="请输入高强密码" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="所属保障部门" required>
              <el-select v-model="userForm.dept" style="width: 100%;">
                <el-option label="弱电智能工程处" value="弱电工程处" />
                <el-option label="赛事技术保障部" value="赛事保障部" />
                <el-option label="总控运行调度中心" value="总控调度中心" />
                <el-option label="场馆领导办公室" value="领导办公室" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="绑定指派角色" required>
              <el-select v-model="userForm.roleCode" style="width: 100%;">
                <el-option
                  v-for="r in roleList"
                  :key="r.code"
                  :label="r.name"
                  :value="r.code"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="联系电话 (用于双因子认证接收)">
          <el-input v-model="userForm.phone" placeholder="例如: 13800138000" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="userModalVisible = false">取消</el-button>
        <el-button type="primary" class="gold-btn-primary" @click="submitUserForm">
          确认登记
        </el-button>
      </template>
    </el-dialog>

    <!-- 抽屉: 用户有效权限透视镜 (Effective Permissions Explorer) -->
    <el-drawer
      v-model="permDrawerVisible"
      :title="`用户【${activeUserForPerm?.realName}】当前生效权限全景透视`"
      size="min(620px, calc(100vw - 24px))"
      append-to-body
      destroy-on-close
    >
      <div class="user-perm-drawer-body">
        <div class="user-summary-badge-bar">
          <div>
            <strong>所属角色:</strong>
            <span class="role-tag-badge ml-1">{{ getRoleName(activeUserForPerm?.roleCode) }}</span>
          </div>
          <div>
            <strong>所属部门:</strong> {{ activeUserForPerm?.dept }}
          </div>
          <div>
            <strong>账号状态:</strong>
            <span class="text-success ml-1" v-if="activeUserForPerm?.status === 'NORMAL'">正常</span>
            <span class="text-danger ml-1" v-else>停用</span>
          </div>
        </div>

        <div class="perm-preview-tree-box">
          <span class="box-title-txt">该账号通过所属角色直接继承的有效权限节点清单:</span>
          <el-tree
            :data="permTreeData"
            default-expand-all
            :default-checked-keys="getUserRoleKeys(activeUserForPerm?.roleCode)"
            show-checkbox
            node-key="id"
            class="sahara-styled-tree disabled-tree"
          >
            <template #default="{ node, data }">
              <div class="custom-tree-node-row">
                <span class="node-main-label">{{ node.label }}</span>
                <span v-if="data.isHighRisk" class="tag-danger-pill">高危指令</span>
                <span v-if="data.isProtocolConfig" class="tag-protocol-pill">敏感协议</span>
              </div>
            </template>
          </el-tree>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User, UserFilled, Plus, Check, Search, Lock, Key, Setting,
  Warning, FolderOpened
} from '@element-plus/icons-vue'
import SvgIcon from '@/components/SvgIcon.vue'

// 1. 顶部 Tab 控制
const activeTab = ref('roles')
const isSavingPolicy = ref(false)

// 2. 角色名录与配置
const selectedRoleCode = ref('operator')
const permTreeRef = ref(null)
const permSearchKeyword = ref('')

const roleList = ref([
  {
    code: 'admin',
    name: '系统管理员',
    isBuiltin: true,
    secLevel: 'L1',
    secLevelText: 'Level 1 · 最高核心权限',
    desc: '拥有全场馆最高控制权，可修改底层通讯协议、硬件波特率、用户权限与沙箱开关',
    userCount: 1
  },
  {
    code: 'ops',
    name: '弱电运维工程师',
    isBuiltin: true,
    secLevel: 'L2',
    secLevelText: 'Level 2 · 运维巡检权限',
    desc: '负责硬件链路排查、串口嗅探、告警处置、模拟沙箱调优与系统自检',
    userCount: 2
  },
  {
    code: 'operator',
    name: '场馆运行操作员',
    isBuiltin: true,
    secLevel: 'L3',
    secLevelText: 'Level 3 · 赛事操作 (硬隔离)',
    desc: '负责日常赛事音效调用、灯光模式切换与大屏推屏，严格物理隔离敏感通讯参数',
    userCount: 6
  },
  {
    code: 'viewer',
    name: '领导决策与只读观察员',
    isBuiltin: true,
    secLevel: 'L4',
    secLevelText: 'Level 4 · 全局只读态势',
    desc: '供赛区组委会领导、调度指挥中心大屏坐席使用，仅支持综合大盘与监控只读',
    userCount: 3
  }
])

const currentRole = computed(() => {
  return roleList.value.find(r => r.code === selectedRoleCode.value) || roleList.value[0]
})

const getRoleName = (code) => {
  const r = roleList.value.find(i => i.code === code)
  return r ? r.name : code
}

// 3. 细粒度权限树数据 (系统、菜单、页面、按钮、物联硬件底层指令)
const permTreeData = ref([
  {
    id: 1,
    label: '1. 综合态势与智能监控中心 (Dashboard)',
    code: 'sys:dashboard:view',
    children: [
      { id: 11, label: '查看 2D 拓扑场馆运行态势', code: 'sys:dashboard:topology' },
      { id: 12, label: '查看全场用电能耗走势与瞬时功率', code: 'sys:dashboard:energy' },
      { id: 13, label: '查看多路水下超清视频实况矩阵', code: 'sys:video:live' },
      { id: 14, label: '处理并消除系统告警通知', code: 'sys:alarm:handle', isSafeAction: true }
    ]
  },
  {
    id: 2,
    label: '2. 场馆应用聚合门户与系统集成 (SSO Integration)',
    code: 'sys:portal:access',
    children: [
      { id: 21, label: '访问应用快捷聚合大厅', code: 'sys:portal:nav' },
      { id: 22, label: 'SSO 免密单点登录至大麦售验票系统', code: 'sys:sso:ticket' },
      { id: 23, label: 'SSO 免密进入全场 LED 导视发布系统', code: 'sys:sso:info_disp' },
      { id: 24, label: '修改外部系统对接 API 密钥与回调配置', code: 'sys:portal:config', isProtocolConfig: true }
    ]
  },
  {
    id: 3,
    label: '3. 场馆物联控制总线 (13类硬件控制台)',
    code: 'iot:bus:matrix',
    children: [
      {
        id: 31,
        label: '专业扩声系统 (Soundcraft / Allen & Heath)',
        code: 'iot:audio:ctrl',
        children: [
          { id: 311, label: '推子通道电平增益调节 (0dB复位)', code: 'iot:audio:fader', isSafeAction: true },
          { id: 312, label: '一键调用赛事预设混音场景', code: 'iot:audio:scene', isSafeAction: true },
          { id: 313, label: '一键全场紧急静音 (MUTE ALL)', code: 'iot:audio:mute', isHighRisk: true }
        ]
      },
      {
        id: 32,
        label: '场地照明系统 (Modbus / DMX512)',
        code: 'iot:light:ctrl',
        children: [
          { id: 321, label: '国际赛事级照明模式切换 (2000 Lux)', code: 'iot:light:match', isSafeAction: true },
          { id: 322, label: '转播训练与保洁清场照明切换', code: 'iot:light:train', isSafeAction: true },
          { id: 323, label: '比赛大厅全场紧急切光 (BLACKOUT)', code: 'iot:light:blackout', isHighRisk: true }
        ]
      },
      {
        id: 33,
        label: '智能升旗系统 (西门子 S7-1200 PLC)',
        code: 'iot:flag:ctrl',
        children: [
          { id: 331, label: '启动 46 秒国歌匀速升旗动作', code: 'iot:flag:anthem', isSafeAction: true },
          { id: 332, label: '升旗机构最高优先级紧急停止 (E-STOP)', code: 'iot:flag:estop', isHighRisk: true },
          { id: 333, label: '旗杆复位下降至底端基准点', code: 'iot:flag:reset', isSafeAction: true }
        ]
      },
      {
        id: 34,
        label: 'LED 大屏播控与推屏调度 (Novastar H9)',
        code: 'iot:screen:ctrl',
        children: [
          { id: 341, label: '中央斗屏输入源矩阵切换 (HDMI/SDI)', code: 'iot:screen:input', isSafeAction: true },
          { id: 342, label: '大屏黑屏与屏保模式切换', code: 'iot:screen:blackout', isHighRisk: true }
        ]
      },
      {
        id: 35,
        label: '赛事计时计分接收与大屏推屏 (Omega ARES 21)',
        code: 'iot:score:ctrl',
        children: [
          { id: 351, label: '单道次/批量道次成绩推送至大屏', code: 'iot:score:push_lane', isSafeAction: true },
          { id: 352, label: '全量推送全场正式榜单至中央大屏', code: 'iot:score:push_all', isSafeAction: true },
          { id: 353, label: '清除大屏成绩叠加层 (恢复视频流)', code: 'iot:score:clear_board', isSafeAction: true },
          { id: 354, label: '计时主控机发令复位 (READY_RESET)', code: 'iot:score:reset', isSafeAction: true }
        ]
      },
      {
        id: 36,
        label: '北斗/GPS 双模时钟同步系统',
        code: 'iot:clock:ctrl',
        children: [
          { id: 361, label: '全场子钟毫秒级网络强制对时', code: 'iot:clock:sync', isSafeAction: true },
          { id: 362, label: '巡检天线卫星锁定星数状态', code: 'iot:clock:query', isSafeAction: true }
        ]
      }
    ]
  },
  {
    id: 4,
    label: '4. 低代码配置中心与底层通讯网关 (敏感核心架构)',
    code: 'sys:config:center',
    isProtocolConfig: true,
    children: [
      { id: 41, label: '修改串口波特率、校验位与 TCP/UDP 目标端口', code: 'sys:protocol:port', isProtocolConfig: true },
      { id: 42, label: '编写/调试硬件底层控制报文 (HEX / ASCII / JSON)', code: 'sys:protocol:payload', isProtocolConfig: true },
      { id: 43, label: '通讯协议模拟仿真沙箱开关与注入测试', code: 'sys:sandbox:inject', isProtocolConfig: true },
      { id: 44, label: '配置模板 JSON 导出、导入与物理重置', code: 'sys:template:manage', isProtocolConfig: true }
    ]
  }
])

// 角色预置权限映射表
const rolePermissionMap = reactive({
  admin: [1, 11, 12, 13, 14, 2, 21, 22, 23, 24, 3, 31, 311, 312, 313, 32, 321, 322, 323, 33, 331, 332, 333, 34, 341, 342, 35, 351, 352, 353, 354, 36, 361, 362, 4, 41, 42, 43, 44],
  ops: [1, 11, 12, 13, 14, 2, 21, 22, 3, 31, 311, 312, 32, 321, 322, 33, 331, 332, 333, 34, 341, 35, 351, 352, 353, 354, 36, 361, 362, 4, 41, 42, 43],
  operator: [1, 11, 12, 13, 14, 2, 21, 22, 23, 3, 31, 311, 312, 32, 321, 322, 33, 331, 333, 34, 341, 35, 351, 352, 353, 354, 36, 362],
  viewer: [1, 11, 12, 13, 2, 21, 36, 362]
})

const currentCheckedKeys = computed(() => {
  return rolePermissionMap[selectedRoleCode.value] || [1, 11]
})

const currentSelectedCount = ref(27)

const selectRole = (r) => {
  selectedRoleCode.value = r.code
  nextTick(() => {
    if (permTreeRef.value) {
      const keys = rolePermissionMap[r.code] || []
      permTreeRef.value.setCheckedKeys(keys)
      currentSelectedCount.value = keys.length
    }
  })
}

const handleTreeCheck = (node, data) => {
  // 防呆红线拦截
  if (selectedRoleCode.value === 'operator' && (node.isProtocolConfig || node.id === 4)) {
    ElMessage.error('防呆红线拦截：场馆操作员角色已被物理隔离，严禁分配底层通信协议参数权限！')
    nextTick(() => {
      if (permTreeRef.value) {
        permTreeRef.value.setChecked(node.id, false, true)
      }
    })
    return
  }

  if (permTreeRef.value) {
    const checked = permTreeRef.value.getCheckedKeys()
    currentSelectedCount.value = checked.length
    rolePermissionMap[selectedRoleCode.value] = checked
  }
}

const expandAllTree = (expand) => {
  if (!permTreeRef.value) return
  const nodes = permTreeRef.value.store._getAllNodes()
  nodes.forEach(node => {
    node.expanded = expand
  })
}

const checkAllTree = (check) => {
  if (!permTreeRef.value) return
  if (check) {
    if (selectedRoleCode.value === 'operator') {
      // 排除第 4 大类协议配置
      const allowed = [1, 11, 12, 13, 14, 2, 21, 22, 23, 3, 31, 311, 312, 313, 32, 321, 322, 323, 33, 331, 332, 333, 34, 341, 342, 35, 351, 352, 353, 354, 36, 361, 362]
      permTreeRef.value.setCheckedKeys(allowed)
      rolePermissionMap[selectedRoleCode.value] = allowed
      currentSelectedCount.value = allowed.length
      ElMessage.warning('操作员全选已自动排除底层协议敏感项')
      return
    }
    const allIds = [1, 11, 12, 13, 14, 2, 21, 22, 23, 24, 3, 31, 311, 312, 313, 32, 321, 322, 323, 33, 331, 332, 333, 34, 341, 342, 35, 351, 352, 353, 354, 36, 361, 362, 4, 41, 42, 43, 44]
    permTreeRef.value.setCheckedKeys(allIds)
    rolePermissionMap[selectedRoleCode.value] = allIds
    currentSelectedCount.value = allIds.length
  } else {
    permTreeRef.value.setCheckedKeys([])
    rolePermissionMap[selectedRoleCode.value] = []
    currentSelectedCount.value = 0
  }
}

const filterPermTree = () => {
  if (permTreeRef.value) {
    permTreeRef.value.filter(permSearchKeyword.value)
  }
}

const filterNodeMethod = (value, data) => {
  if (!value) return true
  const q = value.toLowerCase()
  return (data.label && data.label.toLowerCase().includes(q)) || (data.code && data.code.toLowerCase().includes(q))
}

const saveRolePermissions = () => {
  isSavingPolicy.value = true
  setTimeout(() => {
    isSavingPolicy.value = false
    ElMessage.success(`已为角色【${currentRole.value.name}】更新并热固化细粒度权限矩阵，当前分配 ${currentSelectedCount.value} 个控制节点！`)
  }, 500)
}

// 4. 用户账号数据源与管理
const userList = ref([
  { id: 1, empNo: 'EMP-001', username: 'admin', realName: '王总监', dept: '弱电工程处', roleCode: 'admin', phone: '13800100001', status: 'NORMAL', lastLogin: '2026-10-12 16:45:10' },
  { id: 2, empNo: 'EMP-002', username: 'ops_zhang', realName: '张建军', dept: '弱电工程处', roleCode: 'ops', phone: '13800100002', status: 'NORMAL', lastLogin: '2026-10-12 15:30:22' },
  { id: 3, empNo: 'EMP-003', username: 'ops_li', realName: '李思齐', dept: '弱电工程处', roleCode: 'ops', phone: '13800100003', status: 'NORMAL', lastLogin: '2026-10-12 11:15:00' },
  { id: 4, empNo: 'EMP-004', username: 'operator_swim', realName: '陈志远', dept: '赛事保障部', roleCode: 'operator', phone: '13800100004', status: 'NORMAL', lastLogin: '2026-10-12 16:58:30' },
  { id: 5, empNo: 'EMP-005', username: 'operator_sound', realName: '林秋声', dept: '赛事保障部', roleCode: 'operator', phone: '13800100005', status: 'NORMAL', lastLogin: '2026-10-12 14:20:00' },
  { id: 6, empNo: 'EMP-006', username: 'operator_light', realName: '赵明朗', dept: '赛事保障部', roleCode: 'operator', phone: '13800100006', status: 'NORMAL', lastLogin: '2026-10-12 13:50:18' },
  { id: 7, empNo: 'EMP-007', username: 'operator_screen', realName: '孙立新', dept: '总控调度中心', roleCode: 'operator', phone: '13800100007', status: 'NORMAL', lastLogin: '2026-10-12 16:40:05' },
  { id: 8, empNo: 'EMP-008', username: 'operator_flag', realName: '周正旗', dept: '总控调度中心', roleCode: 'operator', phone: '13800100008', status: 'NORMAL', lastLogin: '2026-10-12 10:05:44' },
  { id: 9, empNo: 'EMP-009', username: 'operator_aux', realName: '吴副官', dept: '赛事保障部', roleCode: 'operator', phone: '13800100009', status: 'DISABLED', lastLogin: '2026-10-10 18:00:12' },
  { id: 10, empNo: 'EMP-010', username: 'director_huang', realName: '黄副局长', dept: '领导办公室', roleCode: 'viewer', phone: '13800100010', status: 'NORMAL', lastLogin: '2026-10-12 09:12:00' },
  { id: 11, empNo: 'EMP-011', username: 'chief_referee', realName: '钱裁判长', dept: '总控调度中心', roleCode: 'viewer', phone: '13800100011', status: 'NORMAL', lastLogin: '2026-10-12 16:50:00' },
  { id: 12, empNo: 'EMP-012', username: 'sec_director', realName: '郑保卫科长', dept: '总控调度中心', roleCode: 'viewer', phone: '13800100012', status: 'NORMAL', lastLogin: '2026-10-11 17:30:20' }
])

const userSearchKeyword = ref('')
const userRoleFilter = ref('')
const userDeptFilter = ref('')
const userStatusFilter = ref('')

const filteredUserList = computed(() => {
  return userList.value.filter(u => {
    if (userRoleFilter.value && u.roleCode !== userRoleFilter.value) return false
    if (userDeptFilter.value && !u.dept.includes(userDeptFilter.value)) return false
    if (userStatusFilter.value && u.status !== userStatusFilter.value) return false
    if (userSearchKeyword.value) {
      const q = userSearchKeyword.value.toLowerCase().trim()
      const match = u.realName.toLowerCase().includes(q) ||
                    u.username.toLowerCase().includes(q) ||
                    u.empNo.toLowerCase().includes(q) ||
                    u.phone.includes(q)
      if (!match) return false
    }
    return true
  })
})

const toggleUserStatus = (row) => {
  const nextStatus = row.status === 'NORMAL' ? 'DISABLED' : 'NORMAL'
  const actionText = nextStatus === 'NORMAL' ? '启用' : '临时停用'
  ElMessageBox.confirm(`确认将账号【${row.realName} (${row.username})】设为${actionText}状态吗？`, '账号状态变更确认', {
    confirmButtonText: '确定变更',
    cancelButtonText: '取消',
    type: nextStatus === 'NORMAL' ? 'info' : 'warning'
  }).then(() => {
    row.status = nextStatus
    ElMessage.success(`已成功${actionText}用户【${row.realName}】`)
  }).catch(() => {})
}

// 5. 新建/编辑角色弹窗
const roleModalVisible = ref(false)
const isEditRole = ref(false)
const currentRoleToEdit = ref(null)

const roleForm = reactive({
  name: '',
  code: '',
  secLevel: 'L3',
  cloneFrom: '',
  desc: ''
})

const openCreateRoleModal = () => {
  isEditRole.value = false
  currentRoleToEdit.value = null
  Object.assign(roleForm, {
    name: '',
    code: '',
    secLevel: 'L3',
    cloneFrom: 'operator',
    desc: ''
  })
  roleModalVisible.value = true
}

const submitRoleForm = () => {
  if (!roleForm.name || !roleForm.code) {
    ElMessage.warning('请填写角色名称和唯一标识码')
    return
  }
  const exist = roleList.value.some(r => r.code === roleForm.code)
  if (!isEditRole.value && exist) {
    ElMessage.warning('该角色标识码已存在，请更换')
    return
  }

  const secLevelMap = {
    L1: 'Level 1 · 最高核心权限',
    L2: 'Level 2 · 运维巡检权限',
    L3: 'Level 3 · 现场操作员 (硬隔离)',
    L4: 'Level 4 · 全局只读态势'
  }

  const newRole = {
    code: roleForm.code,
    name: roleForm.name,
    isBuiltin: false,
    secLevel: roleForm.secLevel,
    secLevelText: secLevelMap[roleForm.secLevel],
    desc: roleForm.desc || '自定义运行角色',
    userCount: 0
  }

  // 继承克隆权限
  if (roleForm.cloneFrom && rolePermissionMap[roleForm.cloneFrom]) {
    rolePermissionMap[roleForm.code] = [...rolePermissionMap[roleForm.cloneFrom]]
  } else {
    rolePermissionMap[roleForm.code] = [1, 11]
  }

  roleList.value.push(newRole)
  roleModalVisible.value = false
  ElMessage.success(`新角色【${roleForm.name}】创建成功！`)
  selectRole(newRole)
}

// 6. 新建/编辑用户账号弹窗
const userModalVisible = ref(false)
const isEditUser = ref(false)
const currentUserToEdit = ref(null)

const userForm = reactive({
  id: null,
  realName: '',
  empNo: '',
  username: '',
  password: '',
  dept: '赛事保障部',
  roleCode: 'operator',
  phone: ''
})

const openCreateUserModal = () => {
  isEditUser.value = false
  currentUserToEdit.value = null
  const newNum = String(userList.value.length + 1).padStart(3, '0')
  Object.assign(userForm, {
    id: null,
    realName: '',
    empNo: `EMP-${newNum}`,
    username: '',
    password: '',
    dept: '赛事保障部',
    roleCode: 'operator',
    phone: ''
  })
  userModalVisible.value = true
}

const openEditUser = (row) => {
  isEditUser.value = true
  currentUserToEdit.value = row
  Object.assign(userForm, {
    id: row.id,
    realName: row.realName,
    empNo: row.empNo,
    username: row.username,
    password: '',
    dept: row.dept,
    roleCode: row.roleCode,
    phone: row.phone
  })
  userModalVisible.value = true
}

const openAssignRole = (row) => {
  openEditUser(row)
}

const submitUserForm = () => {
  if (!userForm.realName || !userForm.username) {
    ElMessage.warning('请填写真实姓名和登录用户名')
    return
  }

  if (isEditUser.value) {
    const target = userList.value.find(u => u.id === userForm.id)
    if (target) {
      target.realName = userForm.realName
      target.empNo = userForm.empNo
      target.dept = userForm.dept
      target.roleCode = userForm.roleCode
      target.phone = userForm.phone
      ElMessage.success(`用户【${target.realName}】资料已更新`)
    }
  } else {
    const newUser = {
      id: Date.now(),
      empNo: userForm.empNo,
      username: userForm.username,
      realName: userForm.realName,
      dept: userForm.dept,
      roleCode: userForm.roleCode,
      phone: userForm.phone,
      status: 'NORMAL',
      lastLogin: '从未登录'
    }
    userList.value.push(newUser)
    // 更新对应角色的计数
    const r = roleList.value.find(item => item.code === userForm.roleCode)
    if (r) r.userCount++
    ElMessage.success(`新用户【${userForm.realName}】登记完成`)
  }
  userModalVisible.value = false
}

// 7. 用户权限透视抽屉
const permDrawerVisible = ref(false)
const activeUserForPerm = ref(null)

const viewUserEffectivePerms = (row) => {
  activeUserForPerm.value = row
  permDrawerVisible.value = true
}

const getUserRoleKeys = (roleCode) => {
  return rolePermissionMap[roleCode] || [1, 11]
}
</script>

<style scoped>
.user-role-workspace {
  display: flex;
  flex-direction: column;
  gap: 14px;
  animation: fadeIn 0.3s ease-out;
}

/* -------------------------------------------------------------
   1. 顶部 Header
   ------------------------------------------------------------- */
.role-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  border-radius: var(--radius-sm, 6px);
  box-shadow: var(--shadow-card, 0 2px 8px rgba(0, 0, 0, 0.04));
  flex-wrap: wrap;
  gap: 12px;
}

.top-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.icon-cube {
  width: 42px;
  height: 42px;
  border-radius: 6px;
  background: linear-gradient(135deg, rgba(var(--th-accent-rgb), 0.2) 0%, rgba(var(--th-accent-deep-rgb), 0.35) 100%);
  border: 1px solid var(--do-border);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--do-gold-deep);
}

.title-meta {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.title-main-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.view-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--do-text-primary);
  letter-spacing: 0.3px;
}

.security-level-pill {
  font-size: 14px;
  font-weight: 700;
  color: var(--do-success-deep);
  background: var(--do-success-bg);
  border: 1px solid var(--do-success-bg);
  padding: 2px 8px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.pulse-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--do-success);
  box-shadow: 0 0 5px var(--do-success);
}

.sub-meta-txt {
  font-size: 14px;
  color: var(--do-text-secondary);
}

.top-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-secondary-action {
  background: var(--do-bg-input) !important;
  border: 1px solid var(--do-border) !important;
  color: var(--do-text-primary) !important;
  font-weight: 600 !important;
}

.btn-secondary-action:hover {
  background: var(--do-bg-card-hover) !important;
  border-color: var(--do-gold) !important;
  color: var(--do-gold-deep) !important;
}

.gold-btn-primary {
  background: linear-gradient(135deg, var(--do-gold) 0%, var(--do-gold-deep) 100%) !important;
  border-color: var(--do-gold-deep) !important;
  color: #FFFFFF !important;
  font-weight: 700 !important;
  box-shadow: 0 2px 6px rgba(var(--th-accent-deep-rgb), 0.35) !important;
}

/* -------------------------------------------------------------
   2. KPI 指标卡片
   ------------------------------------------------------------- */
.security-kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

@media (max-width: 1200px) {
  .security-kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.kpi-card {
  background: linear-gradient(145deg, var(--do-bg-card) 0%, rgba(var(--th-accent-rgb), 0.04) 100%);
  border: 1px solid rgba(var(--th-accent-rgb), 0.22);
  border-radius: var(--radius-md, 8px);
  padding: 14px 18px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: border-color 0.22s ease, box-shadow 0.22s ease;
}

.kpi-card:hover {
  border-color: var(--do-gold);
  box-shadow: 0 4px 16px rgba(var(--th-accent-rgb), 0.16);
}

.kpi-icon-box {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.kpi-icon-box.gold { background: var(--do-gold-light); color: var(--do-warning-deep); }
.kpi-icon-box.coffee { background: var(--do-gold-light); color: var(--do-text-secondary); }
.kpi-icon-box.green { background: var(--do-success-bg); color: var(--do-success-deep); }
.kpi-icon-box.red { background: var(--do-danger-bg); color: var(--do-danger); }

.kpi-content {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex: 1;
}

.kpi-label {
  font-size: 14px;
  color: var(--do-text-secondary);
}

.kpi-val-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
  flex-wrap: wrap;
}

.kpi-number {
  font-size: 22px;
  font-weight: 800;
  color: var(--do-text-primary);
  line-height: 1;
}

.kpi-unit {
  font-size: 14px;
  color: var(--do-text-secondary);
}

.kpi-sub-pill {
  font-size: 14px;
  padding: 1px 6px;
  border-radius: 10px;
  margin-left: auto;
  font-weight: 600;
}

.kpi-sub-pill.normal { background: var(--do-success-bg); color: var(--do-success-deep); }
.kpi-sub-pill.builtin { background: var(--do-bg-input); color: var(--do-gold-deep); }
.kpi-sub-pill.safe { background: var(--do-bg-input); color: var(--do-gold-deep); }
.kpi-sub-pill.danger { background: var(--do-danger-bg); color: var(--do-danger-deep); }

/* -------------------------------------------------------------
   3. 标签页主体
   ------------------------------------------------------------- */
.main-tabs-container {
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  border-radius: var(--radius-sm, 6px);
  padding: 10px 18px 18px 18px;
  box-shadow: var(--shadow-card, 0 2px 8px rgba(0, 0, 0, 0.04));
}

.sahara-styled-tabs :deep(.el-tabs__item) {
  font-size: 14px;
  font-weight: 600;
  color: var(--do-text-secondary);
}

.sahara-styled-tabs :deep(.el-tabs__item.is-active) {
  color: var(--do-gold-deep);
  font-weight: 800;
}

.sahara-styled-tabs :deep(.el-tabs__active-bar) {
  background-color: var(--do-gold);
  height: 3px;
}

/* 角色与权限矩阵 */
.role-perm-matrix-layout {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 16px;
  margin-top: 6px;
}

@media (max-width: 1200px) {
  .role-perm-matrix-layout {
    grid-template-columns: 1fr;
  }
}

.col-role-list,
.col-perm-details {
  border: 1px solid var(--do-border-light);
  border-radius: 6px;
  background: var(--do-bg-card-hover);
  display: flex;
  flex-direction: column;
}

.section-card-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--do-border-light);
  background: rgba(var(--th-accent-rgb), 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
}

.header-title-wrap {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.section-title-txt {
  font-size: 14px;
  font-weight: 800;
  color: var(--do-text-primary);
}

.section-subtitle-txt {
  font-size: 14px;
  color: var(--do-text-secondary);
}

.btn-link-gold {
  color: var(--do-gold-deep) !important;
  font-weight: 700;
}

/* 角色卡片 */
.role-cards-scroll {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-height: calc(100vh - 360px);
  overflow-y: auto;
}

.role-entry-card {
  background: #FFFFFF;
  border: 1px solid var(--do-border-light);
  border-radius: 8px;
  padding: 14px 16px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: all 0.25s ease;
  box-shadow: 0 1px 4px rgba(var(--th-shadow-rgb), 0.03);
}

.role-entry-card:hover {
  border-color: var(--do-gold);
  background: var(--do-bg-input);
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(var(--th-accent-rgb), 0.15);
}

.role-entry-card.active {
  background: var(--do-bg-card-hover);
  border-color: var(--do-gold);
  box-shadow: 0 0 0 1.5px var(--do-gold), 0 4px 12px rgba(var(--th-accent-rgb), 0.22);
}

.role-entry-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.role-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.role-name-txt {
  font-size: 14.5px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.tag-pill {
  font-size: 14px;
  padding: 2px 7px;
  border-radius: 4px;
  font-weight: 600;
}

.tag-pill.builtin { background: var(--do-bg-input); color: var(--do-gold-deep); border: 1px solid var(--do-border); }
.tag-pill.custom { background: var(--do-bg-input); color: var(--do-gold-deep); border: 1px solid var(--do-gold-hover); }

.sec-level-badge {
  font-size: 14px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 4px;
}

.sec-level-badge.L1 { background: var(--do-gold-light); color: var(--do-warning-deep); }
.sec-level-badge.L2 { background: var(--do-border-lighter); color: var(--do-text-secondary); }
.sec-level-badge.L3 { background: var(--do-danger-bg); color: var(--do-danger-deep); }
.sec-level-badge.L4 { background: var(--do-bg-sunken); color: var(--do-text-regular); }

.role-desc-txt {
  font-size: 14px;
  color: var(--do-text-secondary);
  line-height: 1.6;
  margin: 3px 0 4px 0;
}

.role-entry-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 8px;
  border-top: 1px dashed rgba(var(--th-accent-rgb), 0.3);
}

.role-code-badge {
  font-size: 14px;
  font-weight: 600;
  color: var(--do-gold-deep);
}

.role-user-stat {
  font-size: 14px;
  color: var(--do-text-secondary);
  display: inline-flex;
  align-items: center;
}

/* 权限详情右栏 */
.current-role-badge-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.current-role-code {
  font-size: 14px;
  color: var(--do-gold-deep);
  font-weight: 600;
}

.tree-quick-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 操作员安全防呆红线横幅 */
.operator-security-fence {
  margin: 14px 18px 0 18px;
  padding: 12px 16px;
  background: var(--do-warning-bg);
  border: 1px solid var(--do-warning);
  border-radius: 8px;
  display: flex;
  align-items: flex-start;
  gap: 14px;
  box-shadow: 0 2px 6px rgba(245, 158, 11, 0.1);
}

.fence-icon {
  color: var(--do-warning-deep);
  margin-top: 2px;
}

.fence-content {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.fence-title {
  font-size: 13.5px;
  font-weight: 700;
  color: var(--do-warning-deep);
}

.fence-desc {
  font-size: 14px;
  color: var(--do-warning-deep);
  line-height: 1.6;
  margin: 0;
}

/* 权限树过滤栏 */
.tree-filter-bar {
  padding: 12px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--do-border-light);
  flex-wrap: wrap;
  gap: 12px;
}

.legend-pills {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: 14px;
  color: var(--do-text-secondary);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.dot-icon {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot-icon.menu { background: var(--do-text-secondary); }
.dot-icon.action { background: var(--do-gold); }
.dot-icon.risk { background: var(--do-danger); }
.dot-icon.protocol { background: var(--do-warning); }

/* 权限树体样式 */
.tree-viewport {
  padding: 14px 18px 20px 18px;
  max-height: calc(100vh - 430px);
  overflow-y: auto;
}

/* 核心优化：提升 el-tree 节点行高与呼吸感 */
.sahara-styled-tree :deep(.el-tree-node__content) {
  height: 38px;
  border-radius: 6px;
  margin: 3px 0;
  padding-right: 8px;
  transition: all 0.2s ease;
}

.sahara-styled-tree :deep(.el-tree-node__content:hover) {
  background-color: rgba(var(--th-accent-rgb), 0.08);
}

.sahara-styled-tree :deep(.el-tree-node.is-current > .el-tree-node__content) {
  background-color: rgba(var(--th-accent-rgb), 0.12);
}

.sahara-styled-tree :deep(.el-tree-node__expand-icon) {
  color: var(--do-gold-deep);
  font-size: 14px;
  margin-right: 3px;
}

.sahara-styled-tree :deep(.el-checkbox) {
  margin-right: 10px;
}

.sahara-styled-tree :deep(.el-checkbox__inner) {
  border-radius: 4px;
}

.custom-tree-node-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding-right: 8px;
  gap: 14px;
}

.node-main-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--do-text-primary);
  line-height: 1.4;
}

.node-icon.folder { color: var(--do-gold); font-size: 15px; }
.node-icon.leaf { color: var(--do-text-secondary); font-size: 14px; }

.node-tags-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.code-tag {
  font-size: 14px;
  color: var(--do-text-secondary);
  background: rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(140, 123, 107, 0.2);
  padding: 2px 7px;
  border-radius: 4px;
}

.tag-danger-pill {
  font-size: 14px;
  font-weight: 700;
  color: var(--do-danger);
  background: var(--do-danger-bg);
  border: 1px solid var(--do-danger-border);
  padding: 2px 8px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.tag-protocol-pill {
  font-size: 14px;
  font-weight: 700;
  color: var(--do-warning-deep);
  background: var(--do-warning-bg);
  border: 1px solid var(--do-gold-light);
  padding: 2px 8px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.tag-safe-pill {
  font-size: 14px;
  color: var(--do-gold-deep);
  background: var(--do-bg-input);
  border: 1px solid var(--do-gold-light);
  padding: 2px 7px;
  border-radius: 4px;
}

/* -------------------------------------------------------------
   4. 用户管理面板
   ------------------------------------------------------------- */
.user-management-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 6px;
}

.user-filter-toolbar {
  padding: 12px 14px;
  background: var(--do-bg-card-hover);
  border: 1px solid var(--do-border-light);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
}

.filter-inputs {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.user-table {
  border: 1px solid var(--do-border-light);
  border-radius: 6px;
}

.emp-no-pill {
  background: var(--do-bg-input);
  border: 1px solid var(--do-border);
  color: var(--do-text-primary);
  font-weight: 700;
  font-size: 14px;
  padding: 2px 6px;
  border-radius: 3px;
}

.user-profile-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--do-gold) 0%, var(--do-gold-deep) 100%);
  color: #FFFFFF;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  box-shadow: 0 2px 4px rgba(var(--th-accent-deep-rgb), 0.3);
}

.profile-info {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
}

.user-real-name {
  font-weight: 700;
  color: var(--do-text-primary);
  font-size: 14px;
}

.user-username {
  font-size: 14px;
  color: var(--do-text-secondary);
}

.role-tag-badge {
  font-size: 14px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
}

.role-tag-badge.admin { background: var(--do-gold-light); color: var(--do-warning-deep); border: 1px solid var(--do-warning-border); }
.role-tag-badge.ops { background: var(--do-gold-light); color: var(--do-text-regular); border: 1px solid var(--do-gold-hover); }
.role-tag-badge.operator { background: var(--do-success-bg); color: var(--do-success-deep); border: 1px solid var(--do-success-bg); }
.role-tag-badge.viewer { background: var(--do-bg-sunken); color: var(--do-text-regular); border: 1px solid var(--do-border-light); }

.status-tag {
  font-weight: 600;
}

.user-row-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

/* 抽屉样式 */
.user-perm-drawer-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.user-summary-badge-bar {
  padding: 10px 14px;
  background: var(--do-bg-input);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  color: var(--do-text-primary);
}

.perm-preview-tree-box {
  border: 1px solid var(--do-border-light);
  border-radius: 6px;
  padding: 12px;
  background: var(--do-bg-card-hover);
}

.box-title-txt {
  font-size: 14px;
  font-weight: 700;
  color: var(--do-text-primary);
  display: block;
  margin-bottom: 10px;
}

.disabled-tree :deep(.el-checkbox__input.is-disabled .el-checkbox__inner) {
  background-color: var(--do-gold) !important;
  border-color: var(--do-gold) !important;
}

/* ============================================================================
   统一控制台视觉与响应式增强
   对齐“大屏调度”和“计时计分”页面，保留现有 RBAC 交互与安全防呆逻辑
   ============================================================================ */
.user-role-workspace {
  width: 100%;
  min-width: 0;
  color: var(--do-text-primary);
}

.glass-panel {
  border-radius: 10px;
  box-shadow: var(--shadow-sm, var(--shadow-card));
}

.role-top-bar {
  min-width: 0;
  padding: 18px 22px;
  gap: 20px;
  border-radius: 10px;
}

.role-top-bar .top-left {
  min-width: 0;
  flex: 1 1 460px;
  gap: 14px;
}

.role-top-bar .icon-cube {
  width: 52px;
  height: 52px;
  flex: 0 0 auto;
  border-radius: 12px;
}

.role-top-bar .title-meta {
  min-width: 0;
  flex: 1 1 auto;
}

.role-top-bar .title-main-row {
  min-width: 0;
  gap: 10px;
  flex-wrap: wrap;
}

.role-top-bar .view-title {
  min-width: 0;
  overflow: hidden;
  font-size: 21px !important;
  line-height: 1.3;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.security-level-pill {
  flex: 0 0 auto;
  font-size: 13px;
}

.sub-meta-txt {
  display: block;
  margin-top: 5px;
  overflow: hidden;
  font-size: 13px;
  line-height: 1.5;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.role-top-bar .top-right {
  min-width: 0;
  flex: 1 1 520px;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
}

.role-top-bar .top-right :deep(.el-button) {
  margin-left: 0;
}

.security-kpi-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  min-width: 0;
  gap: 12px;
}

.kpi-card,
.kpi-content,
.kpi-val-row {
  min-width: 0;
}

.kpi-card {
  border-radius: 10px;
  box-shadow: var(--shadow-sm, 0 2px 8px rgba(0, 0, 0, .04));
}

.kpi-sub-pill {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.main-tabs-container {
  min-width: 0;
  padding: 10px 18px 18px;
  border-radius: 10px;
  box-shadow: var(--shadow-sm, var(--shadow-card));
}

.sahara-styled-tabs,
.sahara-styled-tabs :deep(.el-tabs__content),
.sahara-styled-tabs :deep(.el-tab-pane) {
  min-width: 0;
}

.role-perm-matrix-layout {
  grid-template-columns: minmax(0, 360px) minmax(0, 1fr);
  min-width: 0;
  gap: 14px;
}

.col-role-list,
.col-perm-details,
.user-management-panel {
  min-width: 0;
  border-radius: 8px;
}

.col-role-list,
.col-perm-details {
  overflow: hidden;
}

.section-card-header,
.header-title-wrap,
.current-role-badge-row,
.tree-quick-actions,
.tree-filter-bar,
.legend-pills,
.custom-tree-node-row,
.node-main-label,
.node-tags-row,
.user-filter-toolbar,
.filter-inputs,
.filter-actions,
.user-profile-cell,
.user-row-actions {
  min-width: 0;
}

.section-card-header {
  gap: 12px;
}

.header-title-wrap {
  flex: 1 1 auto;
}

.section-title-txt,
.section-subtitle-txt,
.current-role-badge-row,
.current-role-code {
  min-width: 0;
}

.section-title-txt,
.section-subtitle-txt {
  overflow: hidden;
  text-overflow: ellipsis;
}

.current-role-badge-row {
  flex-wrap: wrap;
  gap: 6px;
}

.tree-quick-actions {
  flex: 0 1 auto;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 6px;
}

.role-cards-scroll {
  min-width: 0;
}

.role-entry-card {
  min-width: 0;
  border-radius: 8px;
}

.role-entry-top,
.role-title-row,
.role-entry-footer {
  min-width: 0;
  flex-wrap: wrap;
  gap: 8px;
}

.role-name-txt,
.role-desc-txt,
.role-user-stat,
.role-code-badge,
.sec-level-badge {
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}

.role-name-txt,
.role-desc-txt {
  overflow-wrap: anywhere;
}

.role-desc-txt {
  white-space: normal;
}

.operator-security-fence {
  min-width: 0;
}

.fence-content,
.fence-desc,
.fence-title {
  min-width: 0;
}

.fence-desc {
  overflow-wrap: anywhere;
}

.tree-filter-bar {
  align-items: flex-start;
  gap: 10px;
}

.tree-filter-bar > :deep(.el-input) {
  width: min(320px, 100%) !important;
  flex: 1 1 280px;
}

.legend-pills {
  flex: 1 1 360px;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px 14px;
}

.tree-viewport {
  min-width: 0;
  overflow-x: auto;
}

.sahara-styled-tree {
  min-width: 0;
}

.custom-tree-node-row {
  width: 100%;
  gap: 10px;
  flex-wrap: wrap;
}

.node-main-label {
  flex: 1 1 260px;
  overflow: hidden;
}

.node-main-label > span:last-child {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-tags-row {
  flex: 0 1 auto;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 5px;
}

.code-tag,
.tag-danger-pill,
.tag-protocol-pill,
.tag-safe-pill {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-filter-toolbar {
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-inputs {
  min-width: 0;
  flex: 1 1 680px;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-inputs :deep(.el-input),
.filter-inputs :deep(.el-select) {
  min-width: 0;
  flex: 1 1 150px;
}

.filter-actions {
  flex: 0 0 auto;
}

.user-table-scroll {
  width: 100%;
  min-width: 0;
  overflow-x: auto;
}

.user-table {
  min-width: 1160px;
}

.user-profile-cell,
.profile-info {
  min-width: 0;
}

.profile-info {
  overflow: hidden;
}

.user-real-name,
.user-username {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-row-actions {
  justify-content: center;
  flex-wrap: wrap;
  gap: 2px;
}

.user-row-actions :deep(.el-button) {
  margin-left: 0;
}

.user-perm-drawer-body,
.user-summary-badge-bar,
.perm-preview-tree-box {
  min-width: 0;
}

.user-summary-badge-bar {
  gap: 10px;
  flex-wrap: wrap;
}

@media (max-width: 1300px) {
  .security-kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 1200px) {
  .role-perm-matrix-layout {
    grid-template-columns: minmax(0, 1fr);
  }

  .role-cards-scroll {
    max-height: none;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }
}

@media (max-width: 900px) {
  .role-top-bar {
    align-items: flex-start;
  }

  .role-top-bar .top-left,
  .role-top-bar .top-right {
    flex-basis: 100%;
  }

  .role-top-bar .top-right {
    justify-content: flex-start;
  }

  .tree-quick-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .filter-actions {
    width: 100%;
  }

  .filter-actions :deep(.el-button) {
    width: 100%;
  }
}

@media (max-width: 800px) {
  .role-top-bar,
  .main-tabs-container {
    padding: 14px;
  }

  .role-top-bar .icon-cube {
    width: 44px;
    height: 44px;
  }

  .role-top-bar .view-title {
    font-size: 18px !important;
    white-space: normal;
  }

  .role-top-bar .title-main-row {
    align-items: flex-start;
    flex-direction: column;
    gap: 6px;
  }

  .sub-meta-txt {
    white-space: normal;
  }

  .security-kpi-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .role-cards-scroll {
    grid-template-columns: minmax(0, 1fr);
  }

  .tree-filter-bar {
    flex-direction: column;
  }

  .tree-filter-bar > :deep(.el-input),
  .legend-pills {
    width: 100%;
    flex-basis: 100%;
  }

  .legend-pills {
    justify-content: flex-start;
  }

  .section-card-header {
    align-items: flex-start;
  }

  .node-main-label {
    flex-basis: 100%;
  }

  .node-tags-row {
    justify-content: flex-start;
    flex-basis: 100%;
  }

  .filter-inputs :deep(.el-input),
  .filter-inputs :deep(.el-select) {
    flex-basis: 100%;
    width: 100% !important;
  }
}

@media (max-width: 560px) {
  .role-top-bar .top-right :deep(.el-button) {
    width: 100%;
    flex: 1 1 100%;
  }

  .role-entry-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .tree-quick-actions :deep(.el-button) {
    flex: 1 1 calc(50% - 6px);
  }

  .operator-security-fence {
    margin-inline: 12px;
    padding: 10px 12px;
  }

  .tree-viewport {
    padding-inline: 12px;
  }
}
</style>
