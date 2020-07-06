from django.urls import path, include

from django.contrib import admin

admin.autodiscover()

import scraper.views

# To add a new path, first import the app:
# import blog
#
# Then add the new path:
# path('blog/', blog.urls, name="blog")
#
# Learn more here: https://docs.djangoproject.com/en/2.1/topics/http/urls/

urlpatterns = [
    path("", scraper.views.index, name="index"),
    path("tef", scraper.views.update_counter, name="tef"),
    path("send/", scraper.views.sendMethod, name="send/"),
]
