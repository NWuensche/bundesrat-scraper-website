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
    path("loadJSON", scraper.views.loadJSON, name="loadJSON"),
    path("metaStudies", scraper.views.metaStudies, name="metaStudies"),
    path("searchTOPTitles", scraper.views.searchTOPTitles, name="searchTOPTitles"),
]
