-- ==============================================================================
-- 数据清理补丁：删除与 ast_flag_CN 重复的旧演示国旗素材
-- 说明：升旗流程与国家资料库统一使用 ast_flag_CN
--       (/data/venue-ibms/uploads/flags/CN.svg)，原 id=3 的
--       “中华人民共和国国旗标准图形 (国标矢量标样)” 只是素材库历史演示记录，
--       与标准矢量标样重复，需从 biz_media_asset 中移除。
-- ==============================================================================

SET NAMES utf8mb4;

-- 1. 删除固定的历史演示记录 (id=3，名称含“中华人民共和国国旗标准图形”)
DELETE FROM `biz_media_asset`
WHERE `id` = 3
  AND `asset_name` LIKE '%中华人民共和国国旗标准图形%';

-- 2. 兜底：清理所有仍指向旧演示文件 flag_national_standard.svg 的记录
DELETE FROM `biz_media_asset`
WHERE `storage_path` LIKE '%flag_national_standard.svg%'
   OR `access_url` LIKE '%flag_national_standard.svg%';
