from django.conf import settings

from urllib.request import Request, urlopen


def purge_url(url):
    if not settings.VARNISH_URL:
        print("Not purging {0}".format(url))
    else:
        try:
            request = Request(settings.VARNISH_URL, headers={
                'X-Purge': '^' + url,
            })
            response = urlopen(request, timeout=2)
            if response.getcode() != 200:
                raise Exception("Invalid response code %s" % response.getcode())
        except Exception as e:
            raise Exception("Failed to purge '{0}': {1}'".format(url, e))


def purge_root_and_feeds():
    purge_url('/(|rss20.*)$')
