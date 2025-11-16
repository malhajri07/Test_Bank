#!/bin/bash
# Quick script to view CMS data in PostgreSQL

echo "=========================================="
echo "CMS DATA IN POSTGRESQL DATABASE"
echo "=========================================="
echo ""

echo "=== CMS PAGES ==="
psql -U mohammedalhajri -d testbank_db -c "SELECT id, title, slug, status, created_at FROM cms_page ORDER BY created_at DESC;"

echo ""
echo "=== CMS ANNOUNCEMENTS ==="
psql -U mohammedalhajri -d testbank_db -c "SELECT id, title, announcement_type, is_active, show_on_homepage, created_at FROM cms_announcement ORDER BY created_at DESC;"

echo ""
echo "=== CMS MEDIA ==="
psql -U mohammedalhajri -d testbank_db -c "SELECT id, title, media_type, created_at FROM cms_media ORDER BY created_at DESC;"

echo ""
echo "=== CMS CONTENT BLOCKS ==="
psql -U mohammedalhajri -d testbank_db -c "SELECT id, name, slug, block_type, created_at FROM cms_contentblock ORDER BY created_at DESC;"

echo ""
echo "=== SUMMARY ==="
psql -U mohammedalhajri -d testbank_db -c "
SELECT 
    'Pages' as type,
    COUNT(*)::text as total,
    (SELECT COUNT(*)::text FROM cms_page WHERE status = 'published') as published
FROM cms_page
UNION ALL
SELECT 
    'Announcements' as type,
    COUNT(*)::text as total,
    (SELECT COUNT(*)::text FROM cms_announcement WHERE is_active = true) as active
FROM cms_announcement
UNION ALL
SELECT 
    'Media' as type,
    COUNT(*)::text as total,
    'N/A' as active
FROM cms_media
UNION ALL
SELECT 
    'Content Blocks' as type,
    COUNT(*)::text as total,
    'N/A' as active
FROM cms_contentblock;
"

