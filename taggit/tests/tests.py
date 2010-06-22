from __future__ import with_statement
from contextlib import contextmanager
from django.conf import settings

from django.test import TestCase

from taggit.models import Tag
from taggit.tests.forms import FoodForm, DirectFoodForm
from taggit.tests.models import Food, Pet, HousePet, DirectFood, DirectPet, DirectHousePet

from taggit.utils import parse_tags as parse_tag_input, edit_string_for_tags, replace_synonyms_with_tags, filter_tags, normalize_tags, post_process_tags

from taggit.contrib.synonyms.models import TagSynonym



class BaseTaggingTest(TestCase):
    def assert_tags_equal(self, qs, tags, sort=True):
        got = map(lambda tag: tag.name, qs)
        if sort:
            got.sort()
            tags.sort()
        self.assertEqual(got, tags)

    @contextmanager
    def assert_raises(self, exc_type):
        try:
            yield
        except Exception, e:
            self.assert_(type(e) is exc_type, "%s didn't match expected "
                "exception type %s" % (e, exc_type))
        else:
            self.fail("No exception raised, expected %s" % exc_type)


class TaggableManagerTestCase(BaseTaggingTest):
    food_model = Food
    pet_model = Pet
    housepet_model = HousePet

    def test_add_tag(self):
        apple = self.food_model.objects.create(name="apple")
        self.assertEqual(list(apple.tags.all()), [])
        self.assertEqual(list(self.food_model.tags.all()),  [])

        apple.tags.add('green')
        self.assert_tags_equal(apple.tags.all(), ['green'])
        self.assert_tags_equal(self.food_model.tags.all(), ['green'])

        pear = self.food_model.objects.create(name="pear")
        pear.tags.add('green')
        self.assert_tags_equal(pear.tags.all(), ['green'])
        self.assert_tags_equal(self.food_model.tags.all(), ['green'])

        apple.tags.add('red')
        self.assert_tags_equal(apple.tags.all(), ['green', 'red'])
        self.assert_tags_equal(self.food_model.tags.all(), ['green', 'red'])

        self.assert_tags_equal(
            self.food_model.tags.most_common(),
            ['green', 'red'],
            sort=False
        )

        apple.tags.remove('green')
        self.assert_tags_equal(apple.tags.all(), ['red'])
        self.assert_tags_equal(self.food_model.tags.all(), ['green', 'red'])
        tag = Tag.objects.create(name="delicious")
        apple.tags.add(tag)
        self.assert_tags_equal(apple.tags.all(), ["red", "delicious"])

        apple.delete()
        self.assert_tags_equal(self.food_model.tags.all(), ["green"])

        f = self.food_model()
        with self.assert_raises(ValueError):
            f.tags.all()

    def test_unique_slug(self):
        apple = self.food_model.objects.create(name="apple")
        apple.tags.add("Red", "red")

    def test_delete_obj(self):
        apple = self.food_model.objects.create(name="apple")
        apple.tags.add("red")
        self.assert_tags_equal(apple.tags.all(), ["red"])
        strawberry = self.food_model.objects.create(name="strawberry")
        strawberry.tags.add("red")
        apple.delete()
        self.assert_tags_equal(strawberry.tags.all(), ["red"])

    def test_lookup_by_tag(self):
        apple = self.food_model.objects.create(name="apple")
        apple.tags.add("red", "green")
        pear = self.food_model.objects.create(name="pear")
        pear.tags.add("green")

        self.assertEqual(
            list(self.food_model.objects.filter(tags__in=["red"])),
            [apple]
        )
        self.assertEqual(
            list(self.food_model.objects.filter(tags__in=["green"])),
            [apple, pear]
        )

        kitty = self.pet_model.objects.create(name="kitty")
        kitty.tags.add("fuzzy", "red")
        dog = self.pet_model.objects.create(name="dog")
        dog.tags.add("woof", "red")
        self.assertEqual(
            list(self.food_model.objects.filter(tags__in=["red"]).distinct()),
            [apple]
        )

        tag = Tag.objects.get(name="woof")
        self.assertEqual(list(self.pet_model.objects.filter(tags__in=[tag])), [dog])

        cat = self.housepet_model.objects.create(name="cat", trained=True)
        cat.tags.add("fuzzy")

        self.assertEqual(
            map(lambda o: o.pk, self.pet_model.objects.filter(tags__in=["fuzzy"])),
            [kitty.pk, cat.pk]
        )

    def test_similarity_by_tag(self):
        """Test that pears are more similar to apples than watermelons"""
        apple = self.food_model.objects.create(name="apple")
        apple.tags.add("green", "juicy", "small", "sour")

        pear = self.food_model.objects.create(name="pear")
        pear.tags.add("green", "juicy", "small", "sweet")

        watermelon = self.food_model.objects.create(name="watermelon")
        watermelon.tags.add("green", "juicy", "large", "sweet")

        similar_objs = apple.tags.similar_objects()
        self.assertEqual(similar_objs, [pear, watermelon])
        self.assertEqual(map(lambda x: x.similar_tags, similar_objs), [3, 2])

    def test_tag_reuse(self):
        apple = self.food_model.objects.create(name="apple")
        apple.tags.add("juicy", "juicy")
        self.assert_tags_equal(apple.tags.all(), ['juicy'])


class TaggableManagerDirectTestCase(TaggableManagerTestCase):
    food_model = DirectFood
    pet_model = DirectPet
    housepet_model = DirectHousePet


class TaggableFormTestCase(BaseTaggingTest):
    form_class = FoodForm
    food_model = Food

    def test_form(self):
        self.assertEqual(self.form_class.base_fields.keys(), ['name', 'tags'])

        f = self.form_class({'name': 'apple', 'tags': 'green, red, yummy'})
        self.assertEqual(str(f), """<tr><th><label for="id_name">Name:</label></th><td><input id="id_name" type="text" name="name" value="apple" maxlength="50" /></td></tr>\n<tr><th><label for="id_tags">Tags:</label></th><td><input type="text" name="tags" value="green, red, yummy" id="id_tags" /></td></tr>""")
        f.save()
        apple = self.food_model.objects.get(name='apple')
        self.assert_tags_equal(apple.tags.all(), ['green', 'red', 'yummy'])

        f = self.form_class({'name': 'apple', 'tags': 'green, red, yummy, delicious'}, instance=apple)
        f.save()
        apple = self.food_model.objects.get(name='apple')
        self.assert_tags_equal(apple.tags.all(), ['green', 'red', 'yummy', 'delicious'])
        self.assertEqual(self.food_model.objects.count(), 1)

        f = self.form_class({"name": "raspberry"})
        raspberry = f.save()
        self.assert_tags_equal(raspberry.tags.all(), [])

        f = self.form_class(instance=apple)
        self.assertEqual(str(f), """<tr><th><label for="id_name">Name:</label></th><td><input id="id_name" type="text" name="name" value="apple" maxlength="50" /></td></tr>\n<tr><th><label for="id_tags">Tags:</label></th><td><input type="text" name="tags" value="delicious, green, red, yummy" id="id_tags" /></td></tr>""")

class TaggableFormDirectTestCase(TaggableFormTestCase):
    form_class = DirectFoodForm
    food_model = DirectFood

# This class of tests taken from django-tagging
class TestParseTagInput(TestCase):
    def test_with_simple_space_delimited_tags(self):
        """ Test with simple space-delimited tags. """

        self.assertEquals(parse_tag_input('one'), [u'one'])
        self.assertEquals(parse_tag_input('one two'), [u'one', u'two'])
        self.assertEquals(parse_tag_input('one two three'), [u'one', u'three', u'two'])
        self.assertEquals(parse_tag_input('one one two two'), [u'one', u'two'])

    def test_with_comma_delimited_multiple_words(self):
        """ Test with comma-delimited multiple words.
            An unquoted comma in the input will trigger this. """

        self.assertEquals(parse_tag_input(',one'), [u'one'])
        self.assertEquals(parse_tag_input(',one two'), [u'one two'])
        self.assertEquals(parse_tag_input(',one two three'), [u'one two three'])
        self.assertEquals(parse_tag_input('a-one, a-two and a-three'),
            [u'a-one', u'a-two and a-three'])

    def test_with_double_quoted_multiple_words(self):
        """ Test with double-quoted multiple words.
            A completed quote will trigger this.  Unclosed quotes are ignored. """

        self.assertEquals(parse_tag_input('"one'), [u'one'])
        self.assertEquals(parse_tag_input('"one two'), [u'one', u'two'])
        self.assertEquals(parse_tag_input('"one two three'), [u'one', u'three', u'two'])
        self.assertEquals(parse_tag_input('"one two"'), [u'one two'])
        self.assertEquals(parse_tag_input('a-one "a-two and a-three"'),
            [u'a-one', u'a-two and a-three'])

    def test_with_no_loose_commas(self):
        """ Test with no loose commas -- split on spaces. """
        self.assertEquals(parse_tag_input('one two "thr,ee"'), [u'one', u'thr,ee', u'two'])

    def test_with_loose_commas(self):
        """ Loose commas - split on commas """
        self.assertEquals(parse_tag_input('"one", two three'), [u'one', u'two three'])

    def test_tags_with_double_quotes_can_contain_commas(self):
        """ Double quotes can contain commas """
        self.assertEquals(parse_tag_input('a-one "a-two, and a-three"'),
            [u'a-one', u'a-two, and a-three'])
        self.assertEquals(parse_tag_input('"two", one, one, two, "one"'),
            [u'one', u'two'])

    def test_with_naughty_input(self):
        """ Test with naughty input. """

        # Bad users! Naughty users!
        self.assertEquals(parse_tag_input(None), [])
        self.assertEquals(parse_tag_input(''), [])
        self.assertEquals(parse_tag_input('"'), [])
        self.assertEquals(parse_tag_input('""'), [])
        self.assertEquals(parse_tag_input('"' * 7), [])
        self.assertEquals(parse_tag_input(',,,,,,'), [])
        self.assertEquals(parse_tag_input('",",",",",",","'), [u','])
        self.assertEquals(parse_tag_input('a-one "a-two" "a-three'),
            [u'a-one', u'a-three', u'a-two'])

    # this test was requested by Vince Veselosky and is an addition
    # to the django-tagging tests
    def test_round_trip(self):
        """Parse save and return strings for round trip test"""
        tags = []
        for name in parse_tag_input('''1,2,3,"4","5,",6'''):
            tags.append(Tag.objects.create(name=name))
        self.assertEquals(edit_string_for_tags(tags),u'"5,", 1, 2, 3, 4, 6')


class TestEditStringForTags(TestCase):
    def test_recreation_of_tag_list_string_representations(self):
        plain = Tag.objects.create(name='plain')
        spaces = Tag.objects.create(name='spa ces')
        comma = Tag.objects.create(name='com,ma')
        self.assertEquals(edit_string_for_tags([plain]), u'plain')
        self.assertEquals(edit_string_for_tags([plain, spaces]), u'plain, spa ces')
        self.assertEquals(edit_string_for_tags([plain, spaces, comma]), u'"com,ma", plain, spa ces')
        self.assertEquals(edit_string_for_tags([plain, comma]), u'"com,ma", plain')
        self.assertEquals(edit_string_for_tags([comma, spaces]), u'"com,ma", spa ces')

class TestTagPostProcessing(TestCase):
    def test_post_processing(self):
        ''' Test tag post-processing
        just de-duplication and sorting for now
        '''
        tags = ['3','1','1','2']
        ok =   [u'1', u'2', u'3']
        self.assertEquals(post_process_tags(tags),ok)

class TestTagNormalization(TestCase):
    def test_tag_normalization(self):
        tags = ['ABC','def','gHi']
        ok   = ['abc','def','ghi']

        fxn = None
        try:
            fxn = settings.TAGGIT_NORMALIZE_FXN
        except AttributeError:
            pass
        if fxn:
            self.assertEquals(normalize_tags(tags),ok)
            

class TestFilterTags(TestCase):
    def test_filtering_of_tags(self):
        """Test filtering of tags
        filtering depends on a user supplied fxn via settings, so it could
        filter anything.  For tests to be reliable, make sure the settings
        file is exactly what we expect.  if it is not, skip these tests.
        """
        filter_fxn = None
        try:
            filter_fxn = settings.TAGGIT_FILTER_FXN
        except AttributeError:
            pass
        if filter_fxn and filter_fxn=='taggit.tests.settings.filterwords':
            tags = filter_tags(['excluded','should','be','filtered'])
            tags.sort()
            self.assertEquals(tags, [u'be', u'filtered', u'should'])
            tags = filter_tags(['nothing','should','be','filtered'])
            tags.sort()
            self.assertEquals(tags, [u'be', u'filtered', u'nothing', u'should', ])

class TestTagSynonyms(TestCase):
    def setUp(self):
        self.prestxt = u'president barack obama'
        self.prestag = Tag.objects.create(name = self.prestxt )
        TagSynonym.objects.create(tag = self.prestag, name = 'president')
        TagSynonym.objects.create(tag = self.prestag, name = 'barack')
        TagSynonym.objects.create(tag = self.prestag, name = 'obama')
    def test_tag_replaces_synonym(self):
        " tag replaces a synonym "
        self.assertEquals(replace_synonyms_with_tags(['president']),
            [self.prestxt])
        self.assertEquals(replace_synonyms_with_tags(['president','obama']),
            [self.prestxt,self.prestxt])
    def test_tag_does_not_replace_non_synonym(self):
        " tag does not replaces a synonym "
        self.assertEquals(replace_synonyms_with_tags(['notsynonym']),
            [u'notsynonym'])
        self.assertEquals(replace_synonyms_with_tags(
            ['notsynonym',self.prestxt]),[u'notsynonym',self.prestxt])

