-- ==============================================================================
-- 体育场馆应用集成管理系统 (IBMS) 增量迁移升级脚本
-- 功能：新增系统设置 (包含Logo、版权、运营商、本地/OSS存储驱动配置) 与左侧菜单项
-- 对应文件：src/views/system/SystemSetting.vue, src/services/systemSettingService.js
-- 版本：v1.1.0 (2026-10-21)
-- ==============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 1. 创建系统基础设置表 sys_setting (如已存在则跳过)
CREATE TABLE IF NOT EXISTS `sys_setting` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `setting_key` VARCHAR(64) NOT NULL COMMENT '配置唯一键名',
  `setting_value` TEXT COMMENT '配置值(文本/JSON格式)',
  `setting_category` VARCHAR(32) NOT NULL DEFAULT 'SYSTEM' COMMENT '配置大类: SYSTEM(系统基础)/COPYRIGHT(版权信息)/OPERATOR(开发运营)/STORAGE(文件存储)',
  `setting_desc` VARCHAR(255) DEFAULT '' COMMENT '配置描述说明',
  `is_public` TINYINT NOT NULL DEFAULT 1 COMMENT '是否前端公开可见: 1=公开, 0=敏感保密',
  `updated_by` VARCHAR(64) DEFAULT 'admin' COMMENT '最后更新人',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_setting_key` (`setting_key`),
  KEY `idx_category` (`setting_category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统基础配置与对象存储设置表';

-- 2. 插入或更新出厂预设配置项
INSERT INTO `sys_setting` (`setting_key`, `setting_value`, `setting_category`, `setting_desc`, `is_public`, `updated_by`) VALUES
('system_name', '体育场馆应用集成管控平台', 'SYSTEM', '平台系统全称', 1, 'admin'),
('version', 'v1.0.0', 'SYSTEM', '系统版本号', 1, 'admin'),
('system_logo', '', 'SYSTEM', '系统自定义Logo Base64/URL', 1, 'admin'),
('system_logo_preset', 'SvgSettingGear', 'SYSTEM', '系统预设内置图标名', 1, 'admin'),
('copyright_text', '© 2026 体育场馆集成管控中心 保留所有权利', 'COPYRIGHT', '版权声明正文', 1, 'admin'),
('copyright_owner', '国家奥林匹克体育中心 / 智慧场馆运营保障联合指挥部', 'COPYRIGHT', '版权所属单位', 1, 'admin'),
('copyright_year', '2026', 'COPYRIGHT', '版权声明年份', 1, 'admin'),
('icp_license', '京ICP备20268888号-1', 'COPYRIGHT', '工信部ICP备案号', 1, 'admin'),
('security_record', '京公网安备 11010502030110号', 'COPYRIGHT', '公安机关互联网站备案号', 1, 'admin'),
('commercial_license', 'SP2026-STAD-09921', 'COPYRIGHT', '商业运营许可或特许资质编号', 1, 'admin'),
('storage_driver', 'LOCAL', 'STORAGE', '存储驱动方式: LOCAL(本地存储) / OSS(阿里云OSS对象存储)', 1, 'admin'),
('local_storage_config', '{"baseDir":"/data/ibms/uploads","urlPrefix":"/uploads/","maxFileSizeMb":50,"allowedExtensions":["jpg","jpeg","png","gif","svg","mp3","wav","mp4","pdf","json","xlsx"]}', 'STORAGE', '本地文件存储配置详情', 1, 'admin'),
('oss_storage_config', '{"provider":"ALIYUN","endpoint":"oss-cn-beijing.aliyuncs.com","bucketName":"olympic-stadium-ibms","accessKeyId":"LTAI5t********K6Wz","accessKeySecret":"w8Kz9x********9B2e","cdnDomain":"https://cdn.olympic-stadium.cn","basePath":"ibms/attachments/","aclPolicy":"public-read"}', 'STORAGE', 'OSS对象存储配置详情', 0, 'admin')
ON DUPLICATE KEY UPDATE
  `setting_category` = VALUES(`setting_category`),
  `setting_desc` = VALUES(`setting_desc`),
  `is_public` = VALUES(`is_public`);

-- 3. 注册菜单与路由 sys_menu (挂载在配置中心，如不存在则插入)
INSERT INTO `sys_menu` (`id`, `menu_code`, `parent_id`, `menu_name`, `short_name`, `route_name`, `route_path`, `component_name`, `icon_code`, `sort_order`, `terminal_scope`, `baseline_flag`, `dynamic_flag`, `permission_code`, `status`)
SELECT 407, 'MENU_SYS_SETTINGS', 4, '平台系统设置与对象存储中心', '系统设置', 'SystemSetting', '/system/settings', 'SystemSetting.vue', 'SvgSettingGear', 7, 'PC', 1, 0, 'sys:settings:manage', 1
WHERE NOT EXISTS (SELECT 1 FROM `sys_menu` WHERE `menu_code` = 'MENU_SYS_SETTINGS');

-- 4. 注册对应管理员权限 sys_permission (如不存在则插入)
INSERT INTO `sys_permission` (`permission_code`, `permission_name`, `resource_type`, `action_code`, `terminal_scope`, `description`)
SELECT 'sys:settings:manage', '系统基础参数与OSS对象存储配置管理', 'PAGE', 'CONFIG', 'PC', '允许进入系统设置中心，修改平台Logo、版权权属及切换存储引擎'
WHERE NOT EXISTS (SELECT 1 FROM `sys_permission` WHERE `permission_code` = 'sys:settings:manage');

SET FOREIGN_KEY_CHECKS = 1;
