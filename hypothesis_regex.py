from collections import namedtuple
import re
import six
import six.moves
import string
import sre_parse as sre
import sys
import time
import warnings
import hypothesis.errors as he
import hypothesis.strategies as hs

__all__ = ['regex']


HAS_SUBPATTERN_FLAGS = sys.version_info[:2] >= (3, 6)


UNICODE_CATEGORIES = set([
    'Cf', 'Cn', 'Co', 'LC', 'Ll', 'Lm', 'Lo', 'Lt', 'Lu',
    'Mc', 'Me', 'Mn', 'Nd', 'Nl', 'No', 'Pc', 'Pd', 'Pe',
    'Pf', 'Pi', 'Po', 'Ps', 'Sc', 'Sk', 'Sm', 'So', 'Zl',
    'Zp', 'Zs',
])


SPACE_CHARS = u' \t\n\r\f\v'
UNICODE_SPACE_CHARS = SPACE_CHARS + u'\x1c\x1d\x1e\x1f\x85'
UNICODE_DIGIT_CATEGORIES = set(['Nd'])
UNICODE_SPACE_CATEGORIES = set(['Zs', 'Zl', 'Zp'])
UNICODE_LETTER_CATEGORIES = set(['LC', 'Ll', 'Lm', 'Lo', 'Lt', 'Lu'])
UNICODE_WORD_CATEGORIES = UNICODE_LETTER_CATEGORIES | set(['Nd', 'Nl', 'No'])

HAS_WEIRD_WORD_CHARS = (2, 7) <= sys.version_info[:2] < (3, 4)
UNICODE_WEIRD_NONWORD_CHARS = u'\U00012432\U00012433\U00012456\U00012457'


def encourage_user_to_update():
    warnings.warn(
        'The `hypothesis-regex` package has been merged upstream in '
        'Hypothesis 3.19, in 2017.  `hypothesis.strategies.from_regex` has '
        'an identical API, and better handling for several regex constructs. '
        'Sleeping for five seconds to encourage migrating...'
    )
    time.sleep(5)


encourage_user_to_update()


class Context(object):
    __slots__ = ['groups', 'flags']

    def __init__(self, groups=None, flags=0):
        self.groups = groups or {}
        self.flags = flags


class CharactersBuilder(object):
    '''
    Helper object that allows to configure `characters()` strategy with various
    unicode categories and characters. Also allows negation of configured set.

    :param negate: If True, configure `characters()` to match anything other than
        configured character set
    :param flags: Regex flags. They affect how and which characters are matched
    '''
    def __init__(self, negate=False, flags=0):
        self._categories = set()
        self._whitelist_chars = set()
        self._blacklist_chars = set()
        self._negate = negate
        self._ignorecase = flags & re.IGNORECASE
        self._unicode = (not flags & re.ASCII) \
            if six.PY3 else bool(flags & re.UNICODE)

    @property
    def strategy(self):
        'Returns resulting strategy that generates configured char set'
        max_codepoint = None if self._unicode else 127

        strategies = []
        if self._negate:
            if self._categories or self._whitelist_chars:
                strategies.append(
                    hs.characters(
                        blacklist_categories=self._categories | set(['Cc', 'Cs']),
                        blacklist_characters=self._whitelist_chars,
                        max_codepoint=max_codepoint,
                    )
                )
            if self._blacklist_chars:
                strategies.append(
                    hs.sampled_from(
                        list(self._blacklist_chars - self._whitelist_chars)
                    )
                )
        else:
            if self._categories or self._blacklist_chars:
                strategies.append(
                    hs.characters(
                        whitelist_categories=self._categories,
                        blacklist_characters=self._blacklist_chars,
                        max_codepoint=max_codepoint,
                    )
                )
            if self._whitelist_chars:
                strategies.append(
                    hs.sampled_from(
                        list(self._whitelist_chars - self._blacklist_chars)
                    )
                )

        return hs.one_of(*strategies) if strategies else hs.just(u'')

    def add_category(self, category):
        '''
        Add unicode category to set

        Unicode categories are strings like 'Ll', 'Lu', 'Nd', etc.
        See `unicodedata.category()`
        '''
        if category == sre.CATEGORY_DIGIT:
            self._categories |= UNICODE_DIGIT_CATEGORIES
        elif category == sre.CATEGORY_NOT_DIGIT:
            self._categories |= UNICODE_CATEGORIES - UNICODE_DIGIT_CATEGORIES
        elif category == sre.CATEGORY_SPACE:
            self._categories |= UNICODE_SPACE_CATEGORIES
            for c in (UNICODE_SPACE_CHARS if self._unicode else SPACE_CHARS):
                self._whitelist_chars.add(c)
        elif category == sre.CATEGORY_NOT_SPACE:
            self._categories |= UNICODE_CATEGORIES - UNICODE_SPACE_CATEGORIES
            for c in (UNICODE_SPACE_CHARS if self._unicode else SPACE_CHARS):
                self._blacklist_chars.add(c)
        elif category == sre.CATEGORY_WORD:
            self._categories |= UNICODE_WORD_CATEGORIES
            self._whitelist_chars.add(u'_')
            if HAS_WEIRD_WORD_CHARS and self._unicode:
                for c in UNICODE_WEIRD_NONWORD_CHARS:
                    self._blacklist_chars.add(c)
        elif category == sre.CATEGORY_NOT_WORD:
            self._categories |= UNICODE_CATEGORIES - UNICODE_WORD_CATEGORIES
            self._blacklist_chars.add(u'_')
            if HAS_WEIRD_WORD_CHARS and self._unicode:
                for c in UNICODE_WEIRD_NONWORD_CHARS:
                    self._whitelist_chars.add(c)

    def add_chars(self, chars):
        'Add given chars to char set'
        for c in chars:
            if self._ignorecase:
                self._whitelist_chars.add(c.lower())
                self._whitelist_chars.add(c.upper())
            else:
                self._whitelist_chars.add(c)


@hs.defines_strategy
def regex(regex):
    """Return strategy that generates strings that match given regex.

    Regex can be either a string or compiled regex (through `re.compile()`).

    You can use regex flags (such as `re.IGNORECASE`, `re.DOTALL` or `re.UNICODE`)
    to control generation. Flags can be passed either in compiled regex (specify
    flags in call to `re.compile()`) or inside pattern with (?iLmsux) group.

    Some tricky regular expressions are partly supported or not supported at all.
    "^" and "$" do not affect generation. Positive lookahead/lookbehind groups
    are considered normal groups. Negative lookahead/lookbehind groups do not do
    anything. Ternary regex groups ('(?(name)yes-pattern|no-pattern)') are not
    supported at all.
    """
    encourage_user_to_update()
    if not hasattr(regex, 'pattern'):
        regex = re.compile(regex)

    pattern = regex.pattern
    flags = regex.flags

    codes = sre.parse(pattern)

    return _strategy(codes, Context(flags=flags)).filter(regex.match)


def _strategy(codes, context):
    """
    Convert SRE regex parse tree to strategy that generates strings matching that
    regex represented by that parse tree.

    `codes` is either a list of SRE regex elements representations or a particular
    element representation. Each element is a tuple of element code (as string) and
    parameters. E.g. regex 'ab[0-9]+' compiles to following elements:

        [
            ('literal', 97),
            ('literal', 98),
            ('max_repeat', (1, 4294967295, [
                ('in', [
                    ('range', (48, 57))
                ])
            ]))
        ]

    The function recursively traverses regex element tree and converts each element
    to strategy that generates strings that match that element.

    Context stores
    1. List of groups (for backreferences)
    2. Active regex flags (e.g. IGNORECASE, DOTALL, UNICODE, they affect behavior
       of various inner strategies)
    """
    if not isinstance(codes, tuple):
        # List of codes
        strategies = []

        i = 0
        while i < len(codes):
            if codes[i][0] == sre.LITERAL and not (context.flags & re.IGNORECASE):
                # Merge subsequent "literals" into one `just()` strategy
                # that generates corresponding text if no IGNORECASE
                j = i + 1
                while j < len(codes) and codes[j][0] == sre.LITERAL:
                    j += 1

                strategies.append(hs.just(
                    u''.join([six.unichr(charcode) for (_, charcode) in codes[i:j]])
                ))

                i = j
            else:
                strategies.append(_strategy(codes[i], context))
                i += 1

        return hs.tuples(*strategies).map(u''.join)
    else:
        # Single code
        code, value = codes
        if code == sre.LITERAL:
            # Regex 'a' (single char)
            c = six.unichr(value)
            if context.flags & re.IGNORECASE:
                return hs.sampled_from([c.lower(), c.upper()])
            else:
                return hs.just(c)

        elif code == sre.NOT_LITERAL:
            # Regex '[^a]' (negation of a single char)
            c = six.unichr(value)
            blacklist = set([c.lower(), c.upper()]) \
                if context.flags & re.IGNORECASE else [c]
            return hs.characters(blacklist_characters=blacklist)

        elif code == sre.IN:
            # Regex '[abc0-9]' (set of characters)
            charsets = value

            builder = CharactersBuilder(negate=charsets[0][0] == sre.NEGATE,
                                        flags=context.flags)

            for charset_code, charset_value in charsets:
                if charset_code == sre.NEGATE:
                    # Regex '[^...]' (negation)
                    pass
                elif charset_code == sre.LITERAL:
                    # Regex '[a]' (single char)
                    builder.add_chars(six.unichr(charset_value))
                elif charset_code == sre.RANGE:
                    # Regex '[a-z]' (char range)
                    low, high = charset_value
                    for x in six.moves.range(low, high+1):
                        builder.add_chars(six.unichr(x))
                elif charset_code == sre.CATEGORY:
                    # Regex '[\w]' (char category)
                    builder.add_category(charset_value)
                else:
                    raise he.InvalidArgument(
                        'Unknown charset code: %s' % charset_code
                    )

            return builder.strategy

        elif code == sre.ANY:
            # Regex '.' (any char)
            if context.flags & re.DOTALL:
                return hs.characters()
            else:
                return hs.characters(blacklist_characters="\n")

        elif code == sre.AT:
            # Regexes like '^...', '...$', '\bfoo', '\Bfoo'
            if value == sre.AT_END:
                return hs.one_of(hs.just(u''), hs.just(u'\n'))
            return hs.just('')

        elif code == sre.SUBPATTERN:
            # Various groups: '(...)', '(:...)' or '(?P<name>...)'
            old_flags = context.flags
            if HAS_SUBPATTERN_FLAGS:
                context.flags = (context.flags | value[1]) & ~value[2]

            strat = _strategy(value[-1], context)

            context.flags = old_flags

            if value[0]:
                context.groups[value[0]] = strat
                strat = hs.shared(strat, key=value[0])

            return strat

        elif code == sre.GROUPREF:
            # Regex '\\1' or '(?P=name)' (group reference)
            return hs.shared(context.groups[value], key=value)

        elif code == sre.ASSERT:
            # Regex '(?=...)' or '(?<=...)' (positive lookahead/lookbehind)
            return _strategy(value[1], context)

        elif code == sre.ASSERT_NOT:
            # Regex '(?!...)' or '(?<!...)' (negative lookahead/lookbehind)
            return hs.just('')

        elif code == sre.BRANCH:
            # Regex 'a|b|c' (branch)
            return hs.one_of([_strategy(branch, context) for branch in value[1]])

        elif code in [sre.MIN_REPEAT, sre.MAX_REPEAT]:
            # Regexes 'a?', 'a*', 'a+' and their non-greedy variants (repeaters)
            at_least, at_most, regex = value
            if at_most == 4294967295:
                at_most = None
            return hs.lists(_strategy(regex, context),
                            min_size=at_least,
                            max_size=at_most).map(''.join)

        elif code == sre.GROUPREF_EXISTS:
            # Regex '(?(id/name)yes-pattern|no-pattern)' (if group exists selection)
            return hs.one_of(
                _strategy(value[1], context),
                _strategy(value[2], context) if value[2] else hs.just(u''),
            )

        else:
            raise he.InvalidArgument('Unknown code point: %s' % repr(code))
