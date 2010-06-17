from django.contrib import admin
from django.conf import settings
from django.core.urlresolvers import get_callable
from django import forms

from taggit.models import Tag, TaggedItem
from taggit.utils import parse_tags

class TaggedItemInline(admin.StackedInline):
    model = TaggedItem

class TagAdminForm(forms.ModelForm):
    class Meta:
        model = Tag 

    def clean_name(self):
        '''clean the name field of the Tag model in the admin'''
        # allow for filtering of tags by fxn - supplied from settings

        name = self.cleaned_data["name"]

        filter_fxn = None
        try:
            filter_fxn = get_callable(settings.TAGGIT_FILTER_FXN)
        except AttributeError:
            pass
        if filter_fxn:
            words = filter_fxn(words=[name])
            if len(words)==0: #filtered words are not allowed
                # FIX - wordsmithing...
                raise forms.ValidationError("this topic is not allowed")

        # synonyms cannot be topic names
        if 'taggit.contrib.synonyms' in settings.INSTALLED_APPS:
            from taggit.contrib.synonyms.models import TagSynonym
            try:
                synonym = TagSynonym.objects.get(name=name)
                raise forms.ValidationError("this topic is not allowed, it is already a synonym of topic = %s" % synonym.tag.name)
            except TagSynonym.DoesNotExist:
                pass 

        return name


class TagAdmin(admin.ModelAdmin):
    form = TagAdminForm
    prepopulated_fields = { "slug" : ("name",)}
    inlines = [
# Fix - this should not got out to github
# Vince does not wanted Tagged Items in the admin
#        TaggedItemInline
    ]


admin.site.register(Tag, TagAdmin)
#admin.site.register(Tag)
