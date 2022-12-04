from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


def paginator(dbobject, page, limit=settings.POSTLIMIT):
    return Paginator(dbobject, limit).get_page(page)


def index(request):
    posts = (Post.objects
                 .select_related(
                     'group', 'author'
                 ))
    page_obj = paginator(posts, request.GET.get('page'))
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = (group.posts
                  .select_related(
                      'author'
                  ))
    page_obj = paginator(posts, request.GET.get('page'))
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = (author.posts
                   .select_related(
                       'group'
                   ))
    if request.user.is_authenticated:
        following = (Follow.objects.filter(
                     user=request.user, author=author).exists())
    else:
        following = False
    page_obj = paginator(posts, request.GET.get('page'))
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post.objects
                                 .select_related(
                                     'group', 'author'
                                 ), pk=post_id)
    context = {
        'post': post,
        'form': CommentForm(),
        'comments': Comment.objects.select_related('post'),
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)
    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    article = get_object_or_404(Post.objects
                                    .select_related(
                                        'group', 'author'
                                    ), pk=post_id)
    if request.user != article.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=article)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post.objects
                                 .select_related(
                                     'group', 'author'
                                 ), pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator(posts, request.GET.get('page'))
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if not Follow.objects.filter(user=request.user, author=author).exists():
        Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=request.user, author=author)
    if follow.exists():
        follow.delete()
    return redirect('posts:profile', username)
