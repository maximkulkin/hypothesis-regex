import hypothesis as h
import hypothesis.errors as he

from hypothesis_regex import regex, UNICODE_CATEGORIES, UNICODE_DIGIT_CATEGORIES, \
    UNICODE_SPACE_CATEGORIES, UNICODE_WORD_CATEGORIES, UNICODE_WEIRD_NONWORD_CHARS, \
    SPACE_CHARS, UNICODE_SPACE_CHARS, HAS_WEIRD_WORD_CHARS
import pytest
import re
import six
import six.moves
import sys
import unicodedata


def is_ascii(s):
    return all(ord(c) < 128 for c in s)


def is_digit(s):
    return all(unicodedata.category(c) in UNICODE_DIGIT_CATEGORIES for c in s)


def is_space(s):
    return all(c in SPACE_CHARS for c in s)


def is_unicode_space(s):
    return all(
        unicodedata.category(c) in UNICODE_SPACE_CATEGORIES or \
        c in UNICODE_SPACE_CHARS
        for c in s
    )


def is_word(s):
    return all(
        c == '_' or (
            (not HAS_WEIRD_WORD_CHARS or c not in UNICODE_WEIRD_NONWORD_CHARS) and
            unicodedata.category(c) in UNICODE_WORD_CATEGORIES
        )
        for c in s
    )


def ascii_regex(pattern):
    flags = re.ASCII if six.PY3 else 0
    return re.compile(pattern, flags)


def unicode_regex(pattern):
    return re.compile(pattern, re.UNICODE)


class TestRegexUnicodeMatching:
    def _test_matching_pattern(self, pattern, isvalidchar, unicode=False):
        r = unicode_regex(pattern) if unicode else ascii_regex(pattern)

        codepoints = six.moves.range(0, sys.maxunicode+1) \
            if unicode else six.moves.range(1, 128)
        for c in [six.unichr(x) for x in codepoints]:
            if isvalidchar(c):
                assert r.match(c), (
                    '"%s" supposed to match "%s" (%r, category "%s"), '
                    'but it doesnt' % (pattern, c, c, unicodedata.category(c))
                )
            else:
                assert not r.match(c), (
                    '"%s" supposed not to match "%s" (%r, category "%s"), '
                    'but it does' % (pattern, c, c, unicodedata.category(c))
                )

    def test_matching_ascii_word_chars(self):
        self._test_matching_pattern(r'\w', is_word)

    def test_matching_unicode_word_chars(self):
        self._test_matching_pattern(r'\w', is_word, unicode=True)

    def test_matching_ascii_non_word_chars(self):
        self._test_matching_pattern(r'\W', lambda s: not is_word(s))

    def test_matching_unicode_non_word_chars(self):
        self._test_matching_pattern(r'\W', lambda s: not is_word(s), unicode=True)

    def test_matching_ascii_digits(self):
        self._test_matching_pattern(r'\d', is_digit)

    def test_matching_unicode_digits(self):
        self._test_matching_pattern(r'\d', is_digit, unicode=True)

    def test_matching_ascii_non_digits(self):
        self._test_matching_pattern(r'\D', lambda s: not is_digit(s))

    def test_matching_unicode_non_digits(self):
        self._test_matching_pattern(r'\D', lambda s: not is_digit(s), unicode=True)

    def test_matching_ascii_spaces(self):
        self._test_matching_pattern(r'\s', is_space)

    def test_matching_unicode_spaces(self):
        self._test_matching_pattern(r'\s', is_unicode_space, unicode=True)

    def test_matching_ascii_non_spaces(self):
        self._test_matching_pattern(r'\S', lambda s: not is_space(s))

    def test_matching_unicode_non_spaces(self):
        self._test_matching_pattern(r'\S', lambda s: not is_unicode_space(s),
                                    unicode=True)


def assert_all_examples(strategy, predicate):
    '''
    Checks that there are no examples with given strategy
    that do not match predicate.

    :param strategy: Hypothesis strategy to check
    :param predicate: (callable) Predicate that takes string example and returns bool
    '''
    @h.settings(max_examples=1000, max_iterations=5000)
    @h.given(strategy)
    def assert_examples(s):
        assert predicate(s),'Found %r using strategy %s which does not match' % (
            s, strategy,
        )

    assert_examples()


def assert_can_generate(pattern):
    '''
    Checks that regex strategy for given pattern generates examples
    that match that regex pattern
    '''
    compiled_pattern = re.compile(pattern)
    strategy = regex(pattern)

    assert_all_examples(strategy, compiled_pattern.match)


class TestRegexStrategy:
    @pytest.mark.parametrize('pattern', ['abc', '[a][b][c]'])
    def test_literals(self, pattern):
        assert_can_generate(pattern)

    @pytest.mark.parametrize('pattern', [re.compile('a', re.IGNORECASE), '(?i)a'])
    def test_literals_with_ignorecase(self, pattern):
        strategy = regex(pattern)

        h.find(strategy, lambda s: s == 'a')
        h.find(strategy, lambda s: s == 'A')

    def test_not_literal(self):
        assert_can_generate('[^a][^b][^c]')

    @pytest.mark.parametrize('pattern', [
        re.compile('[^a][^b]', re.IGNORECASE),
        '(?i)[^a][^b]'
    ])
    def test_not_literal_with_ignorecase(self, pattern):
        assert_all_examples(
            regex(pattern),
            lambda s: s[0] not in ('a', 'A') and s[1] not in ('b', 'B')
        )

    def test_any(self):
        assert_can_generate('.')

    def test_any_doesnt_generate_newline(self):
        assert_all_examples(regex('.'), lambda s: s != '\n')

    @pytest.mark.parametrize('pattern', [re.compile('.', re.DOTALL), '(?s).'])
    def test_any_with_dotall_generate_newline(self, pattern):
        h.find(regex(pattern), lambda s: s == '\n')

    def test_range(self):
        assert_can_generate('[a-z0-9_]')

    def test_negative_range(self):
        assert_can_generate('[^a-z0-9_]')

    @pytest.mark.parametrize('pattern', [r'\d', '[\d]', '[^\D]'])
    def test_ascii_digits(self, pattern):
        strategy = regex(ascii_regex(pattern))

        assert_all_examples(strategy, lambda s: is_digit(s) and is_ascii(s))

    @pytest.mark.parametrize('pattern', [r'\d', '[\d]', '[^\D]'])
    def test_unicode_digits(self, pattern):
        strategy = regex(unicode_regex(pattern))

        h.find(strategy, lambda s: is_digit(s) and is_ascii(s))
        h.find(strategy, lambda s: is_digit(s) and not is_ascii(s))

        assert_all_examples(strategy, is_digit)

    @pytest.mark.parametrize('pattern', [r'\D', '[\D]', '[^\d]'])
    def test_ascii_non_digits(self, pattern):
        strategy = regex(ascii_regex(pattern))

        assert_all_examples(strategy, lambda s: not is_digit(s) and is_ascii(s))

    @pytest.mark.parametrize('pattern', [r'\D', '[\D]', '[^\d]'])
    def test_unicode_non_digits(self, pattern):
        strategy = regex(unicode_regex(pattern))

        h.find(strategy, lambda s: not is_digit(s) and is_ascii(s))
        h.find(strategy, lambda s: not is_digit(s) and not is_ascii(s))

        assert_all_examples(strategy, lambda s: not is_digit(s))

    @pytest.mark.parametrize('pattern', [r'\s', '[\s]', '[^\S]'])
    def test_ascii_whitespace(self, pattern):
        strategy = regex(ascii_regex(pattern))

        assert_all_examples(strategy, lambda s: is_space(s) and is_ascii(s))

    @pytest.mark.parametrize('pattern', [r'\s', '[\s]', '[^\S]'])
    def test_unicode_whitespace(self, pattern):
        strategy = regex(unicode_regex(pattern))

        h.find(strategy, lambda s: is_unicode_space(s) and is_ascii(s))
        h.find(strategy, lambda s: is_unicode_space(s) and not is_ascii(s))

        assert_all_examples(strategy, is_unicode_space)

    @pytest.mark.parametrize('pattern', [r'\S', '[\S]', '[^\s]'])
    def test_ascii_non_whitespace(self, pattern):
        strategy = regex(ascii_regex(pattern))

        assert_all_examples(strategy, lambda s: not is_space(s) and is_ascii(s))

    @pytest.mark.parametrize('pattern', [r'\S', '[\S]', '[^\s]'])
    def test_unicode_non_whitespace(self, pattern):
        strategy = regex(unicode_regex(pattern))

        h.find(strategy, lambda s: not is_unicode_space(s) and is_ascii(s))
        h.find(strategy, lambda s: not is_unicode_space(s) and not is_ascii(s))

        assert_all_examples(strategy, lambda s: not is_unicode_space(s))

    @pytest.mark.parametrize('pattern', [r'\w', '[\w]', '[^\W]'])
    def test_ascii_word(self, pattern):
        strategy = regex(ascii_regex(pattern))

        assert_all_examples(strategy, lambda s: is_word(s) and is_ascii(s))

    @pytest.mark.parametrize('pattern', [r'\w', '[\w]', '[^\W]'])
    def test_unicode_word(self, pattern):
        strategy = regex(unicode_regex(pattern))

        h.find(strategy, lambda s: is_word(s) and is_ascii(s))
        h.find(strategy, lambda s: is_word(s) and not is_ascii(s))

        assert_all_examples(strategy, is_word)

    @pytest.mark.parametrize('pattern', [r'\W', '[\W]', '[^\w]'])
    def test_ascii_non_word(self, pattern):
        strategy = regex(ascii_regex(pattern))

        assert_all_examples(strategy, lambda s: not is_word(s) and is_ascii(s))

    @pytest.mark.parametrize('pattern', [r'\W', '[\W]', '[^\w]'])
    def test_unicode_non_word(self, pattern):
        strategy = regex(unicode_regex(pattern))

        h.find(strategy, lambda s: not is_word(s) and is_ascii(s))
        h.find(strategy, lambda s: not is_word(s) and not is_ascii(s))

        assert_all_examples(strategy, lambda s: not is_word(s))

    def test_question_mark_quantifier(self):
        assert_can_generate('ab?')

    def test_asterisk_quantifier(self):
        assert_can_generate('ab*')

    def test_plus_quantifier(self):
        assert_can_generate('ab+')

    def test_repeater(self):
        assert_can_generate('ab{5}')
        assert_can_generate('ab{5,10}')
        assert_can_generate('ab{,10}')
        assert_can_generate('ab{5,}')

    def test_branch(self):
        assert_can_generate('ab|cd|ef')

    def test_group(self):
        assert_can_generate('(foo)+')

    def test_group_backreference(self):
        assert_can_generate('([\'"])[a-z]+\\1')

    def test_non_capturing_group(self):
        assert_can_generate('(?:[a-z])([\'"])[a-z]+\\1')

    def test_named_groups(self):
        assert_can_generate('(?P<foo>[\'"])[a-z]+(?P=foo)')

    def test_begining(self):
        assert_can_generate('^abc')

    def test_caret_in_the_middle_does_not_generate_anything(self):
        r = re.compile('a^b')

        with pytest.raises(he.NoSuchExample):
            h.find(regex(r), r.match)

    def test_end(self):
        strategy = regex('abc$')

        h.find(strategy, lambda s: s == 'abc')
        h.find(strategy, lambda s: s == 'abc\n')

    def test_groupref_exists(self):
        assert_all_examples(
            regex('^(<)?a(?(1)>)$'),
            lambda s: s in ('a', 'a\n', '<a>', '<a>\n')
        )
        assert_all_examples(
            regex('^(a)?(?(1)b|c)$'),
            lambda s: s in ('ab', 'ab\n', 'c', 'c\n')
        )

    @pytest.mark.skipif(sys.version_info[:2] < (3, 6), reason='requires Python 3.6')
    def test_subpattern_flags(self):
        strategy = regex('(?i)a(?-i:b)')

        # "a" is case insensitive
        h.find(strategy, lambda s: s[0] == 'a')
        h.find(strategy, lambda s: s[0] == 'A')
        # "b" is case sensitive
        h.find(strategy, lambda s: s[1] == 'b')

        with pytest.raises(he.NoSuchExample):
            h.find(strategy, lambda s: s[1] == 'B')
