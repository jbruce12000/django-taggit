'''models for stopwords app'''
from django.db import models

class StopWord(models.Model):
    """Model to store stop-words 
       which can never be used as a tag/topic"""
    stopword = models.CharField(max_length=200, unique=True)

    def __unicode__(self):
        return self.stopword
