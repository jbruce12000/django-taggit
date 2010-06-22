DATABASE_ENGINE = 'sqlite3'

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'taggit',
    'taggit.tests',
    'taggit.contrib.synonyms',
]

TAGGIT_FILTER_FXN = 'taggit.tests.settings.filterwords'
TAGGIT_NORMALIZE_FXN = lambda tags: [x.lower() for x in tags]

def filterwords(words):
    '''filter words'''
    exclude_these = set(['excluded','words','go','here'])
    return list(set(words).difference(exclude_these))
