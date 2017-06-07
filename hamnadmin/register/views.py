from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.datetime_safe import datetime

from hamnadmin.mailqueue.util import send_simple_mail
from hamnadmin.util.varnish import purge_root_and_feeds, purge_url
from .forms import BlogEditForm
from .models import Post, Blog, Team, AggregatorLog, AuditEntry


def planet_home(request):
    statdate = datetime.now() - timedelta(days=61)
    posts = Post.objects.filter(hidden=False, feed__approved=True).order_by('-dat')[:30]
    topposters = Blog.objects.filter(approved=True, excludestats=False, posts__hidden=False,
                                     posts__dat__gt=statdate).annotate(numposts=Count('posts__id')).order_by(
        '-numposts')[:10]
    topteams = Team.objects.filter(blog__approved=True, blog__excludestats=False, blog__posts__hidden=False,
                                   blog__posts__dat__gt=statdate).annotate(numposts=Count('blog__posts__id')).order_by(
        '-numposts')[:10]
    return render(request, 'index.html', {
        'posts': posts,
        'topposters': topposters,
        'topteams': topteams,
    })


def planet_feeds(request):
    return render(request, 'feeds.html', {
        'feeds': Blog.objects.filter(approved=True, archived=False),
        'teams': Team.objects.filter(blog__approved=True).distinct().order_by('name'),
    })


@login_required
def root(request):
    if request.user.is_superuser and 'admin' in request.GET and request.GET['admin'] == '1':
        blogs = Blog.objects.all().order_by('archived', 'approved', 'name')
    else:
        blogs = Blog.objects.filter(user=request.user).order_by('archived', 'approved', 'name')
    return render(request, 'register/index.html', {
        'blogs': blogs,
        'teams': Team.objects.filter(manager=request.user).order_by('name'),
        'title': 'Your blogs',
    })


@login_required
@transaction.atomic
def edit(request, id=None):
    if id:
        if request.user.is_superuser:
            blog = get_object_or_404(Blog, id=id)
        else:
            blog = get_object_or_404(Blog, id=id, user=request.user)
    else:
        blog = Blog(user=request.user, name=u"{0} {1}".format(request.user.first_name, request.user.last_name))

    if request.method == 'POST':
        saved_url = blog.feedurl
        saved_filter = blog.authorfilter
        saved_team = blog.team
        form = BlogEditForm(request, data=request.POST, instance=blog)
        if form.is_valid():
            if id:
                # This is an existing one. If we change the URL of the blog, it needs to be
                # de-moderated if it was previously approved.
                if blog.approved:
                    if saved_url != form.cleaned_data['feedurl'] or saved_filter != form.cleaned_data['authorfilter']:
                        obj = form.save()
                        obj.approved = False
                        obj.save()

                        send_simple_mail(settings.EMAIL_SENDER,
                                         settings.NOTIFICATION_RECEIVER,
                                         "A blog was edited on Planet PostgreSQL",
                                         u"The blog at {0}\nwas edited by {1} in a way that needs new "
                                         u"moderation.\n\nTo moderate: "
                                         u"https://planet.postgresql.org/register/moderate/\n\n".format(
                                             blog.feedurl, blog.user),
                                         sendername="Planet PostgreSQL",
                                         receivername="Planet PostgreSQL Moderators",
                                         )

                        messages.warning(request,
                                         "Blog has been resubmitted for moderation, and is temporarily disabled.")

                        purge_root_and_feeds()
                        purge_url('/feeds.html')

                        return HttpResponseRedirect(reverse('registration:edit', args=(obj.id,)))

            obj = form.save()

            if obj.team and obj.team != saved_team:
                # We allow anybody to join a team by default, and will just send a notice
                # so the team manager can undo it.
                send_simple_mail(settings.EMAIL_SENDER,
                                 obj.team.manager.email,
                                 "A blog joined your team on Planet PostgreSQL",
                                 u"The blog at {0} by {1} {2}\nhas been added to yor team {3} on Planet "
                                 u"PostgreSQL\n\nIf this is correct, you do not need to do anything.\n\nIf this is "
                                 u"incorrect, please go to\n\nhttps://planet.postgresql.org/register/\n\nand click "
                                 u"the button to remove the blog from your team.\nWe apologize if this causes work "
                                 u"for you.\n\n".format(
                                     obj.feedurl,
                                     obj.user.first_name, obj.user.last_name,
                                     obj.team.name),
                                 sendername="Planet PostgreSQL",
                                 receivername=u"{0} {1}".format(obj.team.manager.first_name,
                                                                obj.team.manager.last_name),
                                 )

            return HttpResponseRedirect("/register/edit/{0}/".format(obj.id))
    else:
        form = BlogEditForm(request, instance=blog)

    return render(request, 'register/edit.html', {
        'new': id is None,
        'form': form,
        'blog': blog,
        'log': AggregatorLog.objects.filter(feed=blog).order_by('-ts')[:30],
        'posts': Post.objects.filter(feed=blog).order_by('-dat')[:10],
        'title': 'Edit blog: %s' % blog.name,
    })


@login_required
@transaction.atomic
def delete(request, id):
    if request.user.is_superuser:
        blog = get_object_or_404(Blog, id=id)
    else:
        blog = get_object_or_404(Blog, id=id, user=request.user)

    send_simple_mail(settings.EMAIL_SENDER,
                     settings.NOTIFICATION_RECEIVER,
                     "A blog was deleted on Planet PostgreSQL",
                     u"The blog at {0} by {1}\nwas deleted by {2}\n\n".format(blog.feedurl, blog.name,
                                                                              request.user.username),
                     sendername="Planet PostgreSQL",
                     receivername="Planet PostgreSQL Moderators",
                     )
    blog.delete()
    messages.info(request, "Blog deleted.")
    purge_root_and_feeds()
    purge_url('/feeds.html')
    return HttpResponseRedirect(reverse('register:root'))


@login_required
@transaction.atomic
def archive(request, id):
    if request.user.is_superuser:
        blog = get_object_or_404(Blog, id=id)
    else:
        blog = get_object_or_404(Blog, id=id, user=request.user)

    send_simple_mail(settings.EMAIL_SENDER,
                     settings.NOTIFICATION_RECEIVER,
                     "A blog was archived on Planet PostgreSQL",
                     u"The blog at {0} by {1}\nwas archived by {2}\n\n".format(blog.feedurl, blog.name,
                                                                               request.user.username),
                     sendername="Planet PostgreSQL",
                     receivername="Planet PostgreSQL Moderators",
                     )
    blog.archived = True
    blog.save()
    messages.info(request, "Blog archived.")
    return HttpResponseRedirect(reverse('register:root'))


@login_required
@transaction.atomic
def remove_from_team(request, teamid, blogid):
    team = get_object_or_404(Team, id=teamid, manager=request.user)
    blog = get_object_or_404(Blog, id=blogid)

    if blog.team != team:
        messages.error(request, "The blog at {0} does not (any more?) belong to the team {1}!".format(
            blog.feedurl,
            team.name))
        return HttpResponseRedirect(reverse('register:root'))

    blog.team = None
    blog.save()

    send_simple_mail(settings.EMAIL_SENDER,
                     settings.NOTIFICATION_RECEIVER,
                     "A blog was removed from a team on Planet PostgreSQL",
                     u"The blog at {0} by {1} {2}\nwas removed from team {3} by {4}.\n".format(
                         blog.feedurl, blog.user.first_name, blog.user.last_name, team.name, request.user.username),
                     sendername="Planet PostgreSQL",
                     receivername="Planet PostgreSQL Moderators",
                     )

    send_simple_mail(settings.EMAIL_SENDER,
                     blog.user.email,
                     "Your blog on Planet PostgreSQL was removed from the team",
                     u"Your blog at {0} has been removed\nfrom the team {1} on Planet PostgreSQL.\n\nIf you believe "
                     u"this to be in error, please contact\nthe team administrator.\n\n".format(
                         blog.feedurl, team.name),
                     sendername="Planet PostgreSQL",
                     receivername=u"{0} {1}".format(blog.user.first_name, blog.user.last_name),
                     )

    messages.info(request, "Blog {0} removed from team {1}".format(blog.feedurl, team.name))
    return HttpResponseRedirect(reverse('register:root'))


def __getvalidblogpost(request, blogid, postid):
    blog = get_object_or_404(Blog, id=blogid)
    post = get_object_or_404(Post, id=postid)
    if not blog.user == request.user and not request.user.is_superuser:
        raise Exception("You can't view/edit somebody elses blog!")
    if not post.feed.id == blog.id:
        raise Exception("Blog does not match post")
    return post


def __setposthide(request, blogid, postid, status):
    post = __getvalidblogpost(request, blogid, postid)
    post.hidden = status
    post.save()
    AuditEntry(request.user.username, 'Set post %s on blog %s visibility to %s' % (postid, blogid, status)).save()
    messages.info(request, 'Set post "%s" to %s' % (post.title, status and "hidden" or "visible"), extra_tags="top")
    purge_root_and_feeds()
    return HttpResponseRedirect(reverse('register:edit', args=(blogid,)))


@login_required
@transaction.atomic
def blogpost_hide(request, blogid, postid):
    return __setposthide(request, blogid, postid, True)


@login_required
@transaction.atomic
def blogpost_unhide(request, blogid, postid):
    return __setposthide(request, blogid, postid, False)


@login_required
@transaction.atomic
def blogpost_delete(request, blogid, postid):
    post = __getvalidblogpost(request, blogid, postid)
    title = post.title

    # Update the feed last fetched date to be just before this entry, so that we end up
    # re-fetching it if necessary.
    post.feed.lastget = post.dat - timedelta(minutes=1)
    post.feed.save()

    # Now actually delete it
    post.delete()
    AuditEntry(request.user.username, 'Deleted post %s from blog %s' % (postid, blogid)).save()
    messages.info(request, 'Deleted post "%s". It will be reloaded on the next scheduled crawl.' % title)
    purge_root_and_feeds()
    return HttpResponseRedirect(reverse('register:edit', args=(blogid,)))
