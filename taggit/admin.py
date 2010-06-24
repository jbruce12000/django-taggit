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
                raise forms.ValidationError("this tag is not allowed")

        # synonyms cannot be topic names
        if 'taggit.contrib.synonyms' in settings.INSTALLED_APPS:
            from taggit.contrib.synonyms.models import TagSynonym
            try:
                synonym = TagSynonym.objects.get(name=name)
                raise forms.ValidationError("this tag is not allowed, it is already a synonym of tag = %s" % synonym.tag.name)
            except TagSynonym.DoesNotExist:
                pass 

        return name


class TagAdmin(admin.ModelAdmin):
    form = TagAdminForm
# this was removed because if a tag is added directly through "add tags"
# urilify.js was removing common words so the same tag could be entered
# but have two different slugs ex. "president of the usa"
#    prepopulated_fields = { "slug" : ("name",)}
    inlines = [
        TaggedItemInline
    ]


admin.site.register(Tag, TagAdmin)
