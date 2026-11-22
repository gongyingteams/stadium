-- ==============================================================================
-- 体育场馆应用集成管控平台 (IBMS) 数据库升级迁移脚本
-- 脚本名称: migration_add_menu_short_name.sql
-- 适用版本: v1.0.0 -> v1.0.1
-- 功能描述: 
--   1. 为 `sys_menu` 表补充 `short_name` (规范4字缩写别名) 列，支持各终端对齐紧凑排版
--   2. 初始化/全量更新预置系统菜单数据，为 5 大一级主分类与 22 个二级业务节点配置 4 字别名
-- 执行方式: mysql -u root -p <dbname> < migration_add_menu_short_name.sql
-- ==============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 1. 幂等性增加 short_name 字段 (统一4字规范缩写别名)
SET @dbname = DATABASE();
SET @tablename = 'sys_menu';
SET @columnname = 'short_name';
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      TABLE_SCHEMA = @dbname
      AND TABLE_NAME = @tablename
      AND COLUMN_NAME = @columnname
  ) > 0,
  'SELECT 1',
  'ALTER TABLE `sys_menu` ADD COLUMN `short_name` VARCHAR(32) NOT NULL DEFAULT \'\' COMMENT \'规范缩写别名(统一4字对齐)\' AFTER `menu_name`;'
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- 2. 全量刷新/插入带统一 4 字别名的系统菜单种子数据
INSERT INTO `sys_menu` (`id`, `menu_code`, `parent_id`, `menu_name`, `short_name`, `route_name`, `route_path`, `component_name`, `icon_code`, `sort_order`, `terminal_scope`, `baseline_flag`, `dynamic_flag`, `permission_code`, `status`)
VALUES
-- 【一级主分类导航 (5大主模块，统一4字规范别名)】
(1, 'MOD_DASHBOARD', 0, '综合态势', '综合态势', '', '/dashboard', '', 'SvgDashboard', 1, 'PC', 1, 0, '', 1),
(2, 'MOD_PORTAL', 0, '应用门户', '应用门户', '', '/portal', '', 'SvgPortal', 2, 'PC', 1, 0, '', 1),
(3, 'MOD_IOT', 0, '物联控制', '物联控制', '', '/iot', '', 'SvgIotControl', 3, 'PC', 1, 0, '', 1),
(4, 'MOD_CONFIG', 0, '配置中心', '配置中心', '', '/config', '', 'SvgLowCodeConfig', 4, 'PC', 1, 0, '', 1),
(5, 'MOD_OPS', 0, '运维安全', '运维安全', '', '/ops', '', 'SvgSecurityShield', 5, 'PC', 1, 0, '', 1),

-- 【二级业务菜单：1. 综合态势】
(101, 'MENU_DASHBOARD_OVERVIEW', 1, '场馆综合态势总览工作台', '态势总览', 'Dashboard', '/dashboard', 'DashboardOverview.vue', 'SvgDashboard', 1, 'PC', 1, 0, 'view:dashboard', 1),

-- 【二级业务菜单：2. 应用门户】
(201, 'MENU_PORTAL_NAV', 2, '场馆应用与网站聚合导航大厅', '应用导航', 'PortalNav', '/portal/nav', 'PortalNavGrid.vue', 'SvgAppGrid', 1, 'PC', 1, 0, 'portal:nav:view', 1),
(202, 'MENU_PORTAL_IFRAME', 2, '第三方系统安全代理内嵌工作台', '外部集成', 'IframeContainer', '/portal/app/:id', 'IframeContainer.vue', 'SvgIframeApp', 2, 'PC', 1, 0, 'portal:app:view', 1),

-- 【二级业务菜单：3. 物联控制】
(301, 'MENU_IOT_AUDIO', 3, '扩声调音与场景音效控制台', '专业扩声', 'AudioMatrixControl', '/iot/audio', 'AudioMatrixControl.vue', 'SvgSoundMatrix', 1, 'PC', 1, 0, 'iot:audio:control', 1),
(302, 'MENU_IOT_LIGHTING', 3, '场地照明场景与能耗监测台', '场地照明', 'LightingEnergyControl', '/iot/lighting', 'LightingEnergyControl.vue', 'SvgLighting', 2, 'PC', 1, 0, 'iot:lighting:control', 1),
(303, 'MENU_IOT_SCREEN', 3, 'LED大屏与推屏调度控制台', '大屏调度', 'ScreenScoreControl', '/iot/screen', 'ScreenScoreControl.vue', 'SvgLedScreen', 3, 'PC', 1, 0, 'iot:screen:control', 1),
(304, 'MENU_IOT_SCORE', 3, '赛事计时计分接收与大屏推屏', '计时计分', 'MatchScoreBoard', '/iot/score', 'MatchScoreBoard.vue', 'SvgMatchScore', 4, 'PC', 1, 0, 'iot:score:control', 1),
(305, 'MENU_IOT_FLAG', 3, '自动升旗仪式与音画同步仿真台', '智能升旗', 'FlagAutoControl', '/iot/flag', 'FlagAutoControl.vue', 'SvgFlagSystem', 5, 'PC', 1, 0, 'iot:flag:control', 1),
(306, 'MENU_IOT_CLOCK', 3, '标准时钟卫星授时与子钟监测台', '时钟同步', 'ClockSyncMonitor', '/iot/clock', 'ClockSyncMonitor.vue', 'SvgMasterClock', 6, 'PC', 1, 0, 'iot:clock:view', 1),
(307, 'MENU_IOT_VIDEO', 3, '现场水下监控与转播监视台', '视频监控', 'VideoLiveMatrix', '/iot/video', 'VideoLiveMatrix.vue', 'SvgCameraMatrix', 7, 'PC', 1, 0, 'iot:video:view', 1),
(308, 'MENU_IOT_MEDIA', 3, '媒体播控台(背景音乐与视频投屏)', '媒体播控', 'MediaPlayConsole', '/iot/media', 'MediaPlayConsole.vue', 'SvgMediaPlayer', 8, 'PC', 1, 0, 'iot:media:control', 1),
(309, 'MENU_IOT_DYNAMIC', 3, '动态低代码通用设备控制台', '动态设备', 'DynamicDeviceConsole', '/iot/dynamic/:groupId', 'DynamicDeviceConsole.vue', 'SvgDynamicDevice', 9, 'PC', 1, 1, 'iot:dynamic:control', 1),

-- 【二级业务菜单：4. 配置中心】
(401, 'MENU_CONFIG_DEVICES', 4, '异构设备与全协议通信配置中心', '设备配置', 'DeviceConfigCenter', '/config/devices', 'DeviceConfigCenter.vue', 'SvgDeviceSetting', 1, 'PC', 1, 0, 'config:devices:manage', 1),
(402, 'MENU_CONFIG_ACTIONS', 4, '菜单分组与自定义操作按钮配置', '动作编排', 'ActionDynamicConfig', '/config/actions', 'ActionDynamicConfig.vue', 'SvgButtonAction', 2, 'PC', 1, 0, 'config:actions:manage', 1),
(403, 'MENU_CONFIG_ADAPTERS', 4, '外置硬件适配与接线登记台账', '硬件适配', 'HardwareAdapterBook', '/config/adapters', 'HardwareAdapterBook.vue', 'SvgAdapterBook', 3, 'PC', 1, 0, 'config:adapters:manage', 1),
(404, 'MENU_CONFIG_MEDIA', 4, '音频与视频媒体素材资源库', '媒体素材', 'MediaResourceLibrary', '/config/media', 'MediaResourceLibrary.vue', 'SvgMediaLibrary', 4, 'PC', 1, 0, 'config:media:manage', 1),
(405, 'MENU_CONFIG_TEMPLATES', 4, '配置模板与JSON导入导出中心', '配置模板', 'ConfigTemplateCenter', '/config/templates', 'ConfigTemplateCenter.vue', 'SvgConfigTemplate', 5, 'PC', 1, 0, 'config:templates:manage', 1),
(406, 'MENU_CONFIG_SANDBOX', 4, '通信沙箱与模拟调试控制台', '协议沙箱', 'ProtocolMockSandbox', '/config/sandbox', 'ProtocolMockSandbox.vue', 'SvgMockSandbox', 6, 'PC', 1, 0, 'config:sandbox:manage', 1),

-- 【二级业务菜单：5. 运维安全】
(501, 'MENU_OPS_ALARMS', 5, '全链路保活监控与实时告警中心', '链路告警', 'AlarmMonitorCenter', '/ops/alarms', 'AlarmMonitorCenter.vue', 'SvgAlarmBell', 1, 'PC', 1, 0, 'ops:alarms:view', 1),
(502, 'MENU_OPS_CHANNELS', 5, '告警规则与通知渠道配置中心', '告警通道', 'AlarmChannelConfig', '/ops/channels', 'AlarmChannelConfig.vue', 'SvgNotifyChannel', 2, 'PC', 1, 0, 'ops:channels:manage', 1),
(503, 'MENU_OPS_AUDIT', 5, '操作审计日志与导出留存中心', '审计日志', 'AuditLogManager', '/ops/audit', 'AuditLogManager.vue', 'SvgAuditLog', 3, 'PC', 1, 0, 'ops:audit:view', 1),
(504, 'MENU_SYS_USERS', 5, '用户角色管理与细粒度权限配置', '角色权限', 'UserRolePermission', '/system/users', 'UserRolePermission.vue', 'SvgUserRole', 4, 'PC', 1, 0, 'sys:users:manage', 1),

-- 【专属终端与公开路由节点】
(601, 'MENU_TABLET_OPERATIONS', 0, '移动平板现场操作横屏工作台', '平板控制', 'TabletControl', '/tablet/control', 'TabletOperationsView.vue', 'SvgTablet', 99, 'TABLET', 1, 0, 'tablet:operations:view', 1),
(701, 'MENU_AUTH_LOGIN', 0, '统一身份认证登录页', '身份认证', 'Login', '/login', 'LoginPage.vue', 'SvgPortal', 0, 'ALL', 1, 0, '', 1)
ON DUPLICATE KEY UPDATE
  `parent_id` = VALUES(`parent_id`),
  `menu_name` = VALUES(`menu_name`),
  `short_name` = VALUES(`short_name`),
  `route_name` = VALUES(`route_name`),
  `route_path` = VALUES(`route_path`),
  `component_name` = VALUES(`component_name`),
  `icon_code` = VALUES(`icon_code`),
  `sort_order` = VALUES(`sort_order`),
  `terminal_scope` = VALUES(`terminal_scope`),
  `baseline_flag` = VALUES(`baseline_flag`),
  `dynamic_flag` = VALUES(`dynamic_flag`),
  `permission_code` = VALUES(`permission_code`),
  `status` = VALUES(`status`);

SET FOREIGN_KEY_CHECKS = 1;

-- 升级执行完成提示
SELECT 'Database schema migrated successfully: short_name added to sys_menu with 28 predefined nodes.' AS result;
