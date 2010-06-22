'''tests for stopwords app'''
from django.test import TestCase
from taggit.contrib.stopwords.utils import filterwords

class TestUtils(TestCase):
    '''test all utilities'''
    def test_filterwords(self):
        '''verify words are properly filtered based on list'''
        words = ['this', 'is', 'a', 'test']
        whats_left = ['test']
        none_filtered = ['branch', 'twig', 'tree', 'trunk']
        got = filterwords(words)
        self.assertEquals(got, whats_left)
        self.assertEquals(none_filtered, none_filtered)
