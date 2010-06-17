from django import forms
from django.contrib import admin
#FIX - should not go out to github
#from taggit.admin import TaggedItemInline
from taggit.contrib.synonyms.models import TagSynonym
from taggit.models import Tag

from taggit.admin import TagAdminForm


class TagSynonymForm(forms.ModelForm):
    class Meta:
        model = TagSynonym

    def clean_name(self):
        '''clean name field of the TagSynonym model in the admin'''

        name = self.cleaned_data["name"]

        # synonyms cannot be a Tag/Topic
        try:
            tag = Tag.objects.get(name=name)
            raise forms.ValidationError("this synonym is not allowed, it is already a topic")
        except Tag.DoesNotExist:
            pass
        return name


class TagSynonymInline(admin.StackedInline):
    model = TagSynonym
    form = TagSynonymForm

class TagSynonymAdmin(admin.ModelAdmin):
    form = TagAdminForm
    prepopulated_fields = { "slug" : ("name",)}
    inlines = [
# FIX - should not go out to github
#        TaggedItemInline,
        TagSynonymInline,
    ]

admin.site.unregister(Tag)
admin.site.register(Tag, TagSynonymAdmin)
