'''stopword utilities'''
from taggit.contrib.stopwords.models import StopWord

def filterwords(words):
    '''filter words'''
    # get a list of all words from the db
    stored_words = set(w.stopword for w in StopWord.objects.all())
    return list(set(words).difference(stored_words))
