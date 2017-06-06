from datetime import timedelta
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
