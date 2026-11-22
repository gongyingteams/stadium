-- ==============================================================================
-- 体育场馆应用集成管理系统 增量数据库迁移脚本
-- 迁移目标：用户专属外部集成与本地软件管理域字段扩充
-- 新增/修改：选填账号与密码凭据、应用图标自动识别与自定义Base64/URL存储、MEDIUMTEXT兼容
-- 执行环境：MySQL 5.7+ / 8.0+ / MariaDB
-- ==============================================================================

SET NAMES utf8mb4;

-- 1. 确保 sys_user_external_app 表存在
CREATE TABLE IF NOT EXISTS `sys_user_external_app` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '集成软件ID',
  `username` VARCHAR(64) NOT NULL COMMENT '所属用户名(多用户独立可见)',
  `app_name` VARCHAR(128) NOT NULL COMMENT '软件系统名称',
  `app_type` VARCHAR(32) NOT NULL DEFAULT 'BS' COMMENT '架构类型: BS(B/S网页系统), CS(C/S桌面软件), UNKNOWN(未知/脚本工具)',
  `target_path` VARCHAR(512) NOT NULL COMMENT '访问地址或本地安装可执行路径 (如 D:\\antigravity\\Antigravity IDE 或 http://...)',
  `start_args` VARCHAR(255) DEFAULT '' COMMENT '启动参数/附加参数',
  `app_desc` VARCHAR(255) DEFAULT '' COMMENT '功能描述与用途备注',
  `auth_username` VARCHAR(64) DEFAULT '' COMMENT '登录账号(选填)',
  `auth_password` VARCHAR(255) DEFAULT '' COMMENT '登录密码(选填/凭据备注)',
  `icon_type` VARCHAR(16) NOT NULL DEFAULT 'PRESET' COMMENT '图标类型: PRESET(内置工控图标), CUSTOM(自定义图片URL/Base64)',
  `icon` VARCHAR(64) DEFAULT 'SvgAppGrid' COMMENT '内置图标编码',
  `custom_icon_url` MEDIUMTEXT DEFAULT NULL COMMENT '自定义图标图片URL或Base64(选填)',
  `sort_order` INT NOT NULL DEFAULT 0 COMMENT '排序号',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 0=禁用, 1=启用',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_type` (`username`, `app_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户专属外部集成软件管理表';

-- 2. 若表已存在，执行增量添加/修改字段保护（兼容老版本升级）
SET @dbname = DATABASE();
SET @tablename = "sys_user_external_app";

-- 检查并添加 auth_username 字段
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (TABLE_SCHEMA = @dbname)
      AND (TABLE_NAME = @tablename)
      AND (COLUMN_NAME = "auth_username")
  ) > 0,
  "SELECT 1",
  "ALTER TABLE `sys_user_external_app` ADD COLUMN `auth_username` VARCHAR(64) DEFAULT '' COMMENT '登录账号(选填)' AFTER `app_desc`;"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- 检查并添加 auth_password 字段
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (TABLE_SCHEMA = @dbname)
      AND (TABLE_NAME = @tablename)
      AND (COLUMN_NAME = "auth_password")
  ) > 0,
  "SELECT 1",
  "ALTER TABLE `sys_user_external_app` ADD COLUMN `auth_password` VARCHAR(255) DEFAULT '' COMMENT '登录密码(选填/凭据备注)' AFTER `auth_username`;"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- 检查并添加 icon_type 字段
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (TABLE_SCHEMA = @dbname)
      AND (TABLE_NAME = @tablename)
      AND (COLUMN_NAME = "icon_type")
  ) > 0,
  "SELECT 1",
  "ALTER TABLE `sys_user_external_app` ADD COLUMN `icon_type` VARCHAR(16) NOT NULL DEFAULT 'PRESET' COMMENT '图标类型: PRESET(内置工控图标), CUSTOM(自定义图片URL/Base64)' AFTER `auth_password`;"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- 检查并修改 custom_icon_url 字段为 MEDIUMTEXT
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (TABLE_SCHEMA = @dbname)
      AND (TABLE_NAME = @tablename)
      AND (COLUMN_NAME = "custom_icon_url")
  ) > 0,
  "ALTER TABLE `sys_user_external_app` MODIFY COLUMN `custom_icon_url` MEDIUMTEXT DEFAULT NULL COMMENT '自定义图标图片URL或Base64(选填)';",
  "ALTER TABLE `sys_user_external_app` ADD COLUMN `custom_icon_url` MEDIUMTEXT DEFAULT NULL COMMENT '自定义图标图片URL或Base64(选填)' AFTER `icon`;"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- 3. 示例测试数据维护 (如表中已无数据则补齐示例)
INSERT IGNORE INTO `sys_user_external_app` 
  (`id`, `username`, `app_name`, `app_type`, `target_path`, `start_args`, `app_desc`, `auth_username`, `auth_password`, `icon_type`, `icon`, `custom_icon_url`, `sort_order`, `status`)
VALUES
  (1, 'admin', 'Antigravity IDE 智能开发环境', 'CS', 'D:\\antigravity\\Antigravity IDE\\antigravity.exe', '--portable', '场馆工控协议自动化二次开发与调测环境', 'admin', 'dev@2026', 'PRESET', 'SvgDynamicDevice', NULL, 1, 1),
  (2, 'admin', '票务检票闸机综合管控后台', 'BS', 'http://192.168.1.88:8080/ticketing/gate', '', '东区与南区观众安检通道智能闸机核销控制系统', 'gate_admin', 'TicketPass#88', 'PRESET', 'SvgAppGrid', NULL, 2, 1),
  (3, 'admin', 'Novastar NovaLCT 屏幕配置工具', 'CS', 'C:\\Program Files\\Novastar\\NovaLCT\\NovaLCT.exe', '', '全彩主大屏箱体映射、灰度校准与多路网口发送卡配置端', '', '', 'PRESET', 'SvgLedScreen', NULL, 3, 1),
  (4, 'admin', 'PLC 备用电源自动化巡检脚本', 'UNKNOWN', 'D:\\scripts\\plc_battery_check.bat', '--fast-check', '双回路UPS与柴油发电机状态探针诊断批处理', '', '', 'PRESET', 'SvgDeviceSetting', NULL, 4, 1);
