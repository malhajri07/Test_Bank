-- View CMS Data in PostgreSQL
-- Run this file with: psql -U mohammedalhajri -d testbank_db -f view_cms_data.sql

-- ============================================
-- CMS PAGES
-- ============================================
\echo '=== CMS PAGES ==='
SELECT 
    id,
    title,
    slug,
    status,
    is_featured,
    created_at,
    published_at
FROM cms_page
ORDER BY created_at DESC;

-- View full page content (first 100 chars)
\echo ''
\echo '=== PAGE CONTENT (Preview) ==='
SELECT 
    id,
    title,
    slug,
    LEFT(content, 100) as content_preview,
    status
FROM cms_page
ORDER BY created_at DESC;

-- ============================================
-- CMS ANNOUNCEMENTS
-- ============================================
\echo ''
\echo '=== CMS ANNOUNCEMENTS ==='
SELECT 
    id,
    title,
    announcement_type,
    is_active,
    show_on_homepage,
    start_date,
    end_date,
    created_at
FROM cms_announcement
ORDER BY created_at DESC;

-- View announcement content (first 100 chars)
\echo ''
\echo '=== ANNOUNCEMENT CONTENT (Preview) ==='
SELECT 
    id,
    title,
    LEFT(content, 100) as content_preview,
    announcement_type,
    is_active
FROM cms_announcement
ORDER BY created_at DESC;

-- ============================================
-- CMS MEDIA
-- ============================================
\echo ''
\echo '=== CMS MEDIA ==='
SELECT 
    id,
    title,
    media_type,
    created_at
FROM cms_media
ORDER BY created_at DESC;

-- ============================================
-- CMS CONTENT BLOCKS
-- ============================================
\echo ''
\echo '=== CMS CONTENT BLOCKS ==='
SELECT 
    id,
    name,
    slug,
    block_type,
    created_at
FROM cms_contentblock
ORDER BY created_at DESC;

-- ============================================
-- SUMMARY COUNTS
-- ============================================
\echo ''
\echo '=== SUMMARY ==='
SELECT 
    (SELECT COUNT(*) FROM cms_page) as total_pages,
    (SELECT COUNT(*) FROM cms_page WHERE status = 'published') as published_pages,
    (SELECT COUNT(*) FROM cms_announcement) as total_announcements,
    (SELECT COUNT(*) FROM cms_announcement WHERE is_active = true) as active_announcements,
    (SELECT COUNT(*) FROM cms_media) as total_media,
    (SELECT COUNT(*) FROM cms_contentblock) as total_content_blocks;

