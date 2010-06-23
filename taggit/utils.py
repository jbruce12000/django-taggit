from functools import wraps
from django.utils.encoding import force_unicode
from django.conf import settings
from django.core.urlresolvers import get_callable

def require_instance_manager(func):
    @wraps(func)
    def inner(self, *args, **kwargs):
        if self.instance is None:
            raise TypeError("Can't call %s with a non-instance manager" % func.__name__)
        return func(self, *args, **kwargs)
    return inner


# this came straight from django-tagging's utils.py
def parse_tags(input):
    """
    Parses tag input, with multiple word input being activated and
    delineated by commas and double quotes. Quotes take precedence, so
    they may contain commas.

    Returns a sorted list of unique tag names.
    """
    if not input:
        return []

    input = force_unicode(input)

    # Special case - if there are no commas or double quotes in the
    # input, we don't *do* a recall... I mean, we know we only need to
    # split on spaces.
    if u',' not in input and u'"' not in input:
        words = split_strip(input, u' ')
        return post_process_tags(words)

    words = []
    buffer = []
    # Defer splitting of non-quoted sections until we know if there are
    # any unquoted commas.
    to_be_split = []
    saw_loose_comma = False
    open_quote = False
    i = iter(input)
    try:
        while 1:
            c = i.next()
            if c == u'"':
                if buffer:
                    to_be_split.append(u''.join(buffer))
                    buffer = []
                # Find the matching quote
                open_quote = True
                c = i.next()
                while c != u'"':
                    buffer.append(c)
                    c = i.next()
                if buffer:
                    word = u''.join(buffer).strip()
                    if word:
                        words.append(word)
                    buffer = []
                open_quote = False
            else:
                if not saw_loose_comma and c == u',':
                    saw_loose_comma = True
                buffer.append(c)
    except StopIteration:
        # If we were parsing an open quote which was never closed treat
        # the buffer as unquoted.
        if buffer:
            if open_quote and u',' in buffer:
                saw_loose_comma = True
            to_be_split.append(u''.join(buffer))
    if to_be_split:
        if saw_loose_comma:
            delimiter = u','
        else:
            delimiter = u' '
        for chunk in to_be_split:
            words.extend(split_strip(chunk, delimiter))
    return post_process_tags(words)

def split_strip(input, delimiter=u','):
    """
    Splits ``input`` on ``delimiter``, stripping each resulting string
    and returning a list of non-empty strings.
    """
    if not input:
        return []

    words = [w.strip() for w in input.split(delimiter)]
    return [w for w in words if w]

def edit_string_for_tags(tags):
    """
    Given list of ``Tag`` instances, creates a string representation of
    the list suitable for editing by the user, such that submitting the
    given string representation back without changing it will give the
    same list of tags.

    Tag names which contain commas will be double quoted.

    If any tag name which isn't being quoted contains whitespace, the
    resulting string of tag names will be comma-delimited, otherwise
    it will be space-delimited.
    """
    names = []
    use_commas = True
    for tag in tags:
        name = tag.name
        if u',' in name:
            names.append('"%s"' % name)
            continue
        elif u' ' in name:
            if not use_commas:
                use_commas = True
        names.append(name)
    names.sort()
    if use_commas:
        glue = u', '
    else:
        glue = u' '
    return glue.join(names)

def post_process_tags(tags):
    tags = filter_tags(tags)
    tags = replace_synonyms_with_tags(tags)
    tags = list(set(tags))
    tags.sort()
    return tags

def filter_tags(tags):
    '''filter tags by a function supplied in settings.py
       ex. TAGGIT_FILTER_FXN = some.function
       which must return a list of filtered tags
    '''
    fxn = None
    try:
        fxn = get_callable(settings.TAGGIT_FILTER_FXN)
        return fxn(tags)
    except AttributeError:
        return tags

def replace_synonyms_with_tags(tags):
    '''replace any synonyms with their parent tags
    '''
    if 'taggit.contrib.synonyms' in settings.INSTALLED_APPS:
        from taggit.contrib.synonyms.models import TagSynonym
        clean_tags = []
        for tag in tags:
            try:
                # subsitute the parent name
                synonym = TagSynonym.objects.get(name=tag)
                clean_tags.append(synonym.tag.name)
            except TagSynonym.DoesNotExist:
                clean_tags.append(tag)
        return clean_tags
    return tags

