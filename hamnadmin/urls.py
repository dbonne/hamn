"""hamnadmin URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView

import hamnadmin.register.views as register_views
from hamnadmin.register.feeds import PostFeed

urlpatterns = [
    url(r'^$', register_views.planet_home, name='planet_home'),
    url(r'^add.html/$', TemplateView.as_view(template_name="add.html")),
    url(r'^feeds.html$', register_views.planet_feeds, name='planet_feeds'),
    url(r'^rss20(?P<type>_short)?\.xml$', PostFeed()),

    url(r'^register/admin/', admin.site.urls),
    url(r'^register/', include('hamnadmin.register.urls')),
]

if settings.DEBUG is True:
    urlpatterns + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    import debug_toolbar

    urlpatterns = [
                      url(r'^__debug__/', include(debug_toolbar.urls)),
                  ] + urlpatterns
