"""
CMS app views for displaying content.

This module provides views for:
- Page detail view (static pages)
- Announcement display
- Content block rendering
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Page, Announcement, ContentBlock, BlogPost, BlogComment
from .forms import BlogCommentForm, BlogCommentReplyForm


def page_detail(request, slug):
    """
    Display a static page.
    
    Args:
        slug: Slug of the page to display
    """
    # Only show published pages to non-staff users
    if request.user.is_staff:
        page = get_object_or_404(Page, slug=slug)
    else:
        page = get_object_or_404(Page, slug=slug, status='published')
    
    return render(request, 'cms/page_detail.html', {
        'page': page,
    })


def get_active_announcements():
    """
    Get currently active announcements.
    
    Utility function for retrieving active announcements.
    Can be used in templates via template tags or context processors.
    
    Returns:
        QuerySet: Active announcements that should be displayed
    """
    now = timezone.now()
    return Announcement.objects.filter(
        is_active=True
    ).filter(
        Q(start_date__isnull=True) | Q(start_date__lte=now)
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=now)
    ).order_by('-created_at')


def get_content_block(slug):
    """
    Get a content block by slug.
    
    Utility function for retrieving content blocks.
    Can be used in templates via template tags or context processors.
    
    Args:
        slug: Slug of the content block
        
    Returns:
        ContentBlock instance or None if not found
    """
    try:
        return ContentBlock.objects.get(slug=slug)
    except ContentBlock.DoesNotExist:
        return None


def blog_list(request):
    """
    Display a list of published blog posts.
    
    Shows paginated list of published blog posts, ordered by published date.
    """
    # Get published blog posts with comment counts
    blog_posts = BlogPost.objects.filter(status='published').annotate(
        comment_count=Count('comments', filter=Q(comments__is_approved=True))
    ).order_by('-published_at', '-created_at')
    
    # If user is staff, show all posts including drafts
    if request.user.is_staff:
        blog_posts = BlogPost.objects.all().annotate(
            comment_count=Count('comments', filter=Q(comments__is_approved=True))
        ).order_by('-published_at', '-created_at')
    
    # Pagination
    paginator = Paginator(blog_posts, 10)  # Show 10 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get featured posts with comment counts
    featured_posts = blog_posts.filter(is_featured=True)[:3]
    
    return render(request, 'cms/blog_list.html', {
        'blog_posts': page_obj,
        'featured_posts': featured_posts,
    })


def blog_detail(request, slug):
    """
    Display a single blog post with comments.
    
    Args:
        slug: Slug of the blog post to display
    """
    # Only show published posts to non-staff users
    if request.user.is_staff:
        post = get_object_or_404(BlogPost, slug=slug)
    else:
        post = get_object_or_404(BlogPost, slug=slug, status='published')
    
    # Get approved comments (top-level comments only, no replies)
    comments = BlogComment.objects.filter(
        blog_post=post,
        is_approved=True,
        parent__isnull=True  # Only top-level comments
    ).order_by('created_at')
    
    # Get related posts (same author or recent posts)
    related_posts = BlogPost.objects.filter(
        status='published'
    ).exclude(
        pk=post.pk
    ).order_by('-published_at')[:3]
    
    # Initialize comment form
    comment_form = BlogCommentForm()
    
    # Handle comment submission
    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = BlogCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.blog_post = post
            comment.user = request.user
            comment.save()
            messages.success(request, 'Your comment has been posted successfully!')
            return redirect('cms:blog_detail', slug=post.slug)
    
    return render(request, 'cms/blog_detail.html', {
        'post': post,
        'related_posts': related_posts,
        'comments': comments,
        'comment_form': comment_form,
    })


@login_required
@require_POST
def add_comment_reply(request, comment_id):
    """
    Handle reply submission to a comment.
    
    Args:
        comment_id: ID of the parent comment
    """
    parent_comment = get_object_or_404(BlogComment, pk=comment_id, is_approved=True)
    
    form = BlogCommentReplyForm(request.POST)
    if form.is_valid():
        reply = form.save(commit=False)
        reply.blog_post = parent_comment.blog_post
        reply.user = request.user
        reply.parent = parent_comment
        reply.save()
        messages.success(request, 'Your reply has been posted successfully!')
        return redirect('cms:blog_detail', slug=parent_comment.blog_post.slug)
    
    messages.error(request, 'There was an error posting your reply.')
    return redirect('cms:blog_detail', slug=parent_comment.blog_post.slug)
