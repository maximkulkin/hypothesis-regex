import hypothesis_regex
import pytest
import re
import six.moves


def assert_can_generate(pattern):
    strategy = hypothesis_regex.regex(pattern)
    for _ in six.moves.range(100):
        s = strategy.example()
        assert re.match(pattern, s) is not None, \
            '"%s" supposed to match "%s" (strategy = %s)' % (s, pattern, strategy)


class TestRegexStrategy:
    def test_literals(self):
        assert_can_generate('abc')

    def test_any(self):
        assert_can_generate('.')

    def test_range(self):
        assert_can_generate('[a-z0-9_]')

    def test_negative_range(self):
        assert_can_generate('[^a-z0-9_]')

    def test_categories(self):
        assert_can_generate('\d')
        assert_can_generate('\D')
        assert_can_generate('\w')
        assert_can_generate('\W')
        assert_can_generate('\s')
        assert_can_generate('\S')

    def test_categories_in_range(self):
        assert_can_generate('[\d]')
        assert_can_generate('[\D]')
        assert_can_generate('[\w]')
        assert_can_generate('[\W]')
        assert_can_generate('[\s]')
        assert_can_generate('[\S]')

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

    def test_end(self):
        assert_can_generate('abc$')
