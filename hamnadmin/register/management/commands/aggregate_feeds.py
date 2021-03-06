import gevent
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from gevent.threadpool import ThreadPool

from hamnadmin.mailqueue.util import send_simple_mail
from hamnadmin.register.models import Blog, Post, AggregatorLog
from hamnadmin.util.aggregate import FeedFetcher
from hamnadmin.util.varnish import purge_root_and_feeds


class BreakoutException(Exception):
    pass


class Command(BaseCommand):
    help = 'Aggregate one or more feeds'

    def add_arguments(self, parser):
        parser.add_argument('--id', type=int, help="Fetch just one feed specified by id")
        parser.add_argument('-d', '--debug', action='store_true', help="Enable debug mode, don't save anything")
        parser.add_argument('-f', '--full', action='store_true', help="Fetch full feed, regardless of last fetch date")
        parser.add_argument('-p', '--parallelism', type=int, default=10, help="Number of parallell requests")

    def trace(self, msg):
        if self.verbose:
            self.stdout.write(msg)

    def handle(self, *args, **options):
        self.verbose = options['verbosity'] > 1
        self.debug = options['debug']
        if self.debug:
            self.verbose = True
        self.full = options['full']

        if options['id']:
            feeds = Blog.objects.filter(pk=options['id'])
        else:
            # Fetch all feeds - that are not archived. We do fetch feeds that are not approved,
            # to make sure they work.
            feeds = Blog.objects.filter(archived=False)

        # Fan out the fetching itself
        fetchers = [FeedFetcher(f, self.trace) for f in feeds]
        num = len(fetchers)
        pool = ThreadPool(options['parallelism'])
        pr = pool.map_async(self._fetch_one_feed, fetchers)
        while not pr.ready():
            gevent.sleep(1)
            self.trace("Fetching feeds (%s/%s done), please wait..." % (num - pool.task_queue.unfinished_tasks, num))

        total_entries = 0
        # Fetching was async, but results processing will be sync. Don't want to deal with
        # multithreaded database connections and such complications.
        try:
            with transaction.atomic():
                for feed, results in pr.get():
                    if isinstance(results, Exception):
                        AggregatorLog(feed=feed,
                                      success=False,
                                      info=results).save()
                    else:
                        if feed.approved:
                            had_entries = True
                        else:
                            had_entries = feed.has_entries
                        entries = 0
                        titles = []

                        for entry in results:
                            self.trace("Found entry at %s" % entry.link)
                            # Entry is a post, but we need to check if it's already there. Check
                            # is done on guid.
                            if not Post.objects.filter(feed=feed, guid=entry.guid).exists():
                                self.trace("Saving entry at %s" % entry.link)
                                entry.save()
                                entry.update_shortlink()
                                AggregatorLog(feed=feed,
                                              success=True,
                                              info="Fetched entry at '%s'" % entry.link).save()
                                entries += 1
                                titles.append(entry.title)
                                total_entries += 1

                        if entries > 0 and feed.approved:
                            # Email a notification that they were picked up
                            send_simple_mail(settings.EMAIL_SENDER,
                                             feed.user.email,
                                             "Posts found at your blog at Planet PostgreSQL",
                                             u"The blog aggregator at Planet PostgreSQL has just picked up the "
                                             u"following\nposts from your blog at {0}:\n\n{1}\n\nIf these entries are "
                                             u"correct, you don't have to do anything.\nIf any entry should not be "
                                             u"there, head over to\n\nhttps://planet.postgresql.org/register/edit/"
                                             u"{2}/\n\nand click the 'Hide' button for those entries as soon\nas "
                                             u"possible.\n\nThank you!\n\n".format(
                                                 feed.blogurl,
                                                 "\n".join(["* " + t for t in titles]),
                                                 feed.id),
                                             sendername="Planet PostgreSQL",
                                             receivername=u"{0} {1}".format(feed.user.first_name, feed.user.last_name),
                                             )

                        if entries > 0 and not had_entries:
                            # Entries showed up on a blog that was previously empty
                            send_simple_mail(settings.EMAIL_SENDER,
                                             settings.NOTIFICATION_RECEIVER,
                                             "A blog was added to Planet PostgreSQL",
                                             u"The blog at {0} by {1}\nwas added to Planet PostgreSQL, and has now "
                                             u"received entries.\n\nTo moderate: "
                                             u"https://planet.postgresql.org/register/moderate/\n\n".format(
                                                 feed.feedurl, feed.user),
                                             sendername="Planet PostgreSQL",
                                             receivername="Planet PostgreSQL Moderators",
                                             )

                        # If the blog URL changed, update it as requested
                        if getattr(feed, 'new_blogurl', None):
                            print("URL changed for %s to %s" % (feed.feedurl, feed.new_blogurl))
                            send_simple_mail(settings.EMAIL_SENDER,
                                             settings.NOTIFICATION_RECEIVER,
                                             "A blog url changed on Planet PostgreSQL",
                                             u"When checking the blog at {0} by {1}\nthe blog URL was updated to:\n"
                                             u"{2}\n(from previous value {3})\n\nTo moderate: "
                                             u"https://planet.postgresql.org/register/moderate/\n\n".format(
                                                 feed.feedurl, feed.user, feed.new_blogurl, feed.blogurl),
                                             sendername="Planet PostgreSQL",
                                             receivername="Planet PostgreSQL Moderators",
                                             )
                            send_simple_mail(settings.EMAIL_SENDER,
                                             feed.user.email,
                                             "URL of your blog at Planet PostgreSQL updated",
                                             u"The blog aggregator at Planet PostgreSQL has update the URL of your "
                                             u"blog\nwith the feed at {0} to:\n{1} (from {2})\nIf this is correct, "
                                             u"you don't have to do anything.\nIf not, please contact "
                                             u"planet@postgresql.org\n".format(
                                                 feed.feedurl,
                                                 feed.new_blogurl,
                                                 feed.blogurl,
                                             ),
                                             sendername="Planet PostgreSQL",
                                             receivername=u"{0} {1}".format(feed.user.first_name, feed.user.last_name),
                                             )
                            feed.blogurl = feed.new_blogurl
                            feed.save()
                if self.debug:
                    # Roll back transaction without error
                    raise BreakoutException()
        except BreakoutException:
            self.stderr.write("Rolling back all changes")
            pass

        if total_entries > 0 and not self.debug:
            purge_root_and_feeds()

    def _fetch_one_feed(self, fetcher):
        if self.full:
            self.trace("Fetching %s" % fetcher.feed.feedurl)
            since = None
        else:
            since = fetcher.feed.lastget
            self.trace("Fetching %s since %s" % (fetcher.feed.feedurl, since))
        try:
            entries = list(fetcher.parse(since))
        except Exception as e:
            self.stderr.write("Failed to fetch '%s': %s" % (fetcher.feed.feedurl, e))
            return fetcher.feed, e
        return fetcher.feed, entries
