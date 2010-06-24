'''tests for stopwords app'''
from django.test import TestCase
from taggit.contrib.stopwords.utils import filterwords

class TestUtils(TestCase):
    '''test all utilities'''
    def test_filterwords(self):
        '''verify words are properly filtered based on list'''
        words = ['this', 'is', 'a', 'test']
        whats_left = ['test']
        none_filtered = ['branch', 'tree', 'trunk', 'twig']
        got = filterwords(words)
        self.assertEquals(got, whats_left)
        got = filterwords(none_filtered);
        got.sort()
        self.assertEquals(got, none_filtered)
