-- ==============================================================================
-- 数据清理补丁：删除与 ast_anthem_CN 重复的旧演示国歌素材
-- 说明：升旗流程统一使用国家资料库中的 ast_anthem_CN
--       (/data/venue-ibms/uploads/audio/CN.mp3)，原 id=1 的
--       “中华人民共和国国歌 (管乐军乐标准版)” 只是素材库历史演示记录，
--       未被升旗流程引用，需从 biz_media_asset 中移除。
-- ==============================================================================

SET NAMES utf8mb4;

-- 1. 删除固定的历史演示记录 (id=1，名称含“管乐军乐”)
DELETE FROM `biz_media_asset`
WHERE `id` = 1
  AND `asset_name` LIKE '%管乐军乐%';

-- 2. 兜底：清理所有仍指向旧演示文件 anthem_cn_standard.mp3 的记录
DELETE FROM `biz_media_asset`
WHERE `storage_path` LIKE '%anthem_cn_standard.mp3%'
   OR `access_url` LIKE '%anthem_cn_standard.mp3%';
