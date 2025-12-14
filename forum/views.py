"""
Views for Forum app.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import ForumCategory, ForumTopic, ForumPost
from .forms import ForumTopicForm, ForumPostForm, ForumCategoryForm


def forum_index(request):
    """
    Display forum index page with all categories.
    """
    categories = ForumCategory.objects.filter(is_active=True).annotate(
        topic_count=Count('topics', filter=Q(topics__is_locked=False)),
        post_count=Count('topics__posts', filter=Q(topics__is_locked=False, topics__posts__isnull=False))
    ).order_by('order', 'name')
    
    # Get recent topics across all categories
    recent_topics = ForumTopic.objects.filter(
        category__is_active=True,
        is_locked=False
    ).select_related('category', 'author').prefetch_related('posts').order_by('-last_activity_at')[:10]
    
    context = {
        'categories': categories,
        'recent_topics': recent_topics,
    }
    
    return render(request, 'forum/index.html', context)


def category_detail(request, slug):
    """
    Display topics within a specific category.
    """
    category = get_object_or_404(ForumCategory, slug=slug, is_active=True)
    
    # Get topics in this category
    topics = ForumTopic.objects.filter(
        category=category,
        is_locked=False
    ).select_related('author', 'category').prefetch_related('posts').annotate(
        reply_count=Count('posts') - 1  # Subtract 1 for the initial post
    ).order_by('-is_pinned', '-last_activity_at')
    
    # Pagination
    paginator = Paginator(topics, 20)  # 20 topics per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'topics': page_obj,
    }
    
    return render(request, 'forum/category_detail.html', context)


@login_required
@require_POST
def category_create_ajax(request):
    """
    Create a new category via AJAX.
    """
    form = ForumCategoryForm(request.POST)
    if form.is_valid():
        category = form.save(commit=False)
        category.is_active = True
        category.save()
        return JsonResponse({
            'success': True,
            'category': {
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
            }
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)


@login_required
def topic_create(request, category_slug=None):
    """
    Create a new forum topic.
    """
    # Get or create a default "General Discussion" category
    default_category, created = ForumCategory.objects.get_or_create(
        slug='general-discussion',
        defaults={
            'name': 'General Discussion',
            'description': 'General topics and discussions',
            'is_active': True,
            'order': 0
        }
    )
    
    if request.method == 'POST':
        form = ForumTopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.author = request.user
            topic.category = default_category  # Auto-assign to default category
            topic.save()
            
            # Create the initial post
            ForumPost.objects.create(
                topic=topic,
                author=request.user,
                content=topic.content
            )
            
            messages.success(request, 'Topic created successfully!')
            return redirect(topic.get_absolute_url())
    else:
        form = ForumTopicForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'forum/topic_create.html', context)


def topic_detail(request, category_slug, topic_slug):
    """
    Display a forum topic with all its posts.
    """
    category = get_object_or_404(ForumCategory, slug=category_slug, is_active=True)
    topic = get_object_or_404(
        ForumTopic,
        category=category,
        slug=topic_slug,
        is_locked=False
    )
    
    # Increment view count
    topic.views_count += 1
    topic.save(update_fields=['views_count'])
    
    # Get all posts in this topic
    posts = topic.posts.select_related('author').order_by('created_at')
    
    # Pagination
    paginator = Paginator(posts, 20)  # 20 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Form for replying
    reply_form = None
    if request.user.is_authenticated:
        reply_form = ForumPostForm()
    
    context = {
        'category': category,
        'topic': topic,
        'posts': page_obj,
        'reply_form': reply_form,
    }
    
    return render(request, 'forum/topic_detail.html', context)


@login_required
@require_POST
def topic_reply(request, category_slug, topic_slug):
    """
    Reply to a forum topic.
    """
    category = get_object_or_404(ForumCategory, slug=category_slug, is_active=True)
    topic = get_object_or_404(
        ForumTopic,
        category=category,
        slug=topic_slug
    )
    
    if topic.is_locked:
        messages.error(request, 'This topic is locked and cannot be replied to.')
        return redirect(topic.get_absolute_url())
    
    form = ForumPostForm(request.POST)
    if form.is_valid():
        post = form.save(commit=False)
        post.topic = topic
        post.author = request.user
        post.save()
        
        messages.success(request, 'Your reply has been posted!')
        return redirect(topic.get_absolute_url())
    else:
        messages.error(request, 'There was an error posting your reply.')
        return redirect(topic.get_absolute_url())


@login_required
def post_edit(request, post_id):
    """
    Edit a forum post.
    """
    post = get_object_or_404(ForumPost, pk=post_id)
    
    # Check if user owns the post
    if post.author != request.user:
        messages.error(request, 'You can only edit your own posts.')
        return redirect(post.topic.get_absolute_url())
    
    if request.method == 'POST':
        form = ForumPostForm(request.POST, instance=post)
        if form.is_valid():
            edited_post = form.save(commit=False)
            edited_post.is_edited = True
            edited_post.edited_at = timezone.now()
            edited_post.save()
            
            messages.success(request, 'Post updated successfully!')
            return redirect(post.topic.get_absolute_url())
    else:
        form = ForumPostForm(instance=post)
    
    context = {
        'form': form,
        'post': post,
        'topic': post.topic,
    }
    
    return render(request, 'forum/post_edit.html', context)
