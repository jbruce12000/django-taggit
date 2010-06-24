from django.core.exceptions import ValidationError
from django.db import models
from taggit.models import Tag

class TagSynonym(models.Model):
    """Model to associate a synonym to a Tag"""
    tag = models.ForeignKey(Tag, related_name = 'synonyms')
    name = models.CharField(max_length = 200, unique = True)

    def __unicode__(self):
        return "Synonym '%s' for Topic '%s'" % (self.name, self.tag.name)

    class Meta:
        verbose_name = "synonym"
        verbose_name_plural = "synonyms"

