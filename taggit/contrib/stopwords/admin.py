'''admin stuff for stopwords app'''
from django.contrib import admin
from taggit.contrib.stopwords.models import StopWord

class StopWordInline(admin.StackedInline):
    '''set stopwords as inline'''
    model = StopWord

class StopWordAdmin(admin.ModelAdmin):
    '''nuttin'''
    pass

admin.site.register(StopWord, StopWordAdmin)
