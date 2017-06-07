from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render_to_response
# Public planet
from django.utils.datetime_safe import datetime

from .models import Post, Blog, Team


def planet_home(request):
    statdate = datetime.now() - timedelta(days=61)
    posts = Post.objects.filter(hidden=False, feed__approved=True).order_by('-dat')[:30]
    topposters = Blog.objects.filter(approved=True, excludestats=False, posts__hidden=False,
                                     posts__dat__gt=statdate).annotate(numposts=Count('posts__id')).order_by(
        '-numposts')[:10]
    topteams = Team.objects.filter(blog__approved=True, blog__excludestats=False, blog__posts__hidden=False,
                                   blog__posts__dat__gt=statdate).annotate(numposts=Count('blog__posts__id')).order_by(
        '-numposts')[:10]
    return render_to_response('index.html', {
        'posts': posts,
        'topposters': topposters,
        'topteams': topteams,
    })


def planet_feeds(request):
    return render_to_response('feeds.html', {
        'feeds': Blog.objects.filter(approved=True, archived=False),
        'teams': Team.objects.filter(blog__approved=True).distinct().order_by('name'),
    })


@login_required
def root(request):
    if request.user.is_superuser and 'admin' in request.GET and request.GET['admin'] == '1':
        blogs = Blog.objects.all().order_by('archived', 'approved', 'name')
    else:
        blogs = Blog.objects.filter(user=request.user).order_by('archived', 'approved', 'name')
    return render_to_response('register/index.html', {
        'blogs': blogs,
        'teams': Team.objects.filter(manager=request.user).order_by('name'),
        'title': 'Your blogs',
    })
